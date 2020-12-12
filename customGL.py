import numpy as np
import math
import pyrr
from PIL import Image
from PySide2.QtGui import QOpenGLFunctions
from PySide2.QtWidgets import QApplication, QMessageBox, QOpenGLWidget
from PySide2.QtCore import Signal, SIGNAL, SLOT, QTimer

try:
    from OpenGL.GL import *
    from OpenGL.GLUT import *
    from OpenGL.GL.shaders import compileProgram, compileShader
except ImportError:
    app = QApplication(sys.argv)
    messageBox = QMessageBox(QMessageBox.Critical, "OpenGL sample",
                                       "PyOpenGL must be installed to run this application. If you are seeing this, try what is in the 'show details' below." +
                                       "\nIf that fails, email me, please.",
                                       QMessageBox.Close)
    messageBox.setDetailedText("Run:\npip install PyOpenGL PyOpenGL_accelerate")
    messageBox.exec_()
    sys.exit(1)

class GLWidget(QOpenGLWidget, QOpenGLFunctions): # QOpenGLWidget, QOpenGLFunctions -> from qt examples | QtOpenGL.QGLWidget
    """
    Custom GL Widget class
    """
    # signals that are emitted from the rotation sliders
    xRotationChanged = Signal(int)
    yRotationChanged = Signal(int)
    zRotationChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setGeometry(180, 30, 1091, 591) # sets the geometry of the OpenGL window area

        # The shapes that we can draw -> maybe eventually allow user to create shapes (hard/time-consuming)
        self.shapes = [None, None, None, None] # array of the current shapes
        self.shapeIndex = 0 # used to get the current shape from the UI

        self.surfaceColor = (1.0, 1.0, 0.0, 1.0) #RGBA -> Yellow
        self.edgeColor = (0.0, 0.0, 1.0, 1.0) #RGBA -> Blue

        self.animate = True # stores whether or not to play rotation/animation this each frame -> set from parent UI
        self.textureMode = False # used to decide whether we draw colors or textures on shapes -> set from parent UI
        self.rainbowMode = False # rainbow mode means we color every vertex on the shape an RNG color each frame -> set from parent UI

        # define the current rotations and rotation speeds for each axis (x,y,z)
        self.x_rot_speed = 0
        self.x_shape_rot = 0
        self.y_rot_speed = 0
        self.y_shape_rot = 0
        self.z_rot_speed = 0
        self.z_shape_rot = 0

    """
    Helpers
    """
    def setSurfaceColor(self, color):
        """Set the color of the current object RGBA"""
        self.surfaceColor = color

    def setEdgeColor(self, color):
        """Set the color of the current object RGBA"""
        self.edgeColor = color

    def toggleAnimation(self):
        """Toggles the animation playback"""
        self.animate = not self.animate

    def setCurrentShape(self, index):
        """Sets the index of the current shape in the shapes array"""
        self.shapeIndex = index

    def toggleRainbowMode(self):
        """Toggles rainbow mode"""
        self.rainbowMode = not self.rainbowMode
    
    """
    Open GL Functions
    """
    def initializeGL(self):
        """
        Set up the rendering context, define display lists etc.
        This is where we can init multiple shape items depending on design
        """
        glEnable(GL_DEPTH_TEST) # enable or disable server-side GL capabilities -> The Depth Test is a per-sample processing operation performed after the Fragment Shader (and sometimes before). 
        glEnable(GL_NORMALIZE) # enable or disable server-side GL capabilities -> calculates the unit vector in the same direction as the original vector
        glClearColor(0.0, 0.0, 0.0, 1) # NOTE: background of the GL viewport

        #NOTE: IMPORTANT initialize all of our shapes
        self.shapes[0] = self.makeCube() # make a cube and store it in index 0 of the shapes array
        self.shapes[1] = self.makePyramid() # make a pyramid and store it in index 1 of the shapes array
        self.shapes[2] = self.makeTetrahedron() # make a tetreahedron and store it in index 2 of the shapes array
        self.shapes[3] = self.makeOctahedron() # make an octahedron and store it in index 3 of the shapes array

        #NOTE: This is effectively the main loop -> we establish a 10ms callback that calls self.step() that will process animations/rotations over that time
        timer = QTimer(self)
        timer.timeout.connect(self.step)
        timer.start(10)

        #NOTE: Testing these for transparency --> seems to work okay... more here: https://stackoverflow.com/questions/1617370/how-to-use-alpha-transparency-in-opengl
        # glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA) 
        # glEnable(GL_BLEND)

    def paintGL(self):
        """Called very often, mostly when we call self.updateGL(), but also on resize events and other things (see docs)"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT) #  clear buffers to preset values
        glPushMatrix() # push and pop the current matrix stack
        self.drawShape(self.shapes[self.shapeIndex], 0, 0, 0.0, #was (-1, -1, 0) #NOTE: this is how we can offset the location of shapes if we want multiple
            (self.x_shape_rot, self.y_shape_rot, self.z_shape_rot))
        glPopMatrix() # push and pop the current matrix stack

    def resizeGL(self, width, height):
        """basic resize handlings, viewport, etc."""

        # This virtual function is called whenever the widget has been resized. Reimplement it in a subclass. 
        # The new size is passed in w and h. There is no need to call makeCurrent() because this has already 
        # been done when this function is called. Additionally, the framebuffer is also bound.

        side = min(width, height)
        if side < 0:
            return

        glViewport(int((width - side) / 2), int((height - side) / 2), side, side) # establish the viewport (x,y,w,h) see: https://www.khronos.org/registry/OpenGL-Refpages/gl4/html/glViewport.xhtml
        glMatrixMode(GL_PROJECTION) # Specifies which matrix stack is the target for subsequent matrix operations
        glLoadIdentity() # glLoadIdentity replaces the current matrix with the identity matrix
        glFrustum(-1.2, +1.2, -1.2, 1.2, 6.0, 70.0) # glFrustum — multiply the current matrix by a perspective matrix
        glMatrixMode(GL_MODELVIEW) # Specifies which matrix stack is the target for subsequent matrix operations
        glLoadIdentity() # glLoadIdentity replaces the current matrix with the identity matrix
        glTranslated(0.0, 0.0, -30.0) # multiply the current matrix by a translation matrix

    def freeResources(self):
        """cleans out resources/list for our shapes so we dont have garbage :)"""

        #Makes the context current in the current thread, against the given surface. Returns true if successful; otherwise returns false. 
        #The latter may happen if the surface is not exposed, or the graphics hardware is not available due to e.g. the application being suspended. - QT docs
        self.makeCurrent()

        # for each of our shapes, delete their respective GLList with a range of 1
        for shape in self.shapes:
            glDeleteLists(shape, 1) # delete a contiguous group of display lists

    """
    Rotation Functions
    """
    # slots
    def setXRotSpeed(self, speed):
        """Set the X-axis rotation speed for the current shape"""
        self.x_rot_speed = speed

    def setYRotSpeed(self, speed):
        """Set the X-axis rotation speed for the current shape"""
        self.y_rot_speed = speed

    def setZRotSpeed(self, speed):
        """Set the X-axis rotation speed for the current shape"""
        self.z_rot_speed = speed

    def step(self):
        """Move the shape one step forward via timer"""
        #NOTE: we ideally would implement Quaternions here so we are not gimbal locked half the time :)
        if self.animate: # if we are in animation mode
            self.x_shape_rot += (self.x_rot_speed / 20) % 360 # our current rotation + the new rotation amount modulo 360
            self.y_shape_rot += (self.y_rot_speed / 20) % 360 # our current rotation + the new rotation amount modulo 360
            self.z_shape_rot += (self.z_rot_speed / 20) % 360 # our current rotation + the new rotation amount modulo 360
            self.update() # call update

    """
    Shape Functions
    """
    def makePyramid(self):
        """Makes a square base pyramid with 4 traingle sides"""
        list = glGenLists(1)
        glNewList(list, GL_COMPILE)

        #NOTE: The 5 vertices of the pyramid
        verticies = (
            (0, 1, 0),      #tip
            (1, -1, 1),     #front right
            (1, -1, -1),    #back right
            (-1, -1, -1),   #back left
            (-1, -1, 1)     #front left
        )

        #NOTE: The 8 edges of the pyramid
        edges = (
            (0, 1), # tip -> front right
            (0, 2), # tip -> back right
            (0, 3), # tip -> back left
            (0, 4), # tip -> front left
            (1, 2), # front right -> back right
            (2, 3), # back right -> back left
            (3, 4), # back left -> front left
            (4, 1)  # front left -> front right
        )

        #NOTE: The 4 traingular faces of the pyramid
        triSurfaces = (
            (0, 1, 2), # tip -> front right -> back right
            (0, 2, 3), # tip -> back right -> back left
            (0, 3, 4), # tip -> back left -> front left
            (0, 4, 1), # tip -> front left -> front right
        )

        #NOTE: The 1 square base of the pyramid
        baseSurface = (1, 2, 3, 4) # front right -> back right -> back left -> front left
        
        # draw the edges (8)
        glBegin(GL_LINES)
        glColor4fv(self.edgeColor)
        for edge in edges:
            for vertex in edge:
                glVertex3fv(verticies[vertex])
        glEnd()

        # draw the triangle surfaces (4)
        glBegin(GL_TRIANGLES)
        glColor4fv(self.surfaceColor)
        for surface in triSurfaces: 
            for vertex in surface:
                glVertex3fv(verticies[vertex])
        glEnd()

        # draw the square base (1)
        glBegin(GL_QUADS)
        glColor4fv(self.surfaceColor)
        for vertex in baseSurface:
            glVertex3fv(verticies[vertex])
        glEnd()

        glEndList()

        return list
        
    def makeCube(self):
        """Makes a cube"""
        list = glGenLists(1)
        glNewList(list, GL_COMPILE)

        # the 8 vertices of the cube
        verticies = (
            (1, -1, -1),
            (1, 1, -1),
            (-1, 1, -1),
            (-1, -1, -1),
            (1, -1, 1),
            (1, 1, 1),
            (-1, -1, 1),
            (-1, 1, 1)
        )

        # the 12 edges of the cube
        edges = (
            (0, 1),
            (0, 3),
            (0, 4),
            (2, 1),
            (2, 3),
            (2, 7),
            (6, 3),
            (6, 4),
            (6, 7),
            (5, 1),
            (5, 4),
            (5, 7)
        )

        # the 6 surfaces of the cube
        surfaces = (
            (0, 1, 2, 3),
            (3, 2, 7, 6),
            (6, 7, 5, 4),
            (4, 5, 1, 0),
            (1, 5, 7, 2),
            (4, 0, 3, 6)
        )

        # draw the edges of the cube
        glBegin(GL_LINES)
        glColor4fv(self.edgeColor)
        for edge in edges:
            for vertex in edge:
                glVertex3fv(verticies[vertex])
        glEnd()

        # draw the surfaces of the cube
        glBegin(GL_QUADS)
        glColor4fv(self.surfaceColor)
        for surface in surfaces:
            for vertex in surface:
                glVertex3fv(verticies[vertex])
        glEnd()

        glEndList()

        return list
    
    def makeTetrahedron(self):
        """Makes a tetrahedron"""
        list = glGenLists(1)
        glNewList(list, GL_COMPILE)

        #NOTE: The 4 vertices of the -> see: https://en.wikipedia.org/wiki/Tetrahedron | # 1.63299316186 == side length before normalize == math.sqrt(8/3)
        normalizer = math.sqrt(3/8)*2.5 #NOTE: this scales the shape to match the size of our other shapes (or close to)
        n = normalizer #NOTE: this is just so our vertex definitions are long
        verticies = (
            (math.sqrt(8/9) * n , 0, -1/3 * n),
            (- math.sqrt(2/9) * n, math.sqrt(2/3) * n, -1/3 * n),
            (- math.sqrt(2/9) * n, - math.sqrt(2/3) * n, -1/3 * n),
            (0, 0, 1 * n)
        )

        #NOTE: The 6 edges of the tetrahedron
        edges = (
            (0, 1),
            (0, 2), 
            (0, 3), 
            (1, 2), 
            (1, 3),
            (2, 3)
        )

        #NOTE: The 4 traingular faces of the tetrahedron
        surfaces = (
            (0, 1, 2),
            (0, 1, 3),  
            (0, 2, 3), 
            (1, 2, 3) 
        )

        # draw the edges (6)
        glBegin(GL_LINES)
        glColor4fv(self.edgeColor)
        for edge in edges:
            for vertex in edge:
                glVertex3fv(verticies[vertex])
        glEnd()

        # draw the triangle surfaces (4)
        glBegin(GL_TRIANGLES)
        glColor4fv(self.surfaceColor)
        for surface in surfaces: # for each of the triangle surfaces
            for vertex in surface:
                glVertex3fv(verticies[vertex])
        glEnd()

        glEndList()

        return list

    def makeOctahedron(self):
        """
        An octahedron with edge length √2 can be placed with its center at the origin and 
        its vertices on the coordinate axes; the Cartesian coordinates of the vertices are then
        ( ±1, 0, 0 );
        ( 0, ±1, 0 );
        ( 0, 0, ±1 ).
        """
        list = glGenLists(1)
        glNewList(list, GL_COMPILE)

        #NOTE: The 6 vertices of the octahedron
        verticies = (
            (0, 1, 0),      #top tip
            (1, 0, 1),     #front right
            (1, 0, -1),    #back right
            (-1, 0, -1),   #back left
            (-1, 0, 1),    #front left
            (0, -1, 0)      #bottom tip
        )

        #NOTE: The 12 edges of the pyramid
        edges = (
            (0, 1),     # top tip -> front right
            (0, 2),     # top tip -> back right
            (0, 3),     # top tip -> back left
            (0, 4),     # top tip -> front left
            (1, 2),     # front right -> back right
            (2, 3),     # back right -> back left
            (3, 4),     # back left -> front left
            (4, 1),     # front left -> front right
            (5, 1),     # bottom tip -> front right
            (5, 2),     # bottom tip -> back right
            (5, 3),     # bottom tip -> back left
            (5, 4)      # bottom tip -> front left
        )

        #NOTE: The 8 traingular faces of the octahedron
        triSurfaces = (
            (0, 1, 2),  # top tip -> front right -> back right
            (0, 2, 3),  # top tip -> back right -> back left
            (0, 3, 4),  # top tip -> back left -> front left
            (0, 4, 1),  # top tip -> front left -> front right
            (5, 1, 2),  # bottom tip -> front right -> back right
            (5, 2, 3),  # bottom tip -> back right -> back left
            (5, 3, 4),  # bottom tip -> back left -> front left
            (5, 4, 1)   # bottom tip -> front left -> front right
        )

        # draw the edges (12)
        glBegin(GL_LINES)
        glColor4fv(self.edgeColor)
        for edge in edges:
            for vertex in edge:
                glVertex3fv(verticies[vertex])
        glEnd()

        # draw the triangle surfaces (8)
        glBegin(GL_TRIANGLES)
        glColor4fv(self.surfaceColor)
        for surface in triSurfaces: # for each of the triangle surfaces
            for vertex in surface:
                glVertex3fv(verticies[vertex])
        glEnd()

        glEndList()

        return list

    #NOTE: TODO
    def makeIcosahedron(self):
        """
        The vertices of an icosahedron centered at the origin with an edge-length 
        of 2 and a circumradius of ϕ + 2 ≈ 1.9 are described by circular permutations of:
        (0, ±1, ±ϕ)
        where ϕ = 1 + √5/2 is the golden ratio. 
        """
        pass
        
    #NOTE: TODO
    def makeDodecahedron(self):
        #NOTE: -> glutSolidDodecahedron()
        """NOTE: The Math
        (±1, ±1, ±1)
        (0, ±1/φ, ±φ)
        (±1/φ, ±φ, 0)
        (±φ, 0, ±1/φ)
        where φ = (1 + √5) / 2 is the golden ratio (also written τ) ≈ 1.618. 
        The edge length is 2/φ = √5 – 1. The containing sphere has a radius of √3.
        """
        """Makes a tetrahedron"""
        pass

    #NOTE: TODO
    def makeSphere(self):
        pass

    #NOTE: TODO
    def makeTorus(self):
        pass

    def drawShape(self, shape, dx, dy, dz, rotation):
        """Helper to translate, rotate and draw the shape."""
        if self.textureMode:
            #NOTE: THIS WILL BE USED FOR TEXTURE MODES
            pass
        else:
            # this draws the current shape from th shapes array depending on the shape index, which comes from the main UI "shapeComboBox"
            if self.shapeIndex == 0:
                self.shapes[self.shapeIndex] = self.makeCube()
            elif self.shapeIndex == 1:
                self.shapes[self.shapeIndex] = self.makePyramid()
            elif self.shapeIndex == 2:
                self.shapes[self.shapeIndex] = self.makeTetrahedron()
            elif self.shapeIndex == 3:
                self.shapes[self.shapeIndex] = self.makeOctahedron()
            
            glPushMatrix()
            if self.animate:
                glTranslated(dx, dy, dz)
                glRotated(rotation[0], 1.0, 0.0, 0.0)
                glRotated(rotation[1], 0.0, 1.0, 0.0)
                glRotated(rotation[2], 0.0, 0.0, 1.0)
            glCallList(shape)
            glPopMatrix()

    """
    Texture Fuctions
    """
    #NOTE: TODO
    def loadTexture(self):
        pass

    #NOTE: TODO
    def applyTexture(self):
        pass
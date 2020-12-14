"""NOTE: IMPORTANT
BUILD NEW UI COMMAND:
pyside2-uic mainwindow.ui > ui_mainwindow.py
PYINSTALLER BUILD COMMAND:
pyinstaller --name="3DGraphicsApp" --windowed --onefile 3DApp.py
"""
import sys
from PySide2.QtWidgets import QApplication, QMainWindow, QSlider

#importing UI class files from QT Creator with pyside2-uic
from ui_mainwindow import Ui_MainWindow

#custom classes
from customGL import GLWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        """
        Basic Configurations
        """
        self.ui = Ui_MainWindow() # the mainwindow UI
        self.ui.setupUi(self) # configure the UI
        title = "3D Graphics Tool" # set the window title
        self.setWindowTitle(title) # set the window title
        self.statusBar().showMessage("Select a shape!") # status bar (at the bottom left)

        """
        UI Bindings 
        """
        # Load our custom Open GL Widget
        self.glWidget = GLWidget(self)

        """
        Basic Labels
        """
        # Select shape label
        self.shapeComboBoxLabel = self.ui.shapeComboBoxLabel
        
        # Surface Sliders Label
        self.surfaceSlidersLabel = self.ui.surfaceSlidersLabel

        # Edge Sliders label
        self.edgeSlidersLabel = self.ui.edgeSlidersLabel

        # Extras label
        self.extrasLabel = self.ui.extrasLabel

        # Select shape combo box
        self.shapeComboBox = self.ui.shapeComboBox
        self.shapeComboBoxLabel = self.ui.shapeComboBoxLabel

        # Rotation sliders -> each of these calls self.setupSlider() which configures the basics for them, as well as binds their emit signals to slot functions
        self.xRotSlider = self.setupSlider(self.ui.xRotSlider, self.glWidget.xRotationChanged, self.glWidget.setXRotSpeed)
        self.yRotSlider = self.setupSlider(self.ui.yRotSlider, self.glWidget.yRotationChanged, self.glWidget.setYRotSpeed)
        self.zRotSlider = self.setupSlider(self.ui.zRotSlider, self.glWidget.zRotationChanged, self.glWidget.setZRotSpeed)

        # Rotation sliders default values
        self.xRotSlider.setValue(5)
        self.yRotSlider.setValue(5)
        self.zRotSlider.setValue(0)

        # rainbow mode radio button
        self.rainbowModeRadioButton = self.ui.rainbowModeRadioButton
        
        # toggle animation push button 
        self.toggleAnimationPushButton = self.ui.toggleAnimationPushButton

        """
        Surface Sliders -> each of the 4 sliders on the left of the UI that control the color of the surfaces
        """
        #RED
        self.redSlider = self.ui.redSlider
        self.redSliderLabel = self.ui.redSliderLabel
        self.redSlider.setValue(255)

        #GREEN
        self.greenSlider = self.ui.greenSlider
        self.greenSliderLabel = self.ui.greenSliderLabel
        self.greenSlider.setValue(255)

        #BLUE
        self.blueSlider = self.ui.blueSlider
        self.blueSliderLabel = self.ui.blueSliderLabel
        self.blueSlider.setValue(0)

        #ALPHA
        self.alphaSlider = self.ui.alphaSlider
        self.alphaSliderLabel = self.ui.alphaSliderLabel
        self.alphaSlider.setValue(255) #NOTE: start max

        """
        Edge Sliders -> each of the 4 sliders on the left of the UI that control to color of the edges
        """
        #RED
        self.redEdgeSlider = self.ui.redEdgeSlider
        self.redEdgeSliderLabel = self.ui.redEdgeSliderLabel
        self.redEdgeSlider.setValue(0)

        #GREEN
        self.greenEdgeSlider = self.ui.greenEdgeSlider
        self.greenEdgeSliderLabel = self.ui.greenEdgeSliderLabel
        self.greenEdgeSlider.setValue(0)

        #BLUE
        self.blueEdgeSlider = self.ui.blueEdgeSlider
        self.blueEdgeSliderLabel = self.ui.blueEdgeSliderLabel
        self.blueEdgeSlider.setValue(255)

        #ALPHA
        self.alphaEdgeSlider = self.ui.alphaEdgeSlider
        self.alphaEdgeSliderLabel = self.ui.alphaEdgeSliderLabel
        self.alphaEdgeSlider.setValue(255) #NOTE: start max

        """
        Rainbow mode
        """
        # rainbow mode speed slider
        self.rainbowModeSpeedSlider = self.ui.rainbowModeSpeedSlider
        self.rainbowModeSpeedSlider.setValue(30) #start close to mid speed
        self.rainbowModeSpeedSliderLabel = self.ui.rainbowModeSpeedSliderLabel
        
        """
        Signals & Slots | UI functions
        """
        # select shape -> calls the onShapeComboBoxCurrentIndexChnaged() function
        self.shapeComboBox.currentIndexChanged.connect(self.onShapeComboBoxCurrentIndexChanged)

        # connect the surface color sliders to their respective value change signal functions
        # these are called whener the slider value changes, and they call their respective
        # on "color" value changed functions
        self.redSlider.valueChanged.connect(self.onRedSliderValueChanged)
        self.greenSlider.valueChanged.connect(self.onGreenSliderValueChanged)
        self.blueSlider.valueChanged.connect(self.onBlueSliderValueChanged)
        self.alphaSlider.valueChanged.connect(self.onAlphaSliderValueChanged)

        # connect the edge color sliders to their respective value change signal functions
        # these are called whener the slider value changes, and they call their respective
        # on "color" value changed functions
        self.redEdgeSlider.valueChanged.connect(self.onRedEdgeSliderValueChanged)
        self.greenEdgeSlider.valueChanged.connect(self.onGreenEdgeSliderValueChanged)
        self.blueEdgeSlider.valueChanged.connect(self.onBlueEdgeSliderValueChanged)
        self.alphaEdgeSlider.valueChanged.connect(self.onAlphaEdgeSliderValueChanged)

        # rainbow mode -> calls onRainbowModeRadioButtonToggled()
        # this sets the shape to use RNG colors for each vertex each frame
        self.rainbowModeRadioButton.toggled.connect(self.onRainbowModeRadioButtonToggled)

        # rainbow mode speed -> calls onRainbowModeSpeedSliderValueChanged()
        # this adjusts the speed of the repaints for rainbow mode
        self.rainbowModeSpeedSlider.valueChanged.connect(self.onRainbowModeSpeedSliderValueChanged)
        
        # toggle animation -> calls the onToggleAnimationPushButtonToggled() function
        self.toggleAnimationPushButton.clicked.connect(self.onToggleAnimationPushButtonToggled)
        
    def setupSlider(self, slider, changedSignal, setterSlot):
        """Configure a slider for the UI (range, step, etc.) and signals/slots"""
        slider.setRange(0, 100) # set the range of the slider
        slider.setSingleStep(1) # set the single step
        slider.setPageStep(1)   # set the page step
        slider.setTickInterval(5) # set the distance between each tick
        slider.setTickPosition(QSlider.TicksRight) # set the tick position

        slider.valueChanged.connect(setterSlot) # connect the value changed parameter to the setter slot paramer (this is whats called when the value changes)
        changedSignal.connect(slider.setValue) # connect the changed signal to setValue

        return slider

    """
    General Sliders and Buttons: shapes, rainbow mode, toggle animation, etc.
    """
    def onShapeComboBoxCurrentIndexChanged(self):
        """Called when the shape combobox index changes"""
        self.glWidget.setCurrentShape(self.shapeComboBox.currentIndex()) # update our GL Widget shape index

    def onRainbowModeRadioButtonToggled(self):
        """Called when the rainbow mode radiobutton is toggled"""
        self.glWidget.toggleRainbowMode() # Toggle the GL Widgets rainbow mode boolean

    def onRainbowModeSpeedSliderValueChanged(self):
        """Adjusts the speed of rainbow mode"""
        self.glWidget.setRainbowModeSpeed(self.rainbowModeSpeedSlider.value()) # set the value of the slider as the speed of the gl widgets rainbow mode value

    def onToggleAnimationPushButtonToggled(self):
        """Called when the toggle animation pushbutton is toggled"""
        self.glWidget.toggleAnimation() # toggle animation playback on our GL Widget

    """
    Surface Color Sliders
    """
    def onRedSliderValueChanged(self):
        """Called when the red surface color slider changes"""
        self.glWidget.setSurfaceColor(self.getSurfaceColor()) # update the surface color of the OpenGL widget
    
    def onGreenSliderValueChanged(self):
        """Called when the green surface color slider changes"""
        self.glWidget.setSurfaceColor(self.getSurfaceColor()) # update the surface color of the OpenGL widget
    
    def onBlueSliderValueChanged(self):
        """Called when the blue surface color slider changes"""
        self.glWidget.setSurfaceColor(self.getSurfaceColor()) # update the surface color of the OpenGL widget
    
    def onAlphaSliderValueChanged(self):
        """Called when the alpha surface slider changes"""
        self.glWidget.setSurfaceColor(self.getSurfaceColor()) # update the surface color of the OpenGL widget

    """
    Edge Color Sliders
    """
    def onRedEdgeSliderValueChanged(self):
        """Called when the red edge color slider changes"""
        self.glWidget.setEdgeColor(self.getEdgeColor()) # update the edge color of the OpenGL widget
    
    def onGreenEdgeSliderValueChanged(self):
        """Called when the green edge color slider changes"""
        self.glWidget.setEdgeColor(self.getEdgeColor()) # update the edge color of the OpenGL widget
    
    def onBlueEdgeSliderValueChanged(self):
        """Called when the blue edge color slider changes"""
        self.glWidget.setEdgeColor(self.getEdgeColor()) # update the edge color of the OpenGL widget
    
    def onAlphaEdgeSliderValueChanged(self):
        """Called when the alpha edge slider changes"""
        self.glWidget.setEdgeColor(self.getEdgeColor()) # update the edge color of the OpenGL widget

    def getSurfaceColor(self) -> tuple:
        """Gets the current surface color from the UI and returns RGBA with each val between 0-1"""
        # get the current slider values
        r = self.redSlider.value()
        g = self.greenSlider.value()
        b = self.blueSlider.value()
        a = self.alphaSlider.value()

        # convert these to between 0 - 1 (i.e. divide by 255 if they are not already 0)
        r = r / 255.0 if r else 0 
        g = g / 255.0 if g else 0
        b = b / 255.0 if b else 0
        a = a / 255.0 if a else 0

        return (r, g, b, a)

    def getEdgeColor(self) -> tuple:
        """Gets the current edge color from the UI and returns RGBA with each val between 0-1"""
        # get the current slider values
        r = self.redEdgeSlider.value()
        g = self.greenEdgeSlider.value()
        b = self.blueEdgeSlider.value()
        a = self.alphaEdgeSlider.value()

        # convert these to between 0 - 1 (i.e. divide by 255 if they are not already 0)
        r = r / 255.0 if r else 0 
        g = g / 255.0 if g else 0
        b = b / 255.0 if b else 0
        a = a / 255.0 if a else 0

        return (r, g, b, a)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    res = app.exec_()
    mainWin.glWidget.freeResources() #NOTE: don't forget to free those resources :)
    sys.exit(res)
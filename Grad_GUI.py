"""
This is a GUI wrapper for the existing gradiometer functionality implemented in Gradiometer.py
It is based on pyqt, and have functionality for calibration, time runs and position runs
"""

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
import matplotlib
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg
import threading
import atexit
import time
import json
import sys
import numpy as np

# This is for remote development. If true it will be able to be used without physical access to the gradiometer
# Note this is only for testing, if this is set to true the GUI will not be functional
remoteDev = False

if not remoteDev:
    from Gradiometer import Gradiometer

# Enables matplotlib with pyqt
matplotlib.use('Qt5Agg')


# This is global variable since otherwise it goes out of scope in TaskSelectDialog
mainWindow = None


def initGrad():
    """Initializes gradiometer and sets atext functions for safe usage
    Only call this function once as only one gradiometer can be created

    Returns:
        Gradiometer: gradiometer that has just been initialized
    """
    g = Gradiometer()
    atexit.register(g.motor.turnOffMotors)
    atexit.register(g.savePos)
    atexit.register(g.labjack.close)
    return g


class TaskSelectDialog(QDialog):
    """Initial Dialog class for GUI"""

    class TaskTypes():
        """Enum for types of tasks to open"""
        cal = 'Calibration'
        posRun = 'Position Run'
        timeRun = 'Time Run'

    def __init__(self, parent=None):
        """Initializes new opening dialog

        Args:
            parent: parent element. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle('Gradiometer GUI')
        layout = QVBoxLayout()
        formLayout = QFormLayout()

        # Selection box for different tasks
        taskSelection = QComboBox()
        taskSelection.addItem(self.TaskTypes.cal)
        taskSelection.addItem(self.TaskTypes.posRun)
        taskSelection.addItem(self.TaskTypes.timeRun)

        formLayout.addRow('Task:', taskSelection)
        layout.addLayout(formLayout)

        btns = QDialogButtonBox()
        btns.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        layout.addWidget(btns)

        # Register button click events
        btns.button(QDialogButtonBox.Cancel).clicked.connect(
            lambda: sys.exit())
        btns.button(QDialogButtonBox.Ok).clicked.connect(
            lambda: self.startMain(taskSelection.currentText()))
        self.setLayout(layout)

    def startMain(self, taskType):
        """Starts the main application of the appropriate type

        Args:
            taskType (str): The type of task to start, given by TaskTypes enum
        """
        global mainWindow
        if taskType == self.TaskTypes.cal:
            mainWindow = CalibrationWindow()
            mainWindow.show()
        elif taskType == self.TaskTypes.posRun:
            mainWindow = RunWindow(RunWindow.RunModes.pos)
            mainWindow.showMaximized()
        elif taskType == self.TaskTypes.timeRun:
            mainWindow = RunWindow(RunWindow.RunModes.time)
            mainWindow.showMaximized()

        self.close()


class CalibrationWindow(QMainWindow):
    """Main window for calibration task"""

    # Variable for calibration distance, might want to change later
    calDist = 80

    def __init__(self, parent=None):
        """Initializes calibration windows.

        Args:
            parent: parent element for QT. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle('Gradiometer Calibration')
        self.setFixedSize(700, 400)
        self.generalLayout = QVBoxLayout()
        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)
        self._centralWidget.setLayout(self.generalLayout)
        # Since window isn't maximized have to set margins or else becomes too small
        self.generalLayout.setContentsMargins(50, 50, 50, 50)
        self.layoutInstructions()

    def layoutInstructions(self):
        """Lays out instructions for calibration"""
        self.title = QLabel('<h1>Calibration Instructions</h2>')
        self.title.setAlignment(Qt.AlignCenter)
        self.generalLayout.addWidget(self.title)

        self.intro = QLabel(
            '<p>This will calibrate the spacing for the stepper motor belt that tends to fluctate daily.</p>')
        self.intro.setWordWrap(True)
        self.generalLayout.addWidget(self.intro)

        self.instructions = QLabel(
            '<p>First, move the fluxgate to the far motor end of the gradiometer and mark the location on the frame so you can references this as the zero point. When done click on the button below. </p>')
        self.instructions.setWordWrap(True)
        self.generalLayout.addWidget(self.instructions)

        self.finishButton = QPushButton("Finished")
        self.finishButton.clicked.connect(self.layoutMeasurement)
        self.generalLayout.addWidget(self.finishButton)

    def layoutMeasurement(self):
        """Lays out UI for taking measurement, to be called after layoutInstructions"""
        self.finishButton.setParent(None)
        self.intro.setText(
            "<p>We will now take the calibration measurement</p>")
        self.instructions.setText(
            "<p>The gradiometer carriage should now move approximately {}cm. Once it's done, take a tape measure and measure this distance precisely. Your measurement will be used to calibrate future step sizes. Enter the measured distance in cm in the space below (will appear when motor finishes moving). </p>".format(self.calDist))

        # Sets up thread for moving the gradiometer so UI thread doesn't block
        if not remoteDev:
            self.gradiometer = initGrad()
            self.gradiometer.zero()

        def goToThread():
            """Helper function that wraps gradiometer running
            """
            if not remoteDev:
                self.steps = self.gradiometer.goTo(self.calDist)
            else:
                self.steps = 700

        # Start physical movement thread
        thread = threading.Thread(target=goToThread)
        thread.start()

        self.distance = QDoubleSpinBox()
        self.distance.setAlignment(Qt.AlignCenter)
        self.generalLayout.addWidget(self.distance)

        def nextScreen():
            """Helper function that wraps calling both calibrate and layout confirmation at once
            """
            if not thread.is_alive():
                self.calibrate(self.distance.value(), self.steps)
                self.layoutConfirmation()

        self.distanceButton = QPushButton("Submit")
        self.distanceButton.clicked.connect(nextScreen)
        self.generalLayout.addWidget(self.distanceButton)

    def calibrate(self, actualDistance, steps):
        """Configures calibration of the gradiometer
        Writes to the file config.json

        Args:
            actualDistance (double): actual distance the gradiometer travelled
            steps (int): Number of steps taken
        """
        with open('./config.json') as f:
            data = json.load(f)
            data["CM_PER_STEP"] = self.calDist/steps
        # Not sure if there's a nice way of not having to open it twice, doesn't look super aesthetically pleasing
        with open('./config.json', 'w') as f:
            # Note: some idiot decided that json.dumps is different from json.dump, be careful if you replicate this elsewhere
            json.dump(data, f)

    def layoutConfirmation(self):
        """Lays out UI for outro, to be called after layoutMeasurement"""
        self.distance.setParent(None)
        self.distanceButton.setParent(None)

        self.intro.setText("<p>All done!</p>")
        self.instructions.setText(
            "<p>Calibration data has been written to file, and you can start measurements now.</p>")

        self.finishButton = QPushButton("Exit")
        self.finishButton.clicked.connect(lambda: sys.exit())
        self.generalLayout.addWidget(self.finishButton)


class RunWindow(QMainWindow):
    """Main class for position runs"""

    # Keeps track of if graph has been initialized
    initGraph = False
    # Gradiometer object
    gradiometer = None
    # Run number currently on
    runNum = 0

    datamutex = threading.Lock()

    # Start and stop of shield in centimeters
    SHIELDSTART = 20
    SHIELDSTOP = 60
    # Between two points to graph
    MINGRAPH = 0
    MAXGRAPH = 80
    # Frequency with which to graph
    GRAPHFREQ = 1

    class RunModes():
        """Enum for run modes"""
        pos = 1
        time = 2

    def __init__(self, mode, parent=None):
        """Initializes posRun class

        Args:
            mode (int): 1 for Gradiometer.posRun
                        2 for Gradiometer.timeRun
                    Use runModes class to ensure consistency
            parent: Parent element to be passed to super. Defaults to None.
        """
        super().__init__(parent)
        self.mode = mode
        self.setWindowTitle('Gradiometer {} Run'.format('Position' if self.mode == self.RunModes.pos else 'Time'))

        # Sets up general layout
        self.generalLayout = QHBoxLayout()
        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)
        self._centralWidget.setLayout(self.generalLayout)

        # Configuration panel on left third of screen
        self.configLayout = QVBoxLayout()
        self.generalLayout.addLayout(self.configLayout, 33)

        # Configuration entries
        self.settingsLayout = QFormLayout()
        self.tagEntry = QLineEdit()
        # TEMP: Remove before final version of GUI
        self.tagEntry.setText('GUITest')
        self.settingsLayout.addRow(
            'Tag (to be appended to file name):', self.tagEntry)

        self.repeatsEntry = QSpinBox()
        self.repeatsEntry.setValue(1)
        self.settingsLayout.addRow(
            "Number of times to repeat measurement:", self.repeatsEntry)

        # UI entry boxes specific to the different modes
        if self.mode == self.RunModes.pos:
            self.startEntry = QDoubleSpinBox()
            self.stopEntry = QDoubleSpinBox()
            self.startEntry.setValue(0)
            self.stopEntry.setValue(10)

            self.samplesPerPosEntry = QSpinBox()
            self.samplesPerPosEntry.setValue(5)

            self.settingsLayout.addRow('Start (cm):', self.startEntry)
            self.settingsLayout.addRow('Stop (cm):', self.stopEntry)
            self.settingsLayout.addRow(
                'Samples per position:', self.samplesPerPosEntry)
        elif self.mode == self.RunModes.time:
            self.secEntry = QSpinBox()
            self.secEntry.setValue(5)

            self.scanFreqEntry = QSpinBox()
            self.scanFreqEntry.setMaximum(5000)
            self.scanFreqEntry.setValue(500)

            self.changePosEntry = QCheckBox()
            self.changePosEntry.toggled.connect(
                lambda: self.cmEntry.setEnabled(self.changePosEntry.isChecked()))

            self.cmEntry = QDoubleSpinBox()
            self.cmEntry.setEnabled(False)

            self.settingsLayout.addRow('Time to scan (s):', self.secEntry)
            self.settingsLayout.addRow(
                'Scan Frequency (Hz):', self.scanFreqEntry)
            self.settingsLayout.addRow(
                'Change position before scan:', self.changePosEntry)
            self.settingsLayout.addRow(
                'Measurement location (cm):', self.cmEntry)

        self.configLayout.addLayout(self.settingsLayout)

        self.operateButton = QPushButton("Start Run")
        # Different functionality for start button depending on mode
        if self.mode == self.RunModes.pos:
            self.operateButton.clicked.connect(lambda: self.startPosRun(self.startEntry.value(
            ), self.stopEntry.value(), self.tagEntry.text(), self.samplesPerPosEntry.value(), self.repeatsEntry.value()))
        elif self.mode == self.RunModes.time:
            self.operateButton.clicked.connect(lambda: self.startTimeRun(self.secEntry.value(), self.tagEntry.text(
            ), self.scanFreqEntry.value(), None if not self.changePosEntry.isChecked() else self.cmEntry.value(), self.repeatsEntry.value()))
        self.configLayout.addWidget(self.operateButton)

        # Initializes graphs
        self.graphLayout = QVBoxLayout()
        self.generalLayout.addLayout(self.graphLayout, 66)

        self.xdata = []
        # Data for moving magnetometer
        # Might want to rename this to ydataPos1 to differentiate it from ydataPos2
        self.ydata = []
        # Data for constant magnetometer
        self.ydataPos2 = []
        # Error bars for data sets defined above
        self.error = []
        self.errorPos2 = []
        # References to each of the error bar plots
        # Note that plots are not the same as graphs: each set of data will have its own plot reference
        self.plotRefs = []
        self.plotDataRefs = []
        self.plotDataRefsPos2 = []
        self.errorItems = []
        self.errorItemsPos2 = []

        # If in position mode should have additional plots for zoomed in version
        self.numPlots = 6 if self.mode == self.RunModes.pos else 3

        for i in range(self.numPlots):
            # Initialize empty arrays
            self.xdata.append([])
            self.ydata.append([])
            self.ydataPos2.append([])
            self.error.append([])
            self.errorPos2.append([])
            self.plotDataRefs.append([])
            self.plotDataRefsPos2.append([])
            self.errorItems.append([])
            self.errorItemsPos2.append([])

            plotWidget = pg.PlotWidget(labels={'bottom': "Position (cm)" if self.mode == self.RunModes.pos else "Time (s)", 'left': "x" if i % 3 == 0 else ("y" if i % 3 == 1 else "z")})
            plotWidget.setBackground('w')

            self.plotRefs.append(plotWidget.getPlotItem())
            self.graphLayout.addWidget(plotWidget)

            # self.plotRefs[i].enableAutoScale()
            # vb = self.plotRefs[i].getViewBox()                     
            # vb.setAspectLocked(lock=False)            
            # vb.setAutoVisible(y=1.0)                
            # vb.enableAutoRange(axis='y', enable=True)


        self.timer=QtCore.QTimer()
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.updateGraph)
        self.timer.start()

    def startPosRun(self, start, stop, tag, samplesPerPos, repeats):
        """Starts position run. Arguments are same as in Gradiometer.posRun"""
        # Disable operation button so two runs don't get started at once
        self.operateButton.setEnabled(False)
        # Nest callback is kind of confusing, there's probably an easier way to do things
        # Basically gradCallback is called every time a measurement is made, while a lambda that uses this callback is given to the thread to run
        gradCallback = lambda i: self.gradiometer.posRun(
            start if i%2==0 else stop, stop if i%2==0 else start, tag, graph=False, samples_per_pos=samplesPerPos, mes_callback=self.updateData)
        self.gradThread = threading.Thread(target=lambda: self.repeatRun(repeats, gradCallback))
        for i in range(6):
            # Right now I'm just settting the axis in a hardcoded way to get them to line up as per Beatrice's request, but if dynamic spacing is required this should work: 
            # self.axes[i].set_xlim([min(self.axes[i].get_xlim()[0], min(
            #     start, stop))-3, max(self.axes[i].get_xlim()[1], max(start, stop))+1])
            # self.axes[i+3].set_xlim([20, 60])
            self.plotRefs[i].setXRange(self.MINGRAPH, self.MAXGRAPH)
        self.gradThread.start()

    def startTimeRun(self, sec, tag, scanFreq, cm, repeats):
        """Starts time run. Arguments are same as in Gradiometer.timeRun"""
        self.operateButton.setEnabled(False)
        # See startPosRun for what nest lambda does
        gradCallback = lambda i: self.gradiometer.timeRun(
            sec, tag, cm, graph=False, scanFreq=scanFreq, mes_callback=self.updateData)
        self.gradThread = threading.Thread(target=lambda: self.repeatRun(repeats, gradCallback))
        # Initializes axes to show maximum range any data series currently uses to avoid cutting any off
        for i in range(3):
            self.plotRefs[i].setXRange(0, max(self.plotRefs[i].viewRange()[0][1], sec)+1)
        self.gradThread.start()

    def setupRun(self):
        """Sets up shared run settings for pos and time runs"""
        # Initialize shared gradiometer if not already done
        if not self.gradiometer:
            self.gradiometer=initGrad()
        for i in range(3):
            self.xdata[i]=np.array([])
            self.ydata[i]=np.array([])
            self.ydataPos2[i] = np.array([])
            self.error[i]=np.array([])
            self.error[i+3]=np.array([])
            self.errorPos2[i] = np.array([])

            self.errorItems[i].append(pg.ErrorBarItem(x=self.xdata[i], y=self.ydata[i], height=self.error[i]))
            self.plotRefs[i].addItem(self.errorItems[i][-1])
            self.plotDataRefs[i].append(self.plotRefs[i].plot(self.xdata[i], self.ydata[i], pen=None, symbol='o'))

            if self.mode == self.RunModes.pos:
                self.errorItems[i+3].append(pg.ErrorBarItem(x=self.xdata[i], y=self.ydataPos2[i], height=self.error[i+3]))
                self.plotRefs[i+3].addItem(self.errorItems[i+3][-1])
                self.plotDataRefs[i+3].append(self.plotRefs[i+3].plot(self.xdata[i], self.ydataPos2[i], symbol='o'))

            self.errorItemsPos2[i].append(pg.ErrorBarItem(x=self.xdata[i], y=self.ydataPos2[i], height=self.errorPos2[i]))
            self.plotRefs[i].addItem(self.errorItemsPos2[i][-1])
            self.plotDataRefsPos2[i].append(self.plotRefs[i].plot(self.xdata[i], self.ydataPos2[i], symbol='o'))
        self.runNum += 1

    def repeatRun(self, repeats, runCallback):
        """Repeats a run of the given callback

        Args:
            repeats (int): number of repeats
            runCallback (Function): Callback that takes which iteration it's on
        """
        for i in range(repeats):
            self.setupRun()
            runCallback(i)
            # Not strictly necessary, just put it in to physically be able to differentiate runs
            time.sleep(1)

    def updateData(self, pos1, pos2, std1, std2): 
        """Updates data, to be called from gradThread Args (All in (x, y, ) format):
            pos1 (List[Float]): List of magnetic fields at position 1
            pos2 (List[Float]): List of magnetic fields at position 2
            std1 (List[Float]): List of standard deviations for pos 1
            std2 (List[Float]): List of standard deviations for pos 1
        """
        self.datamutex.acquire()
        try: 
            # Conversion factor given in user manual
            uTPerVolt = 10
            for i in range(3):
                # y and error are the same between modes
                self.ydata[i] = np.append(self.ydata[i], uTPerVolt*pos1[i])
                self.error[i] = np.append(self.error[i], uTPerVolt*std1[i])
                if self.mode == self.RunModes.pos:
                    self.xdata[i] = np.append(self.xdata[i], self.gradiometer.pos + self.getOffset(i))
                    # Since pos2 has rotated axes a shifting must be done
                    index = 2 if i==0 else (0 if i == 2 else 1)
                    self.ydataPos2[i] = np.append(self.ydataPos2[i], -uTPerVolt*pos2[index])
                    self.errorPos2[i] = np.append(self.errorPos2[i], uTPerVolt*std2[index])
                elif self.mode == self.RunModes.time:
                    if len(self.xdata[i]) == 0:
                        self.startTime = time.time()
                    self.xdata[i] = np.append(self.xdata[i], time.time()-self.startTime)
        finally:
            self.datamutex.release()

    def updateGraph(self):
        """Updates graphs periodically"""
        self.datamutex.acquire()
        try: 
            for i in range(self.numPlots):
                try:
                    if i < 3:
                        self.plotDataRefs[i][-1].setData(self.xdata[i], self.ydata[i])
                        self.errorItems[i][-1].setData(x=self.xdata[i], y=self.ydata[i], height=self.error[i])
                        vb = self.plotRefs[i].getViewBox()                     
                        vb.autoRange(items=self.plotDataRefs[i])
                        if self.mode == self.RunModes.pos:
                            self.plotDataRefsPos2[i][-1].setData(self.xdata[i], self.ydataPos2[i])
                    else:
                        lower=min(i for i, x in enumerate(
                            self.xdata[i % 3]) if x > 30)
                        upper=max(i for i, x in enumerate(
                            self.xdata[i % 3]) if x < 50)
                        self.plotDataRefs[i][-1].setData(self.xdata[i % 3][lower:upper], self.ydata[i % 3][lower:upper])
                        self.errorItems[i][-1].setData(x=self.xdata[i % 3][lower:upper], y=self.ydata[i % 3][lower:upper], height=self.error[i][lower:upper])
                        vb = self.plotRefs[i].getViewBox()                     
                        vb.autoRange(items=self.plotDataRefs[i])
                except (IndexError, ValueError) as e:
                    pass
            try: 
                if not self.gradThread.is_alive():
                    self.operateButton.setEnabled(True)
            except:
                pass
        finally:
            self.datamutex.release()

    def getOffset(self, i):
        """Get's offset of magnetometer inherent in instrument

        Args:
            i (int): axis, 1=x, 2=y, 3=z

        Returns:
            int: offset of the given axis
        """
        if i == 0:
            return -3
        elif i == 1:
            return 0
        elif i == 2:
            return -1.5

# Main entry point
if __name__ == '__main__':
    app=QApplication(sys.argv)
    dlg=TaskSelectDialog()
    dlg.show()
    sys.exit(app.exec_())

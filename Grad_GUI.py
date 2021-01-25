# This is for remote development. If true it will be able to be used without physical access to the gradiometer
# Note this is only for testing, if this is set to true the GUI will not be functional
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
import matplotlib
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import threading
import atexit
import time
import json
import sys
remoteDev = False

if not remoteDev:
    from Gradiometer import Gradiometer

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
        # Clears layout
        # for i in reversed(range(self.generalLayout.count())):
        #     self.generalLayout.itemAt(i).widget().setParent(None)
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
            if not remoteDev:
                self.steps = self.gradiometer.goTo(self.calDist)
            else:
                self.steps = 700

        thread = threading.Thread(target=goToThread)
        thread.start()

        self.distance = QDoubleSpinBox()
        self.distance.setAlignment(Qt.AlignCenter)
        self.generalLayout.addWidget(self.distance)

        def nextScreen():
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

    initGraph = False
    gradiometer = None

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
        self.setWindowTitle('Gradiometer Position Run')

        # self.setFixedSize(1000, 800)
        self.generalLayout = QHBoxLayout()
        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)
        self._centralWidget.setLayout(self.generalLayout)

        self.configLayout = QVBoxLayout()
        self.generalLayout.addLayout(self.configLayout, 33)

        self.settingsLayout = QFormLayout()
        self.tagEntry = QLineEdit()
        # if remoteDev:
        # TEMP: Remove before final version of GUI
        self.tagEntry.setText('GUITest')
        self.settingsLayout.addRow(
            'Tag (to be appended to file name):', self.tagEntry)

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
            self.scanFreqEntry.setValue(1000)
            self.changePosEntry = QCheckBox()
            self.cmEntry = QDoubleSpinBox()

            self.cmEntry.setEnabled(False)
            self.changePosEntry.toggled.connect(
                lambda: self.cmEntry.setEnabled(self.changePosEntry.isChecked()))

            self.settingsLayout.addRow('Time to scan (s):', self.secEntry)
            self.settingsLayout.addRow(
                'Scan Frequency (Hz):', self.scanFreqEntry)
            self.settingsLayout.addRow(
                'Change position before scan:', self.changePosEntry)
            self.settingsLayout.addRow(
                'Measurement location (cm):', self.cmEntry)

        self.configLayout.addLayout(self.settingsLayout)

        self.operateButton = QPushButton("Start Run")
        if self.mode == self.RunModes.pos:
            self.operateButton.clicked.connect(lambda: self.startPosRun(self.startEntry.value(
            ), self.stopEntry.value(), self.tagEntry.text(), self.samplesPerPosEntry.value()))
        elif self.mode == self.RunModes.time:
            self.operateButton.clicked.connect(lambda: self.startTimeRun(self.secEntry.value(), self.tagEntry.text(
            ), self.scanFreqEntry.value(), None if not self.changePosEntry.isChecked() else self.cmEntry.value()))
        self.configLayout.addWidget(self.operateButton)

        self.graphLayout = QVBoxLayout()
        self.generalLayout.addLayout(self.graphLayout, 66)

        fig = Figure(figsize=(5, 4), dpi=100)
        self.graph = FigureCanvasQTAgg(fig)
        self.axes = []
        self.xdata = []
        self.ydata = []
        self.plotRefs = []
        for i in range(3):
            self.xdata.append([])
            self.ydata.append([])
            self.axes.append(fig.add_subplot(3, 1, i+1))
            self.axes[i].set_xlabel(
                "Position (cm)" if self.mode == self.RunModes.pos else "Time (s)")
            self.axes[i].set_ylabel("B{}".format(
                "x" if i == 0 else ("y" if i == 1 else "z")))
            self.plotRefs.append(None)

        self.toolbar = NavigationToolbar(self.graph, self)
        self.graphLayout.addWidget(self.toolbar)
        self.graphLayout.addWidget(self.graph)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.updateGraph)
        self.timer.start()

    def startPosRun(self, start, stop, tag, samplesPerPos):
        """Starts position run. Arguments are same as in Gradiometer.posRun"""
        self.setupRun()
        self.gradThread = threading.Thread(target=lambda: self.gradiometer.posRun(
            start, stop, tag, graph=False, samples_per_pos=samplesPerPos, mes_callback=self.updateData))
        for i in range(3):
            self.axes[i].set_xlim([min(self.axes[i].get_xlim()[0], min(
                start, stop))-1, max(self.axes[i].get_xlim()[1], max(start, stop))+1])
        self.gradThread.start()

    def startTimeRun(self, sec, tag, scanFreq, cm):
        """Starts time run. Arguments are same as in Gradiometer.timeRun"""
        self.setupRun()
        self.gradThread = threading.Thread(target=lambda: self.gradiometer.timeRun(
            sec, tag, cm, graph=False, scanFreq=scanFreq, mes_callback=self.updateData))
        for i in range(3):
            self.axes[i].set_xlim([0, max(self.axes[i].get_ylim()[1], sec)+1])
        self.gradThread.start()

    def setupRun(self):
        """Sets up shared run settings for pos and time runs"""
        self.startTime = time.time()
        if not self.gradiometer:
            self.gradiometer = initGrad()
        for i in range(3):
            self.xdata[i] = []
            self.ydata[i] = []
        self.initGraph = True

    def updateData(self, pos1, pos2, std1, std2):
        """Updates data, to be called from gradThread

        Args (All in (x, y, ) format):
            pos1 (List[Float]): List of magnetic fields at position 1
            pos2 (List[Float]): List of magnetic fields at position 2
            std1 (List[Float]): List of standard deviations for pos 1
            std2 (List[Float]): List of standard deviations for pos 1
        """
        for i in range(3):
            self.ydata[i].append(pos1[i])
            if self.mode == self.RunModes.pos:
                self.xdata[i].append(self.gradiometer.pos + self.getOffset(i))
            elif self.mode == self.RunModes.time:
                self.xdata[i].append(time.time()-self.startTime)

    def updateGraph(self):
        """Updates graphs periodically"""
        # if hasattr(self, 'startTIme'):
        #     print(time.time()-self.startTime)
        for i in range(3):
            if len(self.xdata[i]) == 0:
                return
            if self.initGraph == True:
                self.plotRefs[i] = self.axes[i].plot(
                    self.xdata[i], self.ydata[i])
            else:
                self.plotRefs[i][-1].set_data(self.xdata[i], self.ydata[i])
                self.axes[i].relim()
                self.axes[i].autoscale_view(scalex=False)
        if self.initGraph:
            self.initGraph = False
        self.graph.draw()

    def getOffset(self, i):
        """Get's offset of magnetometer

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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    dlg = TaskSelectDialog()
    dlg.show()
    sys.exit(app.exec_())

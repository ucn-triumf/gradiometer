"""
This is a GUI wrapper for the existing gradiometer functionality implemented in Gradiometer.py
It is based on pyqt, and have functionality for calibration, time runs and position runs
"""

import matplotlib
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
import pyqtgraph as pg
import threading
import atexit
import time
import json
import sys
import numpy as np

# import RPi.GPIO as GPIO uncomment this and comment the line below when using RPi. This is for Windows.
import testRPi.GPIO as GPIO

# This is for remote development. If true it will be able to be used without physical access to the gradiometer
# Note this is only for testing, if this is set to true the GUI will not be functional
remoteDev = False

if not remoteDev:
    from Gradiometer import Gradiometer

# Enables matplotlib with pyqt
matplotlib.use("Qt5Agg")

# This is global variable since otherwise it goes out of scope in TaskSelectDialog
mainWindow = None

LOWER_MOTOR = 1
UPPER_MOTOR = 2
# used in all the cases when the motor speed should not be chosen by the user
STANDARD_MOTOR_SPEED = 60


def init_grad(motorNumber, motorSpeed):
    """Initializes gradiometer and sets atext functions for safe usage
    Only call this function once as only one gradiometer can be created

    Returns:
        Gradiometer: gradiometer that has just been initialized
    """
    g = Gradiometer(motorNumber, motorSpeed)
    atexit.register(g.motor.turn_off_motors)
    atexit.register(g.save_pos)
    atexit.register(g.labjack.close)
    return g


class TaskSelectDialog(QDialog):
    """Initial Dialog class for GUI"""

    class TaskTypes:
        """Enum for types of tasks to open"""

        cal = "Calibration"
        pos_run = "Position Run"
        time_run = "Time Run"

    def __init__(self, parent=None):
        """Initializes new opening dialog

        Args:
            parent: parent element. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Gradiometer GUI")
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Selection box for different tasks
        task_selection = QComboBox()
        task_selection.addItem(self.TaskTypes.cal)
        task_selection.addItem(self.TaskTypes.pos_run)
        task_selection.addItem(self.TaskTypes.time_run)

        form_layout.addRow("Task:", task_selection)
        layout.addLayout(form_layout)

        buttons = QDialogButtonBox()
        buttons.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        layout.addWidget(buttons)

        # Register button click events
        buttons.button(QDialogButtonBox.Cancel).clicked.connect(lambda: sys.exit())
        buttons.button(QDialogButtonBox.Ok).clicked.connect(
            lambda: self.start_main(task_selection.currentText())
        )
        self.setLayout(layout)

    def start_main(self, task_type):
        """Starts the main application of the appropriate type

        Args:
            task_type (str): The type of task to start, given by TaskTypes enum
        """
        global mainWindow
        if task_type == self.TaskTypes.cal:
            mainWindow = CalibrationWindow()
            mainWindow.show()
        elif task_type == self.TaskTypes.pos_run:
            mainWindow = RunWindow(RunWindow.RunModes.pos)
            mainWindow.showMaximized()
        elif task_type == self.TaskTypes.time_run:
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
        self.setWindowTitle("Gradiometer Calibration")
        self.setFixedSize(700, 400)
        self.general_layout = QVBoxLayout()
        self._central_widget = QWidget(self)
        self.setCentralWidget(self._central_widget)
        self._central_widget.setLayout(self.general_layout)
        # Since window isn't maximized have to set margins or else becomes too small
        self.general_layout.setContentsMargins(50, 50, 50, 50)
        self.calibration_screen()

    # MEASURE ACTUAL DISTANCE FOR THIS
    def calibration_screen(self):
        self.title = QLabel("<h1>Calibration</h2>")
        self.title.setAlignment(Qt.AlignCenter)
        self.general_layout.addWidget(self.title)

        self.intro = QLabel(
            "<p>The gradiometer will calibrate the selected belt automatically. Click 'Calibrate' to begin. When finished, you may calibrate again or click 'Back' to return to the task selection screen.</p>"
        )
        self.intro.setWordWrap(True)
        self.general_layout.addWidget(self.intro)

        self.motor_selection = QComboBox()
        self.motor_selection.addItem("Lower belt")
        self.motor_selection.addItem("Upper belt")
        self.motor_selection.setItemData(0, LOWER_MOTOR)
        self.motor_selection.setItemData(1, UPPER_MOTOR)
        self.general_layout.addWidget(self.motor_selection)

        limit_switch_lower_right = 6
        limit_switch_lower_left = 5
        limit_switch_upper_right = 13
        limit_switch_upper_left = 12

        self.finish_button = QPushButton("Calibrate")
        self.finish_button.clicked.connect(
            lambda: threading.Thread(target=calibration_run).start()
        )
        self.general_layout.addWidget(self.finish_button)

        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(
            lambda: self.return_from_calibration(TaskSelectDialog())
        )
        self.general_layout.addWidget(self.back_button)

        # Set up the GPIO pins of the limit switches (left and right as viewed from the desk with the monitor)

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(limit_switch_lower_right, GPIO.IN)
        GPIO.setup(limit_switch_lower_left, GPIO.IN)
        GPIO.setup(limit_switch_upper_right, GPIO.IN)
        GPIO.setup(limit_switch_upper_left, GPIO.IN)

        # Set up the moving thread to not freeze the GUI

        # When the different belts are selected, different switch pins are required.
        # TODO: finish calibration_run left/right selection and calibration
        def calibration_run():

            # Get the correct right and left limit switches
            if self.motor_selection.currentData() == LOWER_MOTOR:
                left = limit_switch_lower_left
                right = limit_switch_lower_right
            elif self.motor_selection.currentData() == UPPER_MOTOR:
                left = limit_switch_upper_left
                right = limit_switch_upper_right

            if not remoteDev:
                # for calibration the motorSpeed is set at 60.
                self.gradiometer = init_grad(
                    self.motor_selection.currentData(), motorSpeed=STANDARD_MOTOR_SPEED
                )
                self.gradiometer.zero()

            # This version of the function is for the lower belt. Goes from to the left switch, then to the right. Stops at the right switch
            self.finish_button.setEnabled(False)
            self.back_button.setEnabled(False)
            self.motor_selection.setEnabled(False)

            steps = 0

            while GPIO.input(limit_switch_lower_left) == 0:
                self.gradiometer.one_step(self.gradiometer.motor.mh.BACKWARD)

            self.gradiometer.save_pos()
            position_right = self.gradiometer.get_pos()

            while GPIO.input(limit_switch_lower_right) == 0:
                self.gradiometer.one_step(self.gradiometer.motor.mh.FORWARD)
                steps = (
                    steps + 1
                )  # Is there a more intellectual way of counting the steps?

            self.gradiometer.save_pos()
            position_left = self.gradiometer.get_pos()

            self.calibrate_grad(position_right, position_left, steps)

            self.finish_button.setEnabled(True)
            self.back_button.setEnabled(True)
            self.motor_selection.setEnabled(True)

    # TODO: which is more accurate: fluxgate position measurements or physical distance between switches measurement?
    def calibrate_grad(self, position_right, position_left, steps):
        actual_distance = 102  # cm
        distance = abs(position_right - position_left)
        with open("./config.json") as f:
            data = json.load(f)
            data["CM_PER_STEP"] = distance / steps
        # Not sure if there's a nice way of not having to open it twice, doesn't look super aesthetically pleasing
        with open("./config.json", "w") as f:
            # Note: some idiot decided that json.dumps is different from json.dump, be careful if you replicate this elsewhere
            json.dump(data, f)
        cm_per_step = distance / steps
        print(
            "distance: {}, steps: {}, cm per step: {}".format(
                distance, steps, cm_per_step
            )
        )

    def return_from_calibration(self, previous_window):
        previous_window.show()
        self.close()
        self.gradiometer.labjack.close()
        self.gradiometer.save_pos()
        self.gradiometer.motor.turn_off_motors()


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
    GRAPHFREQ = 5

    class RunModes:
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
        self.setWindowTitle(
            "Gradiometer {} Run".format(
                "Position" if self.mode == self.RunModes.pos else "Time"
            )
        )

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
        self.tagEntry.setText("GUITest")
        self.settingsLayout.addRow("Tag (to be appended to file name):", self.tagEntry)

        # Motor (belt) selection

        self.motorSelection = QComboBox()
        self.motorSelection.addItem("Lower belt")
        self.motorSelection.addItem("Upper belt")
        self.settingsLayout.addRow("Select belt:", self.motorSelection)
        self.motorSelection.setItemData(0, LOWER_MOTOR)
        self.motorSelection.setItemData(1, UPPER_MOTOR)

        self.repeatsEntry = QSpinBox()
        self.repeatsEntry.setValue(1)
        self.settingsLayout.addRow(
            "Number of times to repeat measurement:", self.repeatsEntry
        )

        # UI entry boxes specific to the different modes
        if self.mode == self.RunModes.pos:
            self.startEntry = QDoubleSpinBox()
            self.stopEntry = QDoubleSpinBox()
            self.startEntry.setValue(0)
            self.stopEntry.setValue(10)

            self.samplesPerPosEntry = QSpinBox()
            self.samplesPerPosEntry.setValue(5)

            self.motorSpeed = QDoubleSpinBox()
            self.motorSpeed.setMinimum(10)
            self.motorSpeed.setValue(30)
            self.motorSpeed.setMaximum(100)
            self.motorSpeed.setSingleStep(1)

            self.settingsLayout.addRow("Start (cm):", self.startEntry)
            self.settingsLayout.addRow("Stop (cm):", self.stopEntry)
            self.settingsLayout.addRow("Samples per position:", self.samplesPerPosEntry)
            self.settingsLayout.addRow("Motor Speed (RPM):", self.motorSpeed)

        elif self.mode == self.RunModes.time:
            self.secEntry = QSpinBox()
            self.secEntry.setValue(5)

            self.scanFreqEntry = QSpinBox()
            self.scanFreqEntry.setMaximum(5000)
            self.scanFreqEntry.setValue(500)

            self.changePosEntry = QCheckBox()
            self.changePosEntry.toggled.connect(
                lambda: self.cmEntry.setEnabled(self.changePosEntry.isChecked())
            )

            self.cmEntry = QDoubleSpinBox()
            self.cmEntry.setEnabled(False)

            self.settingsLayout.addRow("Time to scan (s):", self.secEntry)
            self.settingsLayout.addRow("Scan Frequency (Hz):", self.scanFreqEntry)
            self.settingsLayout.addRow(
                "Change position before scan:", self.changePosEntry
            )
            self.settingsLayout.addRow("Measurement location (cm):", self.cmEntry)

        self.configLayout.addLayout(self.settingsLayout)

        self.operateButton = QPushButton("Start Run")
        # Different functionality for start button depending on mode
        if self.mode == self.RunModes.pos:
            self.operateButton.clicked.connect(
                lambda: self.startPosRun(
                    self.startEntry.value(),
                    self.stopEntry.value(),
                    self.tagEntry.text(),
                    self.motorSelection.currentData(),
                    self.motorSpeed.value(),
                    self.samplesPerPosEntry.value(),
                    self.repeatsEntry.value(),
                )
            )
        elif self.mode == self.RunModes.time:
            self.operateButton.clicked.connect(
                lambda: self.startTimeRun(
                    sec=self.secEntry.value(),
                    tag=self.tagEntry.text(),
                    motorNumber=self.motorSelection.currentData(),
                    motorSpeed=STANDARD_MOTOR_SPEED,
                    scanFreq=self.scanFreqEntry.value(),
                    cm=None
                    if not self.changePosEntry.isChecked()
                    else self.cmEntry.value(),
                    repeats=self.repeatsEntry.value(),
                )
            )
        self.configLayout.addWidget(self.operateButton)

        self.backButton = QPushButton("Back")
        self.backButton.clicked.connect(lambda: self.returnTo(TaskSelectDialog()))
        self.configLayout.addWidget(self.backButton)

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

            plotWidget = pg.PlotWidget(
                labels={
                    "bottom": "Position (cm)"
                    if self.mode == self.RunModes.pos
                    else "Time (s)",
                    "left": "x" if i % 3 == 0 else ("y" if i % 3 == 1 else "z"),
                }
            )
            plotWidget.setBackground("w")

            self.plotRefs.append(plotWidget.getPlotItem())
            # Causes seg fault for some reason, couldn't figure out why
            # self.plotRefs[i].addLegend(offset=(30, 30))
            self.graphLayout.addWidget(plotWidget)

            # self.plotRefs[i].enableAutoScale()
            # vb = self.plotRefs[i].getViewBox()
            # vb.setAspectLocked(lock=False)
            # vb.setAutoVisible(y=1.0)
            # vb.enableAutoRange(axis='y', enable=True)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.updateGraph)
        self.timer.start()

    def returnTo(self, previousWindow):
        previousWindow.show()
        self.close()
        self.gradiometer.labjack.close()
        self.gradiometer.save_pos()
        self.gradiometer.motor.turn_off_motors()

    def startPosRun(
        self, start, stop, tag, motorNumber, motorSpeed, samplesPerPos, repeats
    ):
        """Starts position run. Arguments are same as in Gradiometer.posRun"""

        # Disable operation button so two runs don't get started at once
        self.operateButton.setEnabled(False)
        self.backButton.setEnabled(False)
        # self.backButton.setEnabled(False)
        # Nest callback is kind of confusing, there's probably an easier way to do things
        # Basically gradCallback is called every time a measurement is made, while a lambda that uses this callback is given to the thread to run
        gradCallback = lambda i: self.gradiometer.pos_run(
            start if i % 2 == 0 else stop,
            stop if i % 2 == 0 else start,
            tag,
            graph=False,
            samples_per_pos=samplesPerPos,
            mes_callback=self.updateData,
        )
        self.gradThread = threading.Thread(
            target=lambda: self.repeatRun(
                motorNumber, motorSpeed, repeats, gradCallback
            )
        )
        for i in range(6):
            # Right now I'm just settting the axis in a hardcoded way to get them to line up as per Beatrice's request, but if dynamic spacing is required this should work:
            # self.axes[i].set_xlim([min(self.axes[i].get_xlim()[0], min(
            #     start, stop))-3, max(self.axes[i].get_xlim()[1], max(start, stop))+1])
            # self.axes[i+3].set_xlim([20, 60])
            self.plotRefs[i].setXRange(self.MINGRAPH, self.MAXGRAPH)
        self.gradThread.start()

    def startTimeRun(self, sec, tag, motorNumber, motorSpeed, scanFreq, cm, repeats):
        """Starts time run. Arguments are same as in Gradiometer.timeRun"""
        self.operateButton.setEnabled(False)
        self.backButton.setEnabled(False)
        # self.backButton.setEnabled(False)
        # See startPosRun for what nest lambda does
        gradCallback = lambda i: self.gradiometer.timeRun(
            sec, tag, cm, graph=False, scanFreq=scanFreq, mes_callback=self.updateData
        )
        self.gradThread = threading.Thread(
            target=lambda: self.repeatRun(
                motorNumber, motorSpeed, repeats, gradCallback
            )
        )
        # Initializes axes to show maximum range any data series currently uses to avoid cutting any off
        for i in range(3):
            self.plotRefs[i].setXRange(
                0, max(self.plotRefs[i].viewRange()[0][1], sec) + 1
            )
        self.gradThread.start()

    def setupRun(self, motorNumber, motorSpeed):
        """Sets up shared run settings for pos and time runs"""
        # Initialize shared gradiometer if not already done
        if not self.gradiometer:
            self.gradiometer = init_grad(motorNumber, motorSpeed)

        for i in range(3):
            self.xdata[i].append(np.array([]))
            self.ydata[i].append(np.array([]))
            self.ydataPos2[i].append(np.array([]))
            self.error[i].append(np.array([]))
            self.errorPos2[i].append(np.array([]))

            self.errorItems[i].append(
                pg.ErrorBarItem(
                    x=self.xdata[i][-1], y=self.ydata[i][-1], height=self.error[i][-1]
                )
            )
            self.plotRefs[i].addItem(self.errorItems[i][-1])
            self.plotDataRefs[i].append(
                self.plotRefs[i].plot(
                    self.xdata[i][-1],
                    self.ydata[i][-1],
                    pen=None,
                    symbol="o",
                    symbolBrush=(self.runNum % 5, 5),
                )
            )

            if self.mode == self.RunModes.pos:
                self.error[i + 3].append(np.array([]))
                self.errorItems[i + 3].append(
                    pg.ErrorBarItem(
                        x=self.xdata[i][-1],
                        y=self.ydata[i][-1],
                        height=self.error[i + 3][-1],
                    )
                )
                self.plotRefs[i + 3].addItem(self.errorItems[i + 3][-1])
                self.plotDataRefs[i + 3].append(
                    self.plotRefs[i + 3].plot(
                        self.xdata[i][-1],
                        self.ydataPos2[i][-1],
                        symbol="o",
                        symbolBrush=(self.runNum % 5, 5),
                    )
                )

            self.errorItemsPos2[i].append(
                pg.ErrorBarItem(
                    x=self.xdata[i][-1],
                    y=self.ydataPos2[i][-1],
                    height=self.errorPos2[i][-1],
                )
            )
            self.plotRefs[i].addItem(self.errorItemsPos2[i][-1])
            self.plotDataRefsPos2[i].append(
                self.plotRefs[i].plot(
                    self.xdata[i][-1],
                    self.ydataPos2[i][-1],
                    symbol="o",
                    symbolBrush=(self.runNum % 5, 5),
                )
            )

        self.runNum += 1

    def repeatRun(self, motorNumber, motorSpeed, repeats, runCallback):
        """Repeats a run of the given callback

        Args:
            repeats (int): number of repeats
            runCallback (Function): Callback that takes which iteration it's on
        """
        for i in range(repeats):
            self.setupRun(motorNumber, motorSpeed)
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
                self.ydata[i][-1] = np.append(self.ydata[i][-1], uTPerVolt * pos1[i])
                self.error[i][-1] = np.append(self.error[i][-1], uTPerVolt * std1[i])
                if self.mode == self.RunModes.pos:
                    self.xdata[i][-1] = np.append(
                        self.xdata[i][-1], self.gradiometer.pos + self.getOffset(i)
                    )
                    # Since pos2 has rotated axes a shifting must be done
                    index = 2 if i == 0 else (0 if i == 2 else 1)
                    self.ydataPos2[i][-1] = np.append(
                        self.ydataPos2[i][-1], -uTPerVolt * pos2[index]
                    )
                    self.errorPos2[i][-1] = np.append(
                        self.errorPos2[i][-1], uTPerVolt * std2[index]
                    )
                elif self.mode == self.RunModes.time:
                    if len(self.xdata[i][-1]) == 0:
                        self.startTime = time.time()
                    self.xdata[i][-1] = np.append(
                        self.xdata[i][-1], time.time() - self.startTime
                    )
        finally:
            self.datamutex.release()

    def updateGraph(self):
        """Updates graphs periodically"""
        self.datamutex.acquire()
        downsample = 10 if self.mode == self.RunModes.pos else 1
        try:
            for i in range(self.numPlots):
                try:
                    vb = self.plotRefs[i].getViewBox()
                    vb.autoRange(items=self.plotDataRefs[i])
                    if self.mode == self.RunModes.pos:
                        self.plotRefs[i].setXRange(self.MINGRAPH, self.MAXGRAPH)
                    if i < 3:
                        self.plotDataRefs[i][-1].setData(
                            self.xdata[i][-1], self.ydata[i][-1], downsample=downsample
                        )
                        self.errorItems[i][-1].setData(
                            x=self.xdata[i][-1],
                            y=self.ydata[i][-1],
                            height=self.error[i][-1],
                            downsample=downsample,
                        )
                        # if self.mode == self.RunModes.pos:
                        #     self.plotDataRefsPos2[i][-1].setData(self.xdata[i][-1], self.ydataPos2[i][-1])
                        #     self.errorItemsPos2[i][-1].setData(x=self.xdata[i][-1], y=self.ydataPos2[i][-1], height=self.errorPos2[i][-1])
                    else:
                        data_restricted = [
                            i
                            for i, x in enumerate(self.xdata[i % 3][-1])
                            if x > 30 and x < 50
                        ]
                        lower = min(data_restricted)
                        upper = max(data_restricted)
                        self.plotDataRefs[i][-1].setData(
                            self.xdata[i % 3][-1][lower:upper],
                            self.ydata[i % 3][-1][lower:upper],
                            downsample=downsample,
                        )
                        self.errorItems[i][-1].setData(
                            x=self.xdata[i % 3][-1][lower:upper],
                            y=self.ydata[i % 3][-1][lower:upper],
                            height=self.error[i % 3][-1][lower:upper],
                            downsample=downsample,
                        )
                except (IndexError, ValueError) as e:
                    pass
            try:
                if not self.gradThread.is_alive():
                    self.operateButton.setEnabled(True)
                    self.backButton.setEnabled(True)
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
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = TaskSelectDialog()
    dlg.show()
    sys.exit(app.exec_())

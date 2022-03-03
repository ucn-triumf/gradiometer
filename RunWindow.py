import threading
import time
import numpy as np
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QHBoxLayout,
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
)
import pyqtgraph as pg
from global_imports import (
    STANDARD_MOTOR_SPEED,
    init_grad,
    LOWER_MOTOR,
    UPPER_MOTOR,
    return_to_prev_window,
)


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

        :param mode: 1 for Gradiometer.posRun
                     2 for Gradiometer.timeRun
                     Use runModes class to ensure consistency
        :param parent: Parent element to be passed to super. Defaults to None.
        """
        super().__init__(parent)
        self.mode = mode
        self.setWindowTitle(
            "Gradiometer {} Run".format(
                "Position" if self.mode == self.RunModes.pos else "Time"
            )
        )
        self.setWindowModality(Qt.ApplicationModal)

        # Sets up general layout
        self.generalLayout = QHBoxLayout()
        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)
        self._centralWidget.setLayout(self.generalLayout)

        # Configuration panel on left third of screen
        self.configLayout = QVBoxLayout()
        self.generalLayout.addLayout(self.configLayout, 33)

        # Configuration entries
        self.settings_layout = QFormLayout()
        self.tagEntry = QLineEdit()
        # TEMP: Remove before final version of GUI
        self.tagEntry.setText("GUITest")
        self.settings_layout.addRow("Tag (to be appended to file name):", self.tagEntry)

        # Save folder destination selection
        self.save_folder_path = QLineEdit()
        self.save_folder_path.setText("Run_Data/")
        # TODO: make save folder path field editable but such that it cannot be left empty
        self.save_folder_path.setEnabled(False)
        self.select_folder_button = QPushButton("Select Save Folder")
        self.settings_layout.addRow(self.select_folder_button, self.save_folder_path)

        self.select_folder_button.clicked.connect(
            lambda: self.select_directory(self.save_folder_path)
        )

        # Motor (belt) selection

        self.motor_selection = QComboBox()
        self.motor_selection.addItem("Lower belt")
        self.motor_selection.addItem("Upper belt")
        self.settings_layout.addRow("Belt:", self.motor_selection)
        self.motor_selection.setItemData(0, LOWER_MOTOR)
        self.motor_selection.setItemData(1, UPPER_MOTOR)

        self.repeats_entry = QSpinBox()
        self.repeats_entry.setMinimum(1)
        self.repeats_entry.setValue(1)
        self.settings_layout.addRow(
            "Number of times to repeat measurement:", self.repeats_entry
        )

        # UI entry boxes specific to the different modes
        if self.mode == self.RunModes.pos:
            self.start_entry = QDoubleSpinBox()
            self.stop_entry = QDoubleSpinBox()
            self.start_entry.setValue(0)
            self.stop_entry.setValue(10)

            self.samples_per_pos_entry = QSpinBox()
            self.samples_per_pos_entry.setValue(5)

            self.motor_speed = QDoubleSpinBox()
            self.motor_speed.setMinimum(10)
            self.motor_speed.setValue(30)
            self.motor_speed.setMaximum(100)
            self.motor_speed.setSingleStep(1)

            self.settings_layout.addRow("Start (cm):", self.start_entry)
            self.settings_layout.addRow("Stop (cm):", self.stop_entry)
            self.settings_layout.addRow(
                "Samples per position:", self.samples_per_pos_entry
            )
            self.settings_layout.addRow("Motor Speed (RPM):", self.motor_speed)

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

            self.settings_layout.addRow("Time to scan (s):", self.secEntry)
            self.settings_layout.addRow("Scan Frequency (Hz):", self.scanFreqEntry)
            self.settings_layout.addRow(
                "Change position before scan:", self.changePosEntry
            )
            self.settings_layout.addRow("Measurement location (cm):", self.cmEntry)

        self.configLayout.addLayout(self.settings_layout)

        self.operateButton = QPushButton("Start Run")
        # Different functionality for start button depending on mode
        if self.mode == self.RunModes.pos:
            self.operateButton.clicked.connect(
                lambda: self.start_pos_run(
                    start=self.start_entry.value(),
                    stop=self.stop_entry.value(),
                    tag=self.tagEntry.text(),
                    save_folder_path=self.save_folder_path.text(),
                    motor_number=self.motor_selection.currentData(),
                    motor_speed=self.motor_speed.value(),
                    samples_per_pos=self.samples_per_pos_entry.value(),
                    repeats=self.repeats_entry.value(),
                )
            )
        elif self.mode == self.RunModes.time:
            self.operateButton.clicked.connect(
                lambda: self.start_time_run(
                    sec=self.secEntry.value(),
                    tag=self.tagEntry.text(),
                    save_folder_path=self.save_folder_path.text(),
                    motor_number=self.motor_selection.currentData(),
                    motor_speed=STANDARD_MOTOR_SPEED,
                    scan_freq=self.scanFreqEntry.value(),
                    cm=None
                    if not self.changePosEntry.isChecked()
                    else self.cmEntry.value(),
                    repeats=self.repeats_entry.value(),
                )
            )
        self.configLayout.addWidget(self.operateButton)

        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(lambda: return_to_prev_window(self))
        self.configLayout.addWidget(self.back_button)

        # Initializes graphs
        self.graphLayout = QVBoxLayout()
        self.generalLayout.addLayout(self.graphLayout, 66)

        self.xdata = []
        # Data for moving magnetometer
        # Might want to rename this to ydataPos1 to differentiate it from ydataPos2
        self.ydata_pos1 = []
        # Data for constant magnetometer
        self.ydata_pos2 = []
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
            self.ydata_pos1.append([])
            self.ydata_pos2.append([])
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
        self.timer.timeout.connect(self.update_graph)
        self.timer.start()

    def select_directory(self, entry_field):
        """
        Opens a file dialog to select the save location.

        :param entry_field: QLineEdit field where the user could also manually enter the directory
        """
        dialog = QFileDialog()
        folder_path = dialog.getExistingDirectory(None, "Select Folder")
        entry_field.setText(folder_path)

    def start_pos_run(
        self,
        start,
        stop,
        tag,
        save_folder_path,
        motor_number,
        motor_speed,
        samples_per_pos,
        repeats,
    ):
        """Starts position run. Arguments are same as in Gradiometer.pos_run"""

        # Disable operation button so two runs don't get started at once
        self.operateButton.setEnabled(False)
        self.back_button.setEnabled(False)
        # self.backButton.setEnabled(False) Nest callback is kind of confusing, there's probably an easier way to do
        # things Basically grad_callback is called every time a measurement is made, while a lambda that uses this
        # callback is given to the thread to run

        grad_callback = lambda i: self.gradiometer.pos_run(
            start if i % 2 == 0 else stop,
            stop if i % 2 == 0 else start,
            tag,
            save_folder_path,
            graph=False,
            samples_per_pos=samples_per_pos,
            mes_callback=self.update_data,
        )
        self.grad_thread = threading.Thread(
            target=lambda: self.repeat_run(
                motor_number, motor_speed, repeats, grad_callback
            )
        )
        for i in range(6):
            # Right now I'm just settting the axis in a hardcoded way to get them to line up as per Beatrice's
            # request, but if dynamic spacing is required this should work: self.axes[i].set_xlim([min(self.axes[
            # i].get_xlim()[0], min( start, stop))-3, max(self.axes[i].get_xlim()[1], max(start, stop))+1])
            # self.axes[i+3].set_xlim([20, 60])
            self.plotRefs[i].setXRange(self.MINGRAPH, self.MAXGRAPH)
        self.grad_thread.start()

    def start_time_run(
        self,
        sec,
        tag,
        save_folder_path,
        motor_number,
        motor_speed,
        scan_freq,
        cm,
        repeats,
    ):
        """Starts time run. Arguments are same as in Gradiometer.time_run"""
        self.operateButton.setEnabled(False)
        self.back_button.setEnabled(False)
        # self.backButton.setEnabled(False)
        # See startPosRun for what nest lambda does
        grad_callback = lambda i: self.gradiometer.time_run(
            sec,
            tag,
            save_folder_path,
            cm,
            graph=False,
            scan_freq=scan_freq,
            mes_callback=self.update_data,
        )
        self.grad_thread = threading.Thread(
            target=lambda: self.repeat_run(
                motor_number, motor_speed, repeats, grad_callback
            )
        )
        # Initializes axes to show maximum range any data series currently uses to avoid cutting any off
        for i in range(3):
            self.plotRefs[i].setXRange(
                0, max(self.plotRefs[i].viewRange()[0][1], sec) + 1
            )
        self.grad_thread.start()

    def setup_run(self, motor_number, motor_speed):
        """
        Sets up shared run settings for pos and time runs

        :param motor_number: 1 for lower motor, 2 for upper motor
        :param motor_speed: speed of the motor (RPM)
        """
        # Initialize shared gradiometer if not already done
        if not self.gradiometer:
            self.gradiometer = init_grad(motor_number, motor_speed)

        for i in range(3):
            self.xdata[i].append(np.array([]))
            self.ydata_pos1[i].append(np.array([]))
            self.ydata_pos2[i].append(np.array([]))
            self.error[i].append(np.array([]))
            self.errorPos2[i].append(np.array([]))

            self.errorItems[i].append(
                pg.ErrorBarItem(
                    x=self.xdata[i][-1],
                    y=self.ydata_pos1[i][-1],
                    height=self.error[i][-1],
                )
            )
            self.plotRefs[i].addItem(self.errorItems[i][-1])
            self.plotDataRefs[i].append(
                self.plotRefs[i].plot(
                    self.xdata[i][-1],
                    self.ydata_pos1[i][-1],
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
                        y=self.ydata_pos1[i][-1],
                        height=self.error[i + 3][-1],
                    )
                )
                self.plotRefs[i + 3].addItem(self.errorItems[i + 3][-1])
                self.plotDataRefs[i + 3].append(
                    self.plotRefs[i + 3].plot(
                        self.xdata[i][-1],
                        self.ydata_pos2[i][-1],
                        symbol="o",
                        symbolBrush=(self.runNum % 5, 5),
                    )
                )

            self.errorItemsPos2[i].append(
                pg.ErrorBarItem(
                    x=self.xdata[i][-1],
                    y=self.ydata_pos2[i][-1],
                    height=self.errorPos2[i][-1],
                )
            )
            self.plotRefs[i].addItem(self.errorItemsPos2[i][-1])
            self.plotDataRefsPos2[i].append(
                self.plotRefs[i].plot(
                    self.xdata[i][-1],
                    self.ydata_pos2[i][-1],
                    symbol="o",
                    symbolBrush=(self.runNum % 5, 5),
                )
            )

        self.runNum += 1

    def repeat_run(self, motor_number, motor_speed, repeats, run_callback):
        """
        Repeats a run of the given callback

        :param run_callback: Callback that takes which iteration it's on
        :param repeats: number of repeats
        :param motor_speed: speed of the motor (RPM)
        :param motor_number: 1 for lower motor, 2 for upper motor
        """
        for i in range(repeats):
            self.setup_run(motor_number, motor_speed)
            run_callback(i)
            # Not strictly necessary, just put it in to physically be able to differentiate runs
            time.sleep(1)

    def update_data(self, pos1, pos2, std1, std2):
        """
        Updates data, to be called from gradThread Args (All in (x, y, ) format):

        :param pos1: List of magnetic fields at position 1
        :param pos2: List of magnetic fields at position 2
        :param std1: List of standard deviations for pos 1
        :param std2: List of standard deviations for pos 1
        """
        self.datamutex.acquire()
        try:
            # Conversion factor given in user manual
            u_t_per_volt = 10
            for i in range(3):
                # y and error are the same between modes
                self.ydata_pos1[i][-1] = np.append(
                    self.ydata_pos1[i][-1], u_t_per_volt * pos1[i]
                )
                self.error[i][-1] = np.append(self.error[i][-1], u_t_per_volt * std1[i])
                if self.mode == self.RunModes.pos:
                    self.xdata[i][-1] = np.append(
                        self.xdata[i][-1], self.gradiometer.pos + self.get_offset(i)
                    )
                    # Since pos2 has rotated axes a shifting must be done
                    index = 2 if i == 0 else (0 if i == 2 else 1)
                    self.ydata_pos2[i][-1] = np.append(
                        self.ydata_pos2[i][-1], -u_t_per_volt * pos2[index]
                    )
                    self.errorPos2[i][-1] = np.append(
                        self.errorPos2[i][-1], u_t_per_volt * std2[index]
                    )
                elif self.mode == self.RunModes.time:
                    if len(self.xdata[i][-1]) == 0:
                        self.start_time = time.time()
                    self.xdata[i][-1] = np.append(
                        self.xdata[i][-1], time.time() - self.start_time
                    )
        finally:
            self.datamutex.release()

    def update_graph(self):
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
                            self.xdata[i][-1],
                            self.ydata_pos1[i][-1],
                            downsample=downsample,
                        )
                        self.errorItems[i][-1].setData(
                            x=self.xdata[i][-1],
                            y=self.ydata_pos1[i][-1],
                            height=self.error[i][-1],
                            downsample=downsample,
                        )
                        # if self.mode == self.RunModes.pos: self.plotDataRefsPos2[i][-1].setData(self.xdata[i][-1],
                        # self.ydataPos2[i][-1]) self.errorItemsPos2[i][-1].setData(x=self.xdata[i][-1],
                        # y=self.ydataPos2[i][-1], height=self.errorPos2[i][-1])
                    else:
                        data_restricted = [
                            i
                            for i, x in enumerate(self.xdata[i % 3][-1])
                            if 30 < x < 50
                        ]
                        lower = min(data_restricted)
                        upper = max(data_restricted)
                        self.plotDataRefs[i][-1].setData(
                            self.xdata[i % 3][-1][lower:upper],
                            self.ydata_pos1[i % 3][-1][lower:upper],
                            downsample=downsample,
                        )
                        self.errorItems[i][-1].setData(
                            x=self.xdata[i % 3][-1][lower:upper],
                            y=self.ydata_pos1[i % 3][-1][lower:upper],
                            height=self.error[i % 3][-1][lower:upper],
                            downsample=downsample,
                        )
                except (IndexError, ValueError) as e:
                    pass
            try:
                if not self.grad_thread.is_alive():
                    self.operateButton.setEnabled(True)
                    self.back_button.setEnabled(True)
            except:
                pass
        finally:
            self.datamutex.release()

    def get_offset(self, i):
        """
        Gets offset of magnetometer inherent in instrument

        :param i axis, 1=x, 2=y, 3=z
        :returns int offset of the given axis
        """
        if i == 0:
            return -3
        elif i == 1:
            return 0
        elif i == 2:
            return -1.5

import json
import threading

import RPi.GPIO as GPIO
# uncomment this and comment the line below when using RPi. This is for Windows.
# import testRPi.GPIO as GPIO
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QLabel,
    QComboBox,
    QPushButton,
)

from global_imports import (
    LOWER_MOTOR,
    UPPER_MOTOR,
    remoteDev,
    init_grad,
    STANDARD_MOTOR_SPEED,
    return_to_prev_window,
)


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
        self.setWindowModality(Qt.ApplicationModal)
        self.setFixedSize(700, 400)
        self.general_layout = QVBoxLayout()
        self._central_widget = QWidget(self)
        self.setCentralWidget(self._central_widget)
        self._central_widget.setLayout(self.general_layout)
        # Since window isn't maximized have to set margins or else becomes too small
        self.general_layout.setContentsMargins(50, 50, 50, 50)

        self.title = QLabel("<h1>Calibration</h2>")
        self.title.setAlignment(Qt.AlignCenter)
        self.general_layout.addWidget(self.title)

        self.intro = QLabel(
            "<p>The gradiometer will calibrate the selected belt automatically. Click 'Calibrate' to begin. When "
            "finished, you may calibrate again or click 'Back' to return to the task selection screen.</p> "
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
        self.back_button.clicked.connect(lambda: return_to_prev_window(self))
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
                    self.motor_selection.currentData(), motor_speed=STANDARD_MOTOR_SPEED
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

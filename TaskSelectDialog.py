import sys
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QDialogButtonBox,
)
from CalibrationWindow import CalibrationWindow
from RunWindow import RunWindow


class TaskSelectDialog(QDialog):
    """
    Initial Dialog class for GUI

    :param parent: parent element. Defaults to None.
    """

    class TaskTypes:
        """Enum for types of tasks to open"""

        cal = "Calibration"
        pos_run = "Position Run"
        time_run = "Time Run"

    def __init__(self, parent=None):
        """Constructor method"""
        super().__init__(parent)
        self.setWindowTitle("Gradiometer GUI")
        self.layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Selection box for different tasks
        task_selection = QComboBox()
        task_selection.addItem(self.TaskTypes.cal)
        task_selection.addItem(self.TaskTypes.pos_run)
        task_selection.addItem(self.TaskTypes.time_run)

        form_layout.addRow("Task:", task_selection)
        self.layout.addLayout(form_layout)

        buttons = QDialogButtonBox()
        buttons.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.layout.addWidget(buttons)

        # Register button click events
        buttons.button(QDialogButtonBox.Cancel).clicked.connect(lambda: sys.exit())
        buttons.button(QDialogButtonBox.Ok).clicked.connect(
            lambda: self.start_main(task_selection.currentText())
        )
        self.setLayout(self.layout)

    def start_main(self, task_type):
        """Starts the main application of the appropriate type

        :param task_type: The type of task to start, given by TaskTypes enum
        """

        if task_type == self.TaskTypes.cal:
            main_window = CalibrationWindow()
            main_window.show()
        elif task_type == self.TaskTypes.pos_run:
            main_window = RunWindow(RunWindow.RunModes.pos)
            main_window.showMaximized()
        elif task_type == self.TaskTypes.time_run:
            main_window = RunWindow(RunWindow.RunModes.time)
            main_window.showMaximized()

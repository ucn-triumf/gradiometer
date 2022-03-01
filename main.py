"""
This is a GUI wrapper for the existing gradiometer functionality implemented in Gradiometer.py
It is based on pyqt, and have functionality for calibration, time runs and position runs
"""

import matplotlib
from PyQt5.QtWidgets import *
import sys



# This is for remote development. If true it will be able to be used without physical access to the gradiometer
# Note this is only for testing, if this is set to true the GUI will not be functional
from TaskSelectDialog import TaskSelectDialog

remoteDev = False

if not remoteDev:
    from Gradiometer import Gradiometer

# Enables matplotlib with pyqt
matplotlib.use("Qt5Agg")

# This is global variable since otherwise it goes out of scope in TaskSelectDialog
mainWindow = None


# Main entry point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = TaskSelectDialog()
    dlg.show()
    sys.exit(app.exec_())

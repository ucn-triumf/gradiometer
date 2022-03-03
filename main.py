"""
This is a GUI wrapper for the existing gradiometer functionality implemented in Gradiometer.py
It is based on pyqt, and have functionality for calibration, time runs and position runs
"""

import matplotlib
from PyQt5.QtWidgets import *
import sys
from TaskSelectDialog import TaskSelectDialog

# Enables matplotlib with pyqt
matplotlib.use("Qt5Agg")

# Main entry point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = TaskSelectDialog()
    dlg.show()
    sys.exit(app.exec_())

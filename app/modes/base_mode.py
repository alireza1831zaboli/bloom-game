from PySide6 import QtWidgets, QtCore

class BaseModeWidget(QtWidgets.QWidget):
    scoreChanged = QtCore.Signal(int)
    timeChanged = QtCore.Signal(int)
    bestChanged = QtCore.Signal(int)
    runEnded = QtCore.Signal(int, str, str)
    screenshotSaved = QtCore.Signal(str)
    started = QtCore.Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.running=False
        self.paused=False

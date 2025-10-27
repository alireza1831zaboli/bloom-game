# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtCore, QtGui

class CountdownOverlay(QtWidgets.QWidget):
    """Simple 3..2..1 overlay drawn over the game area. No logic changes to game itself."""
    finished = QtCore.Signal()

    def __init__(self, duration_ms: int = 1800, parent=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground, True)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self._duration = duration_ms
        self._start = QtCore.QElapsedTimer()
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.update)
        self.hide()

    def start(self):
        self.resize(self.parent().size())
        self.show()
        self.raise_()
        self._start.start()
        self._timer.start(16)

    def stop(self):
        self._timer.stop()
        self.hide()

    def paintEvent(self, ev):
        if not self.isVisible():
            return
        elapsed = self._start.elapsed()
        if elapsed >= self._duration:
            self.stop()
            self.finished.emit()
            return

        # compute remaining seconds: 3,2,1
        remain = max(0, self._duration - elapsed)
        sec = int(remain / 600)  # approx 3 steps across 1800ms (3*600ms)
        sec = max(1, min(3, sec))

        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        w, h = self.width(), self.height()
        # dim background
        p.fillRect(0,0,w,h, QtGui.QColor(0,0,0,120))
        # big number
        f = QtGui.QFont("Inter", int(min(w,h)*0.25), QtGui.QFont.Black)
        p.setFont(f)
        p.setPen(QtGui.QPen(QtGui.QColor(255,255,255,220)))
        rect = QtCore.QRectF(0,0,w,h)
        p.drawText(rect, QtCore.Qt.AlignCenter, str(sec))

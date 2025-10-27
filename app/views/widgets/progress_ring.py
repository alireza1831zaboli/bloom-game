from PySide6 import QtWidgets, QtGui, QtCore
import math


class ProgressRing(QtWidgets.QWidget):
    """حلقه‌ی پیشرفت سبک: completed/total را نشان می‌دهد."""

    def __init__(self, completed: int = 0, total: int = 1, parent=None):
        super().__init__(parent)
        self.completed = completed
        self.total = max(1, total)
        self.setMinimumSize(120, 120)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

    def set_values(self, completed: int, total: int):
        self.completed = max(0, completed)
        self.total = max(1, total)
        self.update()

    def paintEvent(self, e: QtGui.QPaintEvent):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        r = min(w, h) * 0.45
        cx, cy = w / 2, h / 2

        # پس‌زمینه‌ی حلقه
        p.setPen(QtGui.QPen(QtGui.QColor(210, 225, 255, 90), 8))
        p.drawEllipse(QtCore.QPointF(cx, cy), r, r)

        # پیشرفت
        frac = min(1.0, float(self.completed) / float(self.total))
        start = -90 * 16
        span = int(360 * frac * 16)
        p.setPen(QtGui.QPen(QtGui.QColor(124, 196, 255, 220), 8))
        rect = QtCore.QRectF(cx - r, cy - r, 2 * r, 2 * r)
        p.drawArc(rect, start, span)

        # متن داخل
        p.setPen(QtGui.QColor(234, 242, 255))
        f = p.font()
        f.setBold(True)
        f.setPointSize(12)
        p.setFont(f)
        txt = f"{self.completed}/{self.total}"
        p.drawText(self.rect(), QtCore.Qt.AlignCenter, txt)

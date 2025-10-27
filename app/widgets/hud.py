from PySide6 import QtGui

class HudPainter:
    # cache common pen/font to avoid per-frame allocations
    _PEN = QtGui.QPen(QtGui.QColor(255, 255, 255, 150))
    _FONT = QtGui.QFont("Inter", 10, QtGui.QFont.Bold)

    @staticmethod
    def draw_footer_title(p, text, w, h):
        p.setPen(HudPainter._PEN)
        p.setFont(HudPainter._FONT)
        p.drawText(10, h - 12, text)

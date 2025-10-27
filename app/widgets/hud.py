from PySide6 import QtGui
class HudPainter:
    @staticmethod
    def draw_footer_title(p,t,w,h):
        p.setPen(QtGui.QPen(QtGui.QColor(255,255,255,150)))
        p.setFont(QtGui.QFont("Inter",10,QtGui.QFont.Bold))
        p.drawText(10,h-12,t)

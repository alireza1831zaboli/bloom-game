# -*- coding: utf-8 -*-
"""
Lightweight HUD helpers used by game modes.

We intentionally keep styling identical to the original inline code
to avoid any visual/behavioral change.
"""
from PySide6 import QtGui

class HudPainter:
    @staticmethod
    def draw_footer_title(p: QtGui.QPainter, text: str, w: int, h: int) -> None:
        # Matches the previous inline style: white, slight transparency, Inter 10 bold
        p.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 150)))
        p.setFont(QtGui.QFont("Inter", 10, QtGui.QFont.Bold))
        p.drawText(10, h - 12, text)

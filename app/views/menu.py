from PySide6 import QtWidgets, QtGui, QtCore
import math, time
from app.i18n import tr
from .widgets.progress_ring import ProgressRing
from ..settings import STORY_LEVELS


class MenuPage(QtWidgets.QWidget):
    # سیگنال‌ها…
    continueStory = QtCore.Signal()
    newStage = QtCore.Signal()
    endless = QtCore.Signal()
    settings = QtCore.Signal()
    about = QtCore.Signal()
    exitApp = QtCore.Signal()

    def __init__(self, unlocked: int, lang: str = "fa", parent=None):
        super().__init__(parent)
        self._unlocked = unlocked
        self._lang = lang
        self._init_ui()

    def set_unlocked(self, unlocked: int):
        self._unlocked = unlocked
        self.btn_continue.setEnabled(self._unlocked > 1)
        self.ring.set_values(
            min(self._unlocked - 1, len(STORY_LEVELS)), len(STORY_LEVELS)
        )

    def retranslate(self, lang: str):
        self._lang = lang
        rtl = lang == "fa"
        self.setLayoutDirection(QtCore.Qt.RightToLeft if rtl else QtCore.Qt.LeftToRight)
        self.title.setText(tr("app.title", lang))
        self.subtitle.setText(tr("tagline", lang))
        self.btn_continue.setText(tr("menu.continue", lang))
        self.btn_new.setText(tr("menu.new", lang))
        self.btn_endless.setText(tr("menu.endless", lang))
        self.btn_settings.setText(tr("menu.settings", lang))
        self.btn_about.setText(tr("menu.about", lang))
        self.btn_exit.setText(tr("menu.quit", lang))

    def _init_ui(self):
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.update)
        self._timer.start(16)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        center = QtWidgets.QWidget(self)
        v = QtWidgets.QVBoxLayout(center)
        v.setAlignment(QtCore.Qt.AlignCenter)

        self.title = QtWidgets.QLabel(tr("app.title", self._lang))
        self.title.setObjectName("nbTitle")
        self.subtitle = QtWidgets.QLabel(tr("tagline", self._lang))
        self.subtitle.setObjectName("nbSubtitle")
        self.subtitle.setAlignment(QtCore.Qt.AlignCenter)

        # Progress Ring
        self.ring = ProgressRing(
            min(self._unlocked - 1, len(STORY_LEVELS)), len(STORY_LEVELS), self
        )

        topbox = QtWidgets.QHBoxLayout()
        topbox.addStretch(1)
        topbox.addWidget(self.ring)
        topbox.addSpacing(16)
        box2 = QtWidgets.QVBoxLayout()
        box2.addWidget(self.title, 0, QtCore.Qt.AlignHCenter)
        box2.addWidget(self.subtitle, 0, QtCore.Qt.AlignHCenter)
        topbox.addLayout(box2)
        topbox.addStretch(1)
        v.addLayout(topbox)
        v.addSpacing(12)

        grid = QtWidgets.QVBoxLayout()
        grid.setSpacing(10)

        def big_button(text):
            b = QtWidgets.QPushButton(text, self)
            b.setObjectName("nbMenuButton")
            b.setMinimumWidth(300)
            b.setMinimumHeight(46)
            b.setCursor(QtCore.Qt.PointingHandCursor)
            return b

        self.btn_continue = big_button(tr("menu.continue", self._lang))
        self.btn_new = big_button(tr("menu.new", self._lang))
        self.btn_endless = big_button(tr("menu.endless", self._lang))
        self.btn_settings = big_button(tr("menu.settings", self._lang))
        self.btn_about = big_button(tr("menu.about", self._lang))
        self.btn_exit = big_button(tr("menu.quit", self._lang))
        self.btn_continue.setEnabled(self._unlocked > 1)

        self.btn_continue.clicked.connect(self.continueStory.emit)
        self.btn_new.clicked.connect(self.newStage.emit)
        self.btn_endless.clicked.connect(self.endless.emit)
        self.btn_settings.clicked.connect(self.settings.emit)
        self.btn_about.clicked.connect(self.about.emit)
        self.btn_exit.clicked.connect(self.exitApp.emit)

        for b in (
            self.btn_continue,
            self.btn_new,
            self.btn_endless,
            self.btn_settings,
            self.btn_about,
            self.btn_exit,
        ):
            grid.addWidget(b, 0, QtCore.Qt.AlignHCenter)

        v.addLayout(grid)
        v.addStretch(1)
        lay.addStretch(1)
        lay.addWidget(center)
        lay.addStretch(1)

    def paintEvent(self, e: QtGui.QPaintEvent):
        # همان پس‌زمینه‌ی گرادیانی روشن‌تر (قبلی)
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        t = time.perf_counter()
        grad = QtGui.QLinearGradient(0, 0, w, h)
        grad.setColorAt(0, QtGui.QColor(18, 30, 58))
        grad.setColorAt(1, QtGui.QColor(22, 46, 86))
        p.fillRect(self.rect(), grad)
        p.setOpacity(0.18)
        cols = [
            QtGui.QColor(124, 196, 255, 180),
            QtGui.QColor(99, 255, 210, 160),
            QtGui.QColor(255, 184, 122, 150),
            QtGui.QColor(216, 136, 255, 150),
        ]
        for i in range(8):
            r = (math.sin(t * 0.7 + i * 0.6) * 0.5 + 0.5) * 160 + 120
            x = (int(i * 137 + math.sin(t * 0.4 + i) * 220) % (w + 400)) - 200
            y = (int(i * 199 + math.cos(t * 0.5 + i) * 160) % (h + 400)) - 200
            p.setBrush(cols[i % len(cols)])
            p.setPen(QtCore.Qt.NoPen)
            p.drawEllipse(QtCore.QPointF(x, y), r, r)
        p.setOpacity(0.06)
        pen = QtGui.QPen(QtGui.QColor(220, 235, 255, 120), 1)
        p.setPen(pen)
        step = 36
        for x in range(-w, w * 2, step):
            p.drawLine(x, 0, x + int(0.5 * h), h)
        vg = QtGui.QRadialGradient(QtCore.QPointF(w * 0.5, h * 0.52), max(w, h) * 0.9)
        vg.setColorAt(0.0, QtGui.QColor(0, 0, 0, 0))
        vg.setColorAt(1.0, QtGui.QColor(0, 0, 0, 130))
        p.setOpacity(1.0)
        p.fillRect(self.rect(), vg)

# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtGui, QtCore
from app.i18n import tr
import math
import random, time


class HubMenu(QtWidgets.QWidget):
    # سیگنال‌ها برای ناوبری
    openClassic = QtCore.Signal()
    openWeave = QtCore.Signal()
    openPhantom = QtCore.Signal()
    openArchitect = QtCore.Signal()
    openMirror = QtCore.Signal()
    openCollapse = QtCore.Signal()
    openSettings = QtCore.Signal()
    openAbout = QtCore.Signal()
    exitApp = QtCore.Signal()

    def __init__(self, lang: str = "fa", parent=None):
        super().__init__(parent)
        self._lang = lang
        self._build_ui()
        self._blobs = []  # لیست حباب‌های نورانی
        self._last_t = time.perf_counter()
        self._anim = QtCore.QTimer(self)
        self._anim.timeout.connect(self._anim_step)
        self._anim.start(33)  # ~30fps نرم

    # با اولین resize بلاب‌ها ساخته می‌شوند
    def _ensure_blobs(self):
        """بر اساس اندازه فعلی، چند حباب نرم می‌سازد."""
        if self._blobs:
            return
        w, h = max(800, self.width()), max(500, self.height())
        cols = [
            QtGui.QColor(124, 196, 255, 160),
            QtGui.QColor(99, 255, 210, 140),
            QtGui.QColor(255, 184, 122, 130),
            QtGui.QColor(216, 136, 255, 140),
        ]
        random.seed(7)
        for i in range(12):
            r = random.uniform(120, 260)
            vx = random.uniform(-8, 8)  # سرعت‌های خیلی کم برای حرکت لطیف
            vy = random.uniform(-5, 5)
            self._blobs.append(
                {
                    "x": random.uniform(-300, w + 300),
                    "y": random.uniform(-300, h + 300),
                    "r": r,
                    "vx": vx,
                    "vy": vy,
                    "c": cols[i % len(cols)],
                }
            )

    def _anim_step(self):
        """آپدیت نرم موقعیت‌ها بدون جهش/ریست."""
        self._ensure_blobs()
        now = time.perf_counter()
        dt = max(0.0, min(0.05, now - self._last_t))
        self._last_t = now
        if not self._blobs:
            return
        w, h = self.width(), self.height()
        pad = 320  # حاشیه بیرون کادر تا رد شدن بی‌درز شود
        for b in self._blobs:
            b["x"] += b["vx"] * dt
            b["y"] += b["vy"] * dt
            # wrap آرام؛ از یک طرف خارج شد، از طرف دیگر با همان سرعت وارد می‌شود
            if b["x"] < -pad:
                b["x"] += w + 2 * pad
            if b["x"] > w + pad:
                b["x"] -= w + 2 * pad
            if b["y"] < -pad:
                b["y"] += h + 2 * pad
            if b["y"] > h + pad:
                b["y"] -= h + 2 * pad
        self.update()

    def showEvent(self, e):
        super().showEvent(e)
        if hasattr(self, "_anim"):
            self._anim.start(33)

    def hideEvent(self, e):
        super().hideEvent(e)
        if hasattr(self, "_anim"):
            self._anim.stop()

    def set_unlocked(self, unlocked: int):
        # اگر خواستی چیزی را بر اساس پیشرفت قفل کنی
        pass

    def retranslate(self, lang: str):
        self._lang = lang
        rtl = lang == "fa"
        self.setLayoutDirection(QtCore.Qt.RightToLeft if rtl else QtCore.Qt.LeftToRight)
        self.title.setText(tr("app.title", lang))
        self.subtitle.setText(tr("tagline", lang))

        # کارت‌ها
        self.cards["classic"]["title"].setText(tr("hub.classic", lang))
        self.cards["classic"]["desc"].setText(tr("desc.classic", lang))
        self.cards["weave"]["title"].setText(tr("hub.weave", lang))
        self.cards["weave"]["desc"].setText(tr("desc.weave", lang))
        self.cards["phantom"]["title"].setText(tr("hub.phantom", lang))
        self.cards["phantom"]["desc"].setText(tr("desc.phantom", lang))
        self.cards["arch"]["title"].setText(tr("hub.arch", lang))
        self.cards["arch"]["desc"].setText(tr("desc.arch", lang))
        self.cards["mirror"]["title"].setText(tr("hub.mirror", lang))
        self.cards["mirror"]["desc"].setText(tr("desc.mirror", lang))
        self.cards["collapse"]["title"].setText(tr("hub.collapse", lang))
        self.cards["collapse"]["desc"].setText(tr("desc.collapse", lang))

        # پایین صفحه
        self.btn_settings.setText(tr("menu.settings", lang))
        self.btn_about.setText(tr("menu.about", lang))
        self.btn_exit.setText(tr("menu.quit", lang))

    def _build_ui(self):
        self.setObjectName("nbHub")
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(14)

        # Header
        head = QtWidgets.QVBoxLayout()
        head.setSpacing(2)
        header_frame = QtWidgets.QFrame()
        header_frame.setObjectName("nbCard")
        hv = QtWidgets.QVBoxLayout(header_frame)
        hv.setContentsMargins(16, 12, 16, 12)
        hv.setSpacing(2)
        self.title = QtWidgets.QLabel(tr("app.title", self._lang))
        self.title.setObjectName("nbTitle")
        self.title.setAlignment(QtCore.Qt.AlignHCenter)
        self.subtitle = QtWidgets.QLabel(tr("tagline", self._lang))
        self.subtitle.setObjectName("nbSubtitle")
        self.subtitle.setAlignment(QtCore.Qt.AlignHCenter)
        hv.addWidget(self.title)
        hv.addWidget(self.subtitle)
        root.addWidget(header_frame)

        # Grid of game cards (2 x 3)
        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)
        self.cards = {}

        def make_card(key: str, icon_char: str, title: str, desc: str, click_cb):
            card = QtWidgets.QFrame()
            card.setObjectName("nbGameCard")
            v = QtWidgets.QVBoxLayout(card)
            v.setContentsMargins(16, 16, 16, 16)
            v.setSpacing(6)

            icon = QtWidgets.QLabel(icon_char)
            icon.setObjectName("nbGameIcon")
            icon.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
            t = QtWidgets.QLabel(title)
            t.setObjectName("nbCardTitle")
            d = QtWidgets.QLabel(desc)
            d.setWordWrap(True)
            d.setObjectName("nbCardDesc")
            btn = QtWidgets.QPushButton(title)
            btn.setObjectName("nbPlayBtn")
            btn.clicked.connect(click_cb)

            v.addWidget(icon, 0)
            v.addSpacing(2)
            v.addWidget(t, 0)
            v.addWidget(d, 1)
            v.addSpacing(8)
            v.addWidget(btn, 0, QtCore.Qt.AlignRight)

            self.cards[key] = {"wrap": card, "title": t, "desc": d, "btn": btn}
            return card

        cards = [
            (
                "classic",
                "◈",
                tr("hub.classic", self._lang),
                tr("desc.classic", self._lang),
                self.openClassic.emit,
            ),
            (
                "weave",
                "⌘",
                tr("hub.weave", self._lang),
                tr("desc.weave", self._lang),
                self.openWeave.emit,
            ),
            (
                "phantom",
                "✺",
                tr("hub.phantom", self._lang),
                tr("desc.phantom", self._lang),
                self.openPhantom.emit,
            ),
            (
                "arch",
                "⟲",
                tr("hub.arch", self._lang),
                tr("desc.arch", self._lang),
                self.openArchitect.emit,
            ),
            (
                "mirror",
                "¤",
                tr("hub.mirror", self._lang),
                tr("desc.mirror", self._lang),
                self.openMirror.emit,
            ),
            (
                "collapse",
                "⚡",
                tr("hub.collapse", self._lang),
                tr("desc.collapse", self._lang),
                self.openCollapse.emit,
            ),
        ]
        r = 0
        c = 0
        for key, ico, ti, de, cb in cards:
            grid.addWidget(make_card(key, ico, ti, de, cb), r, c)
            c += 1
            if c >= 3:
                c = 0
                r += 1
        root.addLayout(grid, 1)

        # Footer buttons
        foot = QtWidgets.QHBoxLayout()
        self.btn_settings = QtWidgets.QPushButton(tr("menu.settings", self._lang))
        self.btn_about = QtWidgets.QPushButton(tr("menu.about", self._lang))
        self.btn_exit = QtWidgets.QPushButton(tr("menu.quit", self._lang))
        self.btn_settings.clicked.connect(self.openSettings.emit)
        self.btn_about.clicked.connect(self.openAbout.emit)
        self.btn_exit.clicked.connect(self.exitApp.emit)
        foot.addWidget(self.btn_settings)
        foot.addStretch(1)
        foot.addWidget(self.btn_about)
        foot.addSpacing(12)
        foot.addWidget(self.btn_exit)
        root.addLayout(foot)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        # در اولین resize، بلاب‌ها ساخته می‌شوند
        self._blobs.clear()
        QtCore.QTimer.singleShot(0, self._ensure_blobs)

    def paintEvent(self, e: QtGui.QPaintEvent):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # گرادیان پایه
        grad = QtGui.QLinearGradient(0, 0, w, h)
        grad.setColorAt(0, QtGui.QColor(18, 30, 58))
        grad.setColorAt(1, QtGui.QColor(22, 46, 86))
        p.fillRect(self.rect(), grad)

        # حباب‌های نرم با شفافیت کم
        self._ensure_blobs()
        p.setPen(QtCore.Qt.NoPen)
        for b in self._blobs:
            p.setBrush(b["c"])
            p.drawEllipse(QtCore.QPointF(b["x"], b["y"]), b["r"], b["r"])

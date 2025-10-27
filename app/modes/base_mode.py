# -*- coding: utf-8 -*-
"""
BaseModeWidget: shared scaffolding for game modes.

- Provides common Qt signals (scoreChanged, timeChanged, bestChanged, runEnded, screenshotSaved, started)
- Centralizes pause/run flags
- Offers helper methods: set_theme/lang/control, toggle_pause, start_run, stop_run
- Optional heartbeat timer: call enable_timer(update_cb) to tick at ~60fps
This class is intentionally lightweight to avoid changing existing mode logic.
"""
from PySide6 import QtWidgets, QtCore

class BaseModeWidget(QtWidgets.QWidget):
    # Unified signals many modes already expose; keeping them here prevents boilerplate.
    scoreChanged = QtCore.Signal(int)
    timeChanged = QtCore.Signal(int)
    bestChanged = QtCore.Signal(int)
    runEnded = QtCore.Signal(int, str, str)
    screenshotSaved = QtCore.Signal(str)
    started = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running: bool = False
        self.paused: bool = False
        self._theme = None
        self._lang = "fa"
        self._control = "mouse"
        self._timer = None  # lazy

    # --- State helpers (non-invasive) ---
    def set_theme(self, theme):
        self._theme = theme
        self.update()

    def set_lang(self, lang: str):
        self._lang = lang

    def set_control(self, control: str):
        # "mouse" | "keys"
        self._control = control

    def toggle_pause(self):
        if not self.running:
            return
        self.paused = not self.paused

    def start_run(self):
        self.running = True
        self.paused = False
        try:
            self.started.emit()
        except Exception:
            pass

    def stop_run(self):
        self.running = False
        self.paused = False

    def enable_timer(self, update_cb, interval_ms: int = 16):
        """Connect a simple timer to call update_cb; optional for modes that already manage timing."""
        if self._timer is None:
            self._timer = QtCore.QTimer(self)
            self._timer.timeout.connect(update_cb)
        self._timer.start(interval_ms)

    def disable_timer(self):
        if self._timer:
            self._timer.stop()

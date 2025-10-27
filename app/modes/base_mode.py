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


    def enable_fixed_timestep(self, update_cb, hz: int = 60):
        """Optional fixed-timestep runner. Modes may opt-in to use this instead of ad-hoc timers."""
        self._elapsed_timer = QtCore.QElapsedTimer()
        self._elapsed_timer.start()
        self._accum = 0.0
        self._dt = 1000.0 / float(hz)
        if self._timer is None:
            self._timer = QtCore.QTimer(self)
        def _tick():
            if not self.running or self.paused:
                return
            ms = self._elapsed_timer.restart()
            self._accum += ms
            while self._accum >= self._dt:
                update_cb()
                self._accum -= self._dt
            self.update()
        try:
            self._timer.timeout.disconnect()
        except Exception:
            pass
        self._timer.timeout.connect(_tick)
        self._timer.start(16)


    # --- Optional hooks; modes may override if they use them ---
    def set_mouse_sensitivity(self, value: float):
        """0.5..2.0 typical. Default: no-op for modes that don't use it."""
        self._mouse_sens = value  # store for reference

    def set_difficulty(self, preset: str):
        """'Chill'|'Normal'|'Hard' typical. Default: no-op."""
        self._difficulty = preset

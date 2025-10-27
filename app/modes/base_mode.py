from PySide6 import QtWidgets
class BaseModeWidget(QtWidgets.QWidget):
    pass


    def _update_dt(self):
        import time
        now = time.perf_counter()
        last = getattr(self, "_last_ts_internal", None)
        self._last_ts_internal = now
        if last is None:
            return 0.016
        return max(0.001, min(0.05, now - last))

    def _move_towards(self, x, y, tx, ty, max_step):
        dx, dy = tx - x, ty - y
        d2 = dx*dx + dy*dy
        if d2 <= max_step*max_step:
            return tx, ty
        import math
        d = math.sqrt(d2) if d2>0 else 1.0
        k = max_step / d
        return x + dx*k, y + dy*k

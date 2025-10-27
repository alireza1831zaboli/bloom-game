# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtGui, QtCore
import math, random, time
from app.modes.base_mode import BaseModeWidget
from app.utils import rect_intersects_circle
from app.settings import (
    THEMES,
    RAMP_DURATION,
    RAMP_RATE,
    MAX_PHASE,
    INITIAL_TIME_ENDLESS,
)

PLAYER_R = 11


def rect_intersects_circle(rx, ry, rw, rh, cx, cy, r):
    nx = max(rx, min(cx, rx + rw))
    ny = max(ry, min(cy, ry + rh))
    dx = cx - nx
    dy = cy - ny
    return (dx * dx + dy * dy) <= (r * r)


class PhantomRunWidget(BaseModeWidget):
    scoreChanged = QtCore.Signal(int)
    timeChanged = QtCore.Signal(int)
    bestChanged = QtCore.Signal(int)
    runEnded = QtCore.Signal(int, str, str)
    screenshotSaved = QtCore.Signal(str)
    started = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self._theme = THEMES["Aurora"]
        self._lang = "fa"
        self._control = "mouse"  # "mouse" | "keys"
        self._mode = "endless"  # endless | story

        self.running = False
        self.paused = False
        self.score = 0
        self.best = 0
        self.time_left = 60

        # player (فقط محور X؛ فلش رو به بالا)
        self.px = (self.width() or 1200) / 2
        self.py = (self.height() or 800) * 0.7
        self.vx = 0.0
        self.mx = self.px
        self.key_left = self.key_right = False
        self.keys_speed = 420.0

        # world
        self.rows = []  # {"y","speed","h":bar_h,"gaps":[(x,w)],"scored":bool}
        self.sparks = []
        self.powerups = []
        self.phase_time = 0.0

        # difficulty
        self._phase = 0.0
        self._elapsed = 0.0
        self._row_timer = 0.0
        self._pow_timer = 3.5

        # guaranteed path
        self._safe_band = None  # (left,right)
        self._pattern = "straight"
        self._pattern_rows_left = 10
        self._snake_t = 0.0  # برای snake
        self._squeeze_dir = -1  # برای کوچک/بزرگ شدن شکاف

        # loop
        self._last = time.perf_counter()
        self._acc = 0.0
        self._step = 1 / 60.0
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000 // 120)

    # ---- public
    def set_lang(self, lang: str):
        self._lang = lang

    def set_theme(self, name: str):
        self._theme = THEMES.get(name, self._theme)
        self.update()

    def set_mode(self, mode: str):
        self._mode = mode

    def set_control_mode(self, mode: str):
        self._control = "keys" if mode.lower().startswith("k") else "mouse"

    def set_music(self, on: bool):
        pass

    def set_sfx(self, on: bool):
        pass

    def prepare_endless(self, _ignore=INITIAL_TIME_ENDLESS):
        self._reset_world()
        self._mode = "endless"
        self.time_left = -1
        self.running = False
        self.update()
        self.scoreChanged.emit(self.score)
        self.bestChanged.emit(self.best)

    def prepare_story(self, idx: int):
        self._reset_world()
        self._mode = "story"
        self.time_left = 70 if idx < 5 else 55
        self.running = False
        self.update()
        self.timeChanged.emit(int(self.time_left))
        self.scoreChanged.emit(self.score)
        self.bestChanged.emit(self.best)

    def start(self):
        if self._mode == "story" and self.time_left <= 0:
            return
        self.running = True
        self.paused = False
        self._last = time.perf_counter()
        self.started.emit()

    def toggle_pause(self):
        if not self.running:
            return
        self.paused = not self.paused

    def reset(self):
        if self._mode == "endless":
            self.prepare_endless()
        else:
            self.prepare_story(0)

    # ---- internal
    def _reset_world(self):
        w = max(1, self.width())
        h = max(1, self.height())
        self.px = w / 2
        self.py = h * 0.7
        self.vx = 0.0
        self.mx = self.px
        self.key_left = self.key_right = False
        self.score = 0
        self.phase_time = 0.0
        self.rows.clear()
        self.sparks.clear()
        self.powerups.clear()
        self._phase = 0.0
        self._elapsed = 0.0
        self._row_timer = 0.0
        self._pow_timer = 2.8
        # safe band اولیه
        g0 = 190
        self._safe_band = (w * 0.5 - g0 / 2, w * 0.5 + g0 / 2)
        self._pattern = "straight"
        self._pattern_rows_left = 10
        self._snake_t = 0.0
        self._squeeze_dir = -1
        # prefill
        for i in range(6):
            self._spawn_row(-i * 120 - 40)

    def _tick(self):
        now = time.perf_counter()
        dt = min(0.05, now - self._last)
        self._last = now
        if self.running and not self.paused:
            self._acc += dt
            while self._acc >= self._step:
                self._update(self._step)
                self._acc -= self._step
            self.update()
        else:
            self.update()

    # ---- pattern selection
    def _maybe_switch_pattern(self):
        if self._pattern_rows_left > 0:
            self._pattern_rows_left -= 1
            return
        # انتخاب وزن‌دار بر اساس سختی
        choices = ["straight", "snake", "squeeze", "jump"]
        weights = [
            4,
            2 + self._phase * 0.1,
            1 + self._phase * 0.08,
            1 + self._phase * 0.12,
        ]
        self._pattern = random.choices(choices, weights=weights, k=1)[0]
        # طول پترن بعدی
        self._pattern_rows_left = random.randint(8, 14)
        if self._pattern == "snake":
            self._snake_t = 0.0
        if self._pattern == "squeeze":
            self._squeeze_dir = -1  # اول باریک‌تر شود

    # محاسبه‌ی باند امن بعدی بر اساس پترن
    def _next_safe_band(self, w, prev_left, prev_right):
        cx_prev = (prev_left + prev_right) * 0.5
        gw_prev = prev_right - prev_left

        # حدود عمومیِ شکاف‌ها با سختی
        min_gap = max(80, 130 - int(self._phase * 5.5))
        max_gap = max(min_gap + 10, 210 - int(self._phase * 7.5))
        # محدودیت‌ها نزدیک لبه
        pad = 60

        if self._pattern == "straight":
            drift = random.uniform(-60, 60) * (0.6 + min(0.8, self._phase * 0.03))
            cx = max(pad, min(w - pad, cx_prev + drift))
            gw = max(min_gap, min(max_gap, int(gw_prev + random.uniform(-18, 18))))

        elif self._pattern == "snake":
            # حرکت سینوسی کنترل‌شده
            self._snake_t += 0.35 + self._phase * 0.015
            amp = min(180, 80 + self._phase * 8)
            cx = max(pad, min(w - pad, cx_prev + math.sin(self._snake_t) * amp))
            gw = max(min_gap, min(max_gap, int(gw_prev + random.uniform(-10, 10))))

        elif self._pattern == "squeeze":
            # باریک و پهن‌شدن آهسته
            delta = 12 + self._phase * 1.1
            gw = int(gw_prev + self._squeeze_dir * delta)
            if gw < min_gap:
                gw = min_gap
                self._squeeze_dir = +1
            elif gw > max_gap:
                gw = max_gap
                self._squeeze_dir = -1
            drift = random.uniform(-45, 45)
            cx = max(pad, min(w - pad, cx_prev + drift))

        else:  # "jump"
            # پرش ناگهانی سمت چپ/راست، اما همچنان ممکن
            jump = random.choice([-1, 1]) * (160 + self._phase * 10)
            cx = max(pad, min(w - pad, cx_prev + jump))
            gw = max(min_gap, min(max_gap, int(gw_prev + random.uniform(-14, 14))))

        left = int(cx - gw / 2)
        right = int(cx + gw / 2)
        return left, right

    # ---- spawn row (guaranteed path + decorative gaps)
    def _spawn_row(self, y=None):
        w = self.width()
        if y is None:
            y = -80

        if self._safe_band is None:
            left, right = int(w * 0.5 - 100), int(w * 0.5 + 100)
        else:
            left, right = self._safe_band

        # شاید پترن را عوض کنیم
        self._maybe_switch_pattern()
        left, right = self._next_safe_band(w, left, right)
        safe_gap = (left, right - left)

        # شکاف‌های تزئینی برای تنوع (بدون بستن مسیر)
        gaps = [safe_gap]
        extra_n = 0
        if self._phase > 3:
            extra_n = 1
        if self._phase > 7:
            extra_n = 2
        if self._phase > 11:
            extra_n = 3
        min_gap = 70
        for _ in range(extra_n):
            gw = random.randint(min_gap, max(90, safe_gap[1] - 10))
            gx = random.randint(20, w - 20 - gw)
            # اگر خیلی به safe نزدیک بود، هل بده
            if abs(gx - safe_gap[0]) < 40:
                gx += 100 if gx < w / 2 else -100
                gx = max(20, min(w - 20 - gw, gx))
            gaps.append((gx, gw))
        gaps.sort(key=lambda g: g[0])

        # سرعت و ضخامت نوار
        base_speed = 130 + self._phase * 18
        bar_h = int(18 + min(6, self._phase * 0.5))  # 18..24
        self.rows.append(
            {"y": y, "speed": base_speed, "h": bar_h, "gaps": gaps, "scored": False}
        )

        # مسیر امن برای ردیف بعد
        self._safe_band = (safe_gap[0], safe_gap[0] + safe_gap[1])

    def _spawn_power(self):
        w = self.width()
        if self._safe_band:
            x = random.uniform(self._safe_band[0] + 20, self._safe_band[1] - 20)
        else:
            x = random.uniform(40, w - 40)
        self.powerups.append({"x": x, "y": -20, "kind": "phase", "life": 10.0})

    # ---- update
    def _update(self, dt: float):
        w, h = self.width(), self.height()

        # ramp
        if self._mode == "endless":
            self._elapsed += dt
            tnorm = max(0.0, min(1.0, self._elapsed / RAMP_DURATION))
            smooth = tnorm * tnorm * (3 - 2 * tnorm)
            target = smooth * MAX_PHASE
            self._phase += (target - self._phase) * RAMP_RATE

        # control (X only)
        if self._control == "mouse":
            accel = 900.0
            damping = 0.88
            maxs = 520.0
            dx = self.mx - self.px
            self.vx += (1 if dx > 0 else -1 if dx < 0 else 0) * accel * dt
            sp = abs(self.vx)
            if sp > maxs:
                self.vx = (self.vx / sp) * maxs
            self.vx *= damping
            self.px += self.vx * dt
        else:
            if self.key_left:
                self.px -= self.keys_speed * dt
            if self.key_right:
                self.px += self.keys_speed * dt

        # wrap
        if self.px < -20:
            self.px += w + 40
        elif self.px > w + 20:
            self.px -= w + 40

        # phase
        if self.phase_time > 0:
            self.phase_time = max(0.0, self.phase_time - dt)

        # rows
        row_speed_mul = 1.0 + self._phase * 0.05
        for r in list(self.rows):
            r["y"] += r["speed"] * row_speed_mul * dt
            if not r["scored"] and r["y"] > self.py + 18:
                self.score += 8
                self.scoreChanged.emit(self.score)
                r["scored"] = True
            if r["y"] > h + 60:
                self.rows.remove(r)

        # row spawn cadence (randomized but bounded)
        self._row_timer -= dt
        if self._row_timer <= 0:
            self._spawn_row()
            min_iv = max(0.36, 1.15 - self._phase * 0.06)
            max_iv = max(min_iv + 0.08, 1.35 - self._phase * 0.05)
            self._row_timer = random.uniform(min_iv, max_iv)

        # powerups
        self._pow_timer -= dt
        if self._pow_timer <= 0:
            self._spawn_power()
            self._pow_timer = random.uniform(5.0, 8.0)

        for P in list(self.powerups):
            P["y"] += 160 * dt
            if (self.px - P["x"]) ** 2 + (self.py - P["y"]) ** 2 < (PLAYER_R + 8) ** 2:
                if P["kind"] == "phase":
                    self.phase_time = 2.2
                    self.score += 15
                    self.scoreChanged.emit(self.score)
                self.powerups.remove(P)
            elif P["y"] > h + 20:
                self.powerups.remove(P)

        # collisions (no phase)
        if self.phase_time <= 0:
            for r in self.rows:
                bar_y, bar_h = r["y"] - r["h"] / 2, r["h"]
                lastx = 0
                for gx, gw in r["gaps"]:
                    if gx - lastx > 2:
                        if rect_intersects_circle(
                            lastx, bar_y, gx - lastx, bar_h, self.px, self.py, PLAYER_R
                        ):
                            self._finish("hit")
                            return
                    lastx = gx + gw
                if w - lastx > 2:
                    if rect_intersects_circle(
                        lastx, bar_y, w - lastx, bar_h, self.px, self.py, PLAYER_R
                    ):
                        self._finish("hit")
                        return

        # story timer
        if self._mode == "story":
            self.time_left = max(0.0, self.time_left - dt)
            if self.time_left == 0.0:
                ok = self.score >= 260
                self._finish("success" if ok else "timeout")
                return

        # sparks
        if abs(self.vx) > 250 and random.random() < 0.25:
            self.sparks.append(
                {
                    "x": self.px,
                    "y": self.py + 8,
                    "vx": random.uniform(-40, 40),
                    "vy": 50,
                    "life": 0.35,
                }
            )
        for s in list(self.sparks):
            s["x"] += s["vx"] * dt
            s["y"] += s["vy"] * dt
            s["life"] -= dt
            if s["life"] <= 0:
                self.sparks.remove(s)
        if len(self.sparks) > 600:
            del self.sparks[: len(self.sparks) - 600]

    # ---- input
    def mouseMoveEvent(self, e):
        if self._control == "mouse":
            self.mx = e.position().x()

    def keyPressEvent(self, e: QtGui.QKeyEvent):
        if e.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            if not self.running:
                self.reset()
                self.start()
                return
        if self._control == "keys":
            if e.key() in (QtCore.Qt.Key_Left, QtCore.Qt.Key_A):
                self.key_left = True
                return
            if e.key() in (QtCore.Qt.Key_Right, QtCore.Qt.Key_D):
                self.key_right = True
                return
        super().keyPressEvent(e)

    def keyReleaseEvent(self, e: QtGui.QKeyEvent):
        if self._control == "keys":
            if e.key() in (QtCore.Qt.Key_Left, QtCore.Qt.Key_A):
                self.key_left = False
                return
            if e.key() in (QtCore.Qt.Key_Right, QtCore.Qt.Key_D):
                self.key_right = False
                return
        super().keyReleaseEvent(e)

    def showEvent(self, e):
        super().showEvent(e)
        self.setFocus(QtCore.Qt.ActiveWindowFocusReason)

    # ---- finish
    def _finish(self, reason: str):
        self.running = False
        self.best = max(self.best, self.score)
        self.bestChanged.emit(self.best)
        mode = "phantom-endless" if self._mode == "endless" else "phantom-story-1"
        self.runEnded.emit(
            self.score, mode, "success" if reason == "success" else reason
        )

    # ---- paint
    def paintEvent(self, e: QtGui.QPaintEvent):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        w, h = self.width(), self.height()
        t = time.perf_counter()

        # BG
        grad = QtGui.QLinearGradient(0, 0, w, h)
        a = self._theme.bgA + math.sin(t * 0.7) * 18
        b = self._theme.bgB + math.cos(t * 0.6) * 18
        grad.setColorAt(0, QtGui.QColor.fromHsl(int(a) % 360, 180, 15))
        grad.setColorAt(1, QtGui.QColor.fromHsl(int(b) % 360, 180, 18))
        p.fillRect(self.rect(), grad)
        p.setOpacity(0.08)
        for i in range(3):
            rad = 180 + i * 140 + (math.sin(t * 0.5 + i) * 40)
            p.setBrush(QtGui.QColor(255, 255, 255, 20))
            p.setPen(QtCore.Qt.NoPen)
            p.drawEllipse(QtCore.QPointF(w * 0.5, h * 0.2 + i * 120), rad, rad)
        p.setOpacity(1.0)

        # rows
        bar_col = QtGui.QColor(220, 235, 255, 48)
        edge_col = QtGui.QColor(220, 235, 255, 120)
        p.setPen(QtCore.Qt.NoPen)
        for r in self.rows:
            y = r["y"]
            hh = r["h"]
            p.setBrush(bar_col)
            p.drawRect(0, int(y - hh / 2), w, int(hh))
            p.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
            for gx, gw in r["gaps"]:
                p.drawRect(int(gx), int(y - hh / 2 - 2), int(gw), int(hh + 4))
            p.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
            p.setPen(QtGui.QPen(edge_col, 1.2))
            p.drawLine(0, int(y - hh / 2), w, int(y - hh / 2))
            p.drawLine(0, int(y + hh / 2), w, int(y + hh / 2))
            p.setPen(QtCore.Qt.NoPen)

        # powerups
        for P in self.powerups:
            pul = 1 + math.sin(t * 8) * 0.2
            col = QtGui.QColor(120, 220, 255, 220)
            glow = QtGui.QColor(120, 220, 255, 90)
            p.setBrush(glow)
            p.drawEllipse(QtCore.QPointF(P["x"], P["y"]), 12 * pul, 12 * pul)
            p.setBrush(col)
            p.drawEllipse(QtCore.QPointF(P["x"], P["y"]), 8 * pul, 8 * pul)

        # player (always facing up)
        sp = abs(self.vx)
        trail = min(sp * 0.03, 12)
        p.save()
        p.translate(self.px, self.py)
        p.rotate(-90)
        glowA = QtGui.QColor(self._theme.playerA)
        glowA.setAlpha(100)
        p.setBrush(glowA)
        p.setPen(QtCore.Qt.NoPen)
        p.drawEllipse(
            QtCore.QPointF(0, 0), PLAYER_R + trail * 0.6, PLAYER_R + trail * 0.6
        )
        grad2 = QtGui.QLinearGradient(-trail, -PLAYER_R, PLAYER_R, PLAYER_R)
        grad2.setColorAt(0, QtGui.QColor(self._theme.playerA))
        grad2.setColorAt(1, QtGui.QColor(self._theme.playerB))
        p.setBrush(QtGui.QBrush(grad2))
        path = QtGui.QPainterPath()
        path.moveTo(PLAYER_R + 2, 0)
        path.lineTo(-PLAYER_R - trail, -PLAYER_R * 0.75)
        path.lineTo(-PLAYER_R - trail, PLAYER_R * 0.75)
        path.closeSubpath()
        p.drawPath(path)
        p.restore()

        if self.phase_time > 0:
            a = int(160 * (0.5 + 0.5 * math.sin(t * 14)))
            p.setPen(QtGui.QPen(QtGui.QColor(120, 220, 255, a), 2))
            p.setBrush(QtCore.Qt.NoBrush)
            p.drawEllipse(QtCore.QPointF(self.px, self.py), PLAYER_R + 6, PLAYER_R + 6)

        p.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 160), 1.2))
        for s in self.sparks:
            p.drawLine(s["x"], s["y"], s["x"] - s["vx"] * 0.03, s["y"] - s["vy"] * 0.03)

        p.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 150)))
        p.setFont(QtGui.QFont("Inter", 10, QtGui.QFont.Bold))
        mode = "Endless" if self._mode == "endless" else "Story"
        ctrl = "Mouse" if self._control == "mouse" else "Keys"
        phase = f" | Phase: {self.phase_time:.1f}s" if self.phase_time > 0 else ""
        p.drawText(10, h - 12, f"Phantom Run — {mode} | Ctrl: {ctrl}{phase}")
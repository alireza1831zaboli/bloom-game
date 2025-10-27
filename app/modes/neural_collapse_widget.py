from PySide6 import QtWidgets, QtGui, QtCore
import math, random, time
from app.settings import (
    THEMES,
    RAMP_DURATION,
    RAMP_RATE,
    MAX_PHASE,
    INITIAL_TIME_ENDLESS,
)

# -------------------------
#  Neural Collapse — Widget
#  Survive inside the shrinking safe circle.
#  – Safe circle shrinks over time (collapse)
#  – Collect "Stabilizer" pickups to freeze/expand
#  – Glitch shards cross the area as moving hazards
#  – Endless: no timer (ends on hit). Story: survive until time=0 (success)
#  – Control: Mouse (soft follow) or Keys (left/right steer + constant forward)
# -------------------------

PLAYER_R = 10
HIT_R2 = 22 * 22  # collision radius^2 vs glitches
PICK_R2 = 26 * 26  # pick distance^2 for stabilizers


class NeuralCollapseWidget(QtWidgets.QWidget):
    # unified signals (compatible with your MainWindow toolbars)
    scoreChanged = QtCore.Signal(int)
    timeChanged = QtCore.Signal(int)  # <= only for Story
    bestChanged = QtCore.Signal(int)
    runEnded = QtCore.Signal(
        int, str, str
    )  # score, mode, reason ("hit","timeout","success")
    screenshotSaved = QtCore.Signal(str)
    started = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setMouseTracking(True)

        # options
        self._lang = "fa"
        self._theme = THEMES.get("Aurora")
        self._mode = "endless"  # "endless" | "story"
        self._control_mode = "mouse"  # "mouse" | "keys"
        self._sfx = True

        # player state
        self.px = self.py = 0.0
        self.vx = self.vy = 0.0
        self.mx = self.my = 0.0
        # keys control
        self.heading = 0.0
        self.turn_speed = math.radians(180)  # rad/s
        self.forward_speed = 240.0
        self.key_left = self.key_right = False

        # run state
        self.running = False
        self.paused = False
        self.score = 0
        self.best = 0
        self.time_left = 0.0  # story only
        self.phase_val = 0.0
        self._elapsed_endless = 0.0

        # collapse mechanics
        self.safe_center = (0.0, 0.0)
        self.safe_r = 160.0  # current radius
        self.safe_r_base = 220.0  # base radius at start
        self.collapse_rate = 8.0  # px / sec, ramps up with phase
        self.freeze_timer = 0.0  # stabilizer effect

        # entities
        self.shards = []  # moving hazards
        self.picks = []  # stabilizers
        self.sparks = []  # cosmetic

        # spawn timers (seconds)
        self.timers = {
            "shard": 1.2,
            "pick": 6.0,
        }
        self.base_timers = dict(self.timers)

        # loop timing
        self._last = time.perf_counter()
        self._acc = 0.0
        self._step = 1 / 60.0
        self._ui_acc = 0.0

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000 // 120)

    # ------------ public config ------------
    def set_lang(self, lang: str):
        self._lang = lang

    def set_theme(self, name: str):
        if name in THEMES:
            self._theme = THEMES[name]
            self.update()

    def set_mode(self, mode: str):
        self._mode = mode

    def set_control_mode(self, mode: str):
        self._control_mode = "keys" if str(mode).lower().startswith("k") else "mouse"

    def set_music(self, on: bool):
        pass

    def set_sfx(self, on: bool):
        self._sfx = on

    # ------------ lifecycle ------------
    def prepare_endless(self, _ignored: int = 0):
        self._reset_world()
        self._mode = "endless"
        self.time_left = 0.0
        self.scoreChanged.emit(self.score)
        self.bestChanged.emit(self.best)
        self.update()

    def prepare_story(self, idx: int = 0):
        # simple story: survive for fixed time; ramps difficulty smoothly
        self._reset_world()
        self._mode = "story"
        self.time_left = 60.0 + idx * 10.0
        self.timeChanged.emit(int(self.time_left))
        self.scoreChanged.emit(self.score)
        self.bestChanged.emit(self.best)
        self.update()

    def start(self):
        if self._mode == "story" and self.time_left <= 0:
            return
        self.running = True
        self.paused = False
        self._last = time.perf_counter()
        self.started.emit()

    def toggle_pause(self):
        if self.running:
            self.paused = not self.paused

    def reset(self):
        if self._mode == "endless":
            self.prepare_endless()
        else:
            self.prepare_story(0)

    # ------------ internals ------------
    def _reset_world(self):
        w = max(1, self.width())
        h = max(1, self.height())
        self.px = w / 2
        self.py = h / 2
        self.vx = self.vy = 0.0
        self.mx = self.px
        self.my = self.py
        self.heading = 0.0
        self.key_left = self.key_right = False

        self.score = 0
        self.phase_val = 0.0
        self._elapsed_endless = 0.0
        self.safe_center = (w / 2.0, h / 2.0)
        self.safe_r_base = min(w, h) * 0.35
        self.safe_r = self.safe_r_base
        self.freeze_timer = 0.0

        self.shards.clear()
        self.picks.clear()
        self.sparks.clear()
        self.timers = dict(self.base_timers)

    def _tick(self):
        now = time.perf_counter()
        dt = min(0.05, now - self._last)
        self._last = now

        if self.running and not self.paused:
            self._acc += dt
            while self._acc >= self._step:
                self._update(self._step)
                self._acc -= self._step
                self._ui_acc += self._step
                if self._mode == "story" and self._ui_acc >= 0.1:
                    self.timeChanged.emit(max(0, int(math.ceil(self.time_left))))
                    self._ui_acc = 0.0
        self.update()

    def _update(self, dt: float):
        w = self.width()
        h = self.height()

        # --- difficulty ramp
        if self._mode == "endless":
            self._elapsed_endless += dt
            tnorm = max(0.0, min(1.0, (self._elapsed_endless / RAMP_DURATION)))
            smooth = tnorm * tnorm * (3 - 2 * tnorm)
            target = smooth * MAX_PHASE
            self.phase_val += (target - self.phase_val) * RAMP_RATE
        else:
            # map from (remaining time) to softer phase ramp
            full = max(30.0, self.time_left + 1.0)
            elapsed = full - self.time_left
            tnorm = max(0.0, min(1.0, elapsed / full))
            smooth = tnorm * tnorm * (3 - 2 * tnorm)
            target = smooth * (MAX_PHASE * 0.6)
            self.phase_val += (target - self.phase_val) * RAMP_RATE

        # --- collapse of safe circle
        if self.freeze_timer > 0:
            self.freeze_timer -= dt
        else:
            self.safe_r = max(
                60.0, self.safe_r - (self.collapse_rate + self.phase_val * 2.2) * dt
            )

        # --- spawns (accelerated by phase)
        acc = 1.0 + self.phase_val * 0.06
        for k in ("shard", "pick"):
            self.timers[k] -= dt * (acc if k == "shard" else 1.0)

        if self.timers["shard"] <= 0:
            self._spawn_shard(w, h)
            # faster spawns as phase grows
            self.timers["shard"] = max(
                0.45, self.base_timers["shard"] - self.phase_val * 0.05
            )

        if self.timers["pick"] <= 0:
            self._spawn_pick(w, h)
            self.timers["pick"] = max(
                3.0, self.base_timers["pick"] + random.uniform(-2, 2)
            )

        # --- movement
        if self._control_mode == "mouse":
            accel = 700.0
            damping = 0.88
            maxs = 300.0
            dx = self.mx - self.px
            dy = self.my - self.py
            self.vx += (1 if dx > 0 else -1 if dx < 0 else 0) * accel * dt
            self.vy += (1 if dy > 0 else -1 if dy < 0 else 0) * accel * dt
            sp = math.hypot(self.vx, self.vy)
            if sp > maxs:
                sc = maxs / sp
                self.vx *= sc
                self.vy *= sc
            self.vx *= damping
            self.vy *= damping
            self.px = max(0, min(w, self.px + self.vx * dt))
            self.py = max(0, min(h, self.py + self.vy * dt))
        else:
            if self.key_left:
                self.heading -= self.turn_speed * dt
            if self.key_right:
                self.heading += self.turn_speed * dt
            self.px = max(
                0, min(w, self.px + math.cos(self.heading) * self.forward_speed * dt)
            )
            self.py = max(
                0, min(h, self.py + math.sin(self.heading) * self.forward_speed * dt)
            )

        # --- shards movement & life
        for s in self.shards:
            s["x"] += s["vx"] * dt
            s["y"] += s["vy"] * dt
            s["life"] -= dt
        self.shards = [s for s in self.shards if s["life"] > 0]

        # --- sparks fade
        for spk in self.sparks:
            spk["x"] += spk["vx"] * dt
            spk["y"] += spk["vy"] * dt
            spk["life"] -= dt
        self.sparks = [spk for spk in self.sparks if spk["life"] > 0]

        # --- collisions
        # outside safe?
        dx = self.px - self.safe_center[0]
        dy = self.py - self.safe_center[1]
        if dx * dx + dy * dy > (self.safe_r - PLAYER_R * 0.5) ** 2:
            # player outside the safe circle
            self._end_run("hit")
            return

        # shards
        i = len(self.shards) - 1
        while i >= 0:
            s = self.shards[i]
            if (self.px - s["x"]) ** 2 + (self.py - s["y"]) ** 2 < HIT_R2:
                self._emit_sparks(s["x"], s["y"], 0, 14, 130)
                self._end_run("hit")
                return
            i -= 1

        # picks
        i = len(self.picks) - 1
        while i >= 0:
            p = self.picks[i]
            if (self.px - p["x"]) ** 2 + (self.py - p["y"]) ** 2 < PICK_R2:
                self.picks.pop(i)
                # effect: small expand + freeze collapse briefly
                self.safe_r = min(self.safe_r_base, self.safe_r + 22.0)
                self.freeze_timer = 2.0
                self.score += 10
                self.scoreChanged.emit(self.score)
                self._emit_sparks(p["x"], p["y"], 200, 20, 150)
            i -= 1

        # story time
        if self._mode == "story":
            self.time_left = max(0.0, self.time_left - dt)
            if self.time_left <= 0.0:
                self._end_run("success")
                return
        else:
            # endless score by survival time
            self.score += int(dt * 5.0)
            # emit sparsely to avoid too many updates
            # (اختیاری) می‌توان هر 0.5s آپدیت کرد؛ برای سادگی همینجا می‌گذاریم:
            self.scoreChanged.emit(self.score)

    # ------------ spawners ------------
    def _spawn_shard(self, w, h):
        # Spawn a shard at ring border with inward velocity + small tangential drift
        cx, cy = self.safe_center
        ang = random.uniform(0, math.tau)
        r = self.safe_r + 18.0
        x = cx + math.cos(ang) * r
        y = cy + math.sin(ang) * r

        speed = 120.0 + self.phase_val * 6.0
        vx = -math.cos(ang) * speed + math.cos(ang + math.pi / 2.0) * random.uniform(
            -28, 28
        )
        vy = -math.sin(ang) * speed + math.sin(ang + math.pi / 2.0) * random.uniform(
            -28, 28
        )
        hue = random.uniform(0, 30)

        self.shards.append(
            {"x": x, "y": y, "vx": vx, "vy": vy, "r": 8.0, "hue": hue, "life": 4.0}
        )

    def _spawn_pick(self, w, h):
        # pick appears inside the safe circle
        cx, cy = self.safe_center
        for _ in range(10):
            ang = random.uniform(0, math.tau)
            rad = random.uniform(30.0, max(30.0, self.safe_r - 30.0))
            x = cx + math.cos(ang) * rad
            y = cy + math.sin(ang) * rad
            # ensure inside
            if (x - cx) ** 2 + (y - cy) ** 2 < (self.safe_r - 18.0) ** 2:
                break
        self.picks.append({"x": x, "y": y, "pulse": 0.0})

    def _emit_sparks(self, x, y, hue, n=12, speed=120):
        for i in range(n):
            ang = (i / n) * math.tau + random.uniform(-0.15, 0.15)
            self.sparks.append(
                {
                    "x": x,
                    "y": y,
                    "vx": math.cos(ang) * (speed + random.uniform(-20, 20)),
                    "vy": math.sin(ang) * (speed + random.uniform(-20, 20)),
                    "life": random.uniform(0.4, 0.8),
                    "hue": hue,
                }
            )

    # ------------ events ------------
    def mouseMoveEvent(self, e: QtGui.QMouseEvent):
        if self._control_mode == "mouse":
            self.mx = e.position().x()
            self.my = e.position().y()

    def resizeEvent(self, e):
        if self.px == 0 and self.py == 0:
            self.px = self.width() / 2
            self.py = self.height() / 2
        # مرکز و شعاع پایگاه را دوباره محاسبه کن
        self.safe_center = (self.width() / 2.0, self.height() / 2.0)
        self.safe_r_base = min(self.width(), self.height()) * 0.35
        self.safe_r = min(max(self.safe_r, 60.0), self.safe_r_base)

    def keyPressEvent(self, e: QtGui.QKeyEvent):
        if self._control_mode == "keys":
            if e.key() in (QtCore.Qt.Key_Left, QtCore.Qt.Key_A):
                self.key_left = True
            if e.key() in (QtCore.Qt.Key_Right, QtCore.Qt.Key_D):
                self.key_right = True
        if e.key() == QtCore.Qt.Key_P:
            self._save_screenshot()

    def keyReleaseEvent(self, e: QtGui.QKeyEvent):
        if e.key() in (QtCore.Qt.Key_Left, QtCore.Qt.Key_A):
            self.key_left = False
        if e.key() in (QtCore.Qt.Key_Right, QtCore.Qt.Key_D):
            self.key_right = False

    # ------------ finish ------------
    def _end_run(self, reason: str):
        self.running = False
        self.best = max(self.best, self.score)
        self.bestChanged.emit(self.best)
        mode_name = "endless" if self._mode == "endless" else "story-0"
        if self._mode == "story" and reason == "success":
            self.runEnded.emit(self.score, mode_name, "success")
        elif self._mode == "story" and reason == "timeout":
            self.runEnded.emit(self.score, mode_name, "fail")
        else:
            self.runEnded.emit(self.score, "endless", "hit")

    # ------------ drawing ------------
    def paintEvent(self, e):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        try:
            w = self.width()
            h = self.height()
            t = time.perf_counter()

            # background gradient with subtle motion
            g = QtGui.QLinearGradient(0, 0, w, h)
            a = (self._theme.bgA + math.sin(t * 0.3) * 18) % 360
            b = (self._theme.bgB + math.cos(t * 0.25) * 18) % 360
            g.setColorAt(0, QtGui.QColor.fromHsl(int(a), 180, 16))
            g.setColorAt(1, QtGui.QColor.fromHsl(int(b), 180, 20))
            p.fillRect(self.rect(), g)

            # safe circle (glow)
            cx, cy = self.safe_center
            # outer halo
            p.setPen(QtCore.Qt.NoPen)
            p.setBrush(QtGui.QColor(120, 200, 255, 45))
            p.drawEllipse(QtCore.QPointF(cx, cy), self.safe_r + 16, self.safe_r + 16)

            # ring core
            pen = QtGui.QPen(QtGui.QColor(180, 220, 255, 160))
            pen.setWidthF(2.0)
            pen.setCapStyle(QtCore.Qt.RoundCap)
            p.setPen(pen)
            p.setBrush(QtCore.Qt.NoBrush)
            p.drawEllipse(QtCore.QPointF(cx, cy), self.safe_r, self.safe_r)

            # shards (hazards)
            for s in self.shards:
                core = QtGui.QColor.fromHsl(int(s["hue"]) % 360, 220, 160, 230)
                halo = QtGui.QColor.fromHsl(int(s["hue"]) % 360, 220, 120, 90)
                p.setPen(QtCore.Qt.NoPen)
                p.setBrush(halo)
                p.drawEllipse(QtCore.QPointF(s["x"], s["y"]), s["r"] + 5, s["r"] + 5)
                p.setBrush(core)
                p.drawEllipse(QtCore.QPointF(s["x"], s["y"]), s["r"], s["r"])

            # stabilizer pickups
            for pk in self.picks:
                pk["pulse"] = pk.get("pulse", 0.0) + 0.016
                pul = 1 + math.sin(pk["pulse"] * 6.0) * 0.25
                col = QtGui.QColor(120, 230, 255, 220)
                glow = QtGui.QColor(120, 230, 255, 90)
                p.setPen(QtCore.Qt.NoPen)
                p.setBrush(glow)
                p.drawEllipse(
                    QtCore.QPointF(pk["x"], pk["y"]), 12 * pul + 3, 12 * pul + 3
                )
                p.setBrush(col)
                p.drawEllipse(QtCore.QPointF(pk["x"], pk["y"]), 12 * pul, 12 * pul)

            # sparks
            pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 180))
            pen.setWidthF(1.4)
            pen.setCapStyle(QtCore.Qt.RoundCap)
            p.setPen(pen)
            for spk in self.sparks:
                alpha = max(0, min(255, int(spk["life"] * 255)))
                pen.setColor(
                    QtGui.QColor.fromHsl(int(spk["hue"]) % 360, 220, 180, alpha)
                )
                p.setPen(pen)
                p.drawLine(
                    spk["x"],
                    spk["y"],
                    spk["x"] - spk["vx"] * 0.03,
                    spk["y"] - spk["vy"] * 0.03,
                )

            # player
            spd = (
                math.hypot(self.vx, self.vy)
                if self._control_mode == "mouse"
                else self.forward_speed
            )
            direction = (
                math.atan2(self.vy, self.vx)
                if self._control_mode == "mouse"
                else self.heading
            )
            trail = min(spd * 0.04, 12)
            p.save()
            p.translate(self.px, self.py)
            p.rotate(math.degrees(direction))
            # glow
            glowA = QtGui.QColor(self._theme.playerA)
            glowA.setAlpha(100)
            p.setBrush(glowA)
            p.setPen(QtCore.Qt.NoPen)
            p.drawEllipse(
                QtCore.QPointF(0, 0), PLAYER_R + trail * 0.5, PLAYER_R + trail * 0.5
            )
            # body
            grad2 = QtGui.QLinearGradient(-trail, -PLAYER_R, PLAYER_R, PLAYER_R)
            grad2.setColorAt(0, QtGui.QColor(self._theme.playerA))
            grad2.setColorAt(1, QtGui.QColor(self._theme.playerB))
            p.setBrush(QtGui.QBrush(grad2))
            p.setPen(QtCore.Qt.NoPen)
            path = QtGui.QPainterPath()
            path.moveTo(PLAYER_R + 2, 0)
            path.lineTo(-PLAYER_R - trail, -PLAYER_R * 0.75)
            path.lineTo(-PLAYER_R - trail, PLAYER_R * 0.75)
            path.closeSubpath()
            p.drawPath(path)
            p.restore()

            # footer chips (pace + ctrl)
            pace = 1 + self.phase_val * 0.15
            p.setFont(QtGui.QFont("Inter", 10, QtGui.QFont.Bold))
            pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 150))
            p.setPen(pen)
            p.drawText(
                10,
                h - 10,
                f"Pace: {pace:.2f}x  |  Ctrl: {self._control_mode.capitalize()}",
            )

        finally:
            p.end()

    # ------------ screenshots ------------
    def _save_screenshot(self):
        scr = QtGui.QGuiApplication.primaryScreen()
        if not scr:
            return
        img = scr.grabWindow(self.winId())
        ts = time.strftime("%Y%m%d_%H%M%S")
        path = f"nb_collapse_{ts}.png"
        img.save(path, "PNG")
        self.screenshotSaved.emit(path)

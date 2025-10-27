from PySide6 import QtWidgets, QtGui, QtCore
import math, random, time, os
from .settings import (
    THEMES,
    MAX_PHASE,
    RAMP_DURATION,
    INITIAL_TIME_ENDLESS,
    STORY_LEVELS,
    RAMP_RATE,
    user_data_path,
)


NODE_GRAB_R2 = 28 * 28
GLITCH_HIT_R2 = 24 * 24
PLAYER_R = 10


class GameWidget(QtWidgets.QWidget):
    scoreChanged = QtCore.Signal(int)
    timeChanged = QtCore.Signal(int)  # only Story uses this
    bestChanged = QtCore.Signal(int)
    runEnded = QtCore.Signal(
        int, str, str
    )  # score, mode, reason ("hit","timeout","success","fail")
    screenshotSaved = QtCore.Signal(str)
    started = QtCore.Signal()

    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self._theme = THEMES["Aurora"]
        self._mode = "endless"  # or "story"
        self._control_mode = "mouse"  # "mouse" | "keys"

        self._sfx = True

        self._bg_nodes = []
        self._bg_edges = []
        self._seed_bg()

        # game state
        self.running = False
        self.paused = False
        self.score = 0
        self.best = 0
        self.combo = 0
        self.time_left = 0.0  # Story only
        self.phase_val = 0.0
        self.story_idx = 0
        self.story_levels = STORY_LEVELS
        self.nohit_failed = False
        self._endless_elapsed = 0.0

        # keyboard control state
        self.heading = 0.0  # radians
        self.turn_speed = math.radians(180)  # rad/s (قابل تغییر)
        self._mouse_sens = 1.0
        self._difficulty = 'Normal'
        self.forward_speed = 240.0  # px/s ثابت در حالت keys
        self.key_left = False
        self.key_right = False

        # level modifiers (story)
        self.level_mods = {
            "spawnMul": 1.0,
            "glitchSpeedMul": 1.0,
            "powerFreq": 9.5,
            "theme": "Aurora",
        }

        # entities
        self.nodes = []
        self.glitches = []
        self.sparks = []
        self.powers = []

        # timers / powers
        self.base_node = 1.1
        self.base_glitch = 2.4
        self.base_power = 9.5
        self.timers = {
            "node": self.base_node,
            "glitch": self.base_glitch,
            "power": self.base_power,
        }
        self.power_state = {"slowmo": 0.0, "shield": 0.0, "burst": 0.0}

        # player physics (mouse mode)
        self.px = 0.0
        self.py = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.mx = 0.0
        self.my = 0.0

        # Fixed timestep loop
        self._last = time.perf_counter()
        self._acc = 0.0
        self._step = 1 / 60.0
        self._ui_acc = 0.0
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000 // 120)

        self._run_started_ts = None
        self._hints = []  # (t_start, t_end, text)
        self._lang = "fa"  # جهت انتخاب متن‌ها؛ از MainWindow ست می‌شود در set_lang

        # برای Photo Mode فلگ کوچک
        self._photo_flash_ts = 0.0

    def set_lang(self, lang: str):
        self._lang = lang

    # ---- Public API
    def set_theme(self, name: str):
        self._theme = THEMES.get(name, self._theme)
        self.update()

    def set_mode(self, mode: str):
        self._mode = mode

    def set_control_mode(self, mode: str):
        self._control_mode = "keys" if mode.lower().startswith("k") else "mouse"

    def set_music(self, on: bool):
        pass

    def set_sfx(self, on: bool):
        self._sfx = on

    def prepare_endless(self, _seconds_ignored: int = 0):
        """Endless: بدون تایمر؛ تا اولین برخورد ادامه دارد."""
        self._reset_world()
        self._endless_elapsed = 0.0
        self.time_left = 0.0  # not used in endless
        self.running = False
        self.update()
        self.scoreChanged.emit(self.score)
        self.bestChanged.emit(self.best)

    def prepare_story(self, idx: int):
        idx = max(0, min(idx, len(self.story_levels) - 1))
        self.story_idx = idx
        lvl = self._current_level()
        self._reset_world()
        self.time_left = float(lvl.get("time", 60.0))
        self._apply_level_mods(lvl.get("mods", {}))
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
        self._run_started_ts = time.perf_counter()
        self._prepare_hints()
        self.started.emit()
        super().start() if hasattr(super(), "start") else None  # در صورت ارث‌بری آینده

    def toggle_pause(self):
        if not self.running:
            return
        self.paused = not self.paused

    def reset(self):
        if self._mode == "endless":
            self.prepare_endless()
        else:
            self.prepare_story(self.story_idx)

    # ---- Internal helpers
    def _reset_world(self):
        self.score = 0
        self.combo = 0
        self.phase_val = 0.0
        self.nohit_failed = False

        self.nodes.clear()
        self.glitches.clear()
        self.sparks.clear()
        self.powers.clear()

        self.base_node = 1.1
        self.base_glitch = 2.4
        self.base_power = 9.5
        self.timers = {"node": 0.6, "glitch": 1.5, "power": 3.5}
        self.power_state = {"slowmo": 0.0, "shield": 0.0, "burst": 0.0}

        w = max(1, self.width())
        h = max(1, self.height())
        self.px = w / 2.0
        self.py = h / 2.0
        self.vx = self.vy = 0.0
        self.mx = self.px
        self.my = self.py

        # reset keyboard heading to the right
        self.heading = 0.0
        self.key_left = self.key_right = False

    def _current_level(self):
        if self.story_levels and 0 <= self.story_idx < len(self.story_levels):
            return self.story_levels[self.story_idx]
        return {
            "id": 0,
            "title": "Level",
            "objective": {},
            "time": 60,
            "mods": self.level_mods,
        }

    def _apply_level_mods(self, mods: dict):
        self.level_mods.update(
            {
                "spawnMul": 1.0,
                "glitchSpeedMul": 1.0,
                "powerFreq": 9.5,
                "theme": "Aurora",
            }
        )
        self.level_mods.update(mods or {})
        self.base_node = 1.1 / max(0.3, self.level_mods["spawnMul"])
        self.base_glitch = 2.4 / max(0.3, self.level_mods["spawnMul"])
        self.base_power = float(self.level_mods["powerFreq"])
        th = self.level_mods.get("theme")
        if th in THEMES:
            self._theme = THEMES[th]

    def _initial_span(self):
        return float(INITIAL_TIME_ENDLESS)

    # ---- Loop
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

    # ---- Update
    def _update(self, dt: float):
        w = self.width()
        h = self.height()

        # phase ramp
        if self._mode == "endless":
            self._endless_elapsed += dt
            tnorm = max(0.0, min(1.0, (self._endless_elapsed / RAMP_DURATION)))
            smooth = tnorm * tnorm * (3 - 2 * tnorm)
            target = smooth * MAX_PHASE
            self.phase_val += (target - self.phase_val) * RAMP_RATE
        else:
            lvl_time = self._current_level().get("time", 60)
            elapsed = max(0.0, lvl_time - self.time_left)
            tnorm = max(0.0, min(1.0, elapsed / max(30.0, float(lvl_time))))
            smooth = tnorm * tnorm * (3 - 2 * tnorm)
            target = smooth * (MAX_PHASE * 0.5)
            self.phase_val += (target - self.phase_val) * RAMP_RATE

        # timers with slowmo
        slowmul = 0.5 if self.power_state["slowmo"] > 0 else 1.0
        self.timers["node"] -= dt * (1 + self.phase_val * 0.04) * slowmul
        self.timers["glitch"] -= dt * (1 + self.phase_val * 0.08) * slowmul
        self.timers["power"] -= dt * slowmul

        if self.timers["node"] <= 0:
            self._spawn_node(w, h)
            self.timers["node"] = max(0.5, self.base_node - self.phase_val * 0.04)
        if self.timers["glitch"] <= 0:
            self._spawn_glitch(w, h)
            self.timers["glitch"] = max(0.8, self.base_glitch - self.phase_val * 0.08)
        if self.timers["power"] <= 0:
            self._spawn_power(w, h)
            self.timers["power"] = max(2.5, self.base_power + random.uniform(-2, 2))

        # movement
        if self._control_mode == "mouse":
            accel = 700
            damping = 0.88
            maxs = 300
            dx = self.mx - self.px
            dy = self.my - self.py
            self.vx += (1 if dx > 0 else -1 if dx < 0 else 0) * accel * dt
            self.vy += (1 if dy > 0 else -1 if dy < 0 else 0) * accel * dt
            sp = math.hypot(self.vx, self.vy)
            if sp > maxs:
                self.vx = self.vx / sp * maxs
                self.vy = self.vy / sp * maxs
            self.vx *= damping
            self.vy *= damping
            self.px += self.vx * dt
            self.py += self.vy * dt
            if self.px < 0:
                self.px += w
            elif self.px > w:
                self.px -= w
            if self.py < 0:
                self.py += h
            elif self.py > h:
                self.py -= h

        else:
            # keys mode: constant forward + left/right turn
            if self.key_left:
                self.heading -= self.turn_speed * dt
            if self.key_right:
                self.heading += self.turn_speed * dt

            self.px += math.cos(self.heading) * self.forward_speed * dt
            self.py += math.sin(self.heading) * self.forward_speed * dt
            if self.px < 0:
                self.px += w
            elif self.px > w:
                self.px -= w
            if self.py < 0:
                self.py += h
            elif self.py > h:
                self.py -= h

        # entities
        for n in self.nodes:
            n["t"] += dt
        for g in self.glitches:
            sm = 0.6 if self.power_state["slowmo"] > 0 else 1.0
            speedmul = self.level_mods.get("glitchSpeedMul", 1.0)
            g["x"] += g["vx"] * dt * sm * speedmul
            g["y"] += g["vy"] * dt * sm * speedmul
            g["life"] -= dt
            if g["x"] < 0 or g["x"] > w:
                g["vx"] *= -1
            if g["y"] < 0 or g["y"] > h:
                g["vy"] *= -1
        self.glitches = [g for g in self.glitches if g["life"] > 0]

        for p in self.sparks:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt
        self.sparks = [p for p in self.sparks if p["life"] > 0]
        for p in self.powers:
            p["pulse"] += dt

        # power timers
        for k in ("slowmo", "shield", "burst"):
            if self.power_state[k] > 0:
                self.power_state[k] -= dt

        # collisions
        i = len(self.nodes) - 1
        while i >= 0:
            n = self.nodes[i]
            if (self.px - n["x"]) ** 2 + (self.py - n["y"]) ** 2 < NODE_GRAB_R2:
                self.nodes.pop(i)
                self._emit_sparks(n["x"], n["y"], n["hue"], 16, 120)
                self.combo = min(99, self.combo + 1)
                gain = 8 + self.combo * 3
                self.score += gain
                self.scoreChanged.emit(self.score)
            i -= 1

        i = len(self.powers) - 1
        while i >= 0:
            p = self.powers[i]
            if (self.px - p["x"]) ** 2 + (self.py - p["y"]) ** 2 < NODE_GRAB_R2:
                self.powers.pop(i)
                if p["type"] == "slowmo":
                    self.power_state["slowmo"] = 4
                if p["type"] == "shield":
                    self.power_state["shield"] = 5
                if p["type"] == "burst":
                    self.power_state["burst"] = 1.2
                self._emit_sparks(p["x"], p["y"], 50, 28, 140)
            i -= 1

        i = len(self.glitches) - 1
        while i >= 0:
            g = self.glitches[i]
            if (self.px - g["x"]) ** 2 + (self.py - g["y"]) ** 2 < GLITCH_HIT_R2:
                if self.power_state["shield"] > 0 or self.power_state["burst"] > 0:
                    self.glitches.pop(i)
                    self._emit_sparks(g["x"], g["y"], g["hue"], 18, 160)
                    self.score += 12
                    self.scoreChanged.emit(self.score)
                else:
                    # ENDLESS & STORY: پایان با برخورد
                    self._game_over("hit")
                    return
            i -= 1

        # time only for Story
        if self._mode == "story":
            self.time_left = max(0.0, self.time_left - dt)
            if self.time_left == 0.0:
                self._finish_story_on_timeout()
                return

    def _finish_story_on_timeout(self):
        self.running = False
        self.best = max(self.best, self.score)
        self.bestChanged.emit(self.best)
        lvl = self._current_level()
        obj = lvl.get("objective", {})
        ok_collect = (
            (self.score >= (obj.get("collect", 0) * 8)) if "collect" in obj else True
        )
        ok_score = (self.score >= obj.get("score", 0)) if "score" in obj else True
        ok_nohit = not (obj.get("nohit") and self.nohit_failed)
        if ok_collect and ok_score and ok_nohit:
            self.runEnded.emit(self.score, f"story-{lvl['id']}", "success")
        else:
            self.runEnded.emit(self.score, f"story-{lvl['id']}", "fail")

    def _game_over(self, reason: str):
        self.running = False
        self.best = max(self.best, self.score)
        self.bestChanged.emit(self.best)
        if self._mode == "endless":
            self.runEnded.emit(self.score, "endless", reason)
        else:
            lvl = self._current_level()
            self.runEnded.emit(
                self.score,
                f"story-{lvl['id']}",
                "fail" if reason != "success" else "success",
            )

    # ---- Spawners
    def _spawn_node(self, w, h):
        self.nodes.append(
            {
                "x": random.uniform(40, w - 40),
                "y": random.uniform(40, h - 40),
                "r": random.uniform(6, 10),
                "t": 0.0,
                "hue": random.uniform(180, 320),
            }
        )

    def _spawn_glitch(self, w, h):
        speed = random.uniform(28, 60) * (1 + self.phase_val * 0.06)
        ang = random.uniform(0, math.tau)
        self.glitches.append(
            {
                "x": random.uniform(0, w),
                "y": random.uniform(0, h),
                "vx": math.cos(ang) * speed,
                "vy": math.sin(ang) * speed,
                "r": random.uniform(9, 12),
                "hue": random.uniform(0, 20),
                "life": random.uniform(6, 12),
            }
        )

    def _spawn_power(self, w, h):
        t = random.choice(["slowmo", "shield", "burst"])
        self.powers.append(
            {
                "x": random.uniform(40, w - 40),
                "y": random.uniform(40, h - 40),
                "r": 10,
                "type": t,
                "pulse": 0.0,
            }
        )

    def _emit_sparks(self, x, y, hue, n=12, speed=90):
        for i in range(n):
            ang = (i / n) * math.tau + random.uniform(-0.1, 0.1)
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

    # ---- Events
    def mouseMoveEvent(self, e):
        if self._control_mode == "mouse":
            self.mx = e.position().x()
            self.my = e.position().y()

    def resizeEvent(self, e):
        if self.px == 0 and self.py == 0:
            self.px = self.width() / 2
            self.py = self.height() / 2

    def keyPressEvent(self, e: QtGui.QKeyEvent):
        # Photo Mode
        if e.key() == QtCore.Qt.Key_P:
            self._save_screenshot()
            return

        # Quick Retry با Enter (وقتی ران تمام شده)
        if e.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            if not self.running:  # به‌جای self._state
                self.reset()
                self.start()
                return

        # کنترل Keys: چپ/راست
        if self._control_mode == "keys":
            if e.key() in (QtCore.Qt.Key_Left, QtCore.Qt.Key_A):
                self.key_left = True
                return
            if e.key() in (QtCore.Qt.Key_Right, QtCore.Qt.Key_D):
                self.key_right = True
                return

        super().keyPressEvent(e)

    def keyReleaseEvent(self, e: QtGui.QKeyEvent):
        if e.key() in (QtCore.Qt.Key_Left, QtCore.Qt.Key_A):
            self.key_left = False
            return
        if e.key() in (QtCore.Qt.Key_Right, QtCore.Qt.Key_D):
            self.key_right = False
            return
        super().keyReleaseEvent(e)

    # ---- Draw helpers (new)
    def _draw_vignette_and_bands(self, p: QtGui.QPainter, w: int, h: int, t: float):
        # Vignette
        vg = QtGui.QRadialGradient(QtCore.QPointF(w * 0.5, h * 0.55), max(w, h) * 0.65)
        vg.setColorAt(0.0, QtGui.QColor(0, 0, 0, 0))
        vg.setColorAt(0.7, QtGui.QColor(0, 0, 0, 80))
        vg.setColorAt(1.0, QtGui.QColor(0, 0, 0, 160))
        p.fillRect(0, 0, w, h, vg)

        # Subtle diagonal bands
        p.save()
        p.setOpacity(0.06)
        stripe = QtGui.QLinearGradient(0, 0, w, h)
        stripe.setColorAt(0.0, QtGui.QColor(255, 255, 255, 20))
        stripe.setColorAt(0.5, QtGui.QColor(255, 255, 255, 0))
        stripe.setColorAt(1.0, QtGui.QColor(255, 255, 255, 20))
        p.fillRect(self.rect().adjusted(-w, 0, w, 0), stripe)
        p.restore()

    def _chip(self, p: QtGui.QPainter, x: int, y: int, text: str):
        # Small HUD chip
        fm = QtGui.QFontMetrics(p.font())
        padx, pady = 10, 6
        w = fm.horizontalAdvance(text) + padx * 2
        h = fm.height() + pady * 2
        rect = QtCore.QRectF(x, y, w, h)
        bg = QtGui.QColor(255, 255, 255, 28)
        pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 40))
        p.setPen(pen)
        p.setBrush(bg)
        p.drawRoundedRect(rect, 10, 10)
        p.drawText(
            rect.adjusted(padx, 0, -padx, 0),
            QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft,
            text,
        )

    def _seed_bg(self):
        # چند گره‌ی کم‌نور برای پس‌زمینه؛ به‌صورت ثابت در طول اجرای برنامه
        import random

        random.seed(42)
        w = max(800, self.width() or 1200)
        h = max(500, self.height() or 800)
        n = 28
        self._bg_nodes = [
            (random.uniform(0, w), random.uniform(0, h)) for _ in range(n)
        ]
        # اتصالات کم برای سبکی
        self._bg_edges.clear()
        for i in range(n):
            for j in range(i + 1, n):
                # فاصله‌ی کوتاه => احتمال اتصال
                dx = self._bg_nodes[i][0] - self._bg_nodes[j][0]
                dy = self._bg_nodes[i][1] - self._bg_nodes[j][1]
                d2 = dx * dx + dy * dy
                if d2 < (260 * 260) and random.random() < 0.12:
                    self._bg_edges.append((i, j))

    # --- draw helpers (new)
    def _draw_bg_network(self, p: QtGui.QPainter, w: int, h: int, t: float):
        p.save()
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        # پارالاکس کوچیک: با زمان کمی جابه‌جا می‌شوند
        ox = math.sin(t * 0.05) * 20
        oy = math.cos(t * 0.06) * 16

        # خطوط
        pen = QtGui.QPen(QtGui.QColor(180, 210, 255, 40), 1.0)
        p.setPen(pen)
        for i, j in self._bg_edges:
            x1 = (self._bg_nodes[i][0] + ox) % (w + 200) - 100
            y1 = (self._bg_nodes[i][1] + oy) % (h + 200) - 100
            x2 = (self._bg_nodes[j][0] + ox) % (w + 200) - 100
            y2 = (self._bg_nodes[j][1] + oy) % (h + 200) - 100
            p.drawLine(x1, y1, x2, y2)

        # گره‌ها
        p.setPen(QtCore.Qt.NoPen)
        for x, y in self._bg_nodes:
            xx = (x + ox) % (w + 200) - 100
            yy = (y + oy) % (h + 200) - 100
            p.setBrush(QtGui.QColor(160, 200, 255, 70))
            p.drawEllipse(QtCore.QPointF(xx, yy), 3.2, 3.2)
        p.restore()

    def _draw_bg_ripples(self, p: QtGui.QPainter, w: int, h: int, t: float):
        # ریپل‌های محو اطراف بازیکن
        p.save()
        p.setPen(QtGui.QPen(QtGui.QColor(200, 220, 255, 45), 1.2))
        # سه حلقه با فاز متفاوت
        for k in range(3):
            r = (t * 35 + k * 60) % 220 + 40
            alpha = int(90 - (r - 40) * 0.35)
            alpha = max(0, min(90, alpha))
            col = QtGui.QColor(200, 220, 255, alpha)
            p.setPen(QtGui.QPen(col, 1.2))
            p.drawEllipse(QtCore.QPointF(self.px, self.py), r, r)
        p.restore()

    def _prepare_hints(self):
        fa = [
            (0.0, 4.0, "با Keys بچرخان (چپ/راست) یا Mouse را انتخاب کن"),
            (4.0, 8.0, "به PowerUp نزدیک شو؛ از گلیچ دوری کن"),
            (8.0, 12.0, "کمبو بگیر تا امتیاز بیشتر شود"),
        ]
        en = [
            (0.0, 4.0, "Use Left/Right to steer (Keys) or choose Mouse"),
            (4.0, 8.0, "Grab PowerUps; avoid glitches"),
            (8.0, 12.0, "Build combos for higher score"),
        ]
        self._hints = fa if self._lang == "fa" else en

    def _save_screenshot(self):
        scr = QtGui.QGuiApplication.primaryScreen()
        if not scr:
            return
        img = scr.grabWindow(self.winId())
        p = user_data_path()
        ts = time.strftime("%Y%m%d_%H%M%S")
        fp = os.path.join(p, f"nb_{ts}.png")
        img.save(fp, "PNG")
        self.screenshotSaved.emit(fp)
        self._photo_flash_ts = time.perf_counter()

    def paintEvent(self, e: QtGui.QPaintEvent):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        w, h = self.width(), self.height()
        t = time.perf_counter()

        # پس‌زمینه: گرادیان
        grad = QtGui.QLinearGradient(0, 0, w, h)
        a = self._theme.bgA + math.sin(t) * 20
        b = self._theme.bgB + math.cos(t * 0.7) * 20
        grad.setColorAt(0, QtGui.QColor.fromHsl(int(a) % 360, 180, 15))
        grad.setColorAt(1, QtGui.QColor.fromHsl(int(b) % 360, 180, 18))
        p.fillRect(self.rect(), grad)

        # شبکه و ریپل‌ها
        self._draw_bg_network(p, w, h, t)
        self._draw_bg_ripples(p, w, h, t)

        # Nodes
        for n in self.nodes:
            s = 1 + math.sin(n["t"] * 3) * 0.15
            core = QtGui.QColor(self._theme.node)
            core.setAlpha(230)
            glow = QtGui.QColor(self._theme.node)
            glow.setAlpha(80)
            p.setPen(QtCore.Qt.NoPen)
            p.setBrush(glow)
            p.drawEllipse(
                QtCore.QPointF(n["x"], n["y"]), n["r"] * s + 6, n["r"] * s + 6
            )
            p.setBrush(core)
            p.drawEllipse(
                QtCore.QPointF(n["x"], n["y"]), n["r"] * s + 2, n["r"] * s + 2
            )

        # Glitches
        for g in self.glitches:
            halo = QtGui.QColor.fromHsl(int(g["hue"]) % 360, 240, 130, 100)
            p.setBrush(halo)
            p.setPen(QtCore.Qt.NoPen)
            p.drawEllipse(QtCore.QPointF(g["x"], g["y"]), g["r"] + 5, g["r"] + 5)
            c = QtGui.QColor.fromHsl(int(g["hue"]) % 360, 240, 180, 220)
            p.setBrush(c)
            p.drawEllipse(QtCore.QPointF(g["x"], g["y"]), g["r"] + 1.5, g["r"] + 1.5)
            p.save()
            p.translate(g["x"], g["y"])
            p.rotate(math.sin(t * 3 + g["x"] * 0.01) * 34)
            p.setPen(
                QtGui.QPen(QtGui.QColor.fromHsl(int(g["hue"]) % 360, 240, 200, 220), 2)
            )
            p.drawLine(-g["r"], 0, g["r"], 0)
            p.drawLine(0, -g["r"], 0, g["r"])
            p.restore()

        # Powerups
        for pw in self.powers:
            pul = 1 + math.sin(pw["pulse"] * 6) * 0.25
            col = (
                self._theme.powerSlow
                if pw["type"] == "slowmo"
                else (
                    self._theme.powerShield
                    if pw["type"] == "shield"
                    else self._theme.powerBurst
                )
            )
            glow = QtGui.QColor(col)
            glow.setAlpha(90)
            p.setPen(QtCore.Qt.NoPen)
            p.setBrush(glow)
            p.drawEllipse(
                QtCore.QPointF(pw["x"], pw["y"]), pw["r"] * pul + 4, pw["r"] * pul + 4
            )
            p.setBrush(QtGui.QColor(col))
            p.drawEllipse(
                QtCore.QPointF(pw["x"], pw["y"]), pw["r"] * pul, pw["r"] * pul
            )

        # Sparks
        pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 180), 1.4)
        p.setPen(pen)
        for s in self.sparks:
            alpha = max(0, min(255, int(s["life"] * 255)))
            pen.setColor(QtGui.QColor.fromHsl(int(s["hue"]) % 360, 220, 180, alpha))
            p.setPen(pen)
            p.drawLine(s["x"], s["y"], s["x"] - s["vx"] * 0.03, s["y"] - s["vy"] * 0.03)

        # Player
        sp = (
            math.hypot(self.vx, self.vy)
            if self._control_mode == "mouse"
            else self.forward_speed
        )
        direction = (
            math.atan2(self.vy, self.vx)
            if self._control_mode == "mouse"
            else self.heading
        )
        trail = min(sp * 0.04, 12)

        p.save()
        p.translate(self.px, self.py)
        p.rotate(math.degrees(direction))
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

        # Overlay زیبایی
        self._draw_vignette_and_bands(p, w, h, t)

        # HUD پایین چپ
        p.setFont(QtGui.QFont("Inter", 10, QtGui.QFont.Bold))
        pace = 1 + self.phase_val * 0.15
        self._chip(p, 10, h - 38, f"Pace: {pace:.2f}x")
        self._chip(p, 120, h - 38, f"Ctrl: {self._control_mode.capitalize()}")

        # Tutorial Hints
        if self._run_started_ts is not None and self.running:
            elapsed = t - self._run_started_ts
            for t0, t1, text in self._hints:
                if t0 <= elapsed <= t1:
                    dur = min(elapsed - t0, t1 - elapsed, 0.8)
                    alpha = int(220 * max(0.0, min(1.0, (dur / 0.8))))
                    p.save()
                    p.setPen(QtCore.Qt.NoPen)
                    bar = QtCore.QRectF(0, 0, w, 40)
                    bar.moveBottom(h - 24)
                    p.setBrush(QtGui.QColor(20, 32, 60, 180))
                    p.drawRoundedRect(bar.adjusted(16, -8, -16, 8), 10, 10)
                    p.setPen(QtGui.QPen(QtGui.QColor(210, 230, 255, alpha)))
                    align = (
                        QtCore.Qt.AlignRight
                        if self._lang == "fa"
                        else QtCore.Qt.AlignLeft
                    )
                    p.drawText(
                        bar.adjusted(28, 0, -28, 0),
                        align | QtCore.Qt.AlignVCenter,
                        text,
                    )
                    p.restore()
                    break
        # در paintEvent انتهای HUD:
        self._chip(p, 220, h - 38, f"Mode: {self.submode().capitalize()}")

        # Photo flash
        if self._photo_flash_ts and t - self._photo_flash_ts < 0.25:
            a = int(255 * (1.0 - (t - self._photo_flash_ts) / 0.25))
            p.fillRect(self.rect(), QtGui.QColor(255, 255, 255, a))

    def set_submode(self, name: str):
        # classic, weave, flow, arch, mirror, collapse
        self._submode = name

    def submode(self) -> str:
        return getattr(self, "_submode", "classic")

    def showEvent(self, e: QtGui.QShowEvent):
        super().showEvent(e)
        self.setFocus(QtCore.Qt.ActiveWindowFocusReason)

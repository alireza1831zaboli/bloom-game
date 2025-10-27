# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtGui, QtCore
import math, random, time, collections
from app.settings import (
    THEMES,
    INITIAL_TIME_ENDLESS,
    RAMP_DURATION,
    RAMP_RATE,
    MAX_PHASE,
)

NODE_R = 10
TARGET_R = 11
GLITCH_R2 = 24 * 24
SELF_COLLIDE_R2 = 12 * 12
TRAIL_MAX = 420  # compat
TRAIL_MAX_LEN = 1200.0  # pixels  # تعداد نقاط رد نور
PLAYER_R = 10


class WeaveWidget(QtWidgets.QWidget):
    # هم‌نام با GameWidget تا نوار ابزار و برچسب‌ها کار کنند
    scoreChanged = QtCore.Signal(int)
    timeChanged = QtCore.Signal(int)
    bestChanged = QtCore.Signal(int)
    runEnded = QtCore.Signal(int, str, str)  # score, mode, reason
    screenshotSaved = QtCore.Signal(str)
    started = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        # تنظیمات و حالت‌ها
        self._theme = THEMES["Aurora"]
        self._lang = "fa"
        self._mode = "endless"  # endless | story
        self._control = "mouse"  # mouse | keys
        self._phase = 0.0
        self._elapsed = 0.0

        # بازیکن
        self.px = self.width() / 2.0
        self._mx = self.px
        self._my = self.height() / 2.0
        self.py = self.height() / 2.0
        self.mx = self.px
        self.my = self.py
        self.vx = 0.0
        self.vy = 0.0
        self.heading = 0.0
        self.turn_speed = math.radians(180)
        self.forward_speed = 240.0
        self.key_left = False
        self.key_right = False

        # بازی
        self.running = False
        self.paused = False
        self.score = 0
        self.best = 0
        self.time_left = 60
        self.trail = collections.deque(maxlen=TRAIL_MAX)  # (x,y)
        self.targets = []  # {x,y,lit:bool,t:float}
        self.glitches = []  # {x,y,vx,vy,life,hue}
        self.power_state = {"shield": 0.0, "slowmo": 0.0}
        self.timers = {"glitch": 1.5, "target": 0.0}

        # گرافیک
        self._last = time.perf_counter()
        self._acc = 0.0
        self._step = 1 / 60.0
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000 // 120)

        # هینت
        self._run_started_ts = None

    # ---------- رابط تنظیمات (سازگار با GameWidget)
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

    # ---------- آماده‌سازی
    def prepare_endless(self, _ignored=INITIAL_TIME_ENDLESS):
        self._reset_world()
        self._mode = "endless"
        self.time_left = 0
        self.running = False
        self.update()
        self.scoreChanged.emit(self.score)
        self.bestChanged.emit(self.best)

    def prepare_story(self, idx: int):
        self._reset_world()
        self._mode = "story"
        # زمان مرحله: بر اساس سختی سبک
        self.time_left = 75 if idx < 5 else 60
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
        self._run_started_ts = self._last
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

    # ---------- منطق
    def _reset_world(self):
        w = max(1, self.width())
        h = max(1, self.height())
        self.score = 0
        self.trail.clear()
        self.px = w / 2
        self.py = h / 2
        self.vx = self.vy = 0.0
        self.heading = 0.0
        self.key_left = self.key_right = False
        self.targets.clear()
        self.glitches.clear()
        self.power_state = {"shield": 0.0, "slowmo": 0.0}
        self.timers = {"glitch": 1.2, "target": 0.0}
        self._phase = 0.0
        self._elapsed = 0.0
        # الگوی اولیه هدف‌ها
        self._spawn_pattern()

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

    def _update(self, dt: float):
        ## HOTFIX_PARTICLES_GUARD
        if not hasattr(self, "particles") or self.particles is None:
            self.particles = []
        ## PARTICLE_SPAWN: fading dots
        if len(self.particles) > 300:
            self.particles = self.particles[-300:]
        self.particles.append((self.px, self.py, 1.0))
        w, h = self.width(), self.height()
        # فاز سختی (نرم و تدریجی)
        if self._mode == "endless":
            self._elapsed += dt
            tnorm = max(0.0, min(1.0, self._elapsed / RAMP_DURATION))
            smooth = tnorm * tnorm * (3 - 2 * tnorm)
            target = smooth * MAX_PHASE
            self._phase += (target - self._phase) * RAMP_RATE

        # حرکت
        if self._control == "mouse":
            accel = 720
            damping = 0.88
            maxs = 320
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

        # ثبت رد نور
        self.trail.append((self.px, self.py))

        # تولید گلیچ + تکان
        spmul = 1 + self._phase * 0.08
        self.timers["glitch"] -= dt
        if self.timers["glitch"] <= 0:
            self._spawn_glitch(w, h)
            self.timers["glitch"] = max(0.6, 1.5 - self._phase * 0.05)

        for g in self.glitches:
            g["x"] += g["vx"] * dt
            g["y"] += g["vy"] * dt
            if g["x"] < 0 or g["x"] > w:
                g["vx"] *= -1
            if g["y"] < 0 or g["y"] > h:
                g["vy"] *= -1
            g["life"] -= dt
        self.glitches = [g for g in self.glitches if g["life"] > 0]

        # برخورد با گلیچ
        for g in self.glitches:
            if (self.px - g["x"]) ** 2 + (self.py - g["y"]) ** 2 < GLITCH_R2:
                if self.power_state["shield"] > 0:
                    # بی‌اثر
                    pass
                else:
                    self._finish("hit")
                    return

        # خودبرخوردی Tail
        if len(self.trail) > 24:
            hx, hy = self.trail[-1]
            for i in range(0, len(self.trail) - 24, 6):
                x, y = self.trail[i]
                if (hx - x) ** 2 + (hy - y) ** 2 < SELF_COLLIDE_R2:
                    if self.power_state["shield"] <= 0:
                        self._finish("self")
                        return
                    break

        # هدف‌ها؛ نزدیک شدن و روشن‌شدن
        all_lit = True
        for t in self.targets:
            t["t"] += dt
            if not t["lit"]:
                if (self.px - t["x"]) ** 2 + (self.py - t["y"]) ** 2 < (
                    TARGET_R + 4
                ) ** 2:
                    t["lit"] = True
                    self.score += 12
                    self.scoreChanged.emit(self.score)
            all_lit = all_lit and t["lit"]

        # اگر همه روشن شدند، پترن بعدی
        if all_lit:
            self.score += 50  # پاداش تکمیل
            self.scoreChanged.emit(self.score)
            self._spawn_pattern()

        # زمان در حالت Story
        if self._mode == "story":
            self.time_left = max(0.0, self.time_left - dt)
            if self.time_left == 0.0:
                # شرط موفقیت: حداقل N پترن؟ (ساده: امتیاز حداقلی)
                ok = self.score >= 150
                self._finish("success" if ok else "timeout")
                return

        # کاهش زمان شیلد/اسلومو
        for k in ("shield", "slowmo"):
            if self.power_state[k] > 0:
                self.power_state[k] -= dt

    def _spawn_glitch(self, w, h):
        sp = random.uniform(28, 60) * (1 + self._phase * 0.06)
        ang = random.uniform(0, math.tau)
        self.glitches.append(
            {
                "x": random.uniform(0, w),
                "y": random.uniform(0, h),
                "vx": math.cos(ang) * sp,
                "vy": math.sin(ang) * sp,
                "r": 10,
                "hue": random.uniform(0, 20),
                "life": random.uniform(6, 12),
            }
        )

    def _spawn_pattern(self):
        """چند چینش ساده: خطی، مثلثی، شش‌ضلعی کوچک، موجی"""
        w, h = self.width() or 1200, self.height() or 800
        cx, cy = w * 0.5, h * 0.5
        typ = random.choice(["line", "tri", "hex", "arc"])
        pts = []
        if typ == "line":
            L = 6
            x0 = cx - 120
            y0 = cy + random.uniform(-80, 80)
            for i in range(L):
                pts.append((x0 + i * 48, y0 + math.sin(i * 0.6) * 22))
        elif typ == "tri":
            r = 120
            for i in range(3):
                a = i * math.tau / 3 + random.uniform(-0.2, 0.2)
                pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        elif typ == "hex":
            r = 130
            for i in range(6):
                a = i * math.tau / 6 + random.uniform(-0.1, 0.1)
                pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        else:  # arc
            R = 150
            a0 = random.uniform(0, math.tau)
            for i in range(6):
                a = a0 + i * math.tau / 9
                pts.append((cx + math.cos(a) * R, cy + math.sin(a) * R * 0.6))

        self.targets = [{"x": x, "y": y, "lit": False, "t": 0.0} for (x, y) in pts]

    # ---------- ورودی‌ها
    def mouseMoveEvent(self, e):
        if self._control == "mouse":
            self.mx = e.position().x()
            self.my = e.position().y()

    def keyPressEvent(self, e: QtGui.QKeyEvent):
        if e.key() in (QtCore.Qt.Key_Left, QtCore.Qt.Key_A):
            self.key_left = True
            return
        if e.key() in (QtCore.Qt.Key_Right, QtCore.Qt.Key_D):
            self.key_right = True
            return
        if e.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            if not self.running:
                self.reset()
                self.start()
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

    def showEvent(self, e):
        super().showEvent(e)
        self.setFocus(QtCore.Qt.ActiveWindowFocusReason)

    # ---------- پایان
    def _finish(self, reason: str):
        self.running = False
        self.best = max(self.best, self.score)
        self.bestChanged.emit(self.best)
        mode_tag = "weave" + ("" if self._mode == "endless" else "-story")
        if self._mode == "endless":
            self.runEnded.emit(self.score, "weave-endless", reason)
        else:
            self.runEnded.emit(
                self.score,
                "weave-story-1",
                "success" if reason == "success" else reason,
            )

    # ---------- رسم

    def _prune_trail_by_length(self):
        import math

        pts = self.trail
        if not pts or len(pts) < 2:
            return
        total = 0.0
        keep = [pts[-1]]
        for i in range(len(pts) - 2, -1, -1):
            x1, y1 = pts[i]
            x2, y2 = keep[-1]
            dx, dy = x2 - x1, y2 - y1
            seg = math.hypot(dx, dy)
            if total + seg > TRAIL_MAX_LEN and len(keep) > 1:
                break
            keep.append((x1, y1))
            total += seg
        keep.reverse()
        self.trail = keep

    def paintEvent(self, e: QtGui.QPaintEvent):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        w, h = self.width(), self.height()
        t = time.perf_counter()

        # پس زمینه
        grad = QtGui.QLinearGradient(0, 0, w, h)
        a = self._theme.bgA + math.sin(t) * 20
        b = self._theme.bgB + math.cos(t * 0.7) * 20
        grad.setColorAt(0, QtGui.QColor.fromHsl(int(a) % 360, 180, 15))
        grad.setColorAt(1, QtGui.QColor.fromHsl(int(b) % 360, 180, 18))
        p.fillRect(self.rect(), grad)

        # --- Trail (با شکست هنگام wrap) ---
        if len(self.trail) > 1:
            it = iter(self.trail)
            x0, y0 = next(it)
            path = QtGui.QPainterPath(QtCore.QPointF(x0, y0))
            prevx, prevy = x0, y0
            for x, y in it:
                # اگر جهش بزرگ (wrap) بود، مسیر جدید شروع کن
                if abs(prevx - x) > w * 0.5 or abs(prevy - y) > h * 0.5:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
                prevx, prevy = x, y
            pen = QtGui.QPen(QtGui.QColor(140, 190, 255, 160), 2.6)
            p.setPen(pen)
            p.drawPath(path)

        # هدف‌ها
        p.setPen(QtCore.Qt.NoPen)
        for tgd in self.targets:
            pul = 1 + math.sin(tgd["t"] * 6) * 0.18
            clr = (
                QtGui.QColor(120, 220, 255, 220)
                if tgd["lit"]
                else QtGui.QColor(200, 210, 255, 160)
            )
            glow = QtGui.QColor(clr)
            glow.setAlpha(80)
            p.setBrush(glow)
            p.drawEllipse(
                QtCore.QPointF(tgd["x"], tgd["y"]),
                TARGET_R * pul + 5,
                TARGET_R * pul + 5,
            )
            p.setBrush(clr)
            p.drawEllipse(
                QtCore.QPointF(tgd["x"], tgd["y"]), TARGET_R * pul, TARGET_R * pul
            )

        # گلیچ‌ها
        for g in self.glitches:
            halo = QtGui.QColor.fromHsl(int(g["hue"]) % 360, 240, 130, 110)
            p.setBrush(halo)
            p.setPen(QtCore.Qt.NoPen)
            p.drawEllipse(QtCore.QPointF(g["x"], g["y"]), 14, 14)
            core = QtGui.QColor.fromHsl(int(g["hue"]) % 360, 240, 180, 230)
            p.setBrush(core)
            p.drawEllipse(QtCore.QPointF(g["x"], g["y"]), 10, 10)

        # بازیکن
        sp = (
            math.hypot(self.vx, self.vy)
            if self._control == "mouse"
            else self.forward_speed
        )
        direction = (
            math.atan2(self.vy, self.vx) if self._control == "mouse" else self.heading
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

        # HUD ساده
        p.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 150)))
        p.setFont(QtGui.QFont("Inter", 10, QtGui.QFont.Bold))
        mode = "Endless" if self._mode == "endless" else "Story"
        p.drawText(10, h - 12, f"Flux Weave — {mode}")

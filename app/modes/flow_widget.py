# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtGui, QtCore
import math, random, time

from app.modes.base_mode import BaseModeWidget
from app.settings import (
    THEMES,
    INITIAL_TIME_ENDLESS,
    RAMP_DURATION,
    RAMP_RATE,
    MAX_PHASE,
)

PLAYER_R = 11
ENERGY_R2 = 16 * 16
GLITCH_R2 = 24 * 24


# ---------- Flow Field (زمینهٔ برداری نرم و بی‌درز)
def flow_vec(x: float, y: float, t: float) -> tuple[float, float]:
    """
    میدان برداری آرام با ترکیب موج‌های سینوسیِ کم‌دامنه.
    خروجی: (fx, fy) که مقدارهای کوچک سرعت/شتاب محیطی‌اند.
    """
    s1 = math.sin((x * 0.005) + t * 0.35)
    s2 = math.cos((y * 0.004) - t * 0.27)
    s3 = math.sin((x * 0.003 + y * 0.003) * 0.9 + t * 0.18)
    fx = 22 * s1 + 14 * s3
    fy = 18 * s2 - 12 * s3
    return fx, fy


class FlowWidget(BaseModeWidget):
    # سیگنال‌ها سازگار با بقیهٔ مودها
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

        # تنظیمات
        self._theme = THEMES["Aurora"]
        self._lang = "fa"
        self._mode = "endless"  # endless | story
        self._control = "mouse"  # mouse | keys

        # وضعیت
        self.running = False
        self.paused = False
        self.score = 0
        self.best = 0
        self.time_left = 60

        # بازیکن
        self.px = self.width() / 2
        self.py = self.height() / 2
        self.mx = self.px
        self.my = self.py
        self.vx = 0.0
        self.vy = 0.0
        self.heading = 0.0
        self.turn_speed = math.radians(180)
        self.forward_speed = 235.0
        self.key_left = False
        self.key_right = False

        # اشیاء میدان
        self.energies = []  # {x,y,t}
        self.glitches = []  # {x,y,vx,vy,life,hue}
        self.sparks = []  # {x,y,vx,vy,life,hue}

        # توانایی‌ها / تکامل
        self.tier = 1  # 1..4
        self.combo_absorb = 0  # برای پالس تکاملی
        self.combo_window = 0.0  # پنجرهٔ زمانی زنجیره
        self.next_tier_need = 10

        # Phase Dash (Blink)
        self.blink_charges = 1  # شارژ موجود
        self.blink_max = 2
        self.blink_cooldown = 0.0  # ثانیه
        self.blink_cd_max = 1.15
        self.blink_afterglow = 0.0  # افکت تصویری
        self.slow_field = 0.0  # پس از پالس تکاملی، میدان کمی کند شود

        # سختی
        self._phase = 0.0
        self._elapsed = 0.0
        self.timers = {"energy": 0.25, "glitch": 0.95}

        # لوپ
        self._last = time.perf_counter()
        self._acc = 0.0
        self._step = 1 / 60.0
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000 // 120)

        # برای رندر خطوط جریان
        self._flow_seeds = []  # هر seed: (x,y,phase)

    # --- API تنظیمات
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

    # --- آماده‌سازی
    def prepare_endless(self, _ignored=INITIAL_TIME_ENDLESS):
        self._reset_world()
        self._mode = "endless"
        self.time_left = -1  # ∞
        self.running = False
        self.update()
        self.scoreChanged.emit(self.score)
        self.bestChanged.emit(self.best)

    def prepare_story(self, idx: int):
        self._reset_world()
        self._mode = "story"
        self.time_left = 80 if idx < 5 else 65
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

    # --- درون‌برنامه
    def _reset_world(self):
        w = max(1, self.width())
        h = max(1, self.height())
        self.px, self.py = w / 2, h / 2
        self.vx = self.vy = 0.0
        self.heading = 0.0
        self.key_left = self.key_right = False

        self.energies.clear()
        self.glitches.clear()
        self.sparks.clear()

        self.tier = 1
        self.combo_absorb = 0
        self.combo_window = 0.0
        self.next_tier_need = 10

        self.blink_charges = 1
        self.blink_cooldown = 0.0
        self.blink_afterglow = 0.0
        self.slow_field = 0.0

        self._phase = 0.0
        self._elapsed = 0.0
        self.score = 0
        self.timers = {"energy": 0.25, "glitch": 0.95}

        # بذرهای خطوط جریان
        self._init_flow_seeds()

    def _init_flow_seeds(self):
        self._flow_seeds.clear()
        w = max(800, self.width())
        h = max(500, self.height())
        random.seed(12)
        for _ in range(60):
            self._flow_seeds.append(
                [
                    random.uniform(0, w),
                    random.uniform(0, h),
                    random.uniform(0, math.tau),
                ]
            )

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
        w, h = self.width(), self.height()

        # سختی نرم
        if self._mode == "endless":
            self._elapsed += dt
            tnorm = max(0.0, min(1.0, self._elapsed / RAMP_DURATION))
            smooth = tnorm * tnorm * (3 - 2 * tnorm)
            target = smooth * MAX_PHASE
            self._phase += (target - self._phase) * RAMP_RATE

        # میدان کند (بعد از پالس تکاملی)
        slowmul = 0.85 if self.slow_field > 0 else 1.0
        if self.slow_field > 0:
            self.slow_field -= dt

        # حرکت + تأثیر میدان + wrap
        fx, fy = flow_vec(self.px, self.py, time.perf_counter())
        if self._control == "mouse":
            accel = (700 + 60 * (self.tier - 1)) * slowmul
            damping = 0.88
            maxs = 300 + 40 * (self.tier - 1)
            dx = self.mx - self.px
            dy = self.my - self.py
            self.vx += (1 if dx > 0 else -1 if dx < 0 else 0) * accel * dt
            self.vy += (1 if dy > 0 else -1 if dy < 0 else 0) * accel * dt
            # اثر میدان (به‌صورت نیروی نرم)
            self.vx += fx * 0.25 * dt
            self.vy += fy * 0.25 * dt
            sp = math.hypot(self.vx, self.vy)
            if sp > maxs:
                self.vx = self.vx / sp * maxs
                self.vy = self.vy / sp * maxs
            self.vx *= damping
            self.vy *= damping
            self.px += self.vx * dt
            self.py += self.vy * dt
        else:
            if self.key_left:
                self.heading -= self.turn_speed * dt
            if self.key_right:
                self.heading += self.turn_speed * dt
            speed = (self.forward_speed + 30 * (self.tier - 1)) * slowmul
            # اثر میدان به‌صورت لغزش جانبی
            self.heading += math.atan2(fy, fx) * 0.0009
            self.px += math.cos(self.heading) * speed * dt + fx * 0.12 * dt
            self.py += math.sin(self.heading) * speed * dt + fy * 0.12 * dt

        # wrap
        if self.px < 0:
            self.px += w
        elif self.px > w:
            self.px -= w
        if self.py < 0:
            self.py += h
        elif self.py > h:
            self.py -= h

        # کول‌داون blink
        if self.blink_cooldown > 0:
            self.blink_cooldown -= dt
        if self.blink_afterglow > 0:
            self.blink_afterglow -= dt

        # اسپاون‌ها
        self.timers["energy"] -= dt * slowmul
        self.timers["glitch"] -= dt

        if self.timers["energy"] <= 0:
            self._spawn_energy(w, h)
            base = 0.45 - min(0.25, self._phase * 0.03)
            self.timers["energy"] = max(0.18, base)

        if self.timers["glitch"] <= 0:
            self._spawn_glitch(w, h)
            self.timers["glitch"] = max(0.6, 1.4 - self._phase * 0.06)

        # حرکت گلیچ‌ها + اثر میدان + wrap
        for g in self.glitches:
            fgx, fgy = flow_vec(g["x"], g["y"], time.perf_counter())
            g["x"] += (g["vx"] + fgx * 0.15) * dt
            g["y"] += (g["vy"] + fgy * 0.15) * dt
            if g["x"] < 0:
                g["x"] += w
            elif g["x"] > w:
                g["x"] -= w
            if g["y"] < 0:
                g["y"] += h
            elif g["y"] > h:
                g["y"] -= h
            g["life"] -= dt
        self.glitches = [g for g in self.glitches if g["life"] > 0]

        # جذب انرژی + زنجیره
        if self.combo_window > 0:
            self.combo_window -= dt
        i = len(self.energies) - 1
        while i >= 0:
            en = self.energies[i]
            en["t"] += dt
            if (self.px - en["x"]) ** 2 + (self.py - en["y"]) ** 2 < ENERGY_R2:
                self.energies.pop(i)
                self._emit_sparks(en["x"], en["y"], 120, 14, 140)
                self.score += 12 + 2 * (self.tier - 1)
                self.scoreChanged.emit(self.score)

                # شارژ blink و زنجیره
                self.blink_charges = min(self.blink_max, self.blink_charges + 0.5)
                if self.combo_window > 0:
                    self.combo_absorb += 1
                else:
                    self.combo_absorb = 1
                self.combo_window = 2.0  # دو ثانیه فرصت زنجیره

                # پالس تکاملی
                if self.combo_absorb >= 4:
                    self.combo_absorb = 0
                    self._evolution_pulse()
            i -= 1

        # برخورد گلیچ (اگر در افترگلو نبودی)
        if self.blink_afterglow <= 0:
            for g in self.glitches:
                if (self.px - g["x"]) ** 2 + (self.py - g["y"]) ** 2 < GLITCH_R2:
                    self._finish("hit")
                    return

        # زمان استوری
        if self._mode == "story":
            self.time_left = max(0.0, self.time_left - dt)
            if self.time_left == 0.0:
                ok = self.score >= (180 + 40 * (self.tier - 1))
                self._finish("success" if ok else "timeout")
                return

        # کاهش عمر اسپارک‌ها
        for s in list(self.sparks):
            s["x"] += s["vx"] * self._step * 2
            s["y"] += s["vy"] * self._step * 2
            s["life"] -= self._step * 2
        self.sparks = [s for s in self.sparks if s["life"] > 0]

    # --- رویدادها و توانایی‌ها
    def _blink(self):
        if self.blink_charges < 1 or self.blink_cooldown > 0:
            return
        self.blink_charges -= 1
        self.blink_cooldown = self.blink_cd_max
        self.blink_afterglow = 0.45  # تا 0.45ثانیه برخورد بی‌اثر و افکت

        # مقصد دَش
        dir_angle = (
            math.atan2(self.vy, self.vx) if self._control == "mouse" else self.heading
        )
        if self._control == "mouse":
            # اگر تقریباً ساکن بودی، جهت به سمت ماوس
            if math.hypot(self.vx, self.vy) < 20:
                dir_angle = math.atan2(self.my - self.py, self.mx - self.px)

        dist = 160 + 20 * (self.tier - 1)
        nx = self.px + math.cos(dir_angle) * dist
        ny = self.py + math.sin(dir_angle) * dist

        # wrap مقصد
        w, h = self.width(), self.height()
        if nx < 0:
            nx += w
        elif nx > w:
            nx -= w
        if ny < 0:
            ny += h
        elif ny > h:
            ny -= h

        # موج شوک: گلیچ‌های نزدیک آسیب ببینند/حذف شوند
        radius2 = (36 + 10 * (self.tier - 1)) ** 2
        j = len(self.glitches) - 1
        while j >= 0:
            g = self.glitches[j]
            if (nx - g["x"]) ** 2 + (ny - g["y"]) ** 2 <= radius2:
                self._emit_sparks(g["x"], g["y"], g["hue"], 18, 160)
                self.glitches.pop(j)
                self.score += 10
            j -= 1
        self.scoreChanged.emit(self.score)

        # تلپورت
        self.px, self.py = nx, ny

    def _evolution_pulse(self):
        # ارتقاء نرم: Tier + میدان کند + امتیاز + شارژ
        if self.tier < 4:
            self.tier += 1
        self.slow_field = 2.5
        self.score += 40
        self.blink_charges = min(self.blink_max, self.blink_charges + 1)
        # افکت اسپارک
        self._emit_sparks(self.px, self.py, 120, 36, 180)

    def mouseMoveEvent(self, e):
        if self._control == "mouse":
            self.mx = e.position().x()
            self.my = e.position().y()

    def keyPressEvent(self, e: QtGui.QKeyEvent):
        k = e.key()
        if k in (QtCore.Qt.Key_Left, QtCore.Qt.Key_A):
            self.key_left = True
            return
        if k in (QtCore.Qt.Key_Right, QtCore.Qt.Key_D):
            self.key_right = True
            return
        if k == QtCore.Qt.Key_Space:
            self._blink()
            return
        if k in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
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

    # --- پایان
    def _finish(self, reason: str):
        self.running = False
        self.best = max(self.best, self.score)
        self.bestChanged.emit(self.best)
        if self._mode == "endless":
            self.runEnded.emit(self.score, "flow-endless", reason)
        else:
            self.runEnded.emit(
                self.score, "flow-story-1", "success" if reason == "success" else reason
            )

    # --- اسپاون / افکت
    def _spawn_energy(self, w, h):
        # انرژی‌ها کمی همراه جریان رانده می‌شوند (در رندر فقط pulsing است)
        self.energies.append(
            {"x": random.uniform(30, w - 30), "y": random.uniform(30, h - 30), "t": 0.0}
        )

    def _spawn_glitch(self, w, h):
        sp = random.uniform(28, 60) * (1 + self._phase * 0.07)
        ang = random.uniform(0, math.tau)
        self.glitches.append(
            {
                "x": random.uniform(0, w),
                "y": random.uniform(0, h),
                "vx": math.cos(ang) * sp,
                "vy": math.sin(ang) * sp,
                "life": random.uniform(7, 12),
                "hue": random.uniform(0, 20),
            }
        )

    def _emit_sparks(self, x, y, hue, n=12, speed=90):
        for i in range(n):
            ang = (i / n) * math.tau + random.uniform(-0.2, 0.2)
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

    # --- رندر
    def _draw_flow_lines(self, p: QtGui.QPainter, w: int, h: int, t: float):
        """
        چندین streamline در پس‌زمینه. هر seed با میدان حرکت می‌کند
        و وقتی از کادر خارج شد wrap می‌شود. خطوط باریک و کم‌نور برای لوکِس.
        """
        pen = QtGui.QPen(QtGui.QColor(180, 220, 255, 45), 1.0)
        p.setPen(pen)
        for s in self._flow_seeds:
            x, y, ph = s
            path = QtGui.QPainterPath(QtCore.QPointF(x, y))
            xx, yy = x, y
            # 12 گام کوتاه روی میدان
            for _ in range(12):
                fx, fy = flow_vec(xx, yy, t + ph * 0.2)
                xx += fx * 0.06
                yy += fy * 0.06
                # wrap ملایم
                if xx < 0:
                    xx += w
                elif xx > w:
                    xx -= w
                if yy < 0:
                    yy += h
                elif yy > h:
                    yy -= h
                path.lineTo(xx, yy)
            p.drawPath(path)
            # seed را کمی جابجا کن تا زنده بماند
            s[0], s[1] = xx, yy
            s[2] += 0.03

    def paintEvent(self, e: QtGui.QPaintEvent):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        w, h = self.width(), self.height()
        t = time.perf_counter()

        # بک‌گراند (HSL گرادیان آرام)
        grad = QtGui.QLinearGradient(0, 0, w, h)
        a = self._theme.bgA + math.sin(t * 0.6) * 18
        b = self._theme.bgB + math.cos(t * 0.5) * 18
        grad.setColorAt(0, QtGui.QColor.fromHsl(int(a) % 360, 180, 15))
        grad.setColorAt(1, QtGui.QColor.fromHsl(int(b) % 360, 180, 18))
        p.fillRect(self.rect(), grad)

        # خطوط جریان
        self._draw_flow_lines(p, w, h, t)

        # انرژی‌ها
        p.setPen(QtCore.Qt.NoPen)
        for en in self.energies:
            en["t"] += self._step
            pul = 1 + math.sin(en["t"] * 6) * 0.20
            base = QtGui.QColor(110, 255, 210, 220)
            glow = QtGui.QColor(110, 255, 210, 90)
            p.setBrush(glow)
            p.drawEllipse(QtCore.QPointF(en["x"], en["y"]), 10 * pul + 5, 10 * pul + 5)
            p.setBrush(base)
            p.drawEllipse(QtCore.QPointF(en["x"], en["y"]), 10 * pul, 10 * pul)

        # گلیچ‌ها
        for g in self.glitches:
            halo = QtGui.QColor.fromHsl(int(g["hue"]) % 360, 240, 130, 110)
            p.setBrush(halo)
            p.setPen(QtCore.Qt.NoPen)
            p.drawEllipse(QtCore.QPointF(g["x"], g["y"]), 14, 14)
            core = QtGui.QColor.fromHsl(int(g["hue"]) % 360, 240, 180, 230)
            p.setBrush(core)
            p.drawEllipse(QtCore.QPointF(g["x"], g["y"]), 10, 10)

        # اسپارک‌ها
        pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 180), 1.4)
        p.setPen(pen)
        for s in self.sparks:
            p.drawLine(s["x"], s["y"], s["x"] - s["vx"] * 0.03, s["y"] - s["vy"] * 0.03)

        # بازیکن (با افکت Blink)
        sp = (
            math.hypot(self.vx, self.vy)
            if self._control == "mouse"
            else (self.forward_speed + 30 * (self.tier - 1))
        )
        direction = (
            math.atan2(self.vy, self.vx) if self._control == "mouse" else self.heading
        )
        trail = min(sp * 0.04, 12)
        p.save()
        p.translate(self.px, self.py)
        p.rotate(math.degrees(direction))
        # glow
        glow = QtGui.QColor(self._theme.playerA)
        glow.setAlpha(100)
        if self.blink_afterglow > 0:
            glow = QtGui.QColor(110, 255, 210, 180)
        p.setBrush(glow)
        p.setPen(QtCore.Qt.NoPen)
        p.drawEllipse(
            QtCore.QPointF(0, 0), PLAYER_R + trail * 0.6, PLAYER_R + trail * 0.6
        )
        # body
        grad2 = QtGui.QLinearGradient(-trail, -PLAYER_R, PLAYER_R, PLAYER_R)
        grad2.setColorAt(0, QtGui.QColor(self._theme.playerA))
        grad2.setColorAt(1, QtGui.QColor(self._theme.playerB))
        if self.blink_afterglow > 0:
            grad2.setColorAt(0, QtGui.QColor(110, 255, 210))
            grad2.setColorAt(1, QtGui.QColor(120, 230, 255))
        p.setBrush(QtGui.QBrush(grad2))
        path = QtGui.QPainterPath()
        path.moveTo(PLAYER_R + 2, 0)
        path.lineTo(-PLAYER_R - trail, -PLAYER_R * 0.75)
        path.lineTo(-PLAYER_R - trail, PLAYER_R * 0.75)
        path.closeSubpath()
        p.drawPath(path)
        p.restore()

        # HUD
        p.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 150)))
        p.setFont(QtGui.QFont("Inter", 10, QtGui.QFont.Bold))
        mode = "Endless" if self._mode == "endless" else "Story"
        blink_txt = f"Blink: {int(self.blink_charges)}/{self.blink_max}" + (
            "" if self.blink_cooldown <= 0 else f" ({self.blink_cooldown:.1f}s)"
        )
        tier_txt = f"Tier {self.tier}"
        p.drawText(10, h - 28, f"Neural Flow — {mode} | {tier_txt} | {blink_txt}")

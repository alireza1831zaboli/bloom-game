from PySide6 import QtWidgets, QtGui, QtCore
import math, random, time

# هماهنگ با بازی‌های دیگر:
from app.modes.base_mode import BaseModeWidget
from app.settings import THEMES, MAX_PHASE, RAMP_DURATION, RAMP_RATE

PLAYER_R = 11
NODE_R2 = 22 * 22
GLITCH_R2 = 18 * 18


class SignalRushWidget(BaseModeWidget):
    scoreChanged = QtCore.Signal(int)
    timeChanged = QtCore.Signal(int)  # در Endless بی‌استفاده (∞)
    bestChanged = QtCore.Signal(int)
    runEnded = QtCore.Signal(int, str, str)  # score, mode, reason("hit","success")
    screenshotSaved = QtCore.Signal(str)
    started = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        # تم و تنظیمات
        self._theme = THEMES["Aurora"]
        self._mode = "endless"  # یا "story"
        self._control_mode = "mouse"  # "mouse" | "keys"
        self._lang = "fa"
        self._sfx = True

        # وضعیت کلی
        self.running = False
        self.paused = False
        self.score = 0
        self.best = 0
        self.phase_val = 0.0

        # بازیکن
        self.px = 300.0
        self.py = 0.0  # ثابت نگه می‌داریم (نمای اسکرول عمودی)
        self.vx = 0.0
        self.mx = 0.0
        self.heading = 0.0
        self.key_left = False
        self.key_right = False

        # دَش (Phase)
        self.dash_cd = 0.0  # زمان باقی‌مانده تا آماده‌شدن بعدی
        self.dash_t = 0.0  # زمان فعال بودن (نامرئی و بدون برخورد)
        self.DASH_COOLDOWN = 2.6
        self.DASH_DURATION = 0.28

        # جهان: نوارهای موجی که رو به پایین حرکت می‌کنند
        self.scroll_y = 0.0
        self.speed = 180.0  # سرعت پایه‌ی اسکرول
        self.elapsed = 0.0

        # موجودیت‌ها
        self.nodes = []  # امتیاز
        self.glitches = []  # گلیچ
        self.powers = []  # پاورآپ (ریست Dash)
        self.sparks = []

        # تایمر اسپان
        self.t_node = 0.8
        self.t_glitch = 1.2
        self.t_power = 6.5

        # حلقه‌ی ثابت
        self._step = 1.0 / 60.0
        self._acc = 0.0
        self._last = time.perf_counter()
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000 // 120)

    # ------------- API از MainWindow
    def set_lang(self, lang: str):
        self._lang = lang

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

    def prepare_endless(self, _ignored: int = 0):
        self._reset_world()
        self.timeChanged.emit(-1)  # ∞
        self.update()

    def prepare_story(self, idx: int = 0):
        self._reset_world()
        # اگر برای Story زمان/هدف خواستی، اینجا ست کن
        self.timeChanged.emit(60)  # نمایشی
        self.update()

    def start(self):
        if self.running and not self.paused:
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

    # ------------- داخلی
    def _reset_world(self):
        w, h = max(1, self.width()), max(1, self.height())
        self.score = 0
        self.scoreChanged.emit(0)
        self.phase_val = 0.0
        self.elapsed = 0.0
        self.scroll_y = 0.0
        self.speed = 180.0
        self.nodes.clear()
        self.glitches.clear()
        self.powers.clear()
        self.sparks.clear()
        self.t_node = 0.3
        self.t_glitch = 0.9
        self.t_power = 3.5
        self.px = w * 0.5
        self.py = h * 0.75
        self.vx = 0.0
        self.mx = self.px
        self.dash_cd = 0.0
        self.dash_t = 0.0
        self.key_left = self.key_right = False

    # ------------- حلقه
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

    def _update(self, dt: float):
        w, h = self.width(), self.height()

        # افزایش تدریجی سختی
        self.elapsed += dt
        tnorm = max(0.0, min(1.0, self.elapsed / RAMP_DURATION))
        smooth = tnorm * tnorm * (3 - 2 * tnorm)
        target_phase = smooth * MAX_PHASE
        self.phase_val += (target_phase - self.phase_val) * RAMP_RATE
        self.speed = 180 + 220 * smooth

        # اسپان‌ها
        self.t_node -= dt
        self.t_glitch -= dt
        self.t_power -= dt
        if self.t_node <= 0:
            self._spawn_node(w)
            self.t_node = max(0.18, 0.6 - self.phase_val * 0.02)
        if self.t_glitch <= 0:
            self._spawn_glitch(w)
            self.t_glitch = max(0.4, 1.2 - self.phase_val * 0.03)
        if self.t_power <= 0:
            self._spawn_power(w)
            self.t_power = random.uniform(4.5, 7.5)

        # اسکرول پایین
        sy = self.speed * dt
        self.scroll_y += sy
        for arr in (self.nodes, self.glitches, self.powers, self.sparks):
            for o in arr:
                o["y"] += sy
        # تمیزکاری خارج قاب
        self.nodes = [o for o in self.nodes if o["y"] < h + 50]
        self.glitches = [o for o in self.glitches if o["y"] < h + 50]
        self.powers = [o for o in self.powers if o["y"] < h + 50]
        self.sparks = [o for o in self.sparks if o["life"] > 0]

        # کنترل افقی
        if self._control_mode == "mouse":
            ax = 800.0
            damp = 0.9
            maxs = 420
            dx = self.mx - self.px
            self.vx += (1 if dx > 0 else -1 if dx < 0 else 0) * ax * dt
            sp = abs(self.vx)
            if sp > maxs:
                self.vx = math.copysign(maxs, self.vx)
            self.vx *= damp
            self.px = max(20, min(w - 20, self.px + self.vx * dt))
        else:
            turn = 360.0
            if self.key_left:
                self.px -= turn * dt
            if self.key_right:
                self.px += turn * dt
            self.px = (self.px + w) % w  # عبور از دیواره‌ها

        # دَش
        if self.dash_cd > 0:
            self.dash_cd -= dt
        if self.dash_t > 0:
            self.dash_t -= dt

        # برخوردها (اگر Dash فعال نیست)
        if self.dash_t <= 0:
            i = len(self.nodes) - 1
            while i >= 0:
                n = self.nodes[i]
                if (self.px - n["x"]) ** 2 + (self.py - n["y"]) ** 2 < NODE_R2:
                    self.nodes.pop(i)
                    self._emit_sparks(n["x"], n["y"], 200, 12, 120)
                    self.score += 10
                    self.scoreChanged.emit(self.score)
                i -= 1

            i = len(self.powers) - 1
            while i >= 0:
                p = self.powers[i]
                if (self.px - p["x"]) ** 2 + (self.py - p["y"]) ** 2 < NODE_R2:
                    self.powers.pop(i)
                    # پاور: ریست کول‌داون Dash
                    self.dash_cd = 0.0
                    self._emit_sparks(p["x"], p["y"], 80, 16, 150)
                i -= 1

            for g in self.glitches:
                if (self.px - g["x"]) ** 2 + (self.py - g["y"]) ** 2 < GLITCH_R2:
                    self._game_over("hit")
                    return

    def _game_over(self, reason: str):
        self.running = False
        self.best = max(self.best, self.score)
        self.bestChanged.emit(self.best)
        mode = "endless" if self._mode == "endless" else "story-1"
        self.runEnded.emit(self.score, mode, reason)

    # ------------- اسپانرها
    def _spawn_node(self, w):
        x = random.uniform(30, w - 30)
        y = -30
        self.nodes.append({"x": x, "y": y, "r": 8, "t": 0.0})

    def _spawn_glitch(self, w):
        x = random.uniform(30, w - 30)
        y = -30
        sway = random.uniform(40, 140)
        freq = random.uniform(0.6, 1.4)
        self.glitches.append(
            {"x": x, "y": y, "r": 10, "t": 0.0, "sway": sway, "freq": freq}
        )
        # حرکت افقی موجی
        # آپدیت در paint (برای ساده‌سازی) یا اینجا با t…

    def _spawn_power(self, w):
        x = random.uniform(30, w - 30)
        y = -30
        self.powers.append({"x": x, "y": y, "r": 10, "pulse": 0.0})

    def _emit_sparks(self, x, y, hue, n=10, speed=120):
        for i in range(n):
            ang = (i / n) * math.tau + random.uniform(-0.15, 0.15)
            self.sparks.append(
                {
                    "x": x,
                    "y": y,
                    "vx": math.cos(ang) * (speed + random.uniform(-20, 20)),
                    "vy": math.sin(ang) * (speed + random.uniform(-20, 20)),
                    "life": random.uniform(0.35, 0.7),
                    "hue": hue,
                }
            )

    # ------------- رخدادها
    def mouseMoveEvent(self, e):
        if self._control_mode == "mouse":
            self.mx = e.position().x()

    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.LeftButton:
            self._try_dash()

    def keyPressEvent(self, e):
        k = e.key()
        if k in (QtCore.Qt.Key_Left, QtCore.Qt.Key_A):
            self.key_left = True
        if k in (QtCore.Qt.Key_Right, QtCore.Qt.Key_D):
            self.key_right = True
        if k in (QtCore.Qt.Key_Space,):
            self._try_dash()
        if k == QtCore.Qt.Key_P:
            self._save_screenshot()

    def keyReleaseEvent(self, e):
        k = e.key()
        if k in (QtCore.Qt.Key_Left, QtCore.Qt.Key_A):
            self.key_left = False
        if k in (QtCore.Qt.Key_Right, QtCore.Qt.Key_D):
            self.key_right = False

    def _try_dash(self):
        if self.dash_cd <= 0.0:
            self.dash_t = self.DASH_DURATION
            self.dash_cd = self.DASH_COOLDOWN

    # ------------- اسکرین‌شات (مثل بقیه مودها)
    def _save_screenshot(self):
        scr = QtGui.QGuiApplication.primaryScreen()
        if not scr:
            return
        img = scr.grabWindow(self.winId())
        import os, time

        path = os.path.join(os.getcwd(), f"rush_{time.strftime('%Y%m%d_%H%M%S')}.png")
        img.save(path, "PNG")
        self.screenshotSaved.emit(path)

    # ------------- نقاشی
    def paintEvent(self, e):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        w, h = self.width(), self.height()
        t = time.perf_counter()

        # پس‌زمینه گرادیانی + شبکه موجی
        grad = QtGui.QLinearGradient(0, 0, w, h)
        a = self._theme.bgA + math.sin(t * 0.4) * 20
        b = self._theme.bgB + math.cos(t * 0.3) * 20
        grad.setColorAt(0, QtGui.QColor.fromHsl(int(a) % 360, 180, 16))
        grad.setColorAt(1, QtGui.QColor.fromHsl(int(b) % 360, 180, 19))
        p.fillRect(self.rect(), grad)

        # خطوط مواج افقی (flow lines)
        p.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 22), 2))
        base = (t * 40) % 200
        for i in range(8):
            yy = (i * h / 8 + base) % (h + 40) - 20
            p.drawLine(0, yy, w, yy)

        # نودها
        p.setPen(QtCore.Qt.NoPen)
        for n in self.nodes:
            n["t"] += 0.016
            rr = 6 + math.sin(n["t"] * 4) * 2
            col = QtGui.QColor(*(120, 200, 255, 210))
            glow = QtGui.QColor(*(120, 200, 255, 60))
            p.setBrush(glow)
            p.drawEllipse(QtCore.QPointF(n["x"], n["y"]), rr + 6, rr + 6)
            p.setBrush(col)
            p.drawEllipse(QtCore.QPointF(n["x"], n["y"]), rr, rr)

        # گلیچ‌ها (حرکت موجی عرضی)
        for g in self.glitches:
            g["t"] += 0.016
            gx = g["x"] + math.sin(g["t"] * g["freq"] * 2.2) * g["sway"]
            col = QtGui.QColor(*(255, 120, 120, 220))
            halo = QtGui.QColor(*(255, 100, 100, 70))
            p.setBrush(halo)
            p.drawEllipse(QtCore.QPointF(gx, g["y"]), 13, 13)
            p.setBrush(col)
            p.drawEllipse(QtCore.QPointF(gx, g["y"]), 9, 9)
            # یک ضربدر باریک
            pen = QtGui.QPen(QtGui.QColor(*(255, 170, 170, 230)), 2)
            pen.setCapStyle(QtCore.Qt.RoundCap)
            p.setPen(pen)
            p.drawLine(gx - 6, g["y"], gx + 6, g["y"])
            p.drawLine(gx, g["y"] - 6, gx, g["y"] + 6)
            p.setPen(QtCore.Qt.NoPen)

        # پاورآپ (ریست Dash)
        for pw in self.powers:
            pw["pulse"] += 0.016
            pul = 1 + math.sin(pw["pulse"] * 6) * 0.25
            col = QtGui.QColor(*(120, 255, 180, 210))
            glow = QtGui.QColor(*(120, 255, 180, 80))
            p.setBrush(glow)
            p.drawEllipse(QtCore.QPointF(pw["x"], pw["y"]), 12, 12)
            p.setBrush(col)
            p.drawEllipse(QtCore.QPointF(pw["x"], pw["y"]), 8 * pul, 8 * pul)

        # اسپارک‌ها
        pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 180), 1.4)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        p.setPen(pen)
        for s in self.sparks:
            s["x"] += s["vx"] * 0.016
            s["y"] += s["vy"] * 0.016
            s["life"] -= 0.016
            a = max(0, min(255, int(s["life"] * 255)))
            pen.setColor(QtGui.QColor.fromHsl(int(s["hue"]) % 360, 220, 180, a))
            p.setPen(pen)
            p.drawLine(s["x"], s["y"], s["x"] - s["vx"] * 0.02, s["y"] - s["vy"] * 0.02)

        # بازیکن (با Dash شفاف)
        p.save()
        p.translate(self.px, self.py)
        trail = 10
        grad2 = QtGui.QLinearGradient(-trail, -PLAYER_R, PLAYER_R, PLAYER_R)
        grad2.setColorAt(0, QtGui.QColor(self._theme.playerA))
        colB = QtGui.QColor(self._theme.playerB)
        if self.dash_t > 0:
            colB.setAlpha(120)
        grad2.setColorAt(1, colB)
        p.setBrush(QtGui.QBrush(grad2))
        p.setPen(QtCore.Qt.NoPen)
        path = QtGui.QPainterPath()
        path.moveTo(PLAYER_R + 2, 0)
        path.lineTo(-PLAYER_R - trail, -PLAYER_R * 0.75)
        path.lineTo(-PLAYER_R - trail, PLAYER_R * 0.75)
        path.closeSubpath()
        p.drawPath(path)
        p.restore()

        # HUD پایین
        p.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 140)))
        p.setFont(QtGui.QFont("Inter", 10, QtGui.QFont.Bold))
        pace = 1 + self.phase_val * 0.15
        p.drawText(
            10,
            h - 10,
            f"Signal Rush — {'Endless' if self._mode=='endless' else 'Story'}  |  Pace: {pace:.2f}x",
        )

    # ------------- اندازه
    def resizeEvent(self, e: QtGui.QResizeEvent):
        if self.px == 0 and self.py == 0:
            self.px = self.width() * 0.5
            self.py = self.height() * 0.75
        return super().resizeEvent(e)

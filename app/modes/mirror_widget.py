# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtGui, QtCore
import math, random, time
from app.modes.base_mode import BaseModeWidget
from app.settings import THEMES, INITIAL_TIME_ENDLESS, RAMP_DURATION, RAMP_RATE, MAX_PHASE

PLAYER_R   = 10
ORB_R2     = 14 * 14
GLITCH_R2  = 22 * 22

class MirrorWidget(BaseModeWidget):
    # سازگار با بقیهٔ مودها
    scoreChanged = QtCore.Signal(int)
    timeChanged  = QtCore.Signal(int)
    bestChanged  = QtCore.Signal(int)
    runEnded     = QtCore.Signal(int, str, str)
    screenshotSaved = QtCore.Signal(str)
    started      = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        # تنظیمات
        self._theme = THEMES["Aurora"]
        self._lang  = "fa"
        self._mode  = "endless"       # endless | story
        self._control = "mouse"       # از Settings با set_control_mode تنظیم می‌شود

        # وضعیت کلی
        self.running = False
        self.paused  = False
        self.score   = 0
        self.best    = 0
        self.time_left = 60

        # بازیکن «اصلی» (فلش شماره 1) — فلش آینه‌ای فقط از روی این محاسبه می‌شود
        self.px = (self.width() or 1200) * 0.45
        self.py = (self.height() or 800) * 0.5
        self.vx = 0.0; self.vy = 0.0
        self.mx = self.px; self.my = self.py         # هدف ماوس

        # حالت Keys
        self.heading = 0.0
        self.turn_speed = math.radians(180)
        self.forward_speed = 240.0
        self.key_left = False; self.key_right = False

        # جهان مشترک
        self.orbs     = []   # (x,y,t)
        self.glitches = []   # {x,y,vx,vy,life,hue}
        self.sparks   = []   # افکت

        # سختی
        self._phase = 0.0
        self._elapsed = 0.0
        self.timers = {"orb": 0.0, "glitch": 1.0}

        # لوپ
        self._last = time.perf_counter()
        self._acc = 0.0; self._step = 1/60.0
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000//120)

    # ---------- API عمومی ----------
    def set_lang(self, lang: str): self._lang = lang
    def set_theme(self, name: str): self._theme = THEMES.get(name, self._theme); self.update()
    def set_mode(self, mode: str):  self._mode = mode
    def set_control_mode(self, mode: str):
        self._control = "keys" if mode.lower().startswith("k") else "mouse"
    def set_music(self, on: bool): pass
    def set_sfx(self, on: bool):   pass

    def prepare_endless(self, _ignored=INITIAL_TIME_ENDLESS):
        self._reset_world()
        self._mode = "endless"
        self.time_left = -1
        self.running = False
        self.update()
        self.scoreChanged.emit(self.score); self.bestChanged.emit(self.best)

    def prepare_story(self, idx: int):
        self._reset_world()
        self._mode = "story"
        self.time_left = 70 if idx < 5 else 55
        self.running = False
        self.update()
        self.timeChanged.emit(int(self.time_left))
        self.scoreChanged.emit(self.score); self.bestChanged.emit(self.best)

    def start(self):
        if self._mode == "story" and self.time_left <= 0: return
        self.running = True; self.paused = False
        self._last = time.perf_counter()
        self.started.emit()

    def toggle_pause(self):
        if not self.running: return
        self.paused = not self.paused

    def reset(self):
        if self._mode == "endless": self.prepare_endless()
        else: self.prepare_story(0)

    # ---------- داخل بازی ----------
    def _reset_world(self):
        w = max(1, self.width()); h = max(1, self.height())
        self.px, self.py = w*0.45, h*0.5
        self.vx = self.vy = 0.0
        self.mx, self.my = self.px, self.py
        self.heading = 0.0
        self.key_left = self.key_right = False

        self.score = 0
        self.orbs.clear()
        self.glitches.clear()
        self.sparks.clear()

        self._phase = 0.0; self._elapsed = 0.0
        self.timers = {"orb": 0.0, "glitch": 1.0}

        for _ in range(6): self._spawn_orb()

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

        # حرکت بازیکن اصلی
        if self._control == "mouse":
            accel, damping, maxs = 720, 0.88, 320
            dx = self.mx - self.px; dy = self.my - self.py
            self.vx += (1 if dx>0 else -1 if dx<0 else 0) * accel * dt
            self.vy += (1 if dy>0 else -1 if dy<0 else 0) * accel * dt
            sp = math.hypot(self.vx, self.vy)
            if sp>maxs:
                self.vx = self.vx/sp*maxs; self.vy = self.vy/sp*maxs
            self.vx *= 0.88; self.vy *= 0.88
            self.px += self.vx*dt; self.py += self.vy*dt
        else:
            if self.key_left:  self.heading -= self.turn_speed * dt
            if self.key_right: self.heading += self.turn_speed * dt
            self.px += math.cos(self.heading)*self.forward_speed*dt
            self.py += math.sin(self.heading)*self.forward_speed*dt

        # wrap
        if self.px < 0: self.px += w
        elif self.px > w: self.px -= w
        if self.py < 0: self.py += h
        elif self.py > h: self.py -= h

        # موقعیت فلش آینه‌ای (دقیقاً قرینهٔ افقی نسبت به مرکز)
        mirror_x = w - self.px
        mirror_y = self.py
        mirror_heading = (math.pi - self.heading) if self._control == "keys" else math.atan2(self.vy, self.vx) + math.pi

        # اسپاون
        self.timers["orb"]   -= dt
        self.timers["glitch"]-= dt
        if self.timers["orb"] <= 0 and len(self.orbs) < 12:
            self._spawn_orb()
            self.timers["orb"] = max(0.25, 1.2 - self._phase*0.05)
        if self.timers["glitch"] <= 0:
            self._spawn_glitch(w, h)
            self.timers["glitch"] = max(0.7, 1.6 - self._phase*0.06)

        # حرکت گلیچ‌ها + برخورد
        for g in list(self.glitches):
            g["x"] += g["vx"]*dt; g["y"] += g["vy"]*dt
            if g["x"] < 0 or g["x"] > w: g["vx"] *= -1
            if g["y"] < 0 or g["y"] > h: g["vy"] *= -1
            g["life"] -= dt
            if g["life"] <= 0:
                self.glitches.remove(g); continue
            # برخورد با هر کدام از دو فلش
            if (self.px - g["x"])**2 + (self.py - g["y"])**2 < GLITCH_R2:
                self._finish("hit"); return
            if (mirror_x - g["x"])**2 + (mirror_y - g["y"])**2 < GLITCH_R2:
                self._finish("hit"); return

        # گرفتن اورب‌ها با «هر کدام» از فلش‌ها
        i = len(self.orbs)-1
        while i >= 0:
            ox, oy, t = self.orbs[i]
            if ((self.px - ox)**2 + (self.py - oy)**2 < ORB_R2) or \
               ((mirror_x - ox)**2 + (mirror_y - oy)**2 < ORB_R2):
                self.orbs.pop(i)
                self._spark(ox, oy, 130)
                self.score += 15
                self.scoreChanged.emit(self.score)
            i -= 1

        # تایمر Story
        if self._mode == "story":
            self.time_left = max(0.0, self.time_left - dt)
            if self.time_left == 0.0:
                ok = self.score >= 220
                self._finish("success" if ok else "timeout")
                return

        # افکت‌ها
        for s in list(self.sparks):
            s["x"] += s["vx"]*dt; s["y"] += s["vy"]*dt
            s["life"] -= dt
            if s["life"] <= 0: self.sparks.remove(s)

        # ذخیره برای رندر
        self._mirror_pos = (mirror_x, mirror_y, mirror_heading)

    # ---------- اسپاون ----------
    def _spawn_orb(self):
        w, h = max(self.width(), 800), max(self.height(), 600)
        self.orbs.append((
            random.uniform(30, w-30),
            random.uniform(30, h-30),
            0.0
        ))

    def _spawn_glitch(self, w, h):
        sp = random.uniform(36, 80) * (1 + self._phase*0.06)
        ang = random.uniform(0, math.tau)
        x = random.uniform(40, w-40)
        y = random.uniform(40, h-40)
        self.glitches.append({
            "x": x, "y": y,
            "vx": math.cos(ang)*sp, "vy": math.sin(ang)*sp,
            "life": random.uniform(6, 12),
            "hue": random.uniform(0, 20)
        })

    def _spark(self, x, y, hue):
        for i in range(14):
            a = (i/14)*math.tau + random.uniform(-0.1, 0.1)
            self.sparks.append({
                "x": x, "y": y,
                "vx": math.cos(a)*160, "vy": math.sin(a)*160,
                "life": 0.45, "hue": hue
            })

    # ---------- ورودی ----------
    def mouseMoveEvent(self, e):
        if self._control == "mouse":
            self.mx = e.position().x(); self.my = e.position().y()

    def keyPressEvent(self, e: QtGui.QKeyEvent):
        if self._control != "keys":
            return super().keyPressEvent(e)
        k = e.key()
        if k in (QtCore.Qt.Key_Left, QtCore.Qt.Key_A):  self.key_left = True;  return
        if k in (QtCore.Qt.Key_Right, QtCore.Qt.Key_D): self.key_right = True; return
        if k in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            if not self.running:
                self.reset(); self.start(); return
        super().keyPressEvent(e)

    def keyReleaseEvent(self, e: QtGui.QKeyEvent):
        if self._control != "keys":
            return super().keyReleaseEvent(e)
        if e.key() in (QtCore.Qt.Key_Left, QtCore.Qt.Key_A):  self.key_left = False;  return
        if e.key() in (QtCore.Qt.Key_Right, QtCore.Qt.Key_D): self.key_right = False; return
        super().keyReleaseEvent(e)

    def showEvent(self, e):
        super().showEvent(e)
        self.setFocus(QtCore.Qt.ActiveWindowFocusReason)

    # ---------- پایان ----------
    def _finish(self, reason: str):
        self.running = False
        self.best = max(self.best, self.score); self.bestChanged.emit(self.best)
        if self._mode == "endless":
            self.runEnded.emit(self.score, "mirror-endless", reason)
        else:
            self.runEnded.emit(self.score, "mirror-story-1", "success" if reason=="success" else reason)

    # ---------- رندر ----------
    def paintEvent(self, e: QtGui.QPaintEvent):
        p = QtGui.QPainter(self); p.setRenderHint(QtGui.QPainter.Antialiasing)
        w,h = self.width(), self.height()
        t = time.perf_counter()

        # بک‌گراند
        grad = QtGui.QLinearGradient(0,0,w,h)
        a = self._theme.bgA + math.sin(t*0.7)*18
        b = self._theme.bgB + math.cos(t*0.6)*18
        grad.setColorAt(0, QtGui.QColor.fromHsl(int(a)%360, 180, 15))
        grad.setColorAt(1, QtGui.QColor.fromHsl(int(b)%360, 180, 18))
        p.fillRect(self.rect(), grad)

        # اورب‌ها
        p.setPen(QtCore.Qt.NoPen)
        for ox,oy,tt in self.orbs:
            pul = 1 + math.sin((tt + t*0.6)*6)*0.20
            base = QtGui.QColor(120, 220, 255, 230)
            glow = QtGui.QColor(base); glow.setAlpha(80)
            p.setBrush(glow); p.drawEllipse(QtCore.QPointF(ox,oy), 11*pul, 11*pul)
            p.setBrush(base); p.drawEllipse(QtCore.QPointF(ox,oy), 8*pul, 8*pul)

        # گلیچ‌ها
        for g in self.glitches:
            halo = QtGui.QColor.fromHsl(int(g["hue"])%360, 240, 130, 110)
            p.setBrush(halo); p.setPen(QtCore.Qt.NoPen)
            p.drawEllipse(QtCore.QPointF(g["x"], g["y"]), 13, 13)
            core = QtGui.QColor.fromHsl(int(g["hue"])%360, 240, 180, 230)
            p.setBrush(core); p.drawEllipse(QtCore.QPointF(g["x"], g["y"]), 9, 9)

        # اسپارک‌ها
        pen2 = QtGui.QPen(QtGui.QColor(255,255,255,170), 1.3)
        p.setPen(pen2)
        for s in self.sparks:
            p.drawLine(s["x"], s["y"], s["x"] - s["vx"]*0.03, s["y"] - s["vy"]*0.03)

        # دو فلش: اصلی + آینه‌ای
        mirror_x, mirror_y, mirror_heading = getattr(self, "_mirror_pos", (w-self.px, self.py, self.heading+math.pi))
        def draw_player(x,y,dir_angle, vx=None, vy=None):
            sp = math.hypot(vx or 0.0, vy or 0.0) if self._control=="mouse" else self.forward_speed
            trail = min(sp * 0.04, 12)
            p.save(); p.translate(x,y); p.rotate(math.degrees(dir_angle))
            glowA = QtGui.QColor(self._theme.playerA); glowA.setAlpha(100)
            p.setBrush(glowA); p.setPen(QtCore.Qt.NoPen)
            p.drawEllipse(QtCore.QPointF(0,0), PLAYER_R + trail*0.6, PLAYER_R + trail*0.6)
            grad2 = QtGui.QLinearGradient(-trail, -PLAYER_R, PLAYER_R, PLAYER_R)
            grad2.setColorAt(0, QtGui.QColor(self._theme.playerA))
            grad2.setColorAt(1, QtGui.QColor(self._theme.playerB))
            p.setBrush(QtGui.QBrush(grad2))
            path = QtGui.QPainterPath()
            path.moveTo(PLAYER_R + 2, 0)
            path.lineTo(-PLAYER_R - trail, -PLAYER_R * 0.75)
            path.lineTo(-PLAYER_R - trail,  PLAYER_R * 0.75)
            path.closeSubpath()
            p.drawPath(path)
            p.restore()

        # جهت فلش اصلی
        direction = math.atan2(self.vy, self.vx) if self._control=="mouse" else self.heading
        draw_player(self.px, self.py, direction, self.vx, self.vy)
        draw_player(mirror_x, mirror_y, mirror_heading)

        # HUD
        p.setPen(QtGui.QPen(QtGui.QColor(255,255,255,150)))
        p.setFont(QtGui.QFont("Inter", 10, QtGui.QFont.Bold))
        mode = "Endless" if self._mode=="endless" else "Story"
        ctrl = "Mouse" if self._control=="mouse" else "Keys"
        p.drawText(10, h-12, f"Mirror Pulse — {mode} | Ctrl: {ctrl}")

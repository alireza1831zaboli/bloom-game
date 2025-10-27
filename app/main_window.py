"""Main window and navigation for Neural Bloom (refactor-safe docstring)."""
from PySide6 import QtWidgets, QtGui, QtCore
from typing import Optional, Callable, Any
from .game_widget import GameWidget
from .leaderboard import LocalLeaderboard, OnlineLeaderboard

# ایمپورت‌ها
from .views.hub_menu import HubMenu
from .views.games.classic_menu import ClassicMenu
from .views.games.weave_menu import WeaveMenu
from .views.games.phantom_menu import PhantomMenu
from .views.games.mirror_menu import MirrorMenu
from .views.games.collapse_menu import CollapseMenu
from .views.settings_page import SettingsPage
from .views.about_page import AboutPage
from .views.dialogs.level_select import LevelSelectDialog
from .views.widgets.countdown import CountdownOverlay
from .modes.weave_widget import WeaveWidget
from .modes.mirror_widget import MirrorWidget
from .modes.phantom_run_widget import PhantomRunWidget

# app/main_window.py (بالا)
from app.modes.neural_collapse_widget import NeuralCollapseWidget
from app.modes.signal_rush_widget import SignalRushWidget
from app.views.games.rush_menu import RushMenu


import json, os

from app.i18n import tr
from .settings import (
    THEMES,
    BRAND_NAME,
    TAGLINE,
    STORY_LEVELS,
    PROGRESS_PATH,
    SETTINGS_PATH,
    LANG_DEFAULT,
)




class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # ---- load persisted settings (lang/control/music/sfx/theme)
        self.settings = self._load_settings()
        self._lang = self.settings.get("lang", LANG_DEFAULT)

        # window basic
        self.setWindowTitle(tr("app.title", self._lang))
        self.setMinimumSize(1120, 700)
        self.setLayoutDirection(
            QtCore.Qt.RightToLeft if self._lang == "fa" else QtCore.Qt.LeftToRight
        )

        # leaderboards & progress
        self.lb_local = LocalLeaderboard()
        self.lb_online = OnlineLeaderboard()
        self.progress = self._load_progress()  # {"unlocked": int, "current": int}

        # --- Stack مرکزی
        self.stack = QtWidgets.QStackedWidget(self)
        self.setCentralWidget(self.stack)

        # --- صفحه بازی (GameWidget + Toolbar)
        game_wrap = QtWidgets.QWidget()
        gv = QtWidgets.QVBoxLayout(game_wrap)
        gv.setContentsMargins(8, 8, 8, 8)
        gv.setSpacing(8)
        self.game = GameWidget()
        top_bar = self._build_game_toolbar()
        gv.addWidget(top_bar)

        # محل نمایش بازی‌های مختلف
        self.game_host = QtWidgets.QStackedWidget()
        gv.addWidget(self.game_host, 1)

        self.active_game = self.game
        self._install_game(self.game)

        # --- Hub Menu (new)
        self.menu = HubMenu(self._lang)
        self.menu.openClassic.connect(lambda: self.stack.setCurrentIndex(2))
        self.menu.openWeave.connect(lambda: self.stack.setCurrentIndex(3))
        self.menu.openPhantom.connect(lambda: self.stack.setCurrentIndex(4))
        self.menu.openArchitect.connect(lambda: self.stack.setCurrentIndex(5))
        self.menu.openMirror.connect(lambda: self.stack.setCurrentIndex(6))
        self.menu.openCollapse.connect(lambda: self.stack.setCurrentIndex(7))
        self.menu.openSettings.connect(lambda: self.stack.setCurrentIndex(8))
        self.menu.openAbout.connect(lambda: self.stack.setCurrentIndex(9))
        self.menu.exitApp.connect(self.close)

        # --- منوهای بازی‌ها
        self.menu_classic = ClassicMenu(self._lang)
        self.menu_weave = WeaveMenu(self._lang)
        self.menu_phantom = PhantomMenu(self._lang)
        self.menu_rush = RushMenu(self._lang)
        self.menu_mirror = MirrorMenu(self._lang)
        self.menu_collapse = CollapseMenu(self._lang)

        for m in (
            self.menu_classic,
            self.menu_weave,
            self.menu_phantom,
            self.menu_rush,
            self.menu_mirror,
            self.menu_collapse,
        ):
            m.goBack.connect(lambda _=None: self.stack.setCurrentIndex(0))

        # شروع بازی از منوها
        self.menu_classic.startEndless.connect(
            lambda: self._start_mode("classic", "endless")
        )
        self.menu_classic.startStory.connect(
            lambda: self._start_mode("classic", "story")
        )
        self.menu_weave.startEndless.connect(
            lambda: self._start_mode("weave", "endless")
        )
        self.menu_weave.startStory.connect(lambda: self._start_mode("weave", "story"))
        self.menu_phantom.startEndless.connect(
            lambda: self._start_mode("phantom", "endless")
        )
        self.menu_phantom.startStory.connect(
            lambda: self._start_mode("phantom", "story")
        )
        self.menu_rush.startEndless.connect(lambda: self._start_mode("rush", "endless"))
        self.menu_rush.startStory.connect(lambda: self._start_mode("rush", "story"))

        self.menu_mirror.startEndless.connect(
            lambda: self._start_mode("mirror", "endless")
        )
        self.menu_mirror.startStory.connect(lambda: self._start_mode("mirror", "story"))
        self.menu_collapse.startEndless.connect(
            lambda: self._start_mode("collapse", "endless")
        )
        self.menu_collapse.startStory.connect(
            lambda: self._start_mode("collapse", "story")
        )

        # --- Quick Retry floating button
        self.quick_retry = QtWidgets.QPushButton("↻", game_wrap)
        self.quick_retry.setObjectName("nbQuickRetry")
        self.quick_retry.setToolTip("Retry (Enter)")
        self.quick_retry.setFixedSize(36, 36)
        self.quick_retry.hide()
        self.quick_retry.clicked.connect(lambda: (self.game.reset(), self.game.start()))

        # ---- Settings page (with current language)
        self.settings_page = SettingsPage(list(THEMES.keys()), lang=self._lang)
        self.settings_page.backToMenu.connect(lambda: self.stack.setCurrentIndex(0))
        self.settings_page.applyRequested.connect(self._apply_settings)

        # ---- About page
        self.about_page = AboutPage(creator_name="(Alireza.Z)")
        self.about_page.backToMenu.connect(lambda: self.stack.setCurrentIndex(0))

        # ---- add pages to stack
        self.stack.addWidget(self.menu)  # 0
        self.stack.addWidget(game_wrap)  # 1
        self.stack.addWidget(self.menu_classic)  # 2
        self.stack.addWidget(self.menu_weave)  # 3
        self.stack.addWidget(self.menu_phantom)  # 4
        self.stack.addWidget(self.menu_rush)  # 5
        self.stack.addWidget(self.menu_mirror)  # 6
        self.stack.addWidget(self.menu_collapse)  # 7
        self.stack.addWidget(self.settings_page)  # 8
        self.stack.addWidget(self.about_page)  # 9

        # ---- status bar
        self.status = self.statusBar()
        self.status.showMessage(TAGLINE)

        # ---- game signals -> toolbar chips
        self.game.scoreChanged.connect(lambda v: self.lbl_score.setText(f"Score: {v}"))
        self.game.timeChanged.connect(lambda v: self.lbl_time.setText(f"Time: {v}s"))
        self.game.bestChanged.connect(lambda v: self.lbl_best.setText(f"Best: {v}"))
        self.game.runEnded.connect(self._on_run_end)

        # ---- player name
        self._load_name()

        # --- وضعیت اولیه بازی از تنظیمات
        self.game.set_control_mode(self.settings.get("control", "Mouse"))
        self.game.set_music(self.settings.get("music", False))
        self.game.set_sfx(self.settings.get("sfx", True))
        self.game.set_theme(self.settings.get("theme", "Aurora"))

        self.game.started.connect(lambda: self.quick_retry.hide())
        self.game.screenshotSaved.connect(
            lambda path: self.status.showMessage(f"Saved: {path}", 3000)
        )

        # start at menu
        self.stack.setCurrentIndex(0)

    # ------------------------------------------------------------------
    # UI pieces

        # final guard: ensure countdown exists
        self._ensure_countdown_created()

        # HUD shadow for readability
        try:
            self._apply_shadow_effect(self.lbl_score)
            self._apply_shadow_effect(self.lbl_time)
            self._apply_shadow_effect(self.lbl_best)
        except Exception:
            pass
    def _build_game_toolbar(self):
        w = QtWidgets.QWidget()
        h = QtWidgets.QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)

        self.btn_menu = QtWidgets.QPushButton(tr("toolbar.back", self._lang))
        self.btn_menu.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        h.addWidget(self.btn_menu)

        h.addSpacing(16)

        # player name
        self.name_edit = QtWidgets.QLineEdit(self)
        self.name_edit.setPlaceholderText(
            "نام بازیکن…" if self._lang == "fa" else "Player name…"
        )
        self.name_edit.setFixedWidth(180)
        self.name_edit.editingFinished.connect(self._save_name)
        name_wrap = QtWidgets.QWidget()
        ly = QtWidgets.QHBoxLayout(name_wrap)
        ly.setContentsMargins(0, 0, 0, 0)
        ly.addWidget(QtWidgets.QLabel("👤"))
        ly.addWidget(self.name_edit)
        h.addWidget(name_wrap)

        h.addSpacing(12)

        # chips
        def chip(lbl: str):
            lab = QtWidgets.QLabel(lbl)
            lab.setObjectName("nbChip")
            return lab

        self.lbl_score = chip("Score: 0")
        self.lbl_time = chip("Time: ∞")
        self.lbl_best = chip("Best: 0")
        h.addWidget(self.lbl_score)
        h.addWidget(self.lbl_time)
        h.addWidget(self.lbl_best)
        h.addStretch(1)

        # start/pause/reset
        self.btn_start = QtWidgets.QPushButton("Start")
        self.btn_start.clicked.connect(lambda: getattr(self.active_game, "start")())

        self.btn_pause = QtWidgets.QPushButton("Pause")
        self.btn_pause.clicked.connect(
            lambda: getattr(self.active_game, "toggle_pause")()
        )

        self.btn_reset = QtWidgets.QPushButton("Reset")
        self.btn_reset.clicked.connect(lambda: getattr(self.active_game, "reset")())
        for b in (self.btn_menu, self.btn_start, self.btn_pause, self.btn_reset):
            b.setFocusPolicy(QtCore.Qt.NoFocus)
        self.name_edit.setFocusPolicy(QtCore.Qt.ClickFocus)  # فقط با کلیک فوکوس بگیرد

        h.addWidget(self.btn_start)
        h.addWidget(self.btn_pause)
        h.addWidget(self.btn_reset)

        return w

    # ------------------------------------------------------------------
    # Settings I/O
    def _load_settings(self):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {
                "lang": LANG_DEFAULT,
                "control": "Mouse",
                "music": False,
                "sfx": True,
                "theme": "Aurora",
                "sensitivity": 1.0,
                "difficulty": "Normal",
            }

    def _save_settings(self):
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)

    def _apply_settings(self, data: dict):
        # persist
        self.settings.update(data)
        self._save_settings()

        # apply to game
        self.game.set_control_mode(self.settings["control"])
        self.game.set_music(self.settings["music"])
        self.game.set_sfx(self.settings["sfx"])
        self.game.set_theme(self.settings["theme"])
        self.game.set_mouse_sensitivity(self.settings.get("sensitivity", 1.0))
        self.game.set_difficulty(self.settings.get("difficulty", "Normal"))

        # language switch
        if data.get("lang") and data["lang"] != self._lang:
            self._lang = data["lang"]
            self._apply_language()

        # toast
        self.statusBar().showMessage(tr("apply", self._lang), 2500)

    def _apply_language(self):
        # direction
        rtl = self._lang == "fa"
        self.setLayoutDirection(QtCore.Qt.RightToLeft if rtl else QtCore.Qt.LeftToRight)

        # window title
        self.setWindowTitle(tr("app.title", self._lang))

        # rebuild toolbar texts
        self.btn_menu.setText(tr("toolbar.back", self._lang))
        self.btn_start.setText(tr("toolbar.start", self._lang))
        self.btn_pause.setText(tr("toolbar.pause", self._lang))
        self.btn_reset.setText(tr("toolbar.reset", self._lang))
        self.name_edit.setPlaceholderText("نام بازیکن…" if rtl else "Player name…")

        # pages that need retranslate
        try:
            self.settings_page.set_lang(self._lang)
        except Exception:
            pass
        try:
            self.menu.retranslate(self._lang)
        except Exception:
            pass
        try:
            self.about_page.retranslate(self._lang)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Progress I/O
    def _load_progress(self):
        if os.path.exists(PROGRESS_PATH):
            try:
                with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    return {
                        "unlocked": max(1, int(d.get("unlocked", 1))),
                        "current": max(0, int(d.get("current", 0))),
                    }
            except Exception:
                pass
        return {"unlocked": 1, "current": 0}

    def _save_progress(self):
        with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # Name I/O
    def _load_name(self):
        try:
            with open("player.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                self.name_edit.setText(data.get("name", "Player"))
        except Exception:
            self.name_edit.setText("Player")

    def _save_name(self):
        name = self.name_edit.text().strip() or "Player"
        with open("player.json", "w", encoding="utf-8") as f:
            json.dump({"name": name}, f, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Menu actions
    def on_continue_story(self):
        if self.progress["unlocked"] <= 1:
            return
        self._go_story(idx=self.progress.get("current", 0), intro=True)

    def on_new_stage(self):
        unlocked = self.progress.get("unlocked", 1)
        dlg = LevelSelectDialog(unlocked, self)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            sel = dlg.selected_index()
            if sel is not None:
                self.progress["current"] = sel
                self._save_progress()
                self._go_story(idx=sel, intro=True)

    def on_endless(self):
        self.game.set_mode("endless")
        self.game.prepare_endless()
        self.lbl_time.setText("Time: ∞")
        self.stack.setCurrentIndex(1)  # اول برو صفحه
        QtCore.QTimer.singleShot(
            0, lambda: self.active_game.setFocus(QtCore.Qt.ActiveWindowFocusReason)
        )
        self._show_intro_endless()

    def open_settings(self):
        self.stack.setCurrentIndex(2)

    def open_about(self):
        self.stack.setCurrentIndex(3)

    # ------------------------------------------------------------------
    # phantom helpers
    def _go_story(self, idx: int, intro: bool = True):
        self.game.set_mode("story")
        self.game.prepare_story(idx)
        self.stack.setCurrentIndex(1)
        QtCore.QTimer.singleShot(
            0, lambda: self.active_game.setFocus(QtCore.Qt.ActiveWindowFocusReason)
        )
        if intro:
            self._show_intro_story(idx)

    def _show_intro_endless(self):
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle(
            "Endless Mode — راهنما" if self._lang == "fa" else "Endless Mode — Help"
        )
        msg.setText(
            "در حالت Endless تایمر نداریم؛ تا وقتی به گلیچ برخورد نکنی ادامه می‌دهی.\nکنترل از تنظیمات: Mouse یا Keys."
            if self._lang == "fa"
            else "No timer in Endless; you play until you hit a glitch.\nPick control mode (Mouse/Keys) in Settings."
        )
        start = msg.addButton(
            "شروع" if self._lang == "fa" else "Start", QtWidgets.QMessageBox.AcceptRole
        )
        msg.addButton(
            "بازگشت" if self._lang == "fa" else "Back", QtWidgets.QMessageBox.RejectRole
        )
        msg.exec()
        # در هر دو متد:
        if msg.clickedButton() == start:
            self._start_with_countdown(self.active_game)
            QtCore.QTimer.singleShot(
                0, lambda: self.active_game.setFocus(QtCore.Qt.ActiveWindowFocusReason)
            )
        else:
            self.stack.setCurrentIndex(0)

    def _show_intro_story(self, idx: int):
        lvl = STORY_LEVELS[idx]
        mods = lvl.get("mods", {})
        if self._lang == "fa":
            details = f"مرحله {lvl['id']}: {lvl['title']}\nهدف: {lvl['desc']}\n"
            details += f"تم: {mods.get('theme','Aurora')} | اسپاون×{mods.get('spawnMul',1.0)} | سرعت گلیچ×{mods.get('glitchSpeedMul',1.0)}"
            title = "شروع مرحله"
            bstart, bback = "شروع", "بازگشت"
        else:
            details = f"Stage {lvl['id']}: {lvl['title']}\nGoal: {lvl['desc']}\n"
            details += f"Theme: {mods.get('theme','Aurora')} | Spawn×{mods.get('spawnMul',1.0)} | Glitch Speed×{mods.get('glitchSpeedMul',1.0)}"
            title = "Stage Intro"
            bstart, bback = "Start", "Back"

        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(details)
        start = msg.addButton(bstart, QtWidgets.QMessageBox.AcceptRole)
        msg.addButton(bback, QtWidgets.QMessageBox.RejectRole)
        msg.exec()
        # در هر دو متد:
        if msg.clickedButton() == start:
            self._start_with_countdown(self.active_game)
            QtCore.QTimer.singleShot(
                0, lambda: self.active_game.setFocus(QtCore.Qt.ActiveWindowFocusReason)
            )
        else:
            self.stack.setCurrentIndex(0)

    # ------------------------------------------------------------------
    # End-of-run dialog
    def _on_run_end(self, score: int, mode: str, reason: str):
        # show quick retry button on game page
        self.quick_retry.show()
        name = self.name_edit.text().strip() or "Player"
        self.lb_local.add(name, score, mode)
        self.lb_online.submit(name, score, mode)

        # تشخیص اینکه کدام ویجت فعال است (classic یا weave و ...)
        G = self.active_game

        if mode.startswith("story-") or "-story" in mode:
            try:
                sid = int(mode.split("-")[1])
            except Exception:
                sid = self.progress.get("current", 0) + 1
            idx = max(0, sid - 1)
            lvl = STORY_LEVELS[idx]
            success = reason == "success"

            mb = QtWidgets.QMessageBox(self)
            mb.setWindowTitle(
                f"مرحله {sid} — " + ("موفقیت 🎉" if success else "ناموفق 😵‍💫")
            )
            mb.setText(f"امتیاز: {score}\n{lvl['title']} — {lvl['desc']}")

            # دکمه‌ها
            if success:
                nextb = mb.addButton("مرحله بعد", QtWidgets.QMessageBox.AcceptRole)
            retry = mb.addButton("دوباره", QtWidgets.QMessageBox.ActionRole)
            choose = mb.addButton("انتخاب مرحله", QtWidgets.QMessageBox.ActionRole)
            menu = mb.addButton("منوی اصلی", QtWidgets.QMessageBox.DestructiveRole)

            mb.exec()

            if success and mb.clickedButton() == nextb:
                nxt = min(idx + 1, len(STORY_LEVELS) - 1)
                self.progress["current"] = nxt
                self._save_progress()
                # بدون اینترو، مستقیم آماده و استارت:
                try:
                    G.prepare_story(nxt)
                except TypeError:
                    G.prepare_story(0)
                self.stack.setCurrentIndex(1)
                self._start_with_countdown(G)
                QtCore.QTimer.singleShot(
                    0, lambda: G.setFocus(QtCore.Qt.ActiveWindowFocusReason)
                )
            elif mb.clickedButton() == retry:
                try:
                    G.prepare_story(idx)
                except TypeError:
                    G.prepare_story(0)
                self.stack.setCurrentIndex(1)
                self._start_with_countdown(G)
                QtCore.QTimer.singleShot(
                    0, lambda: G.setFocus(QtCore.Qt.ActiveWindowFocusReason)
                )
            elif mb.clickedButton() == choose:
                self.on_new_stage()
            else:
                self.stack.setCurrentIndex(0)
            return

        # ---- Endless
        if "endless" in mode:
            msg = QtWidgets.QMessageBox(self)
            msg.setWindowTitle("پایان بازی (Endless)")
            why = "برخورد با گلیچ" if reason in ("hit", "self") else "پایان"
            msg.setText(f"امتیاز: {score}\nدلیل پایان: {why}")
            again = msg.addButton("دوباره", QtWidgets.QMessageBox.AcceptRole)
            menu = msg.addButton("منوی اصلی", QtWidgets.QMessageBox.ActionRole)
            story = msg.addButton("Story", QtWidgets.QMessageBox.ActionRole)
            msg.exec()

            if msg.clickedButton() == again:
                G.set_mode("endless")
                G.prepare_endless()
                self.stack.setCurrentIndex(1)
                self._start_with_countdown(G)  # ← مستقیم شروع
                QtCore.QTimer.singleShot(
                    0, lambda: G.setFocus(QtCore.Qt.ActiveWindowFocusReason)
                )
            elif msg.clickedButton() == story:
                (
                    self.on_continue_story()
                    if self.progress["unlocked"] > 1
                    else self.on_new_stage()
                )
            else:
                self.stack.setCurrentIndex(0)

    def resizeEvent(self, e: QtGui.QResizeEvent):
        super().resizeEvent(e)
        # اگر صفحه‌ی بازی فعال است، دکمه را گوشه‌ی پایین-راست بگذار
        if self.stack.currentIndex() == 1:
            cw = self.stack.widget(1)  # game_wrap
            x = cw.width() - self.quick_retry.width() - 20
            y = cw.height() - self.quick_retry.height() - 20
            self.quick_retry.move(x, y)

    def _start_mode(self, submode: str, runmode: str):
        """submode: classic/weave/flow/arch/mirror/collapse | runmode: endless|story"""

        # انتخاب ویجت بازی
        if submode == "classic":
            gw = getattr(self, "_w_classic", None)
            if gw is None:
                self._w_classic = GameWidget()
                gw = self._w_classic
            self._install_game(gw)
        elif submode == "weave":
            gw = getattr(self, "_w_weave", None)
            if gw is None:
                self._w_weave = WeaveWidget()
                gw = self._w_weave
            self._install_game(gw)
        elif submode == "phantom":
            gw = getattr(self, "_w_phantom", None)
            if gw is None:
                self._w_phantom = PhantomRunWidget()
                gw = self._w_phantom
            self._install_game(gw)
        elif submode == "mirror":
            gw = getattr(self, "_w_mirror", None)
            if gw is None:
                self._w_mirror = MirrorWidget()
                gw = self._w_mirror
            self._install_game(gw)
        elif submode == "collapse":
            # فعلاً سایر مودها را هم با کلاسیک اجرا کن تا صفحه‌ها از کار نیفتند
            gw = getattr(self, "_w_classic", None)
            if gw is None:
                self._w_collapse = NeuralCollapseWidget()
                gw = self._w_collapse
            self._install_game(gw)
        elif submode == "rush":
            gw = getattr(self, "_w_rush", None)
            if gw is None:
                self._w_rush = SignalRushWidget()
                gw = self._w_rush
            self._install_game(gw)
        else:
            gw = getattr(self, "_w_arch", None)
            if gw is None:
                self._w_arch = SignalRushWidget()
                gw = self._w_arch
            self._install_game(gw)

        # تنظیم مود و آماده‌سازی
        if runmode == "endless":
            self.active_game.set_mode("endless")
            self.active_game.prepare_endless()
            self.lbl_time.setText("Time: ∞")
            self.stack.setCurrentIndex(1)
            QtCore.QTimer.singleShot(
                0, lambda: self.active_game.setFocus(QtCore.Qt.ActiveWindowFocusReason)
            )
            self._show_intro_endless()
        else:
            self.active_game.set_mode("story")
            idx = self.progress.get("current", 0)
            try:
                self.active_game.prepare_story(idx)
            except TypeError:
                # بعضی ویجت‌ها شاید ایندکس نخواهند
                self.active_game.prepare_story(0)
            self.stack.setCurrentIndex(1)
            QtCore.QTimer.singleShot(
                0, lambda: self.active_game.setFocus(QtCore.Qt.ActiveWindowFocusReason)
            )
            self._show_intro_story(idx)

    def _apply_language(self):
        # ... (همان نسخه‌ی اصلاحی قبلی)
        # اضافه: ترجمه‌ی منوهای جدید
        try:
            self.menu.retranslate(self._lang)
        except:
            pass
        for m in (
            self.menu_classic,
            self.menu_weave,
            self.menu_phantom,
            self.menu_rush,
            self.menu_mirror,
            self.menu_collapse,
        ):
            try:
                m.retranslate(self._lang)
            except:
                pass
        self.settings_page.set_lang(self._lang)
        try:
            self.about_page.retranslate(self._lang)
        except:
            pass

    def _install_game(self, gw: QtWidgets.QWidget):
        """ویجت بازی را داخل game_host قرار می‌دهد و سیگنال‌ها را می‌بندد."""
        # اگر قبلاً داخل استک نبود، اضافه‌اش کن
        idx = self.game_host.indexOf(gw)
        if idx == -1:
            self.game_host.addWidget(gw)
            idx = self.game_host.indexOf(gw)
        self.game_host.setCurrentIndex(idx)

        self._safe_disconnect()

        self.active_game = gw
        self.active_game.scoreChanged.connect(
            lambda v: self.lbl_score.setText(f"Score: {v}")
        )
        self.active_game.timeChanged.connect(
            lambda v: self.lbl_time.setText(f"Time: {v}s" if v >= 0 else "Time: ∞")
        )
        self.active_game.bestChanged.connect(
            lambda v: self.lbl_best.setText(f"Best: {v}")
        )
        self.active_game.runEnded.connect(self._on_run_end)

        # اعمال تنظیمات فعلی روی بازی
        self.active_game.set_control_mode(self.settings.get("control", "Mouse"))
        self.active_game.set_music(self.settings.get("music", False))
        self.active_game.set_sfx(self.settings.get("sfx", True))
        self.active_game.set_theme(self.settings.get("theme", "Aurora"))
        self.active_game.set_mouse_sensitivity(self.settings.get("sensitivity", 1.0))
        self.active_game.set_difficulty(self.settings.get("difficulty", "Normal"))

        # فوکوس روی خود بازی
        QtCore.QTimer.singleShot(
            0, lambda: self.active_game.setFocus(QtCore.Qt.ActiveWindowFocusReason)
        )

    def _safe_disconnect(self):
        if not hasattr(self, "active_game") or self.active_game is None:
            return
        try:
            if self.active_game.scoreChanged.receivers() > 0:
                self.active_game.scoreChanged.disconnect()
            if self.active_game.timeChanged.receivers() > 0:
                self.active_game.timeChanged.disconnect()
            if self.active_game.bestChanged.receivers() > 0:
                self.active_game.bestChanged.disconnect()
            if self.active_game.runEnded.receivers() > 0:
                self.active_game.runEnded.disconnect()
        except Exception:
            pass

    def _start_with_countdown(self, game_obj):
        def do_start():
            try:
                game_obj.start()
            except Exception:
                pass
        try:
            self._countdown.finished.disconnect()
        except Exception:
            pass
        self._countdown.finished.connect(do_start)
        self._countdown.start()
        # lazy init and resize guard
        if not hasattr(self, "_countdown") or self._countdown is None:
            try:
                self._countdown = CountdownOverlay(parent=self.game_host)
            except Exception:
                try:
                    game_obj.start()
                except Exception:
                    pass
                return
        self._countdown.resize(self.game_host.size())
        # strengthen: ensure overlay exists and sized
        self._ensure_countdown_created()
        if not getattr(self, "_countdown", None):
            try:
                game_obj.start()
            except Exception:
                pass
            return
        try:
            self._countdown.resize(getattr(self, "game_host", self).size())
        except Exception:
            pass


    def resizeEvent(self, ev):
        try:
            if hasattr(self, "_countdown") and self._countdown and self._countdown.isVisible():
                self._countdown.resize(self.game_host.size())
        except Exception:
            pass
        return super().resizeEvent(ev)

    def _ensure_countdown_created(self):
        if not hasattr(self, "_countdown") or self._countdown is None:
            try:
                parent = getattr(self, "game_host", self)
                self._countdown = CountdownOverlay(parent=parent)
            except Exception:
                self._countdown = None


    def _apply_shadow_effect(self, label: QtWidgets.QLabel):
        eff = QtWidgets.QGraphicsDropShadowEffect(self)
        eff.setBlurRadius(8.0)
        eff.setOffset(0, 1)
        eff.setColor(QtGui.QColor(0, 0, 0, 180))
        label.setGraphicsEffect(eff)

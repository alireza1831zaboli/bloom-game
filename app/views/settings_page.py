from PySide6 import QtWidgets, QtCore
from app.i18n import tr


class SettingsPage(QtWidgets.QWidget):
    backToMenu = QtCore.Signal()
    # به‌جای اعمال آنی، همه را یکجا می‌فرستیم:
    applyRequested = QtCore.Signal(dict)

    def __init__(self, themes: list[str], lang: str = "fa", parent=None):
        super().__init__(parent)
        self._themes = themes
        self._lang = lang
        self._build_ui()

    def _build_ui(self):
        self.setLayoutDirection(
            QtCore.Qt.RightToLeft if self._lang == "fa" else QtCore.Qt.LeftToRight
        )
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(14)

        header_row = QtWidgets.QHBoxLayout()
        header = QtWidgets.QLabel(tr("settings.title", self._lang))
        header.setObjectName("nbHeader")
        back = QtWidgets.QPushButton(tr("back", self._lang))
        back.setObjectName("nbBack")
        back.clicked.connect(self.backToMenu.emit)
        header_row.addWidget(header)
        header_row.addStretch(1)
        header_row.addWidget(back)
        root.addLayout(header_row)

        wrapper = QtWidgets.QHBoxLayout()
        wrapper.addStretch(1)
        col = QtWidgets.QVBoxLayout()
        col.setSpacing(12)
        wrapper.addLayout(col)
        wrapper.addStretch(1)
        root.addLayout(wrapper)

        # Card: Preferences
        pref = QtWidgets.QFrame()
        pref.setObjectName("nbCard")
        pl = QtWidgets.QVBoxLayout(pref)
        pl.setSpacing(8)
        title = QtWidgets.QLabel(tr("settings.prefs", self._lang))
        # Mouse sensitivity
        self.slider_sens = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_sens.setMinimum(50)
        self.slider_sens.setMaximum(200)
        self.slider_sens.setValue(100)
        self.slider_sens.setTickInterval(10)
        self.slider_sens.setTickPosition(QtWidgets.QSlider.TicksBelow)
        sens_row = QtWidgets.QHBoxLayout()
        sens_row.addWidget(QtWidgets.QLabel(tr("settings.sens", self._lang)))
        sens_row.addWidget(self.slider_sens)
        pl.addLayout(sens_row)
        # Difficulty preset
        self.cb_diff = QtWidgets.QComboBox()
        self.cb_diff.addItems(["Chill","Normal","Hard"])
        diff_row = QtWidgets.QHBoxLayout()
        diff_row.addWidget(QtWidgets.QLabel(tr("settings.diff", self._lang)))
        diff_row.addWidget(self.cb_diff)
        pl.addLayout(diff_row)
        title.setObjectName("nbCardTitle")
        pl.addWidget(title)

        self.cb_control = QtWidgets.QComboBox()
        self.cb_control.addItems(["Mouse", "Keys"])
        self.chk_sfx = QtWidgets.QCheckBox("SFX")
        self.chk_sfx.setChecked(True)
        self.chk_music = QtWidgets.QCheckBox("Music")
        self.cb_theme = QtWidgets.QComboBox()
        [self.cb_theme.addItem(t) for t in self._themes]
        self.cb_lang = QtWidgets.QComboBox()
        self.cb_lang.addItems(["fa", "en"])
        self.cb_lang.setCurrentText(self._lang)

        pl.addWidget(row_widget(tr("settings.control", self._lang), self.cb_control))
        pl.addWidget(row_widget(tr("settings.sfx", self._lang), self.chk_sfx))
        pl.addWidget(row_widget(tr("settings.music", self._lang), self.chk_music))
        pl.addWidget(row_widget(tr("settings.theme", self._lang), self.cb_theme))
        pl.addWidget(row_widget(tr("settings.lang", self._lang), self.cb_lang))

        # Apply row
        apply_row = QtWidgets.QHBoxLayout()
        apply_row.addStretch(1)
        btn_apply = QtWidgets.QPushButton(tr("apply", self._lang))
        btn_apply.clicked.connect(self._emit_apply)
        apply_row.addWidget(btn_apply)
        pl.addLayout(apply_row)
        col.addWidget(pref)

        # Card: Guide
        guide = QtWidgets.QFrame()
        guide.setObjectName("nbCard")
        gl = QtWidgets.QVBoxLayout(guide)
        gl.setSpacing(6)
        gtitle = QtWidgets.QLabel(tr("settings.guide", self._lang))
        gtitle.setObjectName("nbCardTitle")
        gl.addWidget(gtitle)
        info = QtWidgets.QLabel(tr("settings.hints", self._lang))
        info.setWordWrap(True)
        gl.addWidget(info)
        col.addWidget(guide)
        col.addStretch(1)

        pref.setMinimumWidth(720)
        guide.setMinimumWidth(720)

    def _emit_apply(self):
        data = {
            "control": self.cb_control.currentText(),
            "sfx": self.chk_sfx.isChecked(),
            "music": self.chk_music.isChecked(),
            "theme": self.cb_theme.currentText(),
            "lang": self.cb_lang.currentText(),
            "sensitivity": self.slider_sens.value()/100.0,
            "difficulty": self.cb_diff.currentText(),
        }
        self.applyRequested.emit(data)

    # برای به‌روز شدن متن‌ها بعد از تغییر زبان
    def set_lang(self, lang: str):
        if lang == self._lang:
            return
        self._lang = lang
        # بازسازی کامل UI ساده‌ترین و مطمئن‌ترین روش است
        QtWidgets.QWidget().setLayout(self.layout())  # detach layout
        self._build_ui()


def row_widget(label_text: str, widget: QtWidgets.QWidget) -> QtWidgets.QWidget:
    w = QtWidgets.QWidget()
    h = QtWidgets.QHBoxLayout(w)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(8)
    lbl = QtWidgets.QLabel(label_text)
    lbl.setObjectName("nbFormLabel")
    h.addWidget(lbl, 0)
    h.addWidget(widget, 1)
    return w

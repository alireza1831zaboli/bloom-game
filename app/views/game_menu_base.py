# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtGui, QtCore
from app.i18n import tr


class GameMenuBase(QtWidgets.QWidget):
    startEndless = QtCore.Signal()
    startStory = QtCore.Signal()
    goBack = QtCore.Signal()

    def __init__(
        self,
        key: str,
        title_fa: str,
        title_en: str,
        summary_fa: str,
        summary_en: str,
        tips_fa: str,
        tips_en: str,
        lang: str = "fa",
        parent=None,
    ):
        super().__init__(parent)
        self.key = key
        self.title_fa, self.title_en = title_fa, title_en
        self.summary_fa, self.summary_en = summary_fa, summary_en
        self.tips_fa, self.tips_en = tips_fa, tips_en
        self._lang = lang
        self._build_ui()

    def retranslate(self, lang: str):
        self._lang = lang
        rtl = lang == "fa"
        self.setLayoutDirection(QtCore.Qt.RightToLeft if rtl else QtCore.Qt.LeftToRight)
        title = self.title_fa if rtl else self.title_en
        self.lbl_title.setText(title)
        self.grp_sum.setTitle(tr("gm.summary", lang))
        self.grp_tips.setTitle(tr("gm.tips", lang))
        self.txt_sum.setText(self.summary_fa if rtl else self.summary_en)
        self.txt_tips.setText(self.tips_fa if rtl else self.tips_en)
        self.btn_endless.setText(tr("gm.play.endless", lang))
        self.btn_story.setText(tr("gm.play.story", lang))
        self.btn_back.setText(tr("gm.back", lang))

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(12)

        self.lbl_title = QtWidgets.QLabel(
            self.title_fa if self._lang == "fa" else self.title_en
        )
        self.lbl_title.setObjectName("nbTitle")
        self.lbl_title.setAlignment(QtCore.Qt.AlignHCenter)
        root.addWidget(self.lbl_title)

        # Content
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(14)
        left = QtWidgets.QVBoxLayout()
        right = QtWidgets.QVBoxLayout()
        row.addLayout(left, 2)
        row.addLayout(right, 1)
        root.addLayout(row, 1)

        # Summary card
        # داخل _build_ui همان است، فقط این دو خط را مطمئن باش اضافه شده:
        self.grp_sum = QtWidgets.QGroupBox(tr("gm.summary", self._lang))
        self.grp_sum.setObjectName("nbCard")
        gl = QtWidgets.QVBoxLayout(self.grp_sum)
        self.txt_sum = QtWidgets.QLabel(
            self.summary_fa if self._lang == "fa" else self.summary_en
        )
        self.txt_sum.setWordWrap(True)
        gl.addWidget(self.txt_sum)
        left.addWidget(self.grp_sum)

        # Tips card
        self.grp_tips = QtWidgets.QGroupBox(tr("gm.tips", self._lang))
        self.grp_tips.setObjectName("nbCard")
        tl = QtWidgets.QVBoxLayout(self.grp_tips)
        self.txt_tips = QtWidgets.QLabel(
            self.tips_fa if self._lang == "fa" else self.tips_en
        )
        self.txt_tips.setWordWrap(True)
        tl.addWidget(self.txt_tips)
        left.addWidget(self.grp_tips, 1)

        left.addStretch(1)

        # Side actions
        act = QtWidgets.QFrame()
        act.setObjectName("nbCard")
        al = QtWidgets.QVBoxLayout(act)
        al.setSpacing(10)
        self.btn_endless = QtWidgets.QPushButton(tr("gm.play.endless", self._lang))
        self.btn_story = QtWidgets.QPushButton(tr("gm.play.story", self._lang))
        self.btn_back = QtWidgets.QPushButton(tr("gm.back", self._lang))
        self.btn_endless.clicked.connect(self.startEndless.emit)
        self.btn_story.clicked.connect(self.startStory.emit)
        self.btn_back.clicked.connect(self.goBack.emit)
        al.addWidget(self.btn_endless)
        al.addWidget(self.btn_story)
        al.addStretch(1)
        al.addWidget(self.btn_back)
        right.addWidget(act)
        
    # paintEvent تمیز و بدون overlay تیره اضافی
    def paintEvent(self, e: QtGui.QPaintEvent):
        p = QtGui.QPainter(self); p.setRenderHint(QtGui.QPainter.Antialiasing)
        w,h = self.width(), self.height()
        grad=QtGui.QLinearGradient(0,0,w,h)
        grad.setColorAt(0, QtGui.QColor(18,30,58))
        grad.setColorAt(1, QtGui.QColor(22,46,86))
        p.fillRect(self.rect(), grad)


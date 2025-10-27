from PySide6 import QtWidgets, QtCore, QtGui


class AboutPage(QtWidgets.QWidget):
    backToMenu = QtCore.Signal()

    def __init__(self, creator_name: str = "Your Name", parent=None):
        super().__init__(parent)
        self.creator_name = creator_name
        self.setLayoutDirection(QtCore.Qt.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(14)

        header_row = QtWidgets.QHBoxLayout()
        header = QtWidgets.QLabel("درباره سازنده")
        header.setObjectName("nbHeader")
        back = QtWidgets.QPushButton("↩ بازگشت به منو")
        back.setObjectName("nbBack")
        back.clicked.connect(self.backToMenu.emit)
        header_row.addWidget(header)
        header_row.addStretch(1)
        header_row.addWidget(back)
        root.addLayout(header_row)

        # Centered column with cards
        wrapper = QtWidgets.QHBoxLayout()
        wrapper.addStretch(1)
        col = QtWidgets.QVBoxLayout()
        col.setSpacing(12)
        wrapper.addLayout(col)
        wrapper.addStretch(1)
        root.addLayout(wrapper)

        card = QtWidgets.QFrame()
        card.setObjectName("nbCard")
        cl = QtWidgets.QVBoxLayout(card)
        cl.setSpacing(8)
        title = QtWidgets.QLabel("Neural Bloom")
        title.setObjectName("nbCardTitle")
        cl.addWidget(title)

        body = QtWidgets.QLabel(
            f"این بازی توسط {self.creator_name} ساخته شده است.\n"
            "ایده‌ی اصلی: جریان، کمبو و واکنش سریع.\n"
            "تکنولوژی: Python (PySide6) + QPainter.\n"
            "بازخورد شما باعث بهتر شدن نسخه‌های بعدی می‌شود."
        )
        body.setWordWrap(True)
        cl.addWidget(body)

        col.addWidget(card)
        col.addStretch(1)

        card.setMinimumWidth(720)

    def retranslate(self, lang: str):
        from app.i18n import tr
        rtl = (lang == "fa")
        self.setLayoutDirection(QtCore.Qt.RightToLeft if rtl else QtCore.Qt.LeftToRight)
        # عنوان هدر و متن کارت را با tr به‌روزرسانی کن
        # اگر قبلاً label‌ها را نگه داشته‌ای (self.headerLabel, self.bodyLabel) اینجا setText کن


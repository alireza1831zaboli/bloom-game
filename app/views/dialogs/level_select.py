from PySide6 import QtWidgets, QtCore, QtGui
from app.settings import STORY_LEVELS


class LevelSelectDialog(QtWidgets.QDialog):
    def __init__(self, unlocked: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("انتخاب مرحله")
        self.resize(520, 540)
        v = QtWidgets.QVBoxLayout(self)
        self.list = QtWidgets.QListWidget(self)
        for lvl in STORY_LEVELS[:unlocked]:
            self.list.addItem(f"{lvl['id']:02d} — {lvl['title']}  |  {lvl['desc']}")
        v.addWidget(self.list)
        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)

    def selected_index(self):
        row = self.list.currentRow()
        return row if row >= 0 else None


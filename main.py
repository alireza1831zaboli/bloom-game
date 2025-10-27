from PySide6 import QtWidgets, QtGui, QtCore
from app.main_window import MainWindow
from app.utils import resource_path
import sys, os

def load_qss(app):
    qss_path = resource_path("app/ui_style.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

def load_fonts():
    from PySide6.QtGui import QFontDatabase
    fonts = [
        "app/assets/fonts/Vazirmatn-Regular.ttf",
        "app/assets/fonts/Vazirmatn-Bold.ttf",
        "app/assets/fonts/Inter-Regular.ttf",
        "app/assets/fonts/Inter-Bold.ttf",
    ]
    for rel in fonts:
        path = resource_path(rel)
        if os.path.exists(path):
            QFontDatabase.addApplicationFont(path)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Neural Bloom")

    # فونت‌ها
    load_fonts()
    # فونت پیش‌فرض (فارسی اول، بعد لاتین)
    app.setFont(QtGui.QFont("Vazirmatn", 11))

    # آیکن از SVG (QtSvg لازم است)
    svg_icon = resource_path("app/assets/logo.svg")
    if os.path.exists(svg_icon):
        app.setWindowIcon(QtGui.QIcon(svg_icon))

    load_qss(app)

    # DPI آگاه (تا شفاف و واضح باشد)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())

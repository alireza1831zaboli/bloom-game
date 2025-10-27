# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks.qt import (  # PyInstaller>=5.13+
    add_qt6_dependencies,
    pyside6_library_info,
    QtLibraryInfo,
)

# مسیر پلاگین‌های Qt
qt_info = pyside6_library_info()  # type: QtLibraryInfo
qt_plugins = qt_info.location['PluginsPath']

# فقط پلاگین‌های لازم:
qt_binaries = [
    (os.path.join(qt_plugins, 'platforms', 'qwindows.dll'), 'PySide6/plugins/platforms'),
    (os.path.join(qt_plugins, 'imageformats', 'qjpeg.dll'), 'PySide6/plugins/imageformats'),
    # اگر SVG داخل برنامه می‌خواهی (QIcon از SVG): این سه مورد را نگه دار
    (os.path.join(qt_plugins, 'imageformats', 'qsvg.dll'), 'PySide6/plugins/imageformats'),
    (os.path.join(qt_plugins, 'iconengines', 'qsvgicon.dll'), 'PySide6/plugins/iconengines'),
    # (اختیاری) استایل ویندوز:
    (os.path.join(qt_plugins, 'styles', 'qwindowsvistastyle.dll'), 'PySide6/plugins/styles'),
]

hidden = [
    # ماژول‌های اصلی
    'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets',
    # اگر SVG داخل برنامه می‌خواهی:
    'PySide6.QtSvg',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=qt_binaries,
    datas=[
        ('app/ui_style.qss', 'app'),
        ('app/assets', 'app/assets'),
    ],
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        # هرچیز اضافه Qt که استفاده نمی‌کنی را حذف کن تا سایز کم شود:
        'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets', 'PySide6.QtWebEngineQuick',
        'PySide6.QtNetwork', 'PySide6.QtSql', 'PySide6.QtPrintSupport',
        'PySide6.QtOpenGL', 'PySide6.QtOpenGLWidgets', 'PySide6.QtTest',
        'PySide6.QtCharts', 'PySide6.QtDataVisualization', 'PySide6.Qt3DCore',
        'PySide6.Qt3DRender', 'PySide6.Qt3DInput', 'PySide6.Qt3DExtras',
        'PySide6.QtStateMachine', 'PySide6.QtHelp', 'PySide6.QtLocation',
        'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets',
        'PySide6.QtNfc', 'PySide6.QtPositioning', 'PySide6.QtRemoteObjects',
        'PySide6.QtScxml', 'PySide6.QtSensors', 'PySide6.QtSerialPort',
        'PySide6.QtSpatialAudio', 'PySide6.QtSvgWidgets', 'PySide6.QtTextToSpeech',
        'PySide6.QtXml', 'PySide6.QtXmlPatterns',
    ],
    noarchive=False,
)
# وابستگی‌های پایه Qt6 (platform plugin و …)
add_qt6_dependencies(a)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='Neural Bloom',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,     # با UPX پایین فشرده می‌کنیم
    upx=True,        # اگر UPX نصب است، بهتر!
    console=False,   # بدون پنجره کنسول
    icon=None        # آیکن فایل exe نمی‌خواهی
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=True,
    name='Neural Bloom'
)

# تبدیل به onefile
app = BUNDLE(coll, name='Neural Bloom', launcher=None)

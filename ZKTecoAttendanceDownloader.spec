# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the ZKTeco Attendance Downloader GUI.

Build with:
    pyinstaller ZKTecoAttendanceDownloader.spec --clean

This produces a single windowed .exe at dist/ZKTecoAttendanceDownloader.exe
"""

block_cipher = None

a = Analysis(
    ['zkteco_attendance_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'zk',
        'zk.attendance',
        'zk.base',
        'zk.exception',
        'zk.const',
        'zk.finger',
        'zk.user',
        'zk.transaction',
        'zk.secret',
        'zk.crypto.RSA_lib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'PySide2', 'PySide6', 'PyQt6'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ZKTecoAttendanceDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,        # windowed app: no black cmd window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

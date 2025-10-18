# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main_standalone.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\h0093\\Documents\\MY-Assistant\\.env', '.'), ('C:\\Users\\h0093\\Documents\\MY-Assistant\\venv\\Lib\\site-packages\\openwakeword\\resources', 'openwakeword/resources')],
    hiddenimports=['pyttsx3.drivers', 'pyttsx3.drivers.sapi5', 'win32com.client', 'win32gui', 'win32con', 'win32process', 'psutil', 'spacy', 'whisper', 'torch', 'playwright', 'elevenlabs', 'gtts', 'openwakeword', 'webrtcvad', 'sklearn', 'pandas', 'numpy'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'IPython'],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [('O', None, 'OPTION'), ('O', None, 'OPTION')],
    name='Jarvis',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

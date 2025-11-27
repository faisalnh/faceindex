# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for FaceIndex Local

block_cipher = None

a = Analysis(
    ['main.py', 'database.py', 'workers.py', 'widgets/__init__.py', 'widgets/roi_selector.py', 'widgets/gallery.py', 'widgets/video_player.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('venv/lib/python3.14/site-packages/face_recognition_models/models', 'face_recognition_models/models'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtMultimedia',
        'PyQt6.QtMultimediaWidgets',
        'face_recognition',
        'cv2',
        'numpy',
        'sklearn.cluster',
        'sklearn.neighbors',
        'qdarktheme',
        'database',
        'workers',
        'widgets',
        'widgets.roi_selector',
        'widgets.gallery',
        'widgets.video_player',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter',
        'IPython',
        'pytest',
        'sphinx',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FaceIndex Local',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FaceIndex Local',
)

# macOS App Bundle
app = BUNDLE(
    coll,
    name='FaceIndex Local.app',
    icon=None,  # Add 'app_icon.icns' if you create one
    bundle_identifier='com.faceindex.local',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'CFBundleName': 'FaceIndex Local',
        'CFBundleDisplayName': 'FaceIndex Local',
        'NSHumanReadableCopyright': 'Copyright © 2024',
    },
)

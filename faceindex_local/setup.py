"""
py2app setup file for FaceIndex Local (macOS)
Build with: python setup.py py2app
"""

from setuptools import setup

APP = ["main.py"]
DATA_FILES = []

OPTIONS = {
    "argv_emulation": True,
    "iconfile": None,  # Add 'app_icon.icns' if you create one
    "packages": [
        "PyQt6",
        "cv2",
        "face_recognition",
        "numpy",
        "sklearn",
        "qdarktheme",
    ],
    "includes": [
        "database",
        "workers",
        "widgets.roi_selector",
        "widgets.gallery",
        "widgets.video_player",
    ],
    "excludes": [
        "matplotlib",
        "tkinter",
        "IPython",
        "pytest",
        "sphinx",
    ],
    "plist": {
        "CFBundleName": "FaceIndex Local",
        "CFBundleDisplayName": "FaceIndex Local",
        "CFBundleGetInfoString": "Face detection and video navigation",
        "CFBundleIdentifier": "com.faceindex.local",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "NSHumanReadableCopyright": "Copyright © 2024",
        "NSHighResolutionCapable": True,
    },
}

setup(
    app=APP,
    name="FaceIndex Local",
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)

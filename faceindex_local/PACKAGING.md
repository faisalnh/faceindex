# Packaging FaceIndex Local as a Standalone Application

This guide covers creating standalone, distributable applications for macOS and Linux.

## Option 1: PyInstaller (Recommended)

PyInstaller bundles your Python app with all dependencies into a single executable.

### Installation

```bash
source venv/bin/activate
pip install pyinstaller
```

### Create Spec File

First, let's create a PyInstaller spec file for better control:

```bash
pyi-makespec --name="FaceIndex Local" \
             --windowed \
             --onefile \
             --icon=app_icon.icns \
             main.py
```

### Custom Spec File

Create `FaceIndex_Local.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include any data files if needed
        # ('path/to/resource', 'destination_folder')
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
        'qdarktheme',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='FaceIndex Local',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# macOS App Bundle
app = BUNDLE(
    exe,
    name='FaceIndex Local.app',
    icon='app_icon.icns',
    bundle_identifier='com.faceindex.local',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '1.0.0',
    },
)
```

### Build the Application

**macOS:**
```bash
# Build .app bundle
pyinstaller FaceIndex_Local.spec

# Output will be in dist/FaceIndex Local.app
```

**Linux:**
```bash
# Build single executable
pyinstaller --name="FaceIndex-Local" \
            --onefile \
            --windowed \
            --hidden-import=PyQt6.QtCore \
            --hidden-import=PyQt6.QtGui \
            --hidden-import=PyQt6.QtWidgets \
            --hidden-import=PyQt6.QtMultimedia \
            --hidden-import=PyQt6.QtMultimediaWidgets \
            main.py

# Output will be in dist/FaceIndex-Local
```

### Notes on PyInstaller

**Pros:**
- Single command to create executables
- Works on macOS and Linux
- Includes all dependencies

**Cons:**
- Large file size (200-500 MB due to ML libraries)
- Slower startup time
- May trigger antivirus false positives

## Option 2: py2app (macOS Only)

Better native macOS integration and code signing support.

### Installation

```bash
pip install py2app
```

### Create setup.py

```python
from setuptools import setup

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': [
        'PyQt6',
        'cv2',
        'face_recognition',
        'numpy',
        'sklearn',
        'qdarktheme',
    ],
    'includes': [
        'database',
        'workers',
        'widgets.roi_selector',
        'widgets.gallery',
        'widgets.video_player',
    ],
    'excludes': ['matplotlib', 'tkinter'],
    'iconfile': 'app_icon.icns',
    'plist': {
        'CFBundleName': 'FaceIndex Local',
        'CFBundleDisplayName': 'FaceIndex Local',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'NSHumanReadableCopyright': 'Copyright © 2024',
    }
}

setup(
    app=APP,
    name='FaceIndex Local',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
```

### Build

```bash
# Development build
python setup.py py2app -A

# Production build
python setup.py py2app

# Output: dist/FaceIndex Local.app
```

### Create DMG Installer

```bash
# Install create-dmg
brew install create-dmg

# Create DMG
create-dmg \
  --volname "FaceIndex Local" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "FaceIndex Local.app" 200 190 \
  --hide-extension "FaceIndex Local.app" \
  --app-drop-link 600 185 \
  "FaceIndex-Local-1.0.0.dmg" \
  "dist/FaceIndex Local.app"
```

## Option 3: AppImage (Linux)

Universal Linux package format.

### Using appimage-builder

Create `AppImageBuilder.yml`:

```yaml
version: 1
script:
  - rm -rf AppDir || true
  - mkdir -p AppDir/usr/src
  - cp -r . AppDir/usr/src/faceindex

AppDir:
  path: ./AppDir
  app_info:
    id: com.faceindex.local
    name: FaceIndex Local
    icon: faceindex
    version: 1.0.0
    exec: usr/bin/python3
    exec_args: $APPDIR/usr/src/faceindex/main.py

  apt:
    arch: amd64
    sources:
      - sourceline: 'deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ focal main restricted universe multiverse'
    include:
      - python3
      - python3-pip
      - libgl1

  runtime:
    env:
      PYTHONHOME: '${APPDIR}/usr'
      PYTHONPATH: '${APPDIR}/usr/lib/python3.8/site-packages'

  test:
    fedora:
      image: appimagecrafters/tests-env:fedora-30
      command: ./AppRun
    debian:
      image: appimagecrafters/tests-env:debian-stable
      command: ./AppRun

AppImage:
  update-information: None
  sign-key: None
  arch: x86_64
```

## Option 4: Docker Container (Cross-Platform)

Package as a container with X11 forwarding.

### Dockerfile

```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create data directory
RUN mkdir -p /data

# Set environment
ENV DISPLAY=:0

# Run application
CMD ["python", "main.py"]
```

### Build and Run

```bash
# Build
docker build -t faceindex-local .

# Run (macOS with XQuartz)
xhost +localhost
docker run -it --rm \
  -e DISPLAY=host.docker.internal:0 \
  -v ~/Videos:/videos \
  -v ~/faceindex-data:/data \
  faceindex-local

# Run (Linux)
docker run -it --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v ~/Videos:/videos \
  -v ~/faceindex-data:/data \
  faceindex-local
```

## Recommended Approach by Platform

### macOS
**Best: py2app + DMG**
```bash
pip install py2app
python setup.py py2app
create-dmg ...
```

**Alternative: PyInstaller**
```bash
pip install pyinstaller
pyinstaller FaceIndex_Local.spec
```

### Linux
**Best: PyInstaller + AppImage**
```bash
pip install pyinstaller
pyinstaller --onefile main.py
# Then wrap in AppImage
```

**Alternative: Flatpak or Snap**
- Better system integration
- Sandboxed environment
- Access to app stores

## Code Signing & Notarization (macOS)

For distribution outside the Mac App Store:

```bash
# Sign the app
codesign --force --deep --sign "Developer ID Application: Your Name" \
  "dist/FaceIndex Local.app"

# Create signed DMG
codesign --force --sign "Developer ID Application: Your Name" \
  "FaceIndex-Local-1.0.0.dmg"

# Notarize with Apple
xcrun notarytool submit FaceIndex-Local-1.0.0.dmg \
  --apple-id your@email.com \
  --team-id TEAMID \
  --password app-specific-password

# Staple notarization
xcrun stapler staple FaceIndex-Local-1.0.0.dmg
```

## Reducing File Size

The app will be large (200-500 MB) due to:
- face_recognition/dlib (100+ MB)
- OpenCV (50+ MB)
- PyQt6 (50+ MB)
- NumPy/scikit-learn (50+ MB)

### Tips to Reduce Size:

1. **Use UPX compression** (PyInstaller):
   ```bash
   pyinstaller --onefile --upx-dir=/usr/local/bin main.py
   ```

2. **Exclude unused modules**:
   ```python
   excludes=['matplotlib', 'tkinter', 'IPython']
   ```

3. **Strip debug symbols**:
   ```bash
   strip dist/FaceIndex-Local
   ```

4. **Use lightweight alternatives**:
   - Consider `opencv-python-headless` (smaller)
   - Use `face_recognition` without GPU support

## Distribution Checklist

- [ ] Create app icon (.icns for macOS, .png for Linux)
- [ ] Test on fresh system without Python
- [ ] Verify all video codecs work
- [ ] Check file permissions for database/thumbnails
- [ ] Include README and license
- [ ] Sign and notarize (macOS)
- [ ] Create installer (DMG/AppImage)
- [ ] Test on multiple OS versions
- [ ] Upload to GitHub Releases or website

## Quick Build Script

Save as `build.sh`:

```bash
#!/bin/bash

# FaceIndex Local Build Script

echo "Building FaceIndex Local..."

# Clean previous builds
rm -rf build dist

# Activate virtual environment
source venv/bin/activate

# Install PyInstaller
pip install pyinstaller

# Build
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Building for macOS..."
    pyinstaller FaceIndex_Local.spec
    echo "Done! App bundle: dist/FaceIndex Local.app"
else
    # Linux
    echo "Building for Linux..."
    pyinstaller --onefile --windowed \
                --name="FaceIndex-Local" \
                main.py
    echo "Done! Executable: dist/FaceIndex-Local"
fi
```

Make executable:
```bash
chmod +x build.sh
./build.sh
```

## Next Steps

After building:
1. Test the standalone app thoroughly
2. Create an installer/DMG
3. Write installation instructions for end users
4. Consider hosting on GitHub Releases
5. Add auto-update functionality (future)

Choose the method that best fits your distribution needs!

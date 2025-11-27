# Building Standalone Application

This guide shows how to build FaceIndex Local as a standalone application that users can run without installing Python.

## Quick Build (Recommended)

### Prerequisites

**macOS:**
```bash
brew install cmake
```

**Linux:**
```bash
sudo apt-get install cmake python3-dev build-essential
```

### Build Steps

```bash
# 1. Set up environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
pip install -r requirements-build.txt

# 3. Build
./build.sh
```

**Output:**
- **macOS:** `dist/FaceIndex Local.app`
- **Linux:** `dist/FaceIndex-Local`

That's it! The standalone app is ready to distribute.

## Detailed Instructions

### macOS - Creating .app Bundle

#### Method 1: Using the build script (easiest)

```bash
./build.sh
```

The script will automatically:
- Detect your OS
- Clean previous builds
- Choose the best packaging method (py2app or PyInstaller)
- Create the .app bundle

#### Method 2: Using py2app directly

```bash
source venv/bin/activate
pip install py2app
python setup.py py2app

# Output: dist/FaceIndex Local.app
```

#### Method 3: Using PyInstaller

```bash
source venv/bin/activate
pip install pyinstaller
pyinstaller FaceIndex_Local.spec

# Output: dist/FaceIndex Local.app
```

### Linux - Creating Executable

#### Using the build script

```bash
./build.sh
```

#### Using PyInstaller directly

```bash
source venv/bin/activate
pip install pyinstaller

pyinstaller --onefile \
            --windowed \
            --name="FaceIndex-Local" \
            main.py

# Output: dist/FaceIndex-Local
```

## Testing the Build

### macOS

```bash
# Run the app
open "dist/FaceIndex Local.app"

# Or from command line
./dist/FaceIndex\ Local.app/Contents/MacOS/FaceIndex\ Local
```

### Linux

```bash
# Make executable
chmod +x dist/FaceIndex-Local

# Run
./dist/FaceIndex-Local
```

## Creating Installers

### macOS - DMG Installer

```bash
# Install create-dmg
brew install create-dmg

# Create DMG
create-dmg \
  --volname "FaceIndex Local" \
  --volicon "app_icon.icns" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "FaceIndex Local.app" 150 185 \
  --hide-extension "FaceIndex Local.app" \
  --app-drop-link 450 185 \
  "FaceIndex-Local-1.0.0.dmg" \
  "dist/FaceIndex Local.app"
```

### Linux - AppImage

```bash
# Install appimagetool
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage

# Create AppDir structure
mkdir -p FaceIndex.AppDir/usr/bin
cp dist/FaceIndex-Local FaceIndex.AppDir/usr/bin/

# Create AppRun
cat > FaceIndex.AppDir/AppRun << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin/:${PATH}"
exec "${HERE}/usr/bin/FaceIndex-Local" "$@"
EOF
chmod +x FaceIndex.AppDir/AppRun

# Create .desktop file
cat > FaceIndex.AppDir/faceindex-local.desktop << 'EOF'
[Desktop Entry]
Name=FaceIndex Local
Exec=FaceIndex-Local
Icon=faceindex-local
Type=Application
Categories=AudioVideo;Video;
EOF

# Create icon (placeholder - replace with actual icon)
touch FaceIndex.AppDir/faceindex-local.png

# Build AppImage
./appimagetool-x86_64.AppImage FaceIndex.AppDir FaceIndex-Local-1.0.0-x86_64.AppImage
```

## Expected File Sizes

The standalone application will be large due to included dependencies:

- **macOS .app:** ~300-500 MB
- **Linux executable:** ~250-400 MB
- **DMG installer:** ~200-350 MB (compressed)
- **AppImage:** ~250-400 MB

This is normal for Python applications with ML libraries (face_recognition, OpenCV, scikit-learn).

## Reducing File Size

### 1. Use UPX Compression

**Install UPX:**
```bash
# macOS
brew install upx

# Linux
sudo apt-get install upx-ucl
```

**Build with compression:**
```bash
pyinstaller --onefile --upx-dir=/usr/local/bin FaceIndex_Local.spec
```

Can reduce size by 30-40%.

### 2. Exclude Unused Packages

Edit `FaceIndex_Local.spec` and add to `excludes`:
```python
excludes=[
    'matplotlib',
    'tkinter',
    'IPython',
    'pytest',
    'sphinx',
    'jupyter',
],
```

### 3. Strip Debug Symbols (Linux)

```bash
strip dist/FaceIndex-Local
```

Can reduce size by 10-20%.

## Troubleshooting Build Issues

### "No module named 'PyQt6'"

```bash
# Make sure PyQt6 is installed in venv
pip install PyQt6 PyQt6-Multimedia
```

### "face_recognition not found"

```bash
# Install cmake first
brew install cmake  # macOS
sudo apt-get install cmake  # Linux

# Then reinstall
pip install face_recognition
```

### "ImportError: dlopen() failed"

The app is trying to load a library that wasn't bundled.

**Fix:** Add to `hiddenimports` in `.spec` file:
```python
hiddenimports=[
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    # ... add the missing module here
],
```

### "App crashes on startup"

**Debug mode:** Set `console=True` in `.spec` file to see error messages:
```python
exe = EXE(
    ...
    console=True,  # Changed from False
    ...
)
```

Then rebuild and check the console output.

### Large file size

This is expected due to ML libraries. See "Reducing File Size" section above.

## Distribution Checklist

Before distributing your app:

- [ ] Test on a clean machine without Python installed
- [ ] Verify video playback with different formats (MP4, AVI, MOV)
- [ ] Check that database creation works
- [ ] Test face detection with sample video
- [ ] Verify thumbnails are created and displayed
- [ ] Test on both Intel and Apple Silicon Macs (if macOS)
- [ ] Include README.txt with usage instructions
- [ ] Add LICENSE file
- [ ] Sign the application (macOS) - optional but recommended
- [ ] Create installer (DMG/AppImage)

## Code Signing (macOS)

For distribution outside personal use:

```bash
# Get your Developer ID
security find-identity -v -p codesigning

# Sign the app
codesign --force --deep --sign "Developer ID Application: Your Name (TEAM_ID)" \
  "dist/FaceIndex Local.app"

# Verify
codesign --verify --deep --strict --verbose=2 "dist/FaceIndex Local.app"

# Notarize (requires paid Apple Developer account)
xcrun notarytool submit "FaceIndex-Local-1.0.0.dmg" \
  --apple-id your@email.com \
  --team-id TEAM_ID \
  --password app-specific-password \
  --wait

# Staple
xcrun stapler staple "FaceIndex-Local-1.0.0.dmg"
```

## Automated Build Scripts

### Complete Build + DMG (macOS)

Save as `build-release-mac.sh`:

```bash
#!/bin/bash
set -e

VERSION="1.0.0"

echo "Building FaceIndex Local v${VERSION} for macOS..."

# Build
./build.sh

# Create DMG
if command -v create-dmg &> /dev/null; then
    echo "Creating DMG installer..."
    create-dmg \
      --volname "FaceIndex Local ${VERSION}" \
      --window-size 600 400 \
      --icon-size 100 \
      --app-drop-link 450 150 \
      "FaceIndex-Local-${VERSION}.dmg" \
      "dist/FaceIndex Local.app"
    
    echo "✅ DMG created: FaceIndex-Local-${VERSION}.dmg"
else
    echo "⚠️  create-dmg not found. Install with: brew install create-dmg"
fi
```

### Complete Build + AppImage (Linux)

Save as `build-release-linux.sh`:

```bash
#!/bin/bash
set -e

VERSION="1.0.0"

echo "Building FaceIndex Local v${VERSION} for Linux..."

# Build
./build.sh

echo "✅ Build complete: dist/FaceIndex-Local"
echo ""
echo "To create AppImage, see PACKAGING.md"
```

## Next Steps

After building successfully:

1. **Test thoroughly** on different machines
2. **Create user documentation** (installation guide)
3. **Upload to GitHub Releases** or your website
4. **Consider auto-updates** for future versions
5. **Gather user feedback** and iterate

## Support

If you encounter build issues:

1. Check the error message carefully
2. Verify all dependencies are installed
3. Try building with `console=True` for debugging
4. Check PyInstaller/py2app documentation
5. Search for the specific error online

Common resources:
- PyInstaller docs: https://pyinstaller.org/
- py2app docs: https://py2app.readthedocs.io/
- Face recognition issues: https://github.com/ageitgey/face_recognition/issues

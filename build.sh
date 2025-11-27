#!/bin/bash

# FaceIndex Local Build Script
# Builds standalone application for macOS or Linux

set -e  # Exit on error

echo "======================================"
echo "FaceIndex Local - Build Script"
echo "======================================"
echo ""

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

echo "Detected OS: $OS"
echo ""

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist
echo "Done."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found!"
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install PyInstaller
echo "Installing PyInstaller..."
pip install pyinstaller --quiet

# Build based on OS
if [ "$OS" == "macos" ]; then
    echo ""
    echo "Building macOS application..."
    echo "This may take several minutes..."
    echo ""

    # Option 1: Try py2app first (better for macOS)
    if pip list | grep -q py2app; then
        echo "Using py2app..."
        python setup.py py2app

        echo ""
        echo "======================================"
        echo "Build Complete!"
        echo "======================================"
        echo ""
        echo "Application: dist/FaceIndex Local.app"
        echo ""
        echo "To run:"
        echo "  open 'dist/FaceIndex Local.app'"
        echo ""
        echo "To create DMG (requires create-dmg):"
        echo "  brew install create-dmg"
        echo "  create-dmg --volname 'FaceIndex Local' \\"
        echo "    --window-size 600 400 \\"
        echo "    --icon-size 100 \\"
        echo "    --app-drop-link 450 150 \\"
        echo "    'FaceIndex-Local-1.0.0.dmg' \\"
        echo "    'dist/FaceIndex Local.app'"
    else
        # Fallback to PyInstaller
        echo "Using PyInstaller..."
        pyinstaller FaceIndex_Local.spec

        echo ""
        echo "======================================"
        echo "Build Complete!"
        echo "======================================"
        echo ""
        echo "Application: dist/FaceIndex Local.app"
        echo ""
        echo "To run:"
        echo "  open 'dist/FaceIndex Local.app'"
        echo ""
        echo "Note: For better macOS integration, install py2app:"
        echo "  pip install py2app"
        echo "  Then run this script again"
    fi

elif [ "$OS" == "linux" ]; then
    echo ""
    echo "Building Linux application..."
    echo "This may take several minutes..."
    echo ""

    pyinstaller --onefile \
                --windowed \
                --name="FaceIndex-Local" \
                --hidden-import=PyQt6.QtCore \
                --hidden-import=PyQt6.QtGui \
                --hidden-import=PyQt6.QtWidgets \
                --hidden-import=PyQt6.QtMultimedia \
                --hidden-import=PyQt6.QtMultimediaWidgets \
                --hidden-import=face_recognition \
                --hidden-import=cv2 \
                --hidden-import=sklearn.cluster \
                --hidden-import=qdarktheme \
                main.py

    echo ""
    echo "======================================"
    echo "Build Complete!"
    echo "======================================"
    echo ""
    echo "Executable: dist/FaceIndex-Local"
    echo ""
    echo "To run:"
    echo "  ./dist/FaceIndex-Local"
    echo ""
    echo "To make it double-clickable:"
    echo "  chmod +x dist/FaceIndex-Local"
    echo ""
    echo "To create AppImage (recommended for distribution):"
    echo "  See PACKAGING.md for instructions"
fi

echo ""
echo "Build process finished successfully!"

# Quick Start Guide

## Installation (5 minutes)

### macOS/Linux

**Step 1: Install System Dependencies**

**macOS:**
```bash
brew install cmake
```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install cmake python3-dev python3-pip build-essential
```

**Step 2: Set Up Python Environment**

```bash
cd faceindex_local

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

This will install:
- PyQt6 (GUI framework)
- OpenCV (video processing)
- face_recognition (face detection)
- scikit-learn (clustering)
- qdarktheme (dark UI theme)

**Step 3: Run the Application**

```bash
python main.py
```

Or use the run script:
```bash
./run.sh
```

### Windows Quick Start

1. **Download/Clone** the repository
2. **Open PowerShell** in the project folder
3. **Run**: `.\run.ps1`
4. **Wait** for dependencies to install (first run only)
5. **Use** the application!

**First time?** You may need to allow PowerShell scripts:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Note:** The PowerShell script automatically handles virtual environment creation, dependency installation, and launching the application.

## First Use (2 minutes)

1. **Launch**: The app opens with a dark, modern interface
2. **Add Video**: Click the blue "+ Add Video" button
3. **Select File**: Choose any video file (MP4, AVI, MOV, MKV)
4. **Draw ROI**: 
   - A preview of the first frame appears
   - Click and drag to draw a rectangle around faces
   - OR click "Use Full Frame" to process the entire video
5. **Start Processing**: Click "Start Processing"
6. **Wait**: Progress bar shows detection and clustering progress
7. **Browse**: Circular face thumbnails appear in the gallery
8. **Navigate**: Click any person to see their timeline in the video

## Tips

### Performance
- **ROI Selection**: Draw tight rectangles around face areas for faster processing
- **Large Videos**: First test with a short clip (30-60 seconds)
- **Processing Time**: ~1 minute per minute of video (depends on resolution and CPU)

### Best Results
- **Good Lighting**: Videos with clear, well-lit faces work best
- **Front-Facing**: Works best with frontal or near-frontal faces
- **Resolution**: 720p or higher recommended
- **Stable Video**: Shaky footage may miss some faces

### Navigation
- **Click Person**: Loads their timeline in the video player
- **Blue Markers**: Show where the person appears
- **Previous/Next**: Jump between appearances
- **Right-Click**: Rename or merge people

## Keyboard Shortcuts

- `Ctrl+O` - Add Video
- `Ctrl+Q` - Quit
- `Space` - Play/Pause (when video is loaded)

## File Locations

- **Database**: `faceindex.db` (created automatically)
- **Thumbnails**: `thumbnails/{video_id}/` (created automatically)

## Troubleshooting

### "No faces detected"
- Try using "Full Frame" instead of ROI
- Ensure faces are visible and clear in the video
- Check that faces are at least 40x40 pixels

### Application won't start
```bash
# Check Python version (needs 3.8+)
python3 --version

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Video won't play
```bash
# Install ffmpeg
brew install ffmpeg  # macOS
sudo apt-get install ffmpeg  # Linux
```

## Next Steps

Once you're comfortable:
- Process multiple videos
- Rename detected people
- Merge duplicate faces
- Export clips (feature coming soon)

Enjoy using FaceIndex Local!

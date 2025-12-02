# FaceIndex Local

A professional desktop application for automatic face detection, clustering, and video navigation. Built with PyQt6 and modern computer vision libraries.

## Features

- **Automatic Face Detection**: Detect faces in videos using state-of-the-art face recognition
- **Smart Clustering**: Automatically group similar faces using DBSCAN clustering
- **ROI Selection**: Define specific regions of interest to improve accuracy and performance
- **Video Navigation**: Jump to any appearance of a specific person with one click
- **Modern Dark UI**: Professional, minimalist interface inspired by DaVinci Resolve
- **Non-Blocking Processing**: All heavy processing happens in background threads
- **Local & Private**: Everything runs locally on your machine

## Screenshots

The application features:
- **Gallery View**: Circular face thumbnails showing all detected people
- **Video Player**: Built-in player with timeline visualization showing person appearances
- **ROI Selector**: Interactive tool to define detection regions on video frames

## Installation

### Prerequisites

- Python 3.8 or higher
- macOS, Windows, or Linux
- CMake (required for dlib)

### macOS

```bash
# Install CMake (required for dlib)
brew install cmake

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Linux (Ubuntu/Debian)

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install cmake python3-dev python3-pip

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Windows

**Prerequisites:**
- Python 3.8 or higher
- Git (optional, for cloning)

**Setup and Run:**

1. Clone or download this repository

2. Open PowerShell in the project directory

3. If this is your first time running PowerShell scripts, you may need to allow script execution:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

4. Run the application:
   ```powershell
   .\run.ps1
   ```

The script will automatically:
- Create a virtual environment (if needed)
- Install dependencies
- Launch the application

**Troubleshooting:**
- If you get "Python not found", ensure Python is installed and added to PATH
- If you get execution policy errors, run the Set-ExecutionPolicy command above
- Antivirus may briefly scan the application on first run - this is normal

## Usage

### Running the Application

```bash
cd faceindex_local
python main.py
```

### Basic Workflow

1. **Add Video**: Click "Add Video" button or use Ctrl+O
2. **Select ROI**: Draw a rectangle around the area where faces should be detected (or use "Full Frame")
3. **Processing**: Wait for automatic face detection and clustering to complete
4. **Browse**: View all detected people in the gallery
5. **Navigate**: Click on any person to load their appearances in the video player
6. **Jump**: Use Previous/Next buttons or click the timeline to navigate between appearances

### Advanced Features

#### Rename People

- Right-click on any person card
- Select "Rename"
- Enter a custom name

#### Merge Duplicates

- Right-click on a person
- Select "Merge with..."
- Choose another person to merge with

#### Timeline Visualization

The blue vertical lines in the timeline show exactly where the selected person appears in the video.

## Project Structure

```
faceindex_local/
├── main.py                 # Application entry point
├── database.py             # SQLite database management
├── workers.py              # Background processing threads
├── widgets/
│   ├── roi_selector.py     # ROI selection dialog
│   ├── gallery.py          # Face gallery grid
│   └── video_player.py     # Video player with timeline
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Technical Details

### Architecture

- **GUI Framework**: PyQt6 (pure Qt Widgets, no web technologies)
- **Face Detection**: face_recognition library (using dlib's HOG detector)
- **Face Clustering**: DBSCAN algorithm from scikit-learn
- **Video Processing**: OpenCV (cv2)
- **Database**: SQLite3 (built-in Python)
- **Theme**: qdarktheme for modern dark UI

### Performance Optimizations

- **Frame Skipping**: Processes every 15th frame by default (configurable)
- **ROI Cropping**: Only analyzes specified regions
- **Background Threading**: All processing on QThread to keep UI responsive
- **Incremental Updates**: Progress updates during processing

### Database Schema

Three main tables:
- **videos**: Video metadata and ROI coordinates
- **persons**: Detected people (clusters) with thumbnails
- **face_instances**: Individual face detections with timestamps and encodings

## Configuration

Edit these constants in `workers.py` to tune performance:

```python
self.frame_skip = 15           # Process every Nth frame (higher = faster, less accurate)
self.min_face_size = 40        # Minimum face size in pixels
self.clustering_eps = 0.5      # DBSCAN epsilon (lower = stricter clustering)
self.min_samples = 2           # Minimum faces to form a cluster
```

## Troubleshooting

### dlib Installation Issues

If dlib fails to install:

```bash
# macOS
brew install cmake
pip install dlib

# Linux
sudo apt-get install build-essential cmake
pip install dlib
```

### Video Codec Issues

If videos won't play, install additional codecs:

```bash
# macOS
brew install ffmpeg

# Linux
sudo apt-get install ubuntu-restricted-extras ffmpeg
```

### No Faces Detected

- Ensure ROI includes faces
- Try using "Full Frame" instead of custom ROI
- Increase frame skip interval for longer videos
- Check video quality and face visibility

## License

MIT License - See LICENSE file for details

## Credits

Built with:
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- [face_recognition](https://github.com/ageitgey/face_recognition)
- [OpenCV](https://opencv.org/)
- [qdarktheme](https://github.com/5yutan5/PyQtDarkTheme)

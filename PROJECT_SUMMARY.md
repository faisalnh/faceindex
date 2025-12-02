# FaceIndex Local - Project Summary

## Overview

**FaceIndex Local** is a professional desktop application for automatic face detection, clustering, and video navigation. Built entirely with Python and PyQt6 - no web technologies.

## ✨ Key Features

- **Automatic Face Detection**: Uses face_recognition library with dlib's HOG detector
- **Smart Clustering**: Groups similar faces using DBSCAN algorithm
- **ROI Selection**: Interactive region-of-interest selection for improved accuracy
- **Video Navigation**: Click any person to jump to their appearances in the video
- **Timeline Visualization**: Visual markers showing exactly where people appear
- **Modern Dark UI**: Professional interface using qdarktheme
- **Non-Blocking Processing**: All heavy work runs in background QThreads
- **100% Local & Private**: No cloud, no internet required

## 📁 Project Structure

```
faceindex_local/
├── main.py                     # Application entry point & main window
├── database.py                 # SQLite database management
├── workers.py                  # Background processing threads (QThread)
├── widgets/
│   ├── roi_selector.py         # ROI selection dialog with drawing
│   ├── gallery.py              # Face gallery grid with circular thumbnails
│   └── video_player.py         # Video player with timeline visualization
├── requirements.txt            # Python dependencies
├── requirements-build.txt      # Build tool dependencies
├── FaceIndex_Local.spec        # PyInstaller configuration
├── setup.py                    # py2app configuration (macOS)
├── build.sh                    # Automated build script (macOS/Linux)
├── build.ps1                   # Build script for Windows (PowerShell)
├── run.sh                      # Development run script (macOS/Linux)
├── run.ps1                     # Run script for Windows (PowerShell)
├── .gitattributes              # Git line ending configuration
├── README.md                   # User documentation
├── QUICKSTART.md               # Quick start guide
├── BUILD.md                    # Build instructions
├── PACKAGING.md                # Packaging as standalone app
└── .gitignore                  # Git ignore patterns
```

## 🛠️ Technology Stack

### Core Technologies
- **GUI**: PyQt6 (Widgets, Multimedia, Core)
- **Computer Vision**: face_recognition, OpenCV (cv2)
- **Machine Learning**: scikit-learn (DBSCAN clustering)
- **Database**: SQLite3 (built-in Python)
- **UI Theme**: qdarktheme

### Key Libraries
- `PyQt6` - Modern Qt6 bindings for Python
- `face_recognition` - Face detection and recognition
- `opencv-python` - Video processing and image manipulation
- `scikit-learn` - Machine learning algorithms
- `numpy` - Numerical computations
- `dlib` - Face detection backend

## 🎨 UI Components

### Main Window
- **Left Panel**: Gallery grid of detected people
- **Right Panel**: Video player with timeline
- **Toolbar**: "Add Video" button and controls
- **Menu Bar**: File operations and help

### Custom Widgets

#### ROISelectorLabel (roi_selector.py)
- Interactive canvas for drawing rectangles
- Mouse tracking for ROI selection
- Real-time preview with overlay
- Coordinate conversion to original image space

#### PersonCard (gallery.py)
- Circular face thumbnail
- Person name (editable)
- Appearance count
- Context menu (rename, merge)
- Hover effects

#### VideoPlayerWidget (video_player.py)
- QMediaPlayer integration
- Custom timeline visualization
- Previous/Next navigation
- Timestamp seeking
- Volume control

#### TimelineWidget (video_player.py)
- Custom painted timeline
- Blue markers for person appearances
- Green indicator for current position
- Click-to-seek functionality

## 🔧 Architecture

### MVC-Like Pattern

**Models (Data Layer)**:
- `Database` class: SQLite operations
- Tables: videos, persons, face_instances

**Views (UI Layer)**:
- `MainWindow`: Main application window
- Custom widgets in `widgets/` directory
- Dark theme styling with qdarktheme

**Controllers (Logic Layer)**:
- `FaceProcessingWorker`: Background face detection
- Signal/slot connections for UI updates
- Database operations triggered by user actions

### Threading Model

- **Main Thread**: UI rendering and user interactions
- **QThread Workers**: Heavy processing (video analysis, face detection)
- **Signals**: Cross-thread communication
  - `progress_update(int, str)` - Progress updates
  - `processing_finished(bool, str)` - Completion status
  - `face_found(...)` - Individual face detections

### Data Flow

1. **Video Import**:
   - User selects video → ROI dialog → Database entry → Worker thread

2. **Face Processing**:
   - Read frames → Crop to ROI → Detect faces → Encode → Cluster → Database

3. **Person Selection**:
   - Click person → Query timestamps → Load video → Highlight timeline

4. **Video Navigation**:
   - Click timeline/buttons → Seek to timestamp → Update player

## 💾 Database Schema

### videos table
- Stores video metadata (path, duration, fps, dimensions)
- ROI coordinates (x, y, w, h)
- Processing status

### persons table
- Cluster ID and person info
- Thumbnail path
- Face count
- Custom name

### face_instances table
- Individual face detections
- Timestamp and frame number
- Bounding box coordinates
- Face encoding (128D vector as BLOB)
- Thumbnail path

## 🚀 Building Standalone Apps

### Quick Build
```bash
./build.sh
```

### Output
- **macOS**: `FaceIndex Local.app` (300-500 MB)
- **Linux**: `FaceIndex-Local` executable (250-400 MB)

### Packaging Options
- **PyInstaller**: Cross-platform, single command
- **py2app**: Better macOS integration
- **AppImage**: Universal Linux package
- **DMG**: macOS installer

See `BUILD.md` and `PACKAGING.md` for details.

## 🎯 Performance Optimizations

1. **Frame Skipping**: Process every 15th frame (configurable)
2. **ROI Cropping**: Only analyze specified regions
3. **Background Threading**: UI stays responsive
4. **Efficient Encoding**: 128D face vectors
5. **Database Indexing**: Fast timestamp queries
6. **Thumbnail Caching**: Avoid re-reading images

## 🔐 Privacy & Security

- **100% Local**: No network connections
- **No Telemetry**: No data collection
- **Offline**: Works without internet
- **User Data**: Stays on user's machine
- **SQLite**: Standard, inspectable database format

## 📝 Development Workflow

### Running in Development
```bash
source venv/bin/activate
python main.py
```

### Adding Features
1. Create new widget in `widgets/` if needed
2. Add database schema changes in `database.py`
3. Implement logic in appropriate module
4. Connect signals/slots in `main.py`
5. Test thoroughly

### Debugging
- Set `console=True` in PyInstaller spec for console output
- Use `print()` or Python logging
- Qt Designer can be used for UI prototyping

## 🧪 Testing Recommendations

### Manual Testing
- [ ] Test with various video formats (MP4, AVI, MOV, MKV)
- [ ] Test ROI selection edge cases (full frame, small regions)
- [ ] Verify face detection with different lighting
- [ ] Check timeline navigation accuracy
- [ ] Test rename and merge operations
- [ ] Verify database persistence across sessions

### Performance Testing
- [ ] Short video (30 seconds)
- [ ] Medium video (5 minutes)
- [ ] Long video (30+ minutes)
- [ ] High resolution (4K)
- [ ] Multiple faces in frame

## 📦 Distribution

### For End Users
1. Build standalone app with `./build.sh`
2. Create DMG (macOS) or AppImage (Linux)
3. Sign and notarize (macOS, optional)
4. Upload to GitHub Releases or website
5. Provide installation instructions

### System Requirements
- **OS**: macOS 10.14+, Linux (Ubuntu 20.04+), or Windows 10/11
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB for app + space for videos
- **CPU**: Intel Core i5 or equivalent (faster = better)

### Platform Support
- **macOS**: Full support with .app builds ✅
- **Linux**: Script-based execution and executable builds ✅
- **Windows**: Source code execution via PowerShell ✅
  - Note: Standalone .exe builds not yet available

## 🔮 Future Enhancements

Potential features to add:
- Export video clips of specific people
- Face recognition (train on known faces)
- Multiple video library management
- Search by person across videos
- Batch processing
- GPU acceleration
- Real-time webcam detection
- Export/import person database
- Statistics dashboard

## 📚 Documentation Files

- `README.md` - User-facing documentation
- `QUICKSTART.md` - 5-minute getting started guide
- `BUILD.md` - Building standalone applications
- `PACKAGING.md` - Advanced packaging options
- `PROJECT_SUMMARY.md` - This file (technical overview)

## 🤝 Contributing

To contribute:
1. Fork the repository
2. Create a feature branch
3. Make changes following the existing code style
4. Test thoroughly
5. Submit pull request

## 📄 License

MIT License - See LICENSE file

## 🙏 Credits

Built with amazing open-source libraries:
- [PyQt6](https://riverbankcomputing.com/software/pyqt/) - GUI framework
- [face_recognition](https://github.com/ageitgey/face_recognition) - Face detection
- [OpenCV](https://opencv.org/) - Video processing
- [scikit-learn](https://scikit-learn.org/) - Machine learning
- [qdarktheme](https://github.com/5yutan5/PyQtDarkTheme) - Dark UI theme
- [dlib](http://dlib.net/) - Face detection backend

## 📧 Support

For issues or questions:
- Check existing documentation
- Search GitHub issues
- Create new issue with details

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Status**: Production Ready

# FaceIndex Local - Complete Documentation Index

Welcome to FaceIndex Local! This index helps you find the right documentation for your needs.

## 🚀 Getting Started

### I want to USE the application

1. **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup and first use
   - Installation steps
   - Running the app
   - Processing your first video
   - Basic navigation

2. **[README.md](README.md)** - Complete user guide
   - Features overview
   - Installation instructions
   - Usage workflow
   - Troubleshooting
   - Configuration options

### I want to BUILD a standalone app

3. **[BUILD.md](BUILD.md)** - Building executable applications
   - Quick build with `./build.sh`
   - macOS .app bundle creation
   - Linux executable creation
   - Creating installers (DMG, AppImage)
   - Troubleshooting build issues

4. **[PACKAGING.md](PACKAGING.md)** - Advanced packaging options
   - PyInstaller vs py2app vs Docker
   - Code signing (macOS)
   - Reducing file size
   - Distribution checklist
   - Platform-specific packaging

### I want to DEVELOP or EXTEND the app

5. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Technical overview
   - Architecture and design patterns
   - Technology stack
   - Component breakdown
   - Database schema
   - Performance optimizations

6. **[EXAMPLE_USAGE.md](EXAMPLE_USAGE.md)** - Code examples
   - GUI usage examples
   - Programmatic database access
   - Custom worker usage
   - Integration examples
   - Common workflows

## 📁 Key Files

### Application Code

| File | Size | Description |
|------|------|-------------|
| `main.py` | 14K | Application entry point and main window |
| `database.py` | 9.2K | SQLite database management |
| `workers.py` | 10K | Background processing threads |
| `widgets/roi_selector.py` | 9.2K | ROI selection dialog |
| `widgets/gallery.py` | 10K | Face gallery grid |
| `widgets/video_player.py` | 10K | Video player with timeline |

### Configuration Files

| File | Description |
|------|-------------|
| `requirements.txt` | Python dependencies for running |
| `requirements-build.txt` | Additional build tool dependencies |
| `FaceIndex_Local.spec` | PyInstaller configuration |
| `setup.py` | py2app configuration (macOS) |
| `.gitignore` | Git ignore patterns |

### Scripts

| Script | Purpose |
|--------|---------|
| `run.sh` | Run in development mode |
| `build.sh` | Build standalone application |

### Documentation

| Document | Purpose | Size |
|----------|---------|------|
| README.md | User guide | 5.1K |
| QUICKSTART.md | Quick start | 2.9K |
| BUILD.md | Build guide | 7.8K |
| PACKAGING.md | Packaging guide | 9.6K |
| PROJECT_SUMMARY.md | Technical overview | 9.0K |
| EXAMPLE_USAGE.md | Code examples | 10K |
| INDEX.md | This file | - |

## 🎯 Common Tasks Quick Reference

### Running the Application

```bash
# Development mode
./run.sh

# Or manually
python main.py
```

### Building Standalone App

```bash
# Automated build
./build.sh

# Manual PyInstaller
pyinstaller FaceIndex_Local.spec

# Manual py2app (macOS)
python setup.py py2app
```

### Processing a Video

1. Click "Add Video"
2. Select video file
3. Draw ROI or use full frame
4. Click "Start Processing"
5. Wait for completion
6. Browse detected people

### Database Access

```python
from database import Database

db = Database()
videos = db.get_all_videos()
persons = db.get_persons_by_video(video_id)
instances = db.get_face_instances_by_person(person_id)
db.close()
```

## 📊 Project Statistics

- **Total Python Code**: ~50K+ lines (including comments)
- **Main Modules**: 4 (main, database, workers, widgets)
- **Custom Widgets**: 3 (ROI selector, gallery, video player)
- **Database Tables**: 3 (videos, persons, face_instances)
- **Dependencies**: 10 core packages
- **Supported Platforms**: macOS, Linux
- **UI Framework**: PyQt6 (pure Qt Widgets, no web)

## 🔍 Quick Lookup

### By Task

- **Install dependencies** → QUICKSTART.md → Step 1
- **First run** → QUICKSTART.md → Step 3
- **Add video** → README.md → Basic Workflow
- **Build .app** → BUILD.md → macOS section
- **Create DMG** → BUILD.md → Creating Installers
- **Reduce size** → PACKAGING.md → Reducing File Size
- **Code signing** → PACKAGING.md → Code Signing
- **Database schema** → PROJECT_SUMMARY.md → Database Schema
- **Custom processing** → EXAMPLE_USAGE.md → Programmatic Usage

### By Role

**End User:**
- README.md
- QUICKSTART.md

**Developer:**
- PROJECT_SUMMARY.md
- EXAMPLE_USAGE.md
- Source code files

**Packager/Distributor:**
- BUILD.md
- PACKAGING.md

## 🛠️ Technology Stack Reference

### GUI & Multimedia
- PyQt6 6.7.0
- PyQt6-Multimedia 6.7.0
- qdarktheme 2.1.0

### Computer Vision
- opencv-python 4.10.0
- face-recognition 1.3.0
- dlib 19.24.2

### Machine Learning
- scikit-learn 1.5.0
- numpy 1.26.4

### Build Tools
- pyinstaller 6.3.0
- py2app 0.28.6 (macOS)

## 📞 Support & Resources

### Documentation
- Check INDEX.md (this file) for navigation
- Read appropriate .md file for your task
- Review EXAMPLE_USAGE.md for code samples

### Troubleshooting
- README.md → Troubleshooting section
- BUILD.md → Troubleshooting Build Issues
- EXAMPLE_USAGE.md → Tips & Tricks

### Development
- PROJECT_SUMMARY.md → Architecture
- Source code comments
- PyQt6 documentation: https://www.riverbankcomputing.com/
- face_recognition: https://github.com/ageitgey/face_recognition

## 🗺️ Navigation Guide

```
Start Here
    ↓
Are you a USER or DEVELOPER?
    ↓               ↓
  USER          DEVELOPER
    ↓               ↓
QUICKSTART    PROJECT_SUMMARY
    ↓               ↓
  README      EXAMPLE_USAGE
    ↓               ↓
Want to BUILD?  Want to BUILD?
    ↓               ↓
  BUILD.md      BUILD.md
    ↓               ↓
 PACKAGING.md   PACKAGING.md
```

## 📝 Version History

- **v1.0.0** - Initial release
  - Core face detection and clustering
  - Interactive ROI selection
  - Video player with timeline
  - Modern dark UI
  - SQLite database
  - Standalone app builds

## 🎓 Learning Path

### Beginner (Just want to use it)
1. QUICKSTART.md (5 minutes)
2. README.md (15 minutes)
3. Start using the app!

### Intermediate (Want to customize)
1. PROJECT_SUMMARY.md (20 minutes)
2. EXAMPLE_USAGE.md (30 minutes)
3. Review source code
4. Make modifications

### Advanced (Want to distribute)
1. BUILD.md (30 minutes)
2. PACKAGING.md (45 minutes)
3. Test builds
4. Create installers

## 🔗 File Relationships

```
main.py
├── imports: database.py
├── imports: workers.py
├── imports: widgets/roi_selector.py
├── imports: widgets/gallery.py
└── imports: widgets/video_player.py

workers.py
├── uses: database.py
└── uses: opencv, face_recognition

database.py
└── uses: sqlite3 (built-in)

widgets/
├── roi_selector.py (standalone)
├── gallery.py (standalone)
└── video_player.py (standalone)
```

## ✅ Quick Start Checklist

- [ ] Read QUICKSTART.md
- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Run application (`python main.py`)
- [ ] Add test video
- [ ] Verify face detection works
- [ ] (Optional) Build standalone app
- [ ] (Optional) Read PROJECT_SUMMARY.md for technical details

---

**Next Steps**: Choose your role above and jump to the relevant documentation!

**Version**: 1.0.0  
**Last Updated**: 2024  
**Total Documentation**: 7 files, ~50KB

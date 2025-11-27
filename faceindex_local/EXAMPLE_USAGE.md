# Example Usage Guide

This guide shows how to use FaceIndex Local and provides code examples for programmatic access.

## Basic Usage (GUI)

### 1. Launch the Application

```bash
cd faceindex_local
python main.py
```

### 2. Add Your First Video

1. Click **"+ Add Video"** button
2. Select a video file (e.g., `meeting.mp4`)
3. Draw a rectangle around the area where faces appear
   - Or click **"Use Full Frame"** to analyze the entire video
4. Click **"Start Processing"**

### 3. Wait for Processing

You'll see progress:
```
Detecting faces... Frame 450/1500 (23 faces found)
Clustering faces...
Saving to database...
Processing complete!
```

### 4. Browse Detected People

- Gallery shows circular thumbnails of each person
- Click any person to load their timeline
- Video player jumps to their first appearance

### 5. Navigate the Video

- **Previous/Next buttons**: Jump between appearances
- **Timeline markers**: Click blue lines to seek
- **Play/Pause**: Use space bar or button

### 6. Manage People

**Rename:**
- Right-click on person card
- Select "Rename"
- Enter new name (e.g., "John Smith")

**Merge duplicates:**
- Right-click on person
- Select "Merge with..."
- Choose another person to combine

## Programmatic Usage

### Using the Database Directly

```python
from database import Database

# Open database
db = Database("faceindex.db")

# Get all videos
videos = db.get_all_videos()
for video in videos:
    print(f"Video: {video['file_name']}")
    print(f"  Duration: {video['duration']:.1f}s")
    print(f"  Status: {video['processing_status']}")
    
    # Get persons in this video
    persons = db.get_persons_by_video(video['id'])
    for person in persons:
        print(f"  Person {person['id']}: {person['name']} ({person['face_count']} appearances)")
        
        # Get face instances
        instances = db.get_face_instances_by_person(person['id'])
        timestamps = [inst['timestamp'] for inst in instances]
        print(f"    Appears at: {timestamps[:5]}...")  # First 5 timestamps

db.close()
```

### Running Face Detection Manually

```python
from workers import FaceProcessingWorker
from database import Database
from PyQt6.QtCore import QCoreApplication

# Create Qt application
app = QCoreApplication([])

# Initialize database
db = Database()

# Add video to database
video_id = db.add_video(
    file_path="/path/to/video.mp4",
    file_name="video.mp4",
    duration=120.0,
    fps=30.0,
    width=1920,
    height=1080,
    roi=(0, 0, 1920, 1080)  # Full frame
)

# Create worker
worker = FaceProcessingWorker(
    video_path="/path/to/video.mp4",
    roi=(0, 0, 1920, 1080),
    video_id=video_id,
    database=db
)

# Connect signals
def on_progress(percentage, status):
    print(f"[{percentage}%] {status}")

def on_finished(success, message):
    print(f"Finished: {message}")
    app.quit()

worker.progress_update.connect(on_progress)
worker.processing_finished.connect(on_finished)

# Start processing
worker.start()

# Run event loop
app.exec()
```

### Custom ROI Selection

```python
from PyQt6.QtWidgets import QApplication
from widgets.roi_selector import ROISelectorDialog

app = QApplication([])

# Show ROI selector
dialog = ROISelectorDialog("/path/to/video.mp4")

if dialog.exec() == dialog.DialogCode.Accepted:
    roi = dialog.get_roi()  # (x, y, w, h)
    video_info = dialog.get_video_info()
    
    print(f"ROI: {roi}")
    print(f"Video: {video_info['width']}x{video_info['height']} @ {video_info['fps']} fps")
```

### Loading Video in Player

```python
from PyQt6.QtWidgets import QApplication, QMainWindow
from widgets.video_player import VideoPlayerWidget

app = QApplication([])
window = QMainWindow()

# Create player
player = VideoPlayerWidget()

# Load video with timestamps
timestamps = [5.2, 10.5, 15.8, 23.1, 30.4]  # Seconds
player.load_video("/path/to/video.mp4", timestamps)

# Seek to first timestamp
player._seek_to_timestamp(timestamps[0])

window.setCentralWidget(player)
window.show()

app.exec()
```

### Exporting Data

```python
import json
from database import Database

db = Database()

# Export all persons as JSON
video_id = 1
persons = db.get_persons_by_video(video_id)

export_data = []
for person in persons:
    instances = db.get_face_instances_by_person(person['id'])
    
    person_data = {
        'id': person['id'],
        'name': person['name'],
        'face_count': person['face_count'],
        'timestamps': [inst['timestamp'] for inst in instances],
        'frames': [inst['frame_number'] for inst in instances]
    }
    export_data.append(person_data)

# Save to JSON
with open('export.json', 'w') as f:
    json.dump(export_data, indent=2, fp=f)

print(f"Exported {len(export_data)} people to export.json")
```

## Common Workflows

### Workflow 1: Process Multiple Videos

```python
from pathlib import Path
from database import Database
from workers import FaceProcessingWorker

db = Database()
video_folder = Path("/path/to/videos")

for video_path in video_folder.glob("*.mp4"):
    print(f"Processing {video_path.name}...")
    
    # Add to database
    video_id = db.add_video(
        file_path=str(video_path),
        file_name=video_path.name,
        duration=0,  # Will be detected by worker
        fps=0,
        width=0,
        height=0,
        roi=(0, 0, 1920, 1080)  # Adjust as needed
    )
    
    # Process (simplified - would need Qt event loop)
    # ... create and run worker ...
```

### Workflow 2: Find All Appearances of a Person

```python
from database import Database

db = Database()

# Get a specific person
person_id = 5
instances = db.get_face_instances_by_person(person_id)

print(f"Person appears {len(instances)} times:")
for inst in instances:
    minutes = int(inst['timestamp'] // 60)
    seconds = int(inst['timestamp'] % 60)
    print(f"  Frame {inst['frame_number']}: {minutes:02d}:{seconds:02d}")
```

### Workflow 3: Batch Rename People

```python
from database import Database

db = Database()

# Rename pattern: "Person 1" -> "Unknown Person 1"
persons = db.get_persons_by_video(video_id=1)

for person in persons:
    if person['name'].startswith("Person"):
        new_name = f"Unknown {person['name']}"
        db.update_person_name(person['id'], new_name)
        print(f"Renamed: {person['name']} -> {new_name}")
```

### Workflow 4: Generate Report

```python
from database import Database
from datetime import datetime

db = Database()

# Generate report
report = []
report.append("=" * 50)
report.append("FACEINDEX LOCAL - VIDEO ANALYSIS REPORT")
report.append("=" * 50)
report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
report.append("")

videos = db.get_all_videos()
for video in videos:
    report.append(f"Video: {video['file_name']}")
    report.append(f"  Duration: {video['duration']:.1f}s")
    report.append(f"  Resolution: {video['width']}x{video['height']}")
    
    persons = db.get_persons_by_video(video['id'])
    report.append(f"  People detected: {len(persons)}")
    
    for person in persons:
        report.append(f"    - {person['name']}: {person['face_count']} appearances")
    
    report.append("")

# Print report
print("\n".join(report))

# Save to file
with open("report.txt", "w") as f:
    f.write("\n".join(report))
```

## Configuration

### Adjusting Detection Parameters

Edit `workers.py`:

```python
class FaceProcessingWorker(QThread):
    def __init__(self, ...):
        # Performance vs accuracy tradeoffs
        self.frame_skip = 15        # Lower = more accurate, slower
        self.min_face_size = 40     # Lower = detect smaller faces
        self.clustering_eps = 0.5   # Lower = stricter clustering
        self.min_samples = 2        # Faces needed to form cluster
```

**Recommendations:**
- **Fast processing**: `frame_skip=30, min_face_size=60`
- **Accurate results**: `frame_skip=5, min_face_size=20`
- **Balanced** (default): `frame_skip=15, min_face_size=40`

### Using Different Face Detection Models

In `workers.py`, change the detection model:

```python
# Fast (HOG - current default)
face_locations = face_recognition.face_locations(rgb_frame, model='hog')

# Accurate (CNN - requires GPU for reasonable speed)
face_locations = face_recognition.face_locations(rgb_frame, model='cnn')
```

## Tips & Tricks

### Best Video Quality for Detection

- **Resolution**: 720p or higher
- **Lighting**: Well-lit, even lighting
- **Face angles**: Frontal or near-frontal
- **Face size**: At least 50x50 pixels
- **Motion**: Stable footage (not shaky)

### Optimizing Processing Speed

1. **Use ROI**: Select only the region with faces
2. **Increase frame_skip**: Process fewer frames
3. **Lower resolution**: Pre-process video to 720p
4. **Shorter clips**: Test on 30-second clips first

### Getting Better Clustering

1. **Adjust eps**: Lower value (0.3-0.4) for stricter matching
2. **More samples**: Higher min_samples for cleaner clusters
3. **Good lighting**: Consistent lighting helps matching
4. **Clear faces**: Frontal, unobstructed faces cluster better

### Troubleshooting

**No faces detected?**
- Try "Use Full Frame" instead of ROI
- Check video quality and face visibility
- Lower min_face_size threshold

**Too many clusters?**
- Increase clustering_eps (0.6-0.7)
- Merge duplicate persons manually

**Processing too slow?**
- Increase frame_skip (20-30)
- Use smaller ROI
- Ensure cmake/dlib installed correctly

## Advanced: Custom Integration

### Embedding in Another Qt Application

```python
from PyQt6.QtWidgets import QMainWindow
from main import MainWindow as FaceIndexWindow

class MyApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Embed FaceIndex as a component
        self.faceindex = FaceIndexWindow()
        self.faceindex.show()
```

### Custom Database Queries

```python
from database import Database

db = Database()
cursor = db.connection.cursor()

# Find people appearing in multiple videos
cursor.execute("""
    SELECT p.name, COUNT(DISTINCT p.video_id) as video_count
    FROM persons p
    GROUP BY p.name
    HAVING video_count > 1
""")

for row in cursor.fetchall():
    print(f"{row['name']} appears in {row['video_count']} videos")
```

---

For more examples, see the source code in `main.py` and `widgets/`.

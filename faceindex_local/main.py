"""
FaceIndex Local - Main Application Entry Point
A desktop application for face detection, clustering, and video navigation.
"""

import sys
from pathlib import Path

import qdarktheme

# Import custom modules
from database import Database
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QPalette
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from widgets.gallery import EmptyGalleryWidget, GalleryWidget
from widgets.roi_selector import ROISelectorDialog
from widgets.video_player import VideoPlayerWidget
from workers import FaceProcessingWorker


class ProcessingDialog(QFrame):
    """Dialog showing processing progress."""

    cancel_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                padding: 20px;
            }
        """)

        layout = QVBoxLayout(self)

        # Title
        self.title_label = QLabel("Processing Video")
        self.title_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #fff;"
        )
        layout.addWidget(self.title_label)

        # Status
        self.status_label = QLabel("Initializing...")
        self.status_label.setStyleSheet("color: #aaa; margin-top: 10px;")
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                text-align: center;
                color: #fff;
                background-color: #1e1e1e;
                height: 24px;
            }
            QProgressBar::chunk {
                background-color: #007acc;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: #fff;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
        """)
        layout.addWidget(self.cancel_btn)

    def update_progress(self, value: int, status: str):
        """Update progress bar and status."""
        self.progress_bar.setValue(value)
        self.status_label.setText(status)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Initialize database
        self.database = Database()

        # Clear database on startup for fresh session
        self._clear_session_data()

        # Worker reference
        self.current_worker = None
        self.current_video_id = None

        # In-memory storage for current session
        self.current_cluster_data = None
        self.current_person_timestamps = {}  # person_id -> list of timestamps
        self.current_person_names = {}  # person_id -> custom name

        self._setup_window()
        self._setup_ui()
        self._setup_menu()
        # Don't load existing data - start fresh each time
        # self._load_existing_data()

    def _setup_window(self):
        """Configure main window properties."""
        self.setWindowTitle("FaceIndex Local")
        self.setMinimumSize(1200, 800)

        # Apply dark theme
        self.setStyleSheet(qdarktheme.load_stylesheet("dark"))

    def _setup_ui(self):
        """Set up the main UI layout."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Gallery
        self.left_panel = self._create_left_panel()
        splitter.addWidget(self.left_panel)

        # Right panel - Video Player
        self.right_panel = self._create_right_panel()
        splitter.addWidget(self.right_panel)

        # Set initial sizes (60% left, 40% right)
        splitter.setSizes([720, 480])

        main_layout.addWidget(splitter)

    def _create_left_panel(self):
        """Create the left panel with gallery and controls."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1e1e1e;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #252525; padding: 10px;")
        toolbar_layout = QHBoxLayout(toolbar)

        self.add_video_btn = QPushButton("+ Add Video")
        self.add_video_btn.clicked.connect(self._add_video)
        self.add_video_btn.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        toolbar_layout.addWidget(self.add_video_btn)

        toolbar_layout.addStretch()

        layout.addWidget(toolbar)

        # Stacked widget for gallery/empty state
        self.stack = QStackedWidget()

        # Empty state
        self.empty_widget = EmptyGalleryWidget()
        self.stack.addWidget(self.empty_widget)

        # Gallery
        self.gallery = GalleryWidget()
        self.gallery.person_selected.connect(self._on_person_selected)
        self.gallery.person_renamed.connect(self._on_person_renamed)
        self.stack.addWidget(self.gallery)

        layout.addWidget(self.stack)

        # Processing overlay (hidden by default)
        self.processing_overlay = QWidget(panel)
        self.processing_overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.8);")
        overlay_layout = QVBoxLayout(self.processing_overlay)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.processing_dialog = ProcessingDialog()
        self.processing_dialog.cancel_requested.connect(self._cancel_processing)
        self.processing_dialog.setMaximumWidth(400)
        overlay_layout.addWidget(self.processing_dialog)

        self.processing_overlay.hide()

        return panel

    def _create_right_panel(self):
        """Create the right panel with video player."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1e1e1e;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header = QLabel("Video Player")
        header.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #fff; padding: 10px;"
        )
        layout.addWidget(header)

        # Video player
        self.video_player = VideoPlayerWidget()
        layout.addWidget(self.video_player)

        return panel

    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        add_video_action = QAction("Add Video", self)
        add_video_action.setShortcut("Ctrl+O")
        add_video_action.triggered.connect(self._add_video)
        file_menu.addAction(add_video_action)

        file_menu.addSeparator()

        save_project_action = QAction("Save Project...", self)
        save_project_action.setShortcut("Ctrl+S")
        save_project_action.triggered.connect(self._save_project)
        file_menu.addAction(save_project_action)

        load_project_action = QAction("Load Project...", self)
        load_project_action.setShortcut("Ctrl+L")
        load_project_action.triggered.connect(self._load_project)
        file_menu.addAction(load_project_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _clear_session_data(self):
        """Clear all session data for fresh start."""
        # Clear all database tables
        self.database.connection.execute("DELETE FROM face_instances")
        self.database.connection.execute("DELETE FROM persons")
        self.database.connection.execute("DELETE FROM videos")
        self.database.connection.commit()

        # Clear thumbnails directory
        import shutil

        thumbnails_dir = Path("thumbnails")
        if thumbnails_dir.exists():
            shutil.rmtree(thumbnails_dir)
        thumbnails_dir.mkdir(exist_ok=True)

        # Clear in-memory data
        self.current_cluster_data = None
        self.current_person_timestamps = {}
        self.current_person_names = {}

    def _load_existing_data(self):
        """Load existing videos and persons from database."""
        videos = self.database.get_all_videos()

        if not videos:
            self.stack.setCurrentIndex(0)  # Show empty state
            return

        # Load persons from the most recent completed video
        for video in videos:
            if video["processing_status"] == "completed":
                self._load_persons_for_video(video["id"])
                self.current_video_id = video["id"]
                break

    def _load_persons_for_video(self, video_id: int):
        """Load and display persons for a video."""
        self.gallery.clear()

        persons = self.database.get_persons_by_video(video_id)

        if not persons:
            self.stack.setCurrentIndex(0)
            return

        for person in persons:
            self.gallery.add_person(
                person_id=person["id"],
                name=person["name"] or f"Person {person['cluster_id'] + 1}",
                thumbnail_path=person["thumbnail_path"],
                face_count=person["face_count"],
            )

        self.stack.setCurrentIndex(1)  # Show gallery

    def _add_video(self):
        """Handle add video button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv);;All Files (*)",
        )

        if not file_path:
            return

        # Show ROI selector
        roi_dialog = ROISelectorDialog(file_path, self)
        if roi_dialog.exec() != roi_dialog.DialogCode.Accepted:
            return

        roi = roi_dialog.get_roi()
        video_info = roi_dialog.get_video_info()
        frame_skip = roi_dialog.get_frame_skip()
        time_range = roi_dialog.get_time_range()

        if not roi or not video_info:
            return

        # Don't save to database - just process in memory
        # Use a temporary video_id (0 means unsaved)
        video_id = 0
        self.current_video_id = video_id
        self.current_video_path = file_path
        self.current_video_info = video_info
        self.current_roi = roi

        # Start processing
        self._start_processing(file_path, roi, video_id, frame_skip, time_range)

    def _start_processing(
        self,
        video_path: str,
        roi: tuple,
        video_id: int,
        frame_skip: int = 15,
        time_range: tuple = (0, None),
    ):
        """Start background processing of video."""
        # Show processing overlay
        self.processing_overlay.show()
        self.processing_overlay.setGeometry(self.left_panel.geometry())

        # Create and start worker
        self.current_worker = FaceProcessingWorker(
            video_path, roi, video_id, self.database
        )

        # Set the frame skip value and time range
        self.current_worker.frame_skip = frame_skip
        self.current_worker.start_time = time_range[0]
        self.current_worker.end_time = time_range[1]

        # Connect signals
        self.current_worker.progress_update.connect(self._on_progress_update)
        self.current_worker.processing_finished.connect(self._on_processing_finished)
        self.current_worker.clusters_ready.connect(self._on_clusters_ready)

        # Start processing
        self.current_worker.start()

    def _cancel_processing(self):
        """Cancel ongoing processing."""
        if self.current_worker:
            reply = QMessageBox.question(
                self,
                "Cancel Processing",
                "Are you sure you want to cancel processing?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.current_worker.stop()
                self.processing_overlay.hide()

    def _on_progress_update(self, percentage: int, status: str):
        """Handle progress updates from worker."""
        self.processing_dialog.update_progress(percentage, status)

    def _on_clusters_ready(self, cluster_data):
        """Handle cluster data ready for display."""
        # Store cluster data in memory
        self.current_cluster_data = cluster_data

        # Build person timestamps map
        self.current_person_timestamps = {}
        person_map = cluster_data["person_map"]
        labels = cluster_data["labels"]
        timestamps = cluster_data["face_timestamps"]

        for cluster_id, person_id in person_map.items():
            # Find all face instances for this person
            cluster_indices = [
                i for i, label in enumerate(labels) if label == cluster_id
            ]
            person_timestamps = [timestamps[i] for i in cluster_indices]
            self.current_person_timestamps[person_id] = sorted(person_timestamps)

        # Display persons in gallery
        self._display_clusters_in_gallery(cluster_data)

    def _on_processing_finished(self, success: bool, message: str):
        """Handle processing completion."""
        self.processing_overlay.hide()

        if success:
            QMessageBox.information(self, "Success", message)
            # Data is already displayed via _on_clusters_ready
        else:
            QMessageBox.critical(self, "Error", message)

        self.current_worker = None

    def _display_clusters_in_gallery(self, cluster_data):
        """Display detected persons in the gallery from memory."""
        self.gallery.clear()

        person_map = cluster_data["person_map"]
        thumbnail_dir = cluster_data["thumbnail_dir"]
        labels = cluster_data["labels"]

        if not person_map:
            self.stack.setCurrentIndex(0)  # Show empty state
            return

        # Add each person to gallery
        for cluster_id, person_id in person_map.items():
            thumbnail_path = thumbnail_dir / f"person_{cluster_id}.jpg"

            # Count faces for this person
            face_count = sum(1 for label in labels if label == cluster_id)

            if thumbnail_path.exists():
                self.gallery.add_person(
                    person_id=person_id,
                    name=f"Person {cluster_id + 1}",
                    thumbnail_path=str(thumbnail_path),
                    face_count=face_count,
                )

        # Switch to gallery view
        self.stack.setCurrentIndex(1)

    def _on_person_selected(self, person_id: int):
        """Handle person selection from gallery."""
        # Use in-memory data if available
        if (
            self.current_person_timestamps
            and person_id in self.current_person_timestamps
        ):
            timestamps = self.current_person_timestamps[person_id]

            if timestamps and self.current_video_path:
                # Load video with timestamps
                self.video_player.load_video(self.current_video_path, timestamps)
        else:
            # Fallback to database (for saved projects)
            instances = self.database.get_face_instances_by_person(person_id)

            if not instances:
                return

            # Get video path
            video_id = instances[0]["video_id"]
            video = self.database.get_video_by_id(video_id)

            if not video:
                return

            # Extract timestamps
            timestamps = [inst["timestamp"] for inst in instances]

            # Load video with timestamps
            self.video_player.load_video(video["file_path"], timestamps)

        # Seek to first timestamp
        if timestamps:
            self.video_player._seek_to_timestamp(timestamps[0])

    def _on_person_renamed(self, person_id: int, new_name: str):
        """Handle person rename."""
        # Store in memory during session
        self.current_person_names[person_id] = new_name

        # Also update database if this is a loaded project
        try:
            self.database.update_person_name(person_id, new_name)
        except:
            # Person doesn't exist in database yet (unsaved session)
            pass

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About FaceIndex Local",
            "<h3>FaceIndex Local</h3>"
            "<p>A desktop application for face detection, clustering, and video navigation.</p>"
            "<p><b>Version:</b> 1.0.0</p>"
            "<p><b>Technology:</b> PyQt6, OpenCV, face_recognition</p>",
        )

    def _save_project(self):
        """Save current project to an external database file."""
        if not self.current_cluster_data:
            QMessageBox.warning(
                self,
                "No Data to Save",
                "Please process a video first before saving.",
            )
            return

        # Ask user where to save the project
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project",
            "",
            "FaceIndex Project (*.fip);;All Files (*)",
        )

        if not file_path:
            return

        try:
            import shutil
            import sqlite3

            # Create a new database for this project
            project_db = sqlite3.connect(file_path)
            project_db.row_factory = sqlite3.Row

            # Copy schema from current database
            for line in self.database.connection.iterdump():
                if line not in ("BEGIN;", "COMMIT;"):
                    project_db.execute(line)

            # Store video metadata including path
            cursor = project_db.cursor()
            cursor.execute(
                """
                INSERT INTO videos (file_path, file_name, duration, fps, width, height,
                                   roi_x, roi_y, roi_w, roi_h, processing_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed')
            """,
                (
                    self.current_video_path,
                    Path(self.current_video_path).name,
                    self.current_video_info["duration"],
                    self.current_video_info["fps"],
                    self.current_video_info["width"],
                    self.current_video_info["height"],
                    self.current_roi[0],
                    self.current_roi[1],
                    self.current_roi[2],
                    self.current_roi[3],
                ),
            )
            video_id = cursor.lastrowid

            # Save persons and faces
            cluster_data = self.current_cluster_data
            person_map = cluster_data["person_map"]
            labels = cluster_data["labels"]
            face_images = cluster_data["face_images"]
            face_timestamps = cluster_data["face_timestamps"]
            face_locations = cluster_data["face_locations"]
            face_encodings = cluster_data["face_encodings"]
            thumbnail_dir = cluster_data["thumbnail_dir"]

            # Create thumbnails directory in project file location
            project_thumbnails = (
                Path(file_path).parent / f"{Path(file_path).stem}_thumbnails"
            )
            project_thumbnails.mkdir(exist_ok=True)

            for cluster_id, person_id in person_map.items():
                # Copy person thumbnail
                src_thumb = thumbnail_dir / f"person_{cluster_id}.jpg"
                dest_thumb = project_thumbnails / f"person_{cluster_id}.jpg"
                if src_thumb.exists():
                    shutil.copy(src_thumb, dest_thumb)

                # Get custom name if user renamed this person
                person_name = self.current_person_names.get(
                    person_id, f"Person {cluster_id + 1}"
                )

                # Add person to database
                cursor.execute(
                    """
                    INSERT INTO persons (video_id, cluster_id, name, thumbnail_path)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        video_id,
                        int(cluster_id),
                        person_name,
                        str(dest_thumb),
                    ),
                )
                db_person_id = cursor.lastrowid

                # Add face instances
                cluster_indices = [
                    i for i, label in enumerate(labels) if label == cluster_id
                ]
                for idx in cluster_indices:
                    # Copy face thumbnail
                    src_face = thumbnail_dir / f"face_{idx}.jpg"
                    dest_face = project_thumbnails / f"face_{idx}.jpg"
                    if src_face.exists():
                        shutil.copy(src_face, dest_face)

                    # Get bbox
                    top, right, bottom, left = face_locations[idx]
                    bbox = (left, top, right - left, bottom - top)

                    # Get encoding
                    encoding = face_encodings[idx]
                    encoding_bytes = encoding.tobytes()

                    cursor.execute(
                        """
                        INSERT INTO face_instances (person_id, video_id, timestamp, frame_number,
                                                   bbox_x, bbox_y, bbox_w, bbox_h, encoding, confidence, thumbnail_path)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            db_person_id,
                            video_id,
                            face_timestamps[idx],
                            0,
                            bbox[0],
                            bbox[1],
                            bbox[2],
                            bbox[3],
                            encoding_bytes,
                            1.0,
                            str(dest_face),
                        ),
                    )

            project_db.commit()
            project_db.close()

            QMessageBox.information(
                self,
                "Project Saved",
                f"Project saved successfully to:\n{file_path}",
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Failed to save project:\n{str(e)}",
            )

    def _load_project(self):
        """Load a project from an external database file."""
        # Ask user to select project file
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Project",
            "",
            "FaceIndex Project (*.fip);;All Files (*)",
        )

        if not file_path:
            return

        try:
            import sqlite3

            # Open project database
            project_db = sqlite3.connect(file_path)
            project_db.row_factory = sqlite3.Row
            cursor = project_db.cursor()

            # Get video info
            cursor.execute("SELECT * FROM videos LIMIT 1")
            video_row = cursor.fetchone()

            if not video_row:
                QMessageBox.warning(
                    self, "Invalid Project", "No video data found in project file."
                )
                project_db.close()
                return

            stored_video_path = video_row["file_path"]

            # Check if video file exists at original location
            if not Path(stored_video_path).exists():
                # Ask user to locate the video file
                QMessageBox.information(
                    self,
                    "Locate Video File",
                    f"The original video file was not found at:\n{stored_video_path}\n\n"
                    "Please locate the video file.",
                )

                video_path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Select Video File",
                    "",
                    "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv);;All Files (*)",
                )

                if not video_path:
                    project_db.close()
                    return
            else:
                video_path = stored_video_path

            # Load persons
            cursor.execute(
                "SELECT * FROM persons WHERE video_id = ?", (video_row["id"],)
            )
            persons = cursor.fetchall()

            # Clear current gallery
            self.gallery.clear()

            # Store video info
            self.current_video_path = video_path
            self.current_video_info = {
                "duration": video_row["duration"],
                "fps": video_row["fps"],
                "width": video_row["width"],
                "height": video_row["height"],
            }
            self.current_roi = (
                video_row["roi_x"],
                video_row["roi_y"],
                video_row["roi_w"],
                video_row["roi_h"],
            )

            # Build person timestamps from face instances
            self.current_person_timestamps = {}
            self.current_person_names = {}

            for person in persons:
                person_id = person["id"]

                # Get face instances for this person
                cursor.execute(
                    "SELECT timestamp FROM face_instances WHERE person_id = ? ORDER BY timestamp",
                    (person_id,),
                )
                timestamps = [row["timestamp"] for row in cursor.fetchall()]
                self.current_person_timestamps[person_id] = timestamps

                # Store custom name in memory
                self.current_person_names[person_id] = person["name"]

                # Add to gallery
                thumbnail_path = person["thumbnail_path"]
                if Path(thumbnail_path).exists():
                    self.gallery.add_person(
                        person_id=person_id,
                        name=person["name"],
                        thumbnail_path=thumbnail_path,
                        face_count=len(timestamps),
                    )

            project_db.close()

            # Switch to gallery view
            self.stack.setCurrentIndex(1)

            QMessageBox.information(
                self,
                "Project Loaded",
                f"Project loaded successfully!\n\n"
                f"Found {len(persons)} person(s) in the video.",
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Failed",
                f"Failed to load project:\n{str(e)}",
            )

    def resizeEvent(self, event):
        """Handle window resize to update overlay position."""
        super().resizeEvent(event)
        if self.processing_overlay.isVisible():
            self.processing_overlay.setGeometry(self.left_panel.geometry())

    def closeEvent(self, event):
        """Handle application close."""
        # Stop any running workers
        if self.current_worker:
            self.current_worker.stop()

        # Cleanup video player
        self.video_player.cleanup()

        # Close database
        self.database.close()

        event.accept()


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("FaceIndex Local")
    app.setOrganizationName("FaceIndex")
    app.setApplicationVersion("1.0.0")

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

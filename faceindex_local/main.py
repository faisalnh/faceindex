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

        # Worker reference
        self.current_worker = None
        self.current_video_id = None

        self._setup_window()
        self._setup_ui()
        self._setup_menu()
        self._load_existing_data()

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

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

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

        if not roi or not video_info:
            return

        # Add video to database
        file_name = Path(file_path).name
        video_id = self.database.add_video(
            file_path=file_path,
            file_name=file_name,
            duration=video_info["duration"],
            fps=video_info["fps"],
            width=video_info["width"],
            height=video_info["height"],
            roi=roi,
        )

        self.current_video_id = video_id

        # Start processing
        self._start_processing(file_path, roi, video_id)

    def _start_processing(self, video_path: str, roi: tuple, video_id: int):
        """Start background processing of video."""
        # Show processing overlay
        self.processing_overlay.show()
        self.processing_overlay.setGeometry(self.left_panel.geometry())

        # Create and start worker
        self.current_worker = FaceProcessingWorker(
            video_path, roi, video_id, self.database
        )

        # Connect signals
        self.current_worker.progress_update.connect(self._on_progress_update)
        self.current_worker.processing_finished.connect(self._on_processing_finished)

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

    def _on_processing_finished(self, success: bool, message: str):
        """Handle processing completion."""
        self.processing_overlay.hide()

        if success:
            QMessageBox.information(self, "Success", message)
            # Reload gallery
            if self.current_video_id:
                self._load_persons_for_video(self.current_video_id)
        else:
            QMessageBox.critical(self, "Error", message)

        self.current_worker = None

    def _on_person_selected(self, person_id: int):
        """Handle person selection from gallery."""
        # Get person's face instances
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
        self.database.update_person_name(person_id, new_name)

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

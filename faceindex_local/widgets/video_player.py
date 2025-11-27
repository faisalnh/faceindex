"""
Video Player Widget - Custom video player with timeline visualization using OpenCV.
"""

from typing import List

import cv2
import numpy as np
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class TimelineWidget(QWidget):
    """Custom timeline visualization showing where a person appears."""

    position_clicked = pyqtSignal(float)  # timestamp in seconds

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(40)
        self.duration = 0
        self.timestamps = []  # List of timestamps where person appears
        self.current_position = 0

        self.setStyleSheet("background-color: #2d2d2d; border-radius: 4px;")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_duration(self, duration: float):
        """Set the total video duration in seconds."""
        self.duration = duration
        self.update()

    def set_timestamps(self, timestamps: List[float]):
        """Set the timestamps where the person appears."""
        self.timestamps = timestamps
        self.update()

    def set_current_position(self, position: float):
        """Set the current playback position."""
        self.current_position = position
        self.update()

    def paintEvent(self, event):
        """Custom paint to draw timeline with markers."""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        # Draw background
        painter.fillRect(0, 0, width, height, QColor("#2d2d2d"))

        if self.duration <= 0:
            painter.end()
            return

        # Draw timestamp markers
        painter.setPen(QPen(QColor("#007acc"), 2))
        for timestamp in self.timestamps:
            x = int((timestamp / self.duration) * width)
            painter.drawLine(x, 0, x, height)

        # Draw current position indicator
        if self.current_position > 0:
            x = int((self.current_position / self.duration) * width)
            painter.setPen(QPen(QColor("#00ff00"), 3))
            painter.drawLine(x, 0, x, height)

        painter.end()

    def mousePressEvent(self, event):
        """Handle click to seek to position."""
        if event.button() == Qt.MouseButton.LeftButton and self.duration > 0:
            position = (event.pos().x() / self.width()) * self.duration
            self.position_clicked.emit(position)


class VideoPlayerWidget(QWidget):
    """Complete video player with controls and timeline using OpenCV."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_video_path = None
        self.person_timestamps = []
        self.cap = None
        self.is_playing = False
        self.current_frame_number = 0
        self.total_frames = 0
        self.fps = 30

        self._setup_ui()
        self._setup_timer()

    def _setup_ui(self):
        """Set up the player UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Video display area
        self.video_label = QLabel()
        self.video_label.setMinimumHeight(400)
        self.video_label.setStyleSheet(
            "background-color: #000000; border: 1px solid #3d3d3d;"
        )
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setText("No video loaded")
        self.video_label.setScaledContents(False)
        layout.addWidget(self.video_label)

        # Timeline visualization
        self.timeline = TimelineWidget()
        self.timeline.position_clicked.connect(self._seek_to_timestamp)
        layout.addWidget(self.timeline)

        # Progress slider
        slider_layout = QHBoxLayout()

        self.position_label = QLabel("00:00")
        self.position_label.setStyleSheet("color: #aaa; font-size: 11px;")
        slider_layout.addWidget(self.position_label)

        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #3d3d3d;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #007acc;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #005a9e;
            }
            QSlider::sub-page:horizontal {
                background: #007acc;
                border-radius: 3px;
            }
        """)
        self.position_slider.sliderPressed.connect(self._on_slider_pressed)
        self.position_slider.sliderReleased.connect(self._on_slider_released)
        self.position_slider.valueChanged.connect(self._on_slider_moved)
        slider_layout.addWidget(self.position_slider)

        self.duration_label = QLabel("00:00")
        self.duration_label.setStyleSheet("color: #aaa; font-size: 11px;")
        slider_layout.addWidget(self.duration_label)

        layout.addLayout(slider_layout)

        # Control buttons
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        button_style = """
            QPushButton {
                background-color: #3d3d3d;
                border: none;
                border-radius: 4px;
                color: #ffffff;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
            QPushButton:pressed {
                background-color: #2d2d2d;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #666;
            }
        """

        self.play_button = QPushButton("Play")
        self.play_button.setStyleSheet(button_style)
        self.play_button.clicked.connect(self._toggle_playback)
        self.play_button.setEnabled(False)
        controls_layout.addWidget(self.play_button)

        self.prev_button = QPushButton("← Previous")
        self.prev_button.setStyleSheet(button_style)
        self.prev_button.setEnabled(False)
        self.prev_button.clicked.connect(self._go_to_previous)
        controls_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next →")
        self.next_button.setStyleSheet(button_style)
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self._go_to_next)
        controls_layout.addWidget(self.next_button)

        controls_layout.addStretch()

        layout.addLayout(controls_layout)

    def _setup_timer(self):
        """Set up playback timer."""
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame)
        self.slider_dragging = False

    def load_video(self, video_path: str, timestamps: List[float] = None):
        """Load a video file and optionally set person timestamps."""
        if self.cap:
            self.cap.release()

        self.current_video_path = video_path
        self.person_timestamps = sorted(timestamps) if timestamps else []

        # Open video with OpenCV
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            self.video_label.setText("Error loading video")
            return

        # Get video properties
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        self.duration = self.total_frames / self.fps

        # Update UI
        self.position_slider.setRange(0, self.total_frames - 1)
        self.duration_label.setText(self._format_time(int(self.duration)))
        self.timeline.set_duration(self.duration)

        if timestamps:
            self.timeline.set_timestamps(timestamps)
            self.prev_button.setEnabled(True)
            self.next_button.setEnabled(True)

        self.play_button.setEnabled(True)

        # Show first frame
        self.current_frame_number = 0
        self._show_frame(0)

    def _show_frame(self, frame_number: int):
        """Display a specific frame."""
        if not self.cap:
            return

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()

        if ret:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w

            # Create QImage and QPixmap
            q_image = QImage(
                rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888
            )
            pixmap = QPixmap.fromImage(q_image)

            # Scale to fit label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.video_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            self.video_label.setPixmap(scaled_pixmap)

            # Update position
            self.current_frame_number = frame_number
            timestamp = frame_number / self.fps

            if not self.slider_dragging:
                self.position_slider.setValue(frame_number)

            self.position_label.setText(self._format_time(int(timestamp)))
            self.timeline.set_current_position(timestamp)

    def _update_frame(self):
        """Update frame during playback."""
        if not self.cap or not self.is_playing:
            return

        next_frame = self.current_frame_number + 1

        if next_frame >= self.total_frames:
            # End of video
            self._toggle_playback()
            return

        self._show_frame(next_frame)

    def _toggle_playback(self):
        """Toggle between play and pause."""
        if not self.cap:
            return

        self.is_playing = not self.is_playing

        if self.is_playing:
            self.play_button.setText("Pause")
            interval = int(1000 / self.fps)  # milliseconds
            self.timer.start(interval)
        else:
            self.play_button.setText("Play")
            self.timer.stop()

    def _seek_to_timestamp(self, timestamp: float):
        """Seek to a specific timestamp in seconds."""
        if not self.cap:
            return

        frame_number = int(timestamp * self.fps)
        frame_number = max(0, min(frame_number, self.total_frames - 1))
        self._show_frame(frame_number)

    def _on_slider_pressed(self):
        """Handle slider press."""
        self.slider_dragging = True
        if self.is_playing:
            self._toggle_playback()

    def _on_slider_released(self):
        """Handle slider release."""
        self.slider_dragging = False
        if self.cap:
            self._show_frame(self.position_slider.value())

    def _on_slider_moved(self, value):
        """Handle slider movement."""
        if self.slider_dragging and self.cap:
            timestamp = value / self.fps
            self.position_label.setText(self._format_time(int(timestamp)))

    def _go_to_previous(self):
        """Jump to previous timestamp."""
        if not self.person_timestamps:
            return

        current_time = self.current_frame_number / self.fps

        # Find previous timestamp
        prev_timestamp = None
        for ts in reversed(self.person_timestamps):
            if ts < current_time - 1:  # 1 second threshold
                prev_timestamp = ts
                break

        if prev_timestamp is None and self.person_timestamps:
            # Wrap to last timestamp
            prev_timestamp = self.person_timestamps[-1]

        if prev_timestamp is not None:
            self._seek_to_timestamp(prev_timestamp)

    def _go_to_next(self):
        """Jump to next timestamp."""
        if not self.person_timestamps:
            return

        current_time = self.current_frame_number / self.fps

        # Find next timestamp
        next_timestamp = None
        for ts in self.person_timestamps:
            if ts > current_time + 1:  # 1 second threshold
                next_timestamp = ts
                break

        if next_timestamp is None and self.person_timestamps:
            # Wrap to first timestamp
            next_timestamp = self.person_timestamps[0]

        if next_timestamp is not None:
            self._seek_to_timestamp(next_timestamp)

    def _format_time(self, seconds):
        """Format seconds to MM:SS."""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def stop(self):
        """Stop playback and release resources."""
        if self.is_playing:
            self._toggle_playback()

        if self.cap:
            self.cap.release()
            self.cap = None

    def cleanup(self):
        """Clean up resources."""
        self.stop()
        self.video_label.clear()
        self.video_label.setText("No video loaded")

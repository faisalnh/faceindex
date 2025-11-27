"""
Video Player Widget - Custom video player with timeline visualization.
"""

import os
from typing import List, Tuple

from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QStyle,
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
    """Complete video player with controls and timeline."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_video_path = None
        self.person_timestamps = []

        self._setup_ui()
        self._setup_player()
        self._setup_connections()

    def _setup_ui(self):
        """Set up the player UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Video widget
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(400)
        self.video_widget.setStyleSheet("background-color: #000000;")
        layout.addWidget(self.video_widget)

        # Timeline visualization
        self.timeline = TimelineWidget()
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
        """

        self.play_button = QPushButton("Play")
        self.play_button.setStyleSheet(button_style)
        controls_layout.addWidget(self.play_button)

        self.prev_button = QPushButton("← Previous")
        self.prev_button.setStyleSheet(button_style)
        self.prev_button.setEnabled(False)
        controls_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next →")
        self.next_button.setStyleSheet(button_style)
        self.next_button.setEnabled(False)
        controls_layout.addWidget(self.next_button)

        controls_layout.addStretch()

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.setStyleSheet(self.position_slider.styleSheet())
        controls_layout.addWidget(QLabel("🔊"))
        controls_layout.addWidget(self.volume_slider)

        layout.addLayout(controls_layout)

    def _setup_player(self):
        """Set up the media player."""
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)

        # Set initial volume
        self.audio_output.setVolume(0.7)

    def _setup_connections(self):
        """Connect signals and slots."""
        # Player signals
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.playbackStateChanged.connect(self._on_state_changed)

        # Control signals
        self.play_button.clicked.connect(self._toggle_playback)
        self.position_slider.sliderMoved.connect(self._seek_position)
        self.volume_slider.valueChanged.connect(self._change_volume)

        # Timeline signals
        self.timeline.position_clicked.connect(self._seek_to_timestamp)

        # Navigation signals
        self.prev_button.clicked.connect(self._go_to_previous)
        self.next_button.clicked.connect(self._go_to_next)

    def load_video(self, video_path: str, timestamps: List[float] = None):
        """Load a video file and optionally set person timestamps."""
        if not os.path.exists(video_path):
            print(f"Video file not found: {video_path}")
            return

        self.current_video_path = video_path
        self.person_timestamps = sorted(timestamps) if timestamps else []

        # Load video
        self.player.setSource(QUrl.fromLocalFile(video_path))

        # Update timeline
        if timestamps:
            self.timeline.set_timestamps(timestamps)
            self.prev_button.setEnabled(True)
            self.next_button.setEnabled(True)

    def _toggle_playback(self):
        """Toggle between play and pause."""
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _on_state_changed(self, state):
        """Handle playback state changes."""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setText("Pause")
        else:
            self.play_button.setText("Play")

    def _on_position_changed(self, position):
        """Handle position changes (in milliseconds)."""
        # Update slider
        self.position_slider.setValue(position)

        # Update label
        seconds = position // 1000
        self.position_label.setText(self._format_time(seconds))

        # Update timeline
        self.timeline.set_current_position(seconds)

    def _on_duration_changed(self, duration):
        """Handle duration changes (in milliseconds)."""
        self.position_slider.setRange(0, duration)

        seconds = duration // 1000
        self.duration_label.setText(self._format_time(seconds))
        self.timeline.set_duration(seconds)

    def _seek_position(self, position):
        """Seek to a specific position."""
        self.player.setPosition(position)

    def _seek_to_timestamp(self, timestamp):
        """Seek to a specific timestamp in seconds."""
        self.player.setPosition(int(timestamp * 1000))

    def _change_volume(self, value):
        """Change the volume."""
        self.audio_output.setVolume(value / 100)

    def _go_to_previous(self):
        """Jump to previous timestamp."""
        if not self.person_timestamps:
            return

        current_pos = self.player.position() / 1000  # Convert to seconds

        # Find previous timestamp
        prev_timestamp = None
        for ts in reversed(self.person_timestamps):
            if ts < current_pos - 1:  # 1 second threshold
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

        current_pos = self.player.position() / 1000  # Convert to seconds

        # Find next timestamp
        next_timestamp = None
        for ts in self.person_timestamps:
            if ts > current_pos + 1:  # 1 second threshold
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
        self.player.stop()

    def cleanup(self):
        """Clean up resources."""
        self.player.stop()
        self.player.setSource(QUrl())

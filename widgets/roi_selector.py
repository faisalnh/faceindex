"""
ROI Selector Widget - Allows user to draw a region of interest on a video frame.
"""

import cv2
import numpy as np
from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class TimelineWidget(QWidget):
    """Visual timeline with draggable start/end markers."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(60)
        self.duration = 0
        self.start_time = 0
        self.end_time = 0

        # Dragging state
        self.dragging_start = False
        self.dragging_end = False

        self.setStyleSheet(
            "background-color: #2d2d2d; border: 1px solid #3d3d3d; border-radius: 4px;"
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_duration(self, duration):
        """Set the video duration in seconds."""
        self.duration = duration
        self.end_time = duration
        self.update()

    def set_range(self, start, end):
        """Set the time range."""
        self.start_time = start
        self.end_time = end if end is not None else self.duration
        self.update()

    def get_range(self):
        """Get the current time range."""
        return (
            self.start_time,
            self.end_time if self.end_time < self.duration else None,
        )

    def paintEvent(self, event):
        """Draw the timeline with markers."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        # Draw background
        painter.fillRect(0, 0, width, height, QColor("#2d2d2d"))

        if self.duration <= 0:
            painter.end()
            return

        # Draw timeline bar
        bar_height = 20
        bar_y = (height - bar_height) // 2
        painter.fillRect(10, bar_y, width - 20, bar_height, QColor("#3d3d3d"))

        # Draw time tick marks along the timeline
        painter.setPen(QColor("#666666"))
        num_ticks = min(10, int(self.duration / 10) + 1)  # Show up to 10 ticks
        interval = self.duration / max(num_ticks - 1, 1)

        for i in range(num_ticks):
            time = i * interval
            x = int(10 + (time / self.duration) * (width - 20))

            # Draw tick
            painter.drawLine(x, bar_y - 5, x, bar_y)
            painter.drawLine(x, bar_y + bar_height, x, bar_y + bar_height + 5)

            # Draw time label below
            time_text = self._format_time(time)
            text_width = painter.fontMetrics().horizontalAdvance(time_text)
            painter.setPen(QColor("#888888"))
            painter.drawText(x - text_width // 2, height - 5, time_text)
            painter.setPen(QColor("#666666"))

        # Calculate marker positions
        start_x = int(10 + (self.start_time / self.duration) * (width - 20))
        end_x = int(10 + (self.end_time / self.duration) * (width - 20))

        # Draw selected range
        painter.fillRect(start_x, bar_y, end_x - start_x, bar_height, QColor("#007acc"))

        # Draw start marker
        painter.setBrush(QColor("#00ff00"))
        painter.setPen(QPen(QColor("#ffffff"), 2))
        start_marker = [
            QPoint(start_x, bar_y - 10),
            QPoint(start_x - 8, bar_y - 20),
            QPoint(start_x + 8, bar_y - 20),
        ]
        painter.drawPolygon(start_marker)

        # Draw end marker
        painter.setBrush(QColor("#ff0000"))
        end_marker = [
            QPoint(end_x, bar_y + bar_height + 10),
            QPoint(end_x - 8, bar_y + bar_height + 20),
            QPoint(end_x + 8, bar_y + bar_height + 20),
        ]
        painter.drawPolygon(end_marker)

        # Draw start time label (above marker, with background)
        painter.setPen(QColor("#00ff00"))
        start_text = self._format_time(self.start_time)
        start_text_width = painter.fontMetrics().horizontalAdvance(start_text)

        # Background for start label
        painter.fillRect(
            start_x - start_text_width // 2 - 3,
            5,
            start_text_width + 6,
            16,
            QColor("#1a1a1a"),
        )
        painter.drawText(start_x - start_text_width // 2, 17, start_text)

        # Draw end time label (below marker, with background)
        painter.setPen(QColor("#ff0000"))
        end_text = self._format_time(self.end_time)
        end_text_width = painter.fontMetrics().horizontalAdvance(end_text)

        # Background for end label
        painter.fillRect(
            end_x - end_text_width // 2 - 3,
            bar_y + bar_height + 25,
            end_text_width + 6,
            16,
            QColor("#1a1a1a"),
        )
        painter.drawText(end_x - end_text_width // 2, bar_y + bar_height + 37, end_text)

        painter.end()

    def _format_time(self, seconds):
        """Format seconds as MM:SS."""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def mousePressEvent(self, event):
        """Handle mouse press to start dragging markers."""
        if event.button() != Qt.MouseButton.LeftButton or self.duration <= 0:
            return

        width = self.width()
        bar_y = (self.height() - 20) // 2

        start_x = int(10 + (self.start_time / self.duration) * (width - 20))
        end_x = int(10 + (self.end_time / self.duration) * (width - 20))

        pos = event.pos()

        # Check if clicking near start marker
        if abs(pos.x() - start_x) <= 15 and abs(pos.y() - (bar_y - 15)) <= 25:
            self.dragging_start = True
            return

        # Check if clicking near end marker
        if abs(pos.x() - end_x) <= 15 and abs(pos.y() - (bar_y + 35)) <= 25:
            self.dragging_end = True
            return

    def mouseMoveEvent(self, event):
        """Handle mouse move to drag markers."""
        if not (self.dragging_start or self.dragging_end) or self.duration <= 0:
            return

        width = self.width()
        pos_x = max(10, min(event.pos().x(), width - 10))

        # Calculate time from position
        time = ((pos_x - 10) / (width - 20)) * self.duration
        time = max(0, min(time, self.duration))

        if self.dragging_start:
            self.start_time = min(time, self.end_time - 1)  # Keep at least 1 second
        elif self.dragging_end:
            self.end_time = max(time, self.start_time + 1)  # Keep at least 1 second

        self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release to stop dragging."""
        self.dragging_start = False
        self.dragging_end = False


class ROISelectorLabel(QLabel):
    """Custom QLabel that handles mouse events for drawing ROI rectangle."""

    roi_selected = pyqtSignal(tuple)  # Emits (x, y, w, h) in image coordinates

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)

        # Drawing state
        self.drawing = False
        self.moving = False
        self.resizing = False
        self.resize_handle = None  # Which corner/edge is being resized
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.current_rect = QRect()
        self.drag_offset = QPoint()

        # Original image and pixmap
        self.original_pixmap = None
        self.image_size = None  # Original image size (width, height)

        # Style
        self.setStyleSheet("border: 2px solid #3d3d3d;")

    def set_image(self, image: np.ndarray):
        """Set the image to display (OpenCV BGR format)."""
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w

        # Store original image size
        self.image_size = (w, h)

        # Create QImage and QPixmap
        q_image = QImage(
            rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888
        )
        self.original_pixmap = QPixmap.fromImage(q_image)

        # Scale to fit widget while maintaining aspect ratio
        self._update_display()

    def _update_display(self):
        """Update the displayed pixmap with current ROI rectangle."""
        if self.original_pixmap is None:
            return

        # Scale to fit widget first
        scaled_pixmap = self.original_pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        # Draw the rectangle if it exists
        if not self.current_rect.isNull():
            # Create a transparent overlay pixmap
            overlay = QPixmap(scaled_pixmap.size())
            overlay.fill(Qt.GlobalColor.transparent)

            painter = QPainter(overlay)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Draw semi-transparent overlay outside ROI
            painter.fillRect(overlay.rect(), QColor(0, 0, 0, 120))

            # Clear the ROI area to make it transparent
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_SourceOut
            )
            painter.fillRect(self.current_rect, QColor(0, 0, 0, 255))

            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_SourceOver
            )

            # Green border for ROI
            pen = QPen(QColor(0, 255, 0), 3, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.current_rect)

            # Draw corner handles
            handle_size = 8
            painter.setBrush(QColor(0, 255, 0))
            corners = [
                self.current_rect.topLeft(),
                self.current_rect.topRight(),
                self.current_rect.bottomLeft(),
                self.current_rect.bottomRight(),
            ]
            for corner in corners:
                painter.drawEllipse(corner, handle_size, handle_size)

            painter.end()

            # Composite the overlay onto the scaled image
            final_painter = QPainter(scaled_pixmap)
            final_painter.drawPixmap(0, 0, overlay)
            final_painter.end()

        self.setPixmap(scaled_pixmap)

    def _get_image_offset(self):
        """Get the offset of the scaled image within the widget."""
        if not self.pixmap():
            return (0, 0)

        pixmap_width = self.pixmap().width()
        pixmap_height = self.pixmap().height()

        offset_x = (self.width() - pixmap_width) // 2
        offset_y = (self.height() - pixmap_height) // 2

        return (offset_x, offset_y)

    def _map_to_pixmap_coords(self, widget_pos):
        """Map widget coordinates to pixmap coordinates."""
        offset_x, offset_y = self._get_image_offset()

        pixmap_x = widget_pos.x() - offset_x
        pixmap_y = widget_pos.y() - offset_y

        # Clamp to pixmap bounds
        if self.pixmap():
            pixmap_x = max(0, min(pixmap_x, self.pixmap().width()))
            pixmap_y = max(0, min(pixmap_y, self.pixmap().height()))

        return QPoint(pixmap_x, pixmap_y)

    def _get_resize_handle(self, pos):
        """Check if position is over a resize handle. Returns handle type or None."""
        if self.current_rect.isNull():
            return None

        handle_size = 12
        rect = self.current_rect

        # Check corners
        corners = {
            "top_left": rect.topLeft(),
            "top_right": rect.topRight(),
            "bottom_left": rect.bottomLeft(),
            "bottom_right": rect.bottomRight(),
        }

        for handle_name, corner in corners.items():
            if (
                abs(pos.x() - corner.x()) <= handle_size
                and abs(pos.y() - corner.y()) <= handle_size
            ):
                return handle_name

        return None

    def _is_inside_rect(self, pos):
        """Check if position is inside the rectangle."""
        if self.current_rect.isNull():
            return False
        return self.current_rect.contains(pos)

    def mousePressEvent(self, event):
        """Handle mouse press to start drawing, moving, or resizing."""
        if event.button() == Qt.MouseButton.LeftButton and self.original_pixmap:
            pixmap_pos = self._map_to_pixmap_coords(event.pos())

            # Check if clicking on resize handle
            resize_handle = self._get_resize_handle(pixmap_pos)
            if resize_handle:
                self.resizing = True
                self.resize_handle = resize_handle
                self.start_point = pixmap_pos
                return

            # Check if clicking inside existing rectangle to move it
            if self._is_inside_rect(pixmap_pos):
                self.moving = True
                self.drag_offset = pixmap_pos - self.current_rect.topLeft()
                self.setCursor(Qt.CursorShape.SizeAllCursor)
                return

            # Start drawing new rectangle
            self.drawing = True
            self.start_point = pixmap_pos
            self.current_rect = QRect(self.start_point, self.start_point)
            self._update_display()

    def mouseMoveEvent(self, event):
        """Handle mouse move to update rectangle, move it, or resize it."""
        pixmap_pos = self._map_to_pixmap_coords(event.pos())

        if self.drawing and self.original_pixmap:
            # Drawing new rectangle
            self.end_point = pixmap_pos
            self.current_rect = QRect(self.start_point, self.end_point).normalized()
            self._update_display()
        elif self.moving:
            # Moving existing rectangle
            new_top_left = pixmap_pos - self.drag_offset
            self.current_rect.moveTo(new_top_left)
            self._update_display()
        elif self.resizing:
            # Resizing rectangle
            if self.resize_handle == "top_left":
                self.current_rect.setTopLeft(pixmap_pos)
            elif self.resize_handle == "top_right":
                self.current_rect.setTopRight(pixmap_pos)
            elif self.resize_handle == "bottom_left":
                self.current_rect.setBottomLeft(pixmap_pos)
            elif self.resize_handle == "bottom_right":
                self.current_rect.setBottomRight(pixmap_pos)
            self.current_rect = self.current_rect.normalized()
            self._update_display()
        else:
            # Update cursor based on position
            if not self.current_rect.isNull():
                if self._get_resize_handle(pixmap_pos):
                    self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                elif self._is_inside_rect(pixmap_pos):
                    self.setCursor(Qt.CursorShape.SizeAllCursor)
                else:
                    self.setCursor(Qt.CursorShape.CrossCursor)

    def mouseReleaseEvent(self, event):
        """Handle mouse release to finish drawing, moving, or resizing."""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.drawing:
                self.drawing = False
                self.end_point = self._map_to_pixmap_coords(event.pos())
                self.current_rect = QRect(self.start_point, self.end_point).normalized()
                self._update_display()

                # Emit the ROI in original image coordinates
                roi = self._get_roi_in_image_coords()
                if roi:
                    self.roi_selected.emit(roi)
            elif self.moving:
                self.moving = False
                self.setCursor(Qt.CursorShape.CrossCursor)
                # Emit updated ROI
                roi = self._get_roi_in_image_coords()
                if roi:
                    self.roi_selected.emit(roi)
            elif self.resizing:
                self.resizing = False
                self.resize_handle = None
                self.setCursor(Qt.CursorShape.CrossCursor)
                # Emit updated ROI
                roi = self._get_roi_in_image_coords()
                if roi:
                    self.roi_selected.emit(roi)

    def _get_roi_in_image_coords(self):
        """Convert the drawn rectangle to original image coordinates."""
        if self.current_rect.isNull() or not self.image_size:
            return None

        # Get the scale factor between display and original image
        display_pixmap = self.pixmap()
        if not display_pixmap:
            return None

        scale_x = self.image_size[0] / display_pixmap.width()
        scale_y = self.image_size[1] / display_pixmap.height()

        # Convert to image coordinates (no offset needed as we're already in pixmap coords)
        x = int(self.current_rect.x() * scale_x)
        y = int(self.current_rect.y() * scale_y)
        w = int(self.current_rect.width() * scale_x)
        h = int(self.current_rect.height() * scale_y)

        # Clamp to image bounds
        x = max(0, min(x, self.image_size[0]))
        y = max(0, min(y, self.image_size[1]))
        w = max(0, min(w, self.image_size[0] - x))
        h = max(0, min(h, self.image_size[1] - y))

        return (x, y, w, h)

    def get_roi(self):
        """Get the current ROI coordinates in original image space."""
        return self._get_roi_in_image_coords()

    def clear_roi(self):
        """Clear the current ROI selection."""
        self.current_rect = QRect()
        self._update_display()

    def resizeEvent(self, event):
        """Handle widget resize."""
        super().resizeEvent(event)
        self._update_display()


class ROISelectorDialog(QDialog):
    """Dialog for selecting ROI from a video's first frame."""

    def __init__(self, video_path: str, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.roi = None
        self.video_info = None
        self.frame_skip = 15  # Default frame skip value
        self.start_time = 0.0  # Start time in seconds
        self.end_time = None  # End time in seconds (None = end of video)

        self.setWindowTitle("Select Region of Interest")
        self.setModal(True)
        self.resize(1000, 800)

        self._setup_ui()
        self._load_first_frame()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # ROI Selector
        self.roi_label = ROISelectorLabel()
        self.roi_label.setMinimumSize(800, 500)
        self.roi_label.roi_selected.connect(self._on_roi_selected)
        layout.addWidget(self.roi_label)

        # Instructions
        instructions = QLabel(
            "Click and drag to draw a rectangle around the area where faces should be detected.\n"
            "This helps improve performance and accuracy by focusing on relevant regions."
        )
        instructions.setStyleSheet("color: #aaa; padding: 10px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # FPS Settings Section
        fps_settings_widget = QWidget()
        fps_settings_widget.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        fps_settings_layout = QVBoxLayout(fps_settings_widget)
        fps_settings_layout.setSpacing(8)

        # Title
        fps_title = QLabel("Processing Settings")
        fps_title.setStyleSheet(
            "color: #fff; font-weight: bold; font-size: 13px; background: none; border: none; padding: 0;"
        )
        fps_settings_layout.addWidget(fps_title)

        # Video FPS info
        self.video_fps_label = QLabel("Video FPS: Detecting...")
        self.video_fps_label.setStyleSheet(
            "color: #aaa; font-size: 12px; background: none; border: none; padding: 0;"
        )
        fps_settings_layout.addWidget(self.video_fps_label)

        # Frame skip settings
        frame_skip_layout = QHBoxLayout()
        frame_skip_layout.setSpacing(10)

        frame_skip_label = QLabel("Frame Skip:")
        frame_skip_label.setStyleSheet(
            "color: #ccc; font-size: 12px; background: none; border: none; padding: 0;"
        )
        frame_skip_layout.addWidget(frame_skip_label)

        self.frame_skip_spinbox = QSpinBox()
        self.frame_skip_spinbox.setMinimum(1)
        self.frame_skip_spinbox.setMaximum(120)
        self.frame_skip_spinbox.setValue(15)
        self.frame_skip_spinbox.setSuffix(" frames")
        self.frame_skip_spinbox.setStyleSheet("""
            QSpinBox {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                color: #fff;
                padding: 4px 8px;
                min-width: 100px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #4d4d4d;
                border: none;
                width: 16px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #5d5d5d;
            }
        """)
        self.frame_skip_spinbox.valueChanged.connect(self._update_scan_fps)
        frame_skip_layout.addWidget(self.frame_skip_spinbox)

        self.scan_fps_label = QLabel("→ Scan Rate: Calculating...")
        self.scan_fps_label.setStyleSheet(
            "color: #00ff00; font-size: 12px; background: none; border: none; padding: 0;"
        )
        frame_skip_layout.addWidget(self.scan_fps_label)

        frame_skip_layout.addStretch()

        # Preset buttons
        preset_label = QLabel("Presets:")
        preset_label.setStyleSheet(
            "color: #ccc; font-size: 12px; background: none; border: none; padding: 0;"
        )
        frame_skip_layout.addWidget(preset_label)

        fast_btn = QPushButton("Fast (30)")
        fast_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 12px;
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 3px;
                color: #fff;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
        """)
        fast_btn.clicked.connect(lambda: self.frame_skip_spinbox.setValue(30))
        frame_skip_layout.addWidget(fast_btn)

        balanced_btn = QPushButton("Balanced (15)")
        balanced_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 12px;
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 3px;
                color: #fff;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
        """)
        balanced_btn.clicked.connect(lambda: self.frame_skip_spinbox.setValue(15))
        frame_skip_layout.addWidget(balanced_btn)

        accurate_btn = QPushButton("Accurate (5)")
        accurate_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 12px;
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 3px;
                color: #fff;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
        """)
        accurate_btn.clicked.connect(lambda: self.frame_skip_spinbox.setValue(5))
        frame_skip_layout.addWidget(accurate_btn)

        fps_settings_layout.addLayout(frame_skip_layout)

        # Time range settings with visual timeline
        time_range_label = QLabel("Scan Time Range:")
        time_range_label.setStyleSheet(
            "color: #ccc; font-size: 12px; background: none; border: none; padding: 0; margin-top: 8px;"
        )
        fps_settings_layout.addWidget(time_range_label)

        # Visual timeline
        self.timeline_widget = TimelineWidget()
        fps_settings_layout.addWidget(self.timeline_widget)

        # Duration info
        self.duration_info_label = QLabel(
            "Drag the green (start) and red (end) markers to select time range"
        )
        self.duration_info_label.setStyleSheet(
            "color: #888; font-size: 11px; background: none; border: none; padding: 0;"
        )
        fps_settings_layout.addWidget(self.duration_info_label)

        layout.addWidget(fps_settings_widget)

        # Buttons
        button_layout = QHBoxLayout()

        self.clear_btn = QPushButton("Clear Selection")
        self.clear_btn.clicked.connect(self.roi_label.clear_roi)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                color: #fff;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
        """)

        self.full_frame_btn = QPushButton("Use Full Frame")
        self.full_frame_btn.clicked.connect(self._use_full_frame)
        self.full_frame_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                color: #fff;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
        """)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                color: #fff;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
        """)

        self.process_btn = QPushButton("Start Processing")
        self.process_btn.clicked.connect(self._start_processing)
        self.process_btn.setEnabled(False)
        self.process_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #007acc;
                border: none;
                border-radius: 4px;
                color: #fff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #666;
            }
        """)

        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.full_frame_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.process_btn)

        layout.addLayout(button_layout)

    def _load_first_frame(self):
        """Load the first frame of the video."""
        cap = cv2.VideoCapture(self.video_path)

        if not cap.isOpened():
            QMessageBox.critical(self, "Error", "Failed to open video file.")
            self.reject()
            return

        # Get video info
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0

        self.video_info = {
            "fps": fps,
            "width": width,
            "height": height,
            "frame_count": frame_count,
            "duration": duration,
        }

        # Update FPS display
        self.video_fps_label.setText(f"Video FPS: {fps:.2f} fps")
        self._update_scan_fps()

        # Initialize timeline widget
        self.timeline_widget.set_duration(duration)

        # Read first frame
        ret, frame = cap.read()
        cap.release()

        if ret:
            self.roi_label.set_image(frame)
        else:
            QMessageBox.critical(self, "Error", "Failed to read first frame.")
            self.reject()

    def _update_scan_fps(self):
        """Update the scan FPS label based on current frame skip setting."""
        if self.video_info and self.video_info["fps"] > 0:
            frame_skip = self.frame_skip_spinbox.value()
            scan_fps = self.video_info["fps"] / frame_skip
            self.scan_fps_label.setText(f"→ Scan Rate: {scan_fps:.2f} fps")
        else:
            self.scan_fps_label.setText("→ Scan Rate: Calculating...")

    def _on_roi_selected(self, roi):
        """Handle ROI selection."""
        self.roi = roi
        self.process_btn.setEnabled(True)

    def _use_full_frame(self):
        """Use the entire frame as ROI."""
        if self.video_info:
            self.roi = (0, 0, self.video_info["width"], self.video_info["height"])
            self.process_btn.setEnabled(True)
            QMessageBox.information(
                self,
                "Full Frame Selected",
                "The entire video frame will be used for face detection.",
            )

    def _start_processing(self):
        """Accept dialog and start processing."""
        if self.roi:
            # Store the frame skip value
            self.frame_skip = self.frame_skip_spinbox.value()

            # Get time range from timeline widget
            self.start_time, self.end_time = self.timeline_widget.get_range()

            self.accept()
        else:
            QMessageBox.warning(
                self, "No ROI Selected", "Please select a region or use the full frame."
            )

    def get_roi(self):
        """Get the selected ROI coordinates."""
        return self.roi

    def get_video_info(self):
        """Get video metadata."""
        return self.video_info

    def get_frame_skip(self):
        """Get the selected frame skip value."""
        return self.frame_skip

    def get_time_range(self):
        """Get the selected time range (start_time, end_time)."""
        return (self.start_time, self.end_time)

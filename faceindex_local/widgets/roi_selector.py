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
    QVBoxLayout,
    QWidget,
)


class ROISelectorLabel(QLabel):
    """Custom QLabel that handles mouse events for drawing ROI rectangle."""

    roi_selected = pyqtSignal(tuple)  # Emits (x, y, w, h) in image coordinates

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)

        # Drawing state
        self.drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.current_rect = QRect()

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

        # Create a copy to draw on
        pixmap = self.original_pixmap.copy()

        # Draw the rectangle if it exists
        if not self.current_rect.isNull():
            painter = QPainter(pixmap)

            # Semi-transparent overlay outside ROI
            painter.fillRect(pixmap.rect(), QColor(0, 0, 0, 120))
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(self.current_rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_SourceOver
            )

            # Green border for ROI
            pen = QPen(QColor(0, 255, 0), 3, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
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

        # Scale to fit widget
        scaled_pixmap = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.setPixmap(scaled_pixmap)

    def mousePressEvent(self, event):
        """Handle mouse press to start drawing."""
        if event.button() == Qt.MouseButton.LeftButton and self.original_pixmap:
            self.drawing = True
            self.start_point = event.pos()
            self.current_rect = QRect(self.start_point, self.start_point)
            self._update_display()

    def mouseMoveEvent(self, event):
        """Handle mouse move to update rectangle."""
        if self.drawing and self.original_pixmap:
            self.end_point = event.pos()
            self.current_rect = QRect(self.start_point, self.end_point).normalized()
            self._update_display()

    def mouseReleaseEvent(self, event):
        """Handle mouse release to finish drawing."""
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False
            self.end_point = event.pos()
            self.current_rect = QRect(self.start_point, self.end_point).normalized()
            self._update_display()

            # Emit the ROI in original image coordinates
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

        # Calculate offset (centered image)
        offset_x = (self.width() - display_pixmap.width()) // 2
        offset_y = (self.height() - display_pixmap.height()) // 2

        # Convert to image coordinates
        x = int((self.current_rect.x() - offset_x) * scale_x)
        y = int((self.current_rect.y() - offset_y) * scale_y)
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

        self.setWindowTitle("Select Region of Interest")
        self.setModal(True)
        self.resize(1000, 700)

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

        # Read first frame
        ret, frame = cap.read()
        cap.release()

        if ret:
            self.roi_label.set_image(frame)
        else:
            QMessageBox.critical(self, "Error", "Failed to read first frame.")
            self.reject()

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

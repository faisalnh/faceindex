"""
Gallery Widget - Displays face thumbnails in a grid layout.
"""

from pathlib import Path

import cv2
from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class CircularLabel(QLabel):
    """Custom QLabel that displays images in circular frame."""

    def __init__(self, size=120, parent=None):
        super().__init__(parent)
        self.image_size = size
        self.setFixedSize(size, size)
        self._pixmap = None

    def set_circular_pixmap(self, pixmap: QPixmap):
        """Set pixmap and crop to circular shape."""
        if pixmap.isNull():
            return

        # Scale pixmap to size
        scaled = pixmap.scaled(
            self.image_size,
            self.image_size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )

        # Create circular mask
        target = QPixmap(self.image_size, self.image_size)
        target.fill(Qt.GlobalColor.transparent)

        painter = QPainter(target)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Create circular path
        path = QPainterPath()
        path.addEllipse(0, 0, self.image_size, self.image_size)

        painter.setClipPath(path)

        # Center the image
        x = (self.image_size - scaled.width()) // 2
        y = (self.image_size - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)
        painter.end()

        self._pixmap = target
        self.setPixmap(target)


class PersonCard(QFrame):
    """Card widget representing a person (cluster) with thumbnail and info."""

    clicked = pyqtSignal(int)  # person_id
    rename_requested = pyqtSignal(int)  # person_id
    merge_requested = pyqtSignal(int)  # person_id

    def __init__(
        self,
        person_id: int,
        name: str,
        thumbnail_path: str,
        face_count: int,
        parent=None,
    ):
        super().__init__(parent)
        self.person_id = person_id
        self.name = name
        self.thumbnail_path = thumbnail_path
        self.face_count = face_count

        self._setup_ui()
        self._setup_style()

    def _setup_ui(self):
        """Set up the card UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Circular thumbnail
        self.thumbnail = CircularLabel(size=100)
        self._load_thumbnail()
        self.thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.thumbnail, alignment=Qt.AlignmentFlag.AlignCenter)

        # Name label
        self.name_label = QLabel(self.name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #ffffff;
        """)
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label)

        # Face count label
        count_text = (
            f"{self.face_count} appearance{'s' if self.face_count != 1 else ''}"
        )
        self.count_label = QLabel(count_text)
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setStyleSheet("""
            font-size: 11px;
            color: #aaaaaa;
        """)
        layout.addWidget(self.count_label)

    def _load_thumbnail(self):
        """Load and display the thumbnail image."""
        if Path(self.thumbnail_path).exists():
            # Load with OpenCV and convert to Qt
            img = cv2.imread(self.thumbnail_path)
            if img is not None:
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                bytes_per_line = ch * w
                q_img = QImage(
                    rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888
                )
                pixmap = QPixmap.fromImage(q_img)
                self.thumbnail.set_circular_pixmap(pixmap)
        else:
            # Placeholder if thumbnail doesn't exist
            self.thumbnail.setText("No Image")
            self.thumbnail.setStyleSheet("background-color: #3d3d3d; color: #888;")

    def _setup_style(self):
        """Set up the card styling."""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            PersonCard {
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
                border-radius: 8px;
            }
            PersonCard:hover {
                border: 2px solid #007acc;
                background-color: #333333;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        """Handle mouse click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.person_id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle double click - open timeline."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.person_id)

    def contextMenuEvent(self, event):
        """Show context menu on right click."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
            }
            QMenu::item:selected {
                background-color: #007acc;
            }
        """)

        rename_action = menu.addAction("Rename")
        merge_action = menu.addAction("Merge with...")

        action = menu.exec(event.globalPos())

        if action == rename_action:
            self.rename_requested.emit(self.person_id)
        elif action == merge_action:
            self.merge_requested.emit(self.person_id)

    def update_name(self, name: str):
        """Update the displayed name."""
        self.name = name
        self.name_label.setText(name)


class GalleryWidget(QWidget):
    """Gallery widget displaying all detected persons in a grid."""

    person_selected = pyqtSignal(int)  # person_id
    person_renamed = pyqtSignal(int, str)  # person_id, new_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.person_cards = {}
        self._setup_ui()

    def _setup_ui(self):
        """Set up the gallery UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet("background-color: #252525; padding: 15px;")
        header_layout = QHBoxLayout(header)

        title = QLabel("Detected People")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        self.count_label = QLabel("0 people found")
        self.count_label.setStyleSheet("font-size: 12px; color: #aaaaaa;")
        header_layout.addWidget(self.count_label)

        main_layout.addWidget(header)

        # Scroll area for grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1e1e1e;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666666;
            }
        """)

        # Container for grid
        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(15, 15, 15, 15)

        scroll.setWidget(self.container)
        main_layout.addWidget(scroll)

    def add_person(
        self, person_id: int, name: str, thumbnail_path: str, face_count: int
    ):
        """Add a person card to the gallery."""
        card = PersonCard(person_id, name, thumbnail_path, face_count)
        card.clicked.connect(self.person_selected.emit)
        card.rename_requested.connect(self._handle_rename)

        self.person_cards[person_id] = card

        # Calculate grid position
        num_cards = len(self.person_cards)
        cols = 4  # Number of columns
        row = (num_cards - 1) // cols
        col = (num_cards - 1) % cols

        self.grid_layout.addWidget(card, row, col)

        # Update count
        self._update_count()

    def clear(self):
        """Clear all person cards."""
        for card in self.person_cards.values():
            card.deleteLater()
        self.person_cards.clear()
        self._update_count()

    def _update_count(self):
        """Update the people count label."""
        count = len(self.person_cards)
        text = f"{count} {'person' if count == 1 else 'people'} found"
        self.count_label.setText(text)

    def _handle_rename(self, person_id: int):
        """Handle rename request."""
        card = self.person_cards.get(person_id)
        if not card:
            return

        new_name, ok = QInputDialog.getText(
            self, "Rename Person", "Enter new name:", text=card.name
        )

        if ok and new_name:
            card.update_name(new_name)
            self.person_renamed.emit(person_id, new_name)


class EmptyGalleryWidget(QWidget):
    """Widget displayed when gallery is empty."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the empty state UI."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon/placeholder
        icon_label = QLabel("📹")
        icon_label.setStyleSheet("font-size: 64px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Message
        message = QLabel("No videos processed yet")
        message.setStyleSheet("""
            font-size: 18px;
            color: #888888;
            margin-top: 20px;
        """)
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message)

        # Instruction
        instruction = QLabel("Click 'Add Video' to get started")
        instruction.setStyleSheet("""
            font-size: 14px;
            color: #666666;
            margin-top: 10px;
        """)
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instruction)

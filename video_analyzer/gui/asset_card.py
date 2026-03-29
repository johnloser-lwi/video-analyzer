"""Individual asset card widget for the results grid."""

import os
from pathlib import Path

from PyQt5.QtCore import Qt, QUrl, QMimeData, QPoint, QSize, pyqtSignal, QThreadPool
from PyQt5.QtGui import QPixmap, QDrag
from PyQt5.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy,
)

from .search_engine import SearchResult
from .thumbnail_cache import generate_thumbnail, get_cached_thumbnail, ThumbnailWorker


class AssetCard(QFrame):
    """
    A clickable card showing a media asset's thumbnail, name, and metadata.
    Supports drag-and-drop to external programs.
    """
    clicked = pyqtSignal(object)  # Emits the SearchResult

    CARD_WIDTH = 220
    THUMB_HEIGHT = 140

    def __init__(self, result: SearchResult, parent=None):
        super().__init__(parent)
        self.result = result
        self.setObjectName("assetCard")
        self.setFixedWidth(self.CARD_WIDTH)
        self.setCursor(Qt.PointingHandCursor)
        self._drag_start_pos = None
        self._selected = False
        self._thumb_pixmap = None

        self._setup_ui()
        self._load_thumbnail()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(0)

        # Thumbnail
        self.thumb_label = QLabel()
        self.thumb_label.setObjectName("thumbnailLabel")
        self.thumb_label.setFixedSize(self.CARD_WIDTH - 12, self.THUMB_HEIGHT)
        self.thumb_label.setAlignment(Qt.AlignCenter)
        self.thumb_label.setScaledContents(False)
        layout.addWidget(self.thumb_label)

        # Media type badge + duration
        badge_row = QHBoxLayout()
        badge_row.setContentsMargins(4, 6, 4, 0)
        badge_row.setSpacing(6)

        media_type = self.result.media_type
        badge = QLabel()
        if media_type == "video":
            badge.setText("🎬 VIDEO")
            badge.setObjectName("cardBadge")
        elif media_type == "image":
            badge.setText("📷 IMAGE")
            badge.setObjectName("cardBadgeImage")
        elif media_type == "gif":
            badge.setText("🎞️ GIF")
            badge.setObjectName("cardBadgeGif")
        else:
            badge.setText(media_type.upper())
            badge.setObjectName("cardBadge")
        badge_row.addWidget(badge)

        # Duration for videos
        if media_type == "video" and self.result.duration_formatted:
            dur_label = QLabel(self.result.duration_formatted)
            dur_label.setObjectName("cardMeta")
            badge_row.addWidget(dur_label)

        badge_row.addStretch()

        # Resolution
        if self.result.resolution_w and self.result.resolution_h:
            res_label = QLabel(f"{self.result.resolution_w}×{self.result.resolution_h}")
            res_label.setObjectName("cardMeta")
            badge_row.addWidget(res_label)

        layout.addLayout(badge_row)

        # Filename
        name_label = QLabel(self._truncate(self.result.filename, 28))
        name_label.setObjectName("cardFilename")
        name_label.setToolTip(self.result.filename)
        layout.addWidget(name_label)

        # Size + source
        meta_text = self.result.file_size_human
        if self.result.db_name:
            meta_text += f"  •  {self.result.db_name}"
        meta_label = QLabel(meta_text)
        meta_label.setObjectName("cardMeta")
        layout.addWidget(meta_label)

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)

    def _load_thumbnail(self):
        """Load thumbnail from cache or spawn worker to generate it."""
        db_folder = Path(self.result.db_folder)
        thumb_path = get_cached_thumbnail(self.result.filepath, db_folder)

        if thumb_path and thumb_path.exists():
            self._apply_thumbnail(thumb_path)
        else:
            # Set placeholder
            self.thumb_label.setText("Generating...")
            self.thumb_label.setStyleSheet(
                "color: #5a7a9a; font-size: 12px; font-style: italic; background-color: #1a2332;"
            )

            # Spawn worker
            worker = ThumbnailWorker(
                self.result.filepath,
                db_folder,
                self.result.media_type,
            )
            worker.signals.finished.connect(self._on_thumbnail_ready)
            QThreadPool.globalInstance().start(worker)

    def _on_thumbnail_ready(self, filepath: str, thumb_path: str):
        # Prevent race conditions if the UI updates out of order
        if filepath != self.result.filepath:
            return

        if thumb_path:
            self.thumb_label.setStyleSheet("")  # clear placeholder style
            self._apply_thumbnail(Path(thumb_path))
        else:
            self.thumb_label.setText("No Preview")
            self.thumb_label.setStyleSheet(
                "color: #3a5a7e; font-size: 11px; background-color: #0d1520;"
            )

    def _apply_thumbnail(self, thumb_path: Path):
        pixmap = QPixmap(str(thumb_path))
        scaled = pixmap.scaled(
            self.CARD_WIDTH - 12,
            self.THUMB_HEIGHT,
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation,
        )
        # Center-crop to exact size
        if scaled.width() > self.CARD_WIDTH - 12 or scaled.height() > self.THUMB_HEIGHT:
            x = (scaled.width() - (self.CARD_WIDTH - 12)) // 2
            y = (scaled.height() - self.THUMB_HEIGHT) // 2
            scaled = scaled.copy(
                max(0, x), max(0, y),
                self.CARD_WIDTH - 12, self.THUMB_HEIGHT
            )
        self.thumb_label.setPixmap(scaled)
        self._thumb_pixmap = scaled

    def set_selected(self, selected: bool):
        """Update the visual selection state."""
        self._selected = selected
        if selected:
            self.setStyleSheet(
                "QFrame#assetCard { border: 2px solid #06d6a0; background-color: #1a2a3e; }"
            )
        else:
            self.setStyleSheet("")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.pos()
            self.clicked.emit(self.result)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if self._drag_start_pos is None:
            return

        # Check minimum drag distance
        distance = (event.pos() - self._drag_start_pos).manhattanLength()
        if distance < 15:
            return

        # Initiate drag-and-drop to external programs
        filepath = self.result.filepath
        if not Path(filepath).exists():
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(filepath)])
        drag.setMimeData(mime_data)

        # Set drag preview pixmap
        if self._thumb_pixmap:
            preview = self._thumb_pixmap.scaled(
                120, 80,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            drag.setPixmap(preview)
            drag.setHotSpot(QPoint(preview.width() // 2, preview.height() // 2))

        drag.exec_(Qt.CopyAction)

    @staticmethod
    def _truncate(text: str, max_len: int) -> str:
        if len(text) <= max_len:
            return text
        name, ext = os.path.splitext(text)
        available = max_len - len(ext) - 2
        if available < 4:
            return text[:max_len - 1] + "…"
        return name[:available] + "…" + ext

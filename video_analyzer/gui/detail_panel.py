"""Detail panel showing full metadata and AI descriptions for a selected asset."""

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QScrollArea, QWidget,
    QSizePolicy,
)

from .search_engine import SearchResult
from .thumbnail_cache import generate_thumbnail, get_cached_thumbnail


class DetailPanel(QFrame):
    """Right-side panel showing full info for a selected asset."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("detailPanel")
        self.setFixedWidth(330)

        # Scroll area for content
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        self._layout = QVBoxLayout(self._content)
        self._layout.setContentsMargins(0, 0, 0, 16)
        self._layout.setSpacing(0)

        scroll.setWidget(self._content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self._show_empty()

    def _show_empty(self):
        """Show empty state."""
        self._clear()
        label = QLabel("Select an asset to view details")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #3a5a7e; font-size: 13px; padding: 40px;")
        label.setWordWrap(True)
        self._layout.addWidget(label)
        self._layout.addStretch()

    def _clear(self):
        """Remove all widgets from layout."""
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def show_result(self, result: SearchResult):
        """Display full details for a search result."""
        self._clear()

        # Preview image
        db_folder = Path(result.db_folder)
        thumb = get_cached_thumbnail(result.filepath, db_folder)
        if thumb is None:
            thumb = generate_thumbnail(result.filepath, db_folder, result.media_type)

        if thumb and thumb.exists():
            pixmap = QPixmap(str(thumb))
            preview = QLabel()
            preview.setObjectName("detailPreview")
            preview.setAlignment(Qt.AlignCenter)
            scaled = pixmap.scaled(
                280, 180,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            preview.setPixmap(scaled)
            preview.setFixedHeight(180)
            preview.setContentsMargins(10, 10, 10, 0)
            self._layout.addWidget(preview)

        # Filename
        title = QLabel(result.filename)
        title.setObjectName("detailTitle")
        title.setWordWrap(True)
        self._layout.addWidget(title)

        # ── File Info ──
        self._add_section("FILE INFO")
        self._add_field("Path", result.relative_path)
        self._add_field("Size", result.file_size_human)
        self._add_field("Type", result.media_type.upper())
        self._add_field("Format", result.container_format)
        self._add_field("Source", result.db_name)

        # ── Technical ──
        if result.media_type == "video":
            self._add_section("TECHNICAL")
            if result.duration_formatted:
                self._add_field("Duration", result.duration_formatted)
            if result.resolution_w:
                self._add_field("Resolution", f"{result.resolution_w}×{result.resolution_h}")
            if result.video_codec:
                self._add_field("Video Codec", result.video_codec)
            if result.audio_codec:
                self._add_field("Audio Codec", result.audio_codec)
            if result.framerate:
                self._add_field("Frame Rate", f"{result.framerate} fps")
            if result.bitrate:
                self._add_field("Bitrate", f"{result.bitrate // 1000} kbps")
        elif result.resolution_w:
            self._add_section("TECHNICAL")
            self._add_field("Resolution", f"{result.resolution_w}×{result.resolution_h}")
            if result.video_codec:
                self._add_field("Codec", result.video_codec)

        # ── AI Analysis ──
        has_ai = any([
            result.content_summary, result.scene_description,
            result.key_objects, result.actions,
            result.setting, result.screen_text,
        ])

        if has_ai:
            self._add_section("AI ANALYSIS")
            if result.content_summary:
                self._add_field("Summary", result.content_summary)
            if result.scene_description:
                self._add_field("Scene", result.scene_description)
            if result.key_objects:
                self._add_field("Objects", result.key_objects)
            if result.actions:
                self._add_field("Actions", result.actions)
            if result.setting:
                self._add_field("Setting", result.setting)
            if result.screen_text and result.screen_text.lower() != "none":
                self._add_field("Text", result.screen_text)

        self._layout.addStretch()

    def _add_section(self, title: str):
        label = QLabel(title)
        label.setObjectName("detailSectionTitle")
        self._layout.addWidget(label)

    def _add_field(self, label: str, value: str):
        if not value:
            return
        field = QLabel(f"<b style='color:#7a9abe'>{label}:</b>  {value}")
        field.setObjectName("detailValue")
        field.setWordWrap(True)
        field.setTextFormat(Qt.RichText)
        self._layout.addWidget(field)

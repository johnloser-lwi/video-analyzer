"""Sidebar panel for managing database connections."""

import json
from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QFileDialog, QWidget,
    QScrollArea, QSizePolicy,
)

from .search_engine import SearchEngine

# Settings file for persisting DB connections
SETTINGS_DIR = Path.home() / ".video_analyzer"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"


def load_settings() -> dict:
    """Load saved settings from disk."""
    try:
        if SETTINGS_FILE.exists():
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"databases": []}


def save_settings(settings: dict):
    """Persist settings to disk."""
    try:
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(
            json.dumps(settings, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass


class DatabasePanel(QFrame):
    """Sidebar panel showing connected databases with add/remove controls."""

    databases_changed = pyqtSignal()  # Emitted when DBs are added/removed/toggled

    def __init__(self, search_engine: SearchEngine, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebarFrame")
        self.search_engine = search_engine
        self.setFixedWidth(240)

        self._checkboxes = {}  # path -> QCheckBox
        self._setup_ui()
        self._load_saved_databases()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title
        title = QLabel("DATABASES")
        title.setObjectName("sidebarTitle")
        layout.addWidget(title)

        # Add button
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(12, 8, 12, 8)

        add_btn = QPushButton("+ Add Folder")
        add_btn.setObjectName("addDbBtn")
        add_btn.clicked.connect(self._on_add_database)
        add_btn.setToolTip("Select a folder containing video_catalog.db")
        btn_layout.addWidget(add_btn)

        layout.addWidget(btn_container)

        # Scrollable list of databases
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._list_container = QWidget()
        self._list_container.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(8, 4, 8, 8)
        self._list_layout.setSpacing(4)
        self._list_layout.addStretch()

        scroll.setWidget(self._list_container)
        layout.addWidget(scroll, 1)

    def _on_add_database(self):
        """Open a folder picker to add a database."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select folder containing video_catalog.db",
            "",
            QFileDialog.ShowDirsOnly,
        )
        if not folder:
            return

        db_path = Path(folder) / "video_catalog.db"
        if not db_path.exists():
            return

        if self.search_engine.add_database(str(db_path)):
            self._add_db_widget(str(db_path.resolve()))
            self._save_databases()
            self.databases_changed.emit()

    def _add_db_widget(self, db_path: str):
        """Add a database item widget to the sidebar."""
        if db_path in self._checkboxes:
            return

        db_info = None
        for info in self.search_engine.get_databases():
            if info["path"] == db_path:
                db_info = info
                break

        if not db_info:
            return

        item_frame = QFrame()
        item_frame.setObjectName("dbItem")
        item_layout = QVBoxLayout(item_frame)
        item_layout.setContentsMargins(4, 4, 4, 4)
        item_layout.setSpacing(2)

        # Checkbox + name row
        top_row = QHBoxLayout()
        checkbox = QCheckBox(db_info["name"])
        checkbox.setChecked(True)
        checkbox.setToolTip(db_info["folder"])
        checkbox.stateChanged.connect(
            lambda state, p=db_path: self._on_toggle(p, state)
        )
        top_row.addWidget(checkbox)
        top_row.addStretch()

        # Remove button
        remove_btn = QPushButton("✕")
        remove_btn.setObjectName("removeDbBtn")
        remove_btn.setFixedSize(22, 22)
        remove_btn.setToolTip("Remove this database")
        remove_btn.clicked.connect(
            lambda checked, p=db_path, f=item_frame: self._on_remove(p, f)
        )
        top_row.addWidget(remove_btn)
        item_layout.addLayout(top_row)

        # File count
        count_label = QLabel(f"  {db_info['count']} files")
        count_label.setStyleSheet("color: #4a6a8a; font-size: 10px;")
        item_layout.addWidget(count_label)

        self._checkboxes[db_path] = checkbox

        # Insert before the stretch
        idx = self._list_layout.count() - 1
        self._list_layout.insertWidget(idx, item_frame)

    def _on_toggle(self, db_path: str, state: int):
        """Toggle a database's enabled state."""
        enabled = state == Qt.Checked
        self.search_engine.toggle_database(db_path, enabled)
        self.databases_changed.emit()

    def _on_remove(self, db_path: str, widget: QFrame):
        """Remove a database connection."""
        self.search_engine.remove_database(db_path)
        widget.setParent(None)
        widget.deleteLater()
        self._checkboxes.pop(db_path, None)
        self._save_databases()
        self.databases_changed.emit()

    def _save_databases(self):
        """Save current database list to settings."""
        dbs = []
        for info in self.search_engine.get_databases():
            dbs.append({
                "path": info["path"],
                "name": info["name"],
            })
        save_settings({"databases": dbs})

    def _load_saved_databases(self):
        """Restore previously connected databases."""
        settings = load_settings()
        for db in settings.get("databases", []):
            path = db.get("path", "")
            name = db.get("name", "")
            if path and Path(path).exists():
                if self.search_engine.add_database(path, name):
                    self._add_db_widget(path)

        if self.search_engine.get_databases():
            self.databases_changed.emit()

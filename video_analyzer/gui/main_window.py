"""Main window for the Video Analyzer search GUI."""

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QSplitter, QStatusBar, QLabel,
)

from .database_panel import DatabasePanel
from .detail_panel import DetailPanel
from .results_grid import ResultsGrid
from .search_engine import SearchEngine, SearchResult


class MainWindow(QMainWindow):
    """Main application window with search, results grid, and detail panel."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Analyzer — Media Search")
        self.setMinimumSize(1100, 700)
        self.resize(1400, 850)

        # Search engine
        self.search_engine = SearchEngine()

        # Search debounce timer
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self._execute_search)

        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Top bar (search) ──────────────────────────
        top_bar = QWidget()
        top_bar.setStyleSheet("background-color: #0b1219; padding: 0;")
        top_bar.setFixedHeight(60)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 10, 16, 10)
        top_layout.setSpacing(12)

        # App icon/title
        app_label = QLabel("🔍")
        app_label.setStyleSheet("font-size: 22px; background: transparent;")
        top_layout.addWidget(app_label)

        # Search input
        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("searchBar")
        self.search_bar.setPlaceholderText("Search by keyword across all databases...")
        self.search_bar.textChanged.connect(self._on_search_changed)
        self.search_bar.setClearButtonEnabled(True)
        top_layout.addWidget(self.search_bar, 1)

        # Result count label
        self.result_count_label = QLabel("")
        self.result_count_label.setStyleSheet(
            "color: #5a7a9a; font-size: 12px; background: transparent; padding-right: 8px;"
        )
        top_layout.addWidget(self.result_count_label)

        main_layout.addWidget(top_bar)

        # ── Content area (splitter) ───────────────────
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        # Left sidebar: database panel
        self.db_panel = DatabasePanel(self.search_engine)
        self.db_panel.databases_changed.connect(self._on_databases_changed)
        splitter.addWidget(self.db_panel)

        # Center: results grid
        self.results_grid = ResultsGrid()
        self.results_grid.card_selected.connect(self._on_card_selected)
        splitter.addWidget(self.results_grid)

        # Right: detail panel
        self.detail_panel = DetailPanel()
        splitter.addWidget(self.detail_panel)

        # Set splitter proportions
        splitter.setStretchFactor(0, 0)  # sidebar: fixed
        splitter.setStretchFactor(1, 1)  # results: stretch
        splitter.setStretchFactor(2, 0)  # detail: fixed

        main_layout.addWidget(splitter, 1)

        # ── Status bar ────────────────────────────────
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status()

    def _on_search_changed(self, text: str):
        """Debounce search input."""
        self._search_timer.start()

    def _on_databases_changed(self):
        """When databases are added/removed/toggled, refresh results."""
        self._execute_search()
        self._update_status()

    def _execute_search(self):
        """Run the actual search and display results."""
        query = self.search_bar.text().strip()
        results = self.search_engine.search(query)
        self.results_grid.display_results(results)

        # Update counts
        count = len(results)
        if query:
            self.result_count_label.setText(f"{count} result{'s' if count != 1 else ''}")
        else:
            self.result_count_label.setText(f"{count} file{'s' if count != 1 else ''}")

        self._update_status()

    def _on_card_selected(self, result: SearchResult):
        """Show details for the selected asset."""
        self.detail_panel.show_result(result)

    def _update_status(self):
        """Update the status bar text."""
        dbs = self.search_engine.get_databases()
        active = sum(1 for d in dbs if d["enabled"])
        total_files = sum(d["count"] for d in dbs if d["enabled"])
        self.status_bar.showMessage(
            f"  {active} database{'s' if active != 1 else ''} connected  •  "
            f"{total_files} total files"
        )

    def closeEvent(self, event):
        """Clean up database connections on close."""
        self.search_engine.close_all()
        super().closeEvent(event)

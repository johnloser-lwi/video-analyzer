"""Scrollable flow-layout grid for displaying asset cards."""

from typing import List, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout, QLabel, QSizePolicy,
)

from .asset_card import AssetCard
from .search_engine import SearchResult


class FlowLayout:
    """
    Simple flow layout manager that arranges cards in rows,
    wrapping to the next row when the available width is exceeded.
    """
    def __init__(self, parent_widget: QWidget, spacing: int = 12):
        self.parent_widget = parent_widget
        self.spacing = spacing
        self.items: List[AssetCard] = []

    def add_widget(self, widget: AssetCard):
        widget.setParent(self.parent_widget)
        self.items.append(widget)

    def clear(self):
        for item in self.items:
            item.setParent(None)
            item.deleteLater()
        self.items.clear()

    def do_layout(self, width: int) -> int:
        """Arrange items in rows. Returns the total required height."""
        if not self.items:
            return 0

        x = self.spacing
        y = self.spacing
        row_height = 0

        for item in self.items:
            item_w = item.sizeHint().width()
            item_h = item.sizeHint().height()

            if x + item_w + self.spacing > width and x > self.spacing:
                # Wrap to next row
                x = self.spacing
                y += row_height + self.spacing
                row_height = 0

            item.setGeometry(x, y, item_w, item_h)
            item.show()

            x += item_w + self.spacing
            row_height = max(row_height, item_h)

        return y + row_height + self.spacing


class ResultsGrid(QScrollArea):
    """Scrollable grid of asset cards with flow layout."""

    card_selected = pyqtSignal(object)  # Emits SearchResult

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("resultsArea")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Content container
        self._container = QWidget()
        self._container.setStyleSheet("background-color: #0f1923;")
        self.setWidget(self._container)

        self._flow = FlowLayout(self._container, spacing=12)
        self._selected_card: Optional[AssetCard] = None
        self._empty_label: Optional[QLabel] = None

        self._show_empty("Connect a database and search to browse your media.")

    def _show_empty(self, message: str):
        """Show an empty state message."""
        self._clear_empty()
        self._empty_label = QLabel(message)
        self._empty_label.setParent(self._container)
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet(
            "color: #3a5a7e; font-size: 15px; padding: 60px;"
        )
        self._empty_label.setWordWrap(True)
        self._empty_label.show()

    def _clear_empty(self):
        if self._empty_label:
            self._empty_label.setParent(None)
            self._empty_label.deleteLater()
            self._empty_label = None

    def display_results(self, results: List[SearchResult]):
        """Display a list of search results as cards."""
        self._flow.clear()
        self._selected_card = None
        self._clear_empty()

        if not results:
            self._show_empty("No results found. Try different keywords.")
            self._container.setMinimumHeight(200)
            return

        for result in results:
            card = AssetCard(result)
            card.clicked.connect(self._on_card_clicked)
            self._flow.add_widget(card)

        # Trigger layout
        self._relayout()

    def _on_card_clicked(self, result: SearchResult):
        """Handle card selection."""
        # Deselect previous
        if self._selected_card:
            self._selected_card.set_selected(False)

        # Find and select the clicked card
        sender = self.sender()
        if isinstance(sender, AssetCard):
            sender.set_selected(True)
            self._selected_card = sender

        self.card_selected.emit(result)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout()

    def _relayout(self):
        """Re-run the flow layout with current width."""
        width = self.viewport().width()
        total_h = self._flow.do_layout(width)
        self._container.setMinimumHeight(max(total_h, 200))

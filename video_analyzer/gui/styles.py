"""Dark theme stylesheet for the Video Analyzer GUI."""

DARK_THEME = """
/* ── Global ─────────────────────────────────────────── */
QWidget {
    background-color: #0f1923;
    color: #e0e6ed;
    font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", sans-serif;
    font-size: 13px;
}

/* ── Main Window ────────────────────────────────────── */
QMainWindow {
    background-color: #0f1923;
}

/* ── Search Bar ─────────────────────────────────────── */
QLineEdit#searchBar {
    background-color: #1a2736;
    border: 2px solid #2a3a4e;
    border-radius: 12px;
    padding: 10px 16px 10px 40px;
    font-size: 15px;
    color: #e0e6ed;
    selection-background-color: #06d6a0;
    selection-color: #0f1923;
}
QLineEdit#searchBar:focus {
    border-color: #06d6a0;
    background-color: #1e2f42;
}
QLineEdit#searchBar::placeholder {
    color: #5a6a7e;
}

/* ── Buttons ────────────────────────────────────────── */
QPushButton {
    background-color: #1a2736;
    border: 1px solid #2a3a4e;
    border-radius: 8px;
    padding: 8px 16px;
    color: #e0e6ed;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #243447;
    border-color: #06d6a0;
}
QPushButton:pressed {
    background-color: #06d6a0;
    color: #0f1923;
}
QPushButton#addDbBtn {
    background-color: #06d6a0;
    color: #0f1923;
    font-weight: 700;
    border: none;
    padding: 8px 20px;
}
QPushButton#addDbBtn:hover {
    background-color: #05c493;
}
QPushButton#removeDbBtn {
    background-color: transparent;
    border: 1px solid #e74c6f;
    color: #e74c6f;
    padding: 6px 12px;
    font-size: 12px;
}
QPushButton#removeDbBtn:hover {
    background-color: #e74c6f;
    color: #ffffff;
}

/* ── Sidebar (Database Panel) ───────────────────────── */
QFrame#sidebarFrame {
    background-color: #131f2e;
    border-right: 1px solid #1e2f42;
    border-radius: 0px;
}
QLabel#sidebarTitle {
    font-size: 11px;
    font-weight: 700;
    color: #5a7a9a;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 12px 16px 4px 16px;
}

/* ── Database list items ────────────────────────────── */
QFrame#dbItem {
    background-color: transparent;
    border-radius: 6px;
    padding: 4px 8px;
}
QFrame#dbItem:hover {
    background-color: #1a2736;
}
QCheckBox {
    spacing: 8px;
    color: #c0cad6;
    font-size: 12px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid #3a4a5e;
    background-color: #1a2736;
}
QCheckBox::indicator:checked {
    background-color: #06d6a0;
    border-color: #06d6a0;
}
QCheckBox::indicator:hover {
    border-color: #06d6a0;
}

/* ── Results Grid (scroll area) ─────────────────────── */
QScrollArea#resultsArea {
    background-color: #0f1923;
    border: none;
}
QScrollArea#resultsArea > QWidget > QWidget {
    background-color: #0f1923;
}

/* ── Asset Card ─────────────────────────────────────── */
QFrame#assetCard {
    background-color: #162030;
    border: 1px solid #1e2f42;
    border-radius: 10px;
}
QFrame#assetCard:hover {
    border-color: #06d6a0;
    background-color: #1a2a3e;
}
QLabel#cardFilename {
    font-size: 11px;
    font-weight: 600;
    color: #d0dae6;
    padding: 4px 8px 2px 8px;
}
QLabel#cardMeta {
    font-size: 10px;
    color: #5a7a9a;
    padding: 0px 8px 6px 8px;
}
QLabel#cardBadge {
    background-color: rgba(6, 214, 160, 0.15);
    color: #06d6a0;
    font-size: 9px;
    font-weight: 700;
    border-radius: 4px;
    padding: 2px 6px;
}
QLabel#cardBadgeImage {
    background-color: rgba(99, 145, 255, 0.15);
    color: #6391ff;
    font-size: 9px;
    font-weight: 700;
    border-radius: 4px;
    padding: 2px 6px;
}
QLabel#cardBadgeGif {
    background-color: rgba(255, 159, 67, 0.15);
    color: #ff9f43;
    font-size: 9px;
    font-weight: 700;
    border-radius: 4px;
    padding: 2px 6px;
}
QLabel#thumbnailLabel {
    background-color: #0d1520;
    border-radius: 8px;
}
QLabel#selectedCard {
    border: 2px solid #06d6a0;
}

/* ── Detail Panel ───────────────────────────────────── */
QFrame#detailPanel {
    background-color: #131f2e;
    border-left: 1px solid #1e2f42;
}
QLabel#detailTitle {
    font-size: 16px;
    font-weight: 700;
    color: #e0e6ed;
    padding: 16px 16px 4px 16px;
}
QLabel#detailSectionTitle {
    font-size: 11px;
    font-weight: 700;
    color: #06d6a0;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 12px 16px 4px 16px;
}
QLabel#detailValue {
    font-size: 12px;
    color: #a0b0c4;
    padding: 2px 16px;
    word-wrap: true;
}
QLabel#detailPreview {
    background-color: #0d1520;
    border-radius: 8px;
}

/* ── Scrollbars ─────────────────────────────────────── */
QScrollBar:vertical {
    background-color: #0f1923;
    width: 10px;
    margin: 0;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background-color: #2a3a4e;
    min-height: 40px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background-color: #3a5a7e;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
QScrollBar:horizontal {
    height: 0px;
}

/* ── Status Bar ─────────────────────────────────────── */
QStatusBar {
    background-color: #0b1219;
    color: #5a7a9a;
    font-size: 11px;
    border-top: 1px solid #1e2f42;
    padding: 4px 12px;
}

/* ── Splitter ───────────────────────────────────────── */
QSplitter::handle {
    background-color: #1e2f42;
    width: 1px;
}
QSplitter::handle:hover {
    background-color: #06d6a0;
}

/* ── Tooltips ───────────────────────────────────────── */
QToolTip {
    background-color: #1e2f42;
    color: #e0e6ed;
    border: 1px solid #2a3a4e;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}
"""

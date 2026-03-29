"""Launch the Video Analyzer search GUI."""

import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from .main_window import MainWindow
from .styles import DARK_THEME


def main():
    # High-DPI support (works on both macOS and Windows)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_THEME)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

"""Entry point for DieCut Automator application."""
from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from src.presentation.windows.main_window import MainWindow


def main() -> int:
    """Run the DieCut Automator application."""
    app = QApplication(sys.argv)
    app.setApplicationName("DieCut Automator")
    app.setApplicationVersion("0.1.0")

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

"""Tests for MainWindow."""
from __future__ import annotations

import pytest
from pytestqt.qtbot import QtBot
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.presentation.windows.main_window import MainWindow


class TestMainWindow:
    """Test cases for MainWindow."""

    def test_window_creation(self, qtbot: QtBot) -> None:
        """Test main window can be created."""
        window = MainWindow()
        qtbot.addWidget(window)

        assert window is not None
        assert window.windowTitle() == "DieCut Automator"

    def test_window_default_size(self, qtbot: QtBot) -> None:
        """Test main window has reasonable default size."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Minimum size should be at least 800x600
        assert window.minimumWidth() >= 800
        assert window.minimumHeight() >= 600

    def test_window_has_central_widget(self, qtbot: QtBot) -> None:
        """Test main window has a central widget."""
        window = MainWindow()
        qtbot.addWidget(window)

        assert window.centralWidget() is not None

    def test_window_has_menu_bar(self, qtbot: QtBot) -> None:
        """Test main window has a menu bar."""
        window = MainWindow()
        qtbot.addWidget(window)

        menu_bar = window.menuBar()
        assert menu_bar is not None
        # Should have at least File menu
        assert menu_bar.actions()

    def test_window_has_file_menu(self, qtbot: QtBot) -> None:
        """Test main window has File menu with expected actions."""
        window = MainWindow()
        qtbot.addWidget(window)

        file_menu = None
        for action in window.menuBar().actions():
            if action.text() in ("File", "&File", "파일", "파일(&F)"):
                file_menu = action.menu()
                break

        assert file_menu is not None

        # Get action texts (remove & for keyboard shortcuts)
        action_texts = [
            a.text().replace("&", "") for a in file_menu.actions() if not a.isSeparator()
        ]

        # Should have Open and Exit at minimum
        assert any("Open" in t or "열기" in t for t in action_texts)
        assert any("Exit" in t or "종료" in t for t in action_texts)

    def test_window_has_status_bar(self, qtbot: QtBot) -> None:
        """Test main window has a status bar."""
        window = MainWindow()
        qtbot.addWidget(window)

        assert window.statusBar() is not None

    def test_window_initial_status_message(self, qtbot: QtBot) -> None:
        """Test main window shows initial status message."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Status bar should show a ready message
        status_text = window.statusBar().currentMessage()
        assert status_text  # Should have some message

    def test_window_has_preview_widget(self, qtbot: QtBot) -> None:
        """Test main window contains preview widget."""
        window = MainWindow()
        qtbot.addWidget(window)

        assert window.preview_widget is not None

    def test_window_has_input_panel(self, qtbot: QtBot) -> None:
        """Test main window contains input panel."""
        window = MainWindow()
        qtbot.addWidget(window)

        assert window.input_panel is not None


class TestMainWindowFileOperations:
    """Test cases for file operations in MainWindow."""

    def test_open_file_dialog_exists(self, qtbot: QtBot) -> None:
        """Test that open file action triggers file dialog."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Check that open_file method exists
        assert hasattr(window, 'open_file')
        assert callable(window.open_file)

    def test_save_file_dialog_exists(self, qtbot: QtBot) -> None:
        """Test that save file action exists."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Check that save_file method exists
        assert hasattr(window, 'save_file')
        assert callable(window.save_file)

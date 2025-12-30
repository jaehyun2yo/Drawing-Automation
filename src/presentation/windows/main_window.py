"""Main application window."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
import json

from PyQt6.QtCore import Qt, QSettings, QMimeData
from PyQt6.QtGui import QAction, QKeySequence, QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QSplitter,
    QFileDialog,
    QMessageBox,
    QToolBar,
    QMenu,
)

from src.presentation.widgets.preview_widget import PreviewWidget
from src.presentation.widgets.input_panel import InputPanel

if TYPE_CHECKING:
    from src.domain.entities.entity import Entity


class MainWindow(QMainWindow):
    """Main application window for DieCut Automator."""

    MAX_RECENT_FILES = 10

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the main window."""
        super().__init__(parent)

        self._current_file: Path | None = None
        self._entities: list[Entity] = []
        self._recent_files: list[str] = []
        self._settings = QSettings("DieCutAutomator", "DieCutAutomator")

        self._load_recent_files()
        self._init_ui()
        self._init_menus()
        self._init_toolbar()
        self._init_status_bar()

        # Enable drag and drop
        self.setAcceptDrops(True)

    def _init_ui(self) -> None:
        """Initialize UI components."""
        self.setWindowTitle("DieCut Automator")
        self.setMinimumSize(800, 600)

        # Central widget with splitter
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(5, 5, 5, 5)

        # Splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side: Input panel
        self._input_panel = InputPanel()
        self._input_panel.setMaximumWidth(350)
        self._input_panel.process_requested.connect(self._on_process)
        splitter.addWidget(self._input_panel)

        # Right side: Preview widget
        self._preview_widget = PreviewWidget()
        splitter.addWidget(self._preview_widget)

        # Set splitter proportions
        splitter.setSizes([300, 500])

        layout.addWidget(splitter)

    def _init_menus(self) -> None:
        """Initialize menu bar."""
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("&File")

        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        # Recent files submenu
        self._recent_menu = QMenu("Recent Files", self)
        self._update_recent_menu()
        file_menu.addMenu(self._recent_menu)

        file_menu.addSeparator()

        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self._save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menu_bar.addMenu("&View")

        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.triggered.connect(self._preview_widget.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.triggered.connect(self._preview_widget.zoom_out)
        view_menu.addAction(zoom_out_action)

        fit_action = QAction("&Fit to Window", self)
        fit_action.setShortcut("Ctrl+0")
        fit_action.triggered.connect(self._preview_widget.zoom_to_fit)
        view_menu.addAction(fit_action)

        view_menu.addSeparator()

        grid_action = QAction("Show &Grid", self)
        grid_action.setCheckable(True)
        grid_action.setChecked(True)
        grid_action.triggered.connect(self._preview_widget.toggle_grid)
        view_menu.addAction(grid_action)

        # Help menu
        help_menu = menu_bar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _init_toolbar(self) -> None:
        """Initialize toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_file)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.triggered.connect(self._preview_widget.zoom_in)
        toolbar.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.triggered.connect(self._preview_widget.zoom_out)
        toolbar.addAction(zoom_out_action)

        fit_action = QAction("Fit", self)
        fit_action.triggered.connect(self._preview_widget.zoom_to_fit)
        toolbar.addAction(fit_action)

    def _init_status_bar(self) -> None:
        """Initialize status bar."""
        self.statusBar().showMessage("Ready - Open a drawing file to begin (DXF, AI, SVG, EPS)")

    @property
    def preview_widget(self) -> PreviewWidget:
        """Get the preview widget."""
        return self._preview_widget

    @property
    def input_panel(self) -> InputPanel:
        """Get the input panel."""
        return self._input_panel

    # Supported file extensions
    SUPPORTED_EXTENSIONS = ('.dxf', '.ai', '.svg', '.eps')

    # Drag and Drop Support
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                if url.toLocalFile().lower().endswith(self.SUPPORTED_EXTENSIONS):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop event."""
        urls = event.mimeData().urls()
        for url in urls:
            file_path = url.toLocalFile()
            if file_path.lower().endswith(self.SUPPORTED_EXTENSIONS):
                self._load_file(Path(file_path))
                break

    # Recent Files Management
    def _load_recent_files(self) -> None:
        """Load recent files from settings."""
        recent = self._settings.value("recent_files", [])
        if isinstance(recent, list):
            self._recent_files = recent
        else:
            self._recent_files = []

    def _save_recent_files(self) -> None:
        """Save recent files to settings."""
        self._settings.setValue("recent_files", self._recent_files)

    def _add_to_recent_files(self, file_path: Path) -> None:
        """Add a file to recent files list."""
        path_str = str(file_path)

        # Remove if already exists
        if path_str in self._recent_files:
            self._recent_files.remove(path_str)

        # Add to front
        self._recent_files.insert(0, path_str)

        # Keep only MAX_RECENT_FILES
        self._recent_files = self._recent_files[:self.MAX_RECENT_FILES]

        self._save_recent_files()
        self._update_recent_menu()

    def _update_recent_menu(self) -> None:
        """Update the recent files menu."""
        self._recent_menu.clear()

        if not self._recent_files:
            no_recent_action = QAction("(No recent files)", self)
            no_recent_action.setEnabled(False)
            self._recent_menu.addAction(no_recent_action)
            return

        for i, file_path in enumerate(self._recent_files):
            path = Path(file_path)
            action = QAction(f"{i + 1}. {path.name}", self)
            action.setData(file_path)
            action.triggered.connect(lambda checked, p=file_path: self._open_recent_file(p))
            self._recent_menu.addAction(action)

        self._recent_menu.addSeparator()

        clear_action = QAction("Clear Recent Files", self)
        clear_action.triggered.connect(self._clear_recent_files)
        self._recent_menu.addAction(clear_action)

    def _open_recent_file(self, file_path: str) -> None:
        """Open a recent file."""
        path = Path(file_path)
        if path.exists():
            self._load_file(path)
        else:
            QMessageBox.warning(
                self,
                "File Not Found",
                f"The file no longer exists:\n{file_path}"
            )
            # Remove from recent files
            if file_path in self._recent_files:
                self._recent_files.remove(file_path)
                self._save_recent_files()
                self._update_recent_menu()

    def _clear_recent_files(self) -> None:
        """Clear the recent files list."""
        self._recent_files = []
        self._save_recent_files()
        self._update_recent_menu()

    def open_file(self) -> None:
        """Open a drawing file (DXF, AI, SVG, or EPS)."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Drawing File",
            "",
            "Drawing Files (*.dxf *.ai *.svg *.eps);;DXF Files (*.dxf);;AI Files (*.ai *.eps);;SVG Files (*.svg);;All Files (*.*)"
        )

        if file_path:
            self._load_file(Path(file_path))

    def _load_file(self, file_path: Path) -> None:
        """Load entities from drawing file (DXF, AI, or SVG)."""
        try:
            from src.infrastructure.file_reader_factory import FileReaderFactory

            self._entities = FileReaderFactory.read_file(file_path)
            self._current_file = file_path

            self._preview_widget.set_entities(self._entities)
            self._preview_widget.zoom_to_fit()

            # Add to recent files
            self._add_to_recent_files(file_path)

            self.statusBar().showMessage(
                f"Loaded: {file_path.name} ({len(self._entities)} entities)"
            )
            self.setWindowTitle(f"DieCut Automator - {file_path.name}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load file:\n{e}"
            )

    def save_file(self) -> None:
        """Save the current file."""
        if self._current_file:
            self._save_to_file(self._current_file)
        else:
            self._save_file_as()

    def _save_file_as(self) -> None:
        """Save to a new file."""
        # Generate suggested filename
        suggested_name = ""
        if self._current_file:
            from src.application.services.filename_generator import FilenameGenerator
            from src.domain.services.text_generator import JobInfo

            job_info = JobInfo(
                date=self._input_panel.job_date,
                job_number=self._input_panel.job_number or "001",
                package_name=self._input_panel.package_name or "Unknown",
                side=self._input_panel.side,
                plate_type=self._input_panel.plate_type,
            )
            generator = FilenameGenerator()
            suggested_name = generator.generate(job_info)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save DXF File",
            suggested_name,
            "DXF Files (*.dxf);;All Files (*.*)"
        )

        if file_path:
            self._save_to_file(Path(file_path))

    def _save_to_file(self, file_path: Path) -> None:
        """Save entities to DXF file."""
        try:
            from src.infrastructure.dxf.ezdxf_adapter import EzdxfWriter

            writer = EzdxfWriter()
            writer.write(self._entities, file_path)
            self._current_file = file_path

            self.statusBar().showMessage(f"Saved: {file_path.name}")
            self.setWindowTitle(f"DieCut Automator - {file_path.name}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save file:\n{e}"
            )

    def _on_process(self) -> None:
        """Handle process button click."""
        if not self._entities:
            QMessageBox.warning(
                self,
                "No File",
                "Please open a drawing file first (DXF, AI, SVG, or EPS)."
            )
            return

        self.statusBar().showMessage("Processing...")

        try:
            from src.application.use_cases.process_drawing import (
                ProcessDrawingUseCase,
                ProcessingOptions,
            )
            from src.domain.value_objects.bridge_settings import BridgeSettings
            from src.domain.services.text_generator import JobInfo

            # Create job info from input panel
            job_info = JobInfo(
                date=self._input_panel.job_date,
                job_number=self._input_panel.job_number or "001",
                package_name=self._input_panel.package_name or "Unknown",
                side=self._input_panel.side,
                plate_type=self._input_panel.plate_type,
            )

            # Get options from input panel
            options = ProcessingOptions(
                side=self._input_panel.side,
                plate_type=self._input_panel.plate_type,
                apply_bridges=True,
                generate_plywood=True,
                generate_text=True,
                apply_straight_knife=self._input_panel.apply_straight_knife,
                remove_external=self._input_panel.remove_external_elements,
                connect_segments=self._input_panel.connect_segments,
                job_info=job_info,
                paper_size=self._input_panel.paper_size,
                cut_bridge_settings=BridgeSettings(
                    gap_size=self._input_panel.cut_gap,
                    target_interval=self._input_panel.cut_interval,
                ),
                crease_bridge_settings=BridgeSettings(
                    gap_size=self._input_panel.crease_gap,
                    target_interval=self._input_panel.crease_interval,
                ),
            )

            # Execute processing
            use_case = ProcessDrawingUseCase()
            result = use_case.execute(self._entities, options)

            if result.success:
                self._entities = result.entities
                self._preview_widget.set_entities(self._entities)
                self._preview_widget.zoom_to_fit()

                stats = result.statistics or {}
                status_parts = [
                    f"Cut: {stats.get('cut_count', 0)}",
                    f"Crease: {stats.get('crease_count', 0)}",
                    f"Plywood: {stats.get('plywood_count', 0)}",
                    f"Text: {stats.get('text_count', 0)}",
                ]
                if result.removed_count > 0:
                    status_parts.append(f"Removed: {result.removed_count}")
                if result.connection_count > 0:
                    status_parts.append(f"Connected: {result.connection_count}")

                self.statusBar().showMessage("Processed: " + ", ".join(status_parts))
            else:
                QMessageBox.warning(self, "Processing Failed", result.message)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Processing failed:\n{e}"
            )

    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About DieCut Automator",
            "DieCut Automator v0.2.0\n\n"
            "A tool for automating die-cut drawing processing.\n\n"
            "Features:\n"
            "- Load and preview DXF, AI, SVG, EPS files\n"
            "- Automatic bridge insertion\n"
            "- Mirror for front/back sides\n"
            "- Plywood layout generation\n"
            "- Straight knife insertion\n"
            "- External element removal\n"
            "- Segment connection\n"
            "- Drag and drop support\n"
            "- Recent files list"
        )

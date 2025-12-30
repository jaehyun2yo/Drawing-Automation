"""Input panel for job information."""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QDateEdit,
    QComboBox,
    QDoubleSpinBox,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QStackedWidget,
    QCheckBox,
)

from src.domain.types import PlateType, Side
from src.domain.value_objects.paper_size import PaperSize


class InputPanel(QWidget):
    """Panel for entering job information and processing settings."""

    # Signals
    process_requested = pyqtSignal()
    settings_changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the input panel."""
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)

        # Job Info Group
        job_group = QGroupBox("작업 정보")
        job_layout = QFormLayout(job_group)

        self._date_edit = QDateEdit()
        self._date_edit.setDate(date.today())
        self._date_edit.setCalendarPopup(True)
        job_layout.addRow("날짜:", self._date_edit)

        self._job_number = QLineEdit()
        self._job_number.setPlaceholderText("예: 001")
        job_layout.addRow("작업 번호:", self._job_number)

        self._package_name = QLineEdit()
        self._package_name.setPlaceholderText("예: 박스A")
        job_layout.addRow("품명:", self._package_name)

        self._side_combo = QComboBox()
        self._side_combo.addItem("앞면 (Front)", Side.FRONT)
        self._side_combo.addItem("뒷면 (Back)", Side.BACK)
        job_layout.addRow("면:", self._side_combo)

        self._plate_combo = QComboBox()
        self._plate_combo.addItem("동판 (Copper)", PlateType.COPPER)
        self._plate_combo.addItem("자동 (Auto)", PlateType.AUTO)
        job_layout.addRow("판 종류:", self._plate_combo)

        layout.addWidget(job_group)

        # Paper Size Group
        paper_group = QGroupBox("종이 규격")
        paper_layout = QVBoxLayout(paper_group)

        # Standard size radio + dropdown
        standard_layout = QHBoxLayout()
        self._standard_radio = QRadioButton("표준 규격")
        self._standard_radio.setChecked(True)
        standard_layout.addWidget(self._standard_radio)

        self._paper_combo = QComboBox()
        for name in PaperSize.get_standard_names():
            size = PaperSize.STANDARD_SIZES[name]
            self._paper_combo.addItem(f"{name} ({size[0]}×{size[1]})", name)
        standard_layout.addWidget(self._paper_combo, 1)
        paper_layout.addLayout(standard_layout)

        # Custom size radio + inputs
        custom_layout = QHBoxLayout()
        self._custom_radio = QRadioButton("사용자 정의")
        custom_layout.addWidget(self._custom_radio)

        self._custom_width = QDoubleSpinBox()
        self._custom_width.setRange(PaperSize.MIN_SIZE, PaperSize.MAX_WIDTH)
        self._custom_width.setValue(500)
        self._custom_width.setSuffix(" mm")
        self._custom_width.setDecimals(1)
        custom_layout.addWidget(self._custom_width)

        custom_layout.addWidget(QLabel("×"))

        self._custom_height = QDoubleSpinBox()
        self._custom_height.setRange(PaperSize.MIN_SIZE, PaperSize.MAX_HEIGHT)
        self._custom_height.setValue(700)
        self._custom_height.setSuffix(" mm")
        self._custom_height.setDecimals(1)
        custom_layout.addWidget(self._custom_height)

        paper_layout.addLayout(custom_layout)

        # Radio button group
        self._paper_mode_group = QButtonGroup(self)
        self._paper_mode_group.addButton(self._standard_radio, 0)
        self._paper_mode_group.addButton(self._custom_radio, 1)

        layout.addWidget(paper_group)

        # Bridge Settings Group
        bridge_group = QGroupBox("브릿지 설정")
        bridge_layout = QFormLayout(bridge_group)

        self._cut_gap = QDoubleSpinBox()
        self._cut_gap.setRange(0.5, 10.0)
        self._cut_gap.setValue(3.0)
        self._cut_gap.setSuffix(" mm")
        self._cut_gap.setDecimals(1)
        bridge_layout.addRow("칼선 간격:", self._cut_gap)

        self._crease_gap = QDoubleSpinBox()
        self._crease_gap.setRange(0.5, 10.0)
        self._crease_gap.setValue(2.0)
        self._crease_gap.setSuffix(" mm")
        self._crease_gap.setDecimals(1)
        bridge_layout.addRow("괘선 간격:", self._crease_gap)

        self._cut_interval = QDoubleSpinBox()
        self._cut_interval.setRange(20.0, 200.0)
        self._cut_interval.setValue(60.0)
        self._cut_interval.setSuffix(" mm")
        self._cut_interval.setDecimals(0)
        bridge_layout.addRow("칼선 브릿지 간격:", self._cut_interval)

        self._crease_interval = QDoubleSpinBox()
        self._crease_interval.setRange(20.0, 200.0)
        self._crease_interval.setValue(100.0)
        self._crease_interval.setSuffix(" mm")
        self._crease_interval.setDecimals(0)
        bridge_layout.addRow("괘선 브릿지 간격:", self._crease_interval)

        layout.addWidget(bridge_group)

        # Processing Options Group
        options_group = QGroupBox("처리 옵션")
        options_layout = QVBoxLayout(options_group)

        self._apply_straight_knife = QCheckBox("일자칼 적용")
        self._apply_straight_knife.setChecked(True)
        options_layout.addWidget(self._apply_straight_knife)

        self._remove_external = QCheckBox("외부 요소 제거")
        self._remove_external.setChecked(True)
        options_layout.addWidget(self._remove_external)

        self._connect_segments = QCheckBox("세그먼트 연결")
        self._connect_segments.setChecked(False)
        options_layout.addWidget(self._connect_segments)

        layout.addWidget(options_group)

        # Process Button
        self._process_btn = QPushButton("처리 시작")
        self._process_btn.setMinimumHeight(40)
        self._process_btn.clicked.connect(self.process_requested.emit)
        layout.addWidget(self._process_btn)

        # Add stretch at bottom
        layout.addStretch()

        # Connect signals
        self._cut_gap.valueChanged.connect(self.settings_changed.emit)
        self._crease_gap.valueChanged.connect(self.settings_changed.emit)
        self._cut_interval.valueChanged.connect(self.settings_changed.emit)
        self._crease_interval.valueChanged.connect(self.settings_changed.emit)
        self._paper_combo.currentIndexChanged.connect(self.settings_changed.emit)
        self._custom_width.valueChanged.connect(self.settings_changed.emit)
        self._custom_height.valueChanged.connect(self.settings_changed.emit)
        self._standard_radio.toggled.connect(self._on_paper_mode_changed)
        self._custom_radio.toggled.connect(self._on_paper_mode_changed)

    def _on_paper_mode_changed(self) -> None:
        """Handle paper mode radio button change."""
        is_standard = self._standard_radio.isChecked()
        self._paper_combo.setEnabled(is_standard)
        self._custom_width.setEnabled(not is_standard)
        self._custom_height.setEnabled(not is_standard)
        self.settings_changed.emit()

    @property
    def job_date(self) -> date:
        """Get job date."""
        return self._date_edit.date().toPyDate()

    @property
    def job_number(self) -> str:
        """Get job number."""
        return self._job_number.text()

    @property
    def package_name(self) -> str:
        """Get package name."""
        return self._package_name.text()

    @property
    def side(self) -> Side:
        """Get selected side."""
        return self._side_combo.currentData()

    @property
    def plate_type(self) -> PlateType:
        """Get selected plate type."""
        return self._plate_combo.currentData()

    @property
    def paper_size(self) -> PaperSize:
        """Get selected paper size."""
        if self._standard_radio.isChecked():
            name = self._paper_combo.currentData()
            return PaperSize.from_standard(name)
        else:
            return PaperSize.custom(
                self._custom_width.value(),
                self._custom_height.value()
            )

    @property
    def cut_gap(self) -> float:
        """Get cut line bridge gap size."""
        return self._cut_gap.value()

    @property
    def crease_gap(self) -> float:
        """Get crease line bridge gap size."""
        return self._crease_gap.value()

    @property
    def cut_interval(self) -> float:
        """Get cut line bridge interval."""
        return self._cut_interval.value()

    @property
    def crease_interval(self) -> float:
        """Get crease line bridge interval."""
        return self._crease_interval.value()

    @property
    def apply_straight_knife(self) -> bool:
        """Get whether to apply straight knife."""
        return self._apply_straight_knife.isChecked()

    @property
    def remove_external_elements(self) -> bool:
        """Get whether to remove external elements."""
        return self._remove_external.isChecked()

    @property
    def connect_segments(self) -> bool:
        """Get whether to connect segments."""
        return self._connect_segments.isChecked()

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable all inputs."""
        self._date_edit.setEnabled(enabled)
        self._job_number.setEnabled(enabled)
        self._package_name.setEnabled(enabled)
        self._side_combo.setEnabled(enabled)
        self._plate_combo.setEnabled(enabled)
        self._paper_combo.setEnabled(enabled and self._standard_radio.isChecked())
        self._custom_width.setEnabled(enabled and self._custom_radio.isChecked())
        self._custom_height.setEnabled(enabled and self._custom_radio.isChecked())
        self._standard_radio.setEnabled(enabled)
        self._custom_radio.setEnabled(enabled)
        self._cut_gap.setEnabled(enabled)
        self._crease_gap.setEnabled(enabled)
        self._cut_interval.setEnabled(enabled)
        self._crease_interval.setEnabled(enabled)
        self._apply_straight_knife.setEnabled(enabled)
        self._remove_external.setEnabled(enabled)
        self._connect_segments.setEnabled(enabled)
        self._process_btn.setEnabled(enabled)

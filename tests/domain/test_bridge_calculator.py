"""
Tests for BridgeCalculator domain service.
TDD: Tests written first, then implementation.
"""
import pytest
from src.domain.services.bridge_calculator import BridgeCalculator
from src.domain.value_objects.bridge_settings import BridgeSettings
from src.domain.entities.point import Point
from src.domain.entities.line import Line
from src.domain.types import LineCategory


class TestBridgeSettings:
    """Tests for BridgeSettings value object."""

    def test_default_settings(self) -> None:
        """Test default bridge settings."""
        settings = BridgeSettings.default()
        assert settings.min_length == 20.0
        assert settings.single_bridge_max == 50.0
        assert settings.target_interval == 60.0
        assert settings.gap_size == 3.0
        assert settings.edge_margin == 10.0

    def test_cut_settings(self) -> None:
        """Test settings for cut lines."""
        settings = BridgeSettings.for_cut()
        assert settings.gap_size == 3.0
        assert settings.target_interval == 60.0

    def test_crease_settings(self) -> None:
        """Test settings for crease lines."""
        settings = BridgeSettings.for_crease()
        assert settings.gap_size == 2.0
        assert settings.target_interval == 50.0

    def test_custom_settings(self) -> None:
        """Test custom bridge settings."""
        settings = BridgeSettings(
            min_length=15.0,
            single_bridge_max=40.0,
            target_interval=50.0,
            gap_size=2.5,
            edge_margin=8.0
        )
        assert settings.min_length == 15.0
        assert settings.gap_size == 2.5

    def test_invalid_min_length(self) -> None:
        """Test that negative min_length raises error."""
        with pytest.raises(ValueError):
            BridgeSettings(min_length=-1.0)

    def test_invalid_single_bridge_max(self) -> None:
        """Test that single_bridge_max < min_length raises error."""
        with pytest.raises(ValueError):
            BridgeSettings(min_length=30.0, single_bridge_max=20.0)


class TestBridgeCalculator:
    """Tests for BridgeCalculator service."""

    @pytest.fixture
    def calculator(self) -> BridgeCalculator:
        """Create a BridgeCalculator with default settings."""
        return BridgeCalculator(BridgeSettings.default())

    def test_no_bridge_for_short_line(self, calculator: BridgeCalculator) -> None:
        """Test that lines shorter than min_length get no bridges."""
        positions = calculator.calculate_bridge_positions(15.0)
        assert positions == []

    def test_no_bridge_at_min_length_boundary(self, calculator: BridgeCalculator) -> None:
        """Test that line exactly at min_length gets no bridges."""
        # Line length < min_length should have no bridges
        positions = calculator.calculate_bridge_positions(19.9)
        assert positions == []

    def test_single_bridge_at_center(self, calculator: BridgeCalculator) -> None:
        """Test that line between min_length and single_bridge_max gets one bridge."""
        positions = calculator.calculate_bridge_positions(30.0)
        assert len(positions) == 1
        assert positions[0] == 0.5  # Center

    def test_single_bridge_near_single_max(self, calculator: BridgeCalculator) -> None:
        """Test single bridge for line just under single_bridge_max."""
        positions = calculator.calculate_bridge_positions(49.0)
        assert len(positions) == 1
        assert positions[0] == 0.5

    def test_multiple_bridges_for_long_line(self, calculator: BridgeCalculator) -> None:
        """Test that long lines get multiple bridges."""
        # 100mm line with 60mm target interval should get 2 bridges
        positions = calculator.calculate_bridge_positions(100.0)
        assert len(positions) >= 2

    def test_bridge_positions_in_valid_range(self, calculator: BridgeCalculator) -> None:
        """Test that all bridge positions are between 0 and 1."""
        positions = calculator.calculate_bridge_positions(150.0)
        for pos in positions:
            assert 0.0 < pos < 1.0

    def test_bridge_positions_sorted(self, calculator: BridgeCalculator) -> None:
        """Test that bridge positions are sorted in ascending order."""
        positions = calculator.calculate_bridge_positions(200.0)
        assert positions == sorted(positions)

    def test_edge_margin_respected(self, calculator: BridgeCalculator) -> None:
        """Test that bridges respect edge margin."""
        line_length = 100.0
        positions = calculator.calculate_bridge_positions(line_length)

        # First bridge should be at least edge_margin from start
        first_pos = positions[0] * line_length
        assert first_pos >= calculator.settings.edge_margin

        # Last bridge should be at least edge_margin from end
        last_pos = positions[-1] * line_length
        assert (line_length - last_pos) >= calculator.settings.edge_margin

    def test_calculate_bridge_gaps(self, calculator: BridgeCalculator) -> None:
        """Test calculation of gap ranges for bridges."""
        line_length = 100.0
        gaps = calculator.calculate_bridge_gaps(line_length)

        # Each gap should be a tuple of (start_ratio, end_ratio)
        for start, end in gaps:
            assert 0.0 < start < 1.0
            assert 0.0 < end < 1.0
            assert start < end

    def test_gap_size_correct(self, calculator: BridgeCalculator) -> None:
        """Test that gap size matches settings."""
        line_length = 100.0
        gaps = calculator.calculate_bridge_gaps(line_length)

        if gaps:
            start, end = gaps[0]
            actual_gap = (end - start) * line_length
            assert abs(actual_gap - calculator.settings.gap_size) < 0.01


class TestBridgeCalculatorApply:
    """Tests for applying bridges to lines."""

    @pytest.fixture
    def calculator(self) -> BridgeCalculator:
        """Create a BridgeCalculator with default settings."""
        return BridgeCalculator(BridgeSettings.default())

    def test_apply_no_bridges_to_short_line(self, calculator: BridgeCalculator) -> None:
        """Test that short lines are returned unchanged."""
        line = Line(start=Point(0.0, 0.0), end=Point(10.0, 0.0))
        result = calculator.apply_bridges(line)
        assert len(result) == 1
        assert result[0].start == line.start
        assert result[0].end == line.end

    def test_apply_single_bridge(self, calculator: BridgeCalculator) -> None:
        """Test applying single bridge to line."""
        line = Line(start=Point(0.0, 0.0), end=Point(30.0, 0.0))
        result = calculator.apply_bridges(line)

        # Should have 2 segments (line split by one bridge)
        assert len(result) == 2

        # Total length should be less than original (gap removed)
        total_length = sum(seg.length for seg in result)
        assert total_length < line.length
        assert abs(total_length - (line.length - calculator.settings.gap_size)) < 0.01

    def test_apply_multiple_bridges(self, calculator: BridgeCalculator) -> None:
        """Test applying multiple bridges to long line."""
        line = Line(start=Point(0.0, 0.0), end=Point(150.0, 0.0))
        result = calculator.apply_bridges(line)

        # Should have more segments than bridges
        assert len(result) >= 2

        # Segments should be continuous (end of one = start of next, with gaps)
        for i in range(len(result) - 1):
            gap_start = result[i].end.x
            gap_end = result[i + 1].start.x
            assert gap_end > gap_start  # There's a gap

    def test_segments_preserve_attributes(self, calculator: BridgeCalculator) -> None:
        """Test that segments preserve line attributes."""
        line = Line(
            start=Point(0.0, 0.0),
            end=Point(100.0, 0.0),
            layer="CUT",
            color=1,
            category=LineCategory.CUT
        )
        result = calculator.apply_bridges(line)

        for segment in result:
            assert segment.layer == line.layer
            assert segment.color == line.color
            assert segment.category == line.category

    def test_apply_bridges_horizontal_line(self, calculator: BridgeCalculator) -> None:
        """Test bridges on horizontal line."""
        line = Line(start=Point(10.0, 50.0), end=Point(110.0, 50.0))
        result = calculator.apply_bridges(line)

        # All segments should be at same Y
        for segment in result:
            assert segment.start.y == 50.0
            assert segment.end.y == 50.0

    def test_apply_bridges_vertical_line(self, calculator: BridgeCalculator) -> None:
        """Test bridges on vertical line."""
        line = Line(start=Point(50.0, 0.0), end=Point(50.0, 100.0))
        result = calculator.apply_bridges(line)

        # All segments should be at same X
        for segment in result:
            assert segment.start.x == 50.0
            assert segment.end.x == 50.0

    def test_apply_bridges_diagonal_line(self, calculator: BridgeCalculator) -> None:
        """Test bridges on diagonal line."""
        line = Line(start=Point(0.0, 0.0), end=Point(100.0, 100.0))
        result = calculator.apply_bridges(line)

        # Should have segments
        assert len(result) >= 1

        # Total length check (accounting for gaps)
        total_length = sum(seg.length for seg in result)
        expected_gaps = len(result) - 1
        expected_length = line.length - (expected_gaps * calculator.settings.gap_size)
        assert abs(total_length - expected_length) < 0.1

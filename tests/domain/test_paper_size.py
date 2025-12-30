"""Tests for PaperSize value object."""
from __future__ import annotations

import pytest

from src.domain.value_objects.paper_size import PaperSize


class TestPaperSizeCreation:
    """Test PaperSize creation."""

    def test_create_paper_size(self) -> None:
        """Test creating a paper size."""
        paper = PaperSize(name="Test", width=500, height=700)

        assert paper.name == "Test"
        assert paper.width == 500
        assert paper.height == 700

    def test_create_from_standard_gukjeon(self) -> None:
        """Test creating from standard size - 국전."""
        paper = PaperSize.from_standard("국전")

        assert paper.name == "국전"
        assert paper.width == 636
        assert paper.height == 939

    def test_create_from_standard_a3(self) -> None:
        """Test creating from standard size - A3."""
        paper = PaperSize.from_standard("A3")

        assert paper.name == "A3"
        assert paper.width == 297
        assert paper.height == 420

    def test_create_from_standard_4x6_full(self) -> None:
        """Test creating from standard size - 4x6전지."""
        paper = PaperSize.from_standard("4x6전지")

        assert paper.width == 788
        assert paper.height == 1091

    def test_create_from_unknown_standard_raises(self) -> None:
        """Test that unknown standard name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown standard size"):
            PaperSize.from_standard("UnknownSize")

    def test_create_custom(self) -> None:
        """Test creating custom paper size."""
        paper = PaperSize.custom(650, 900)

        assert paper.name == "650x900"
        assert paper.width == 650
        assert paper.height == 900


class TestPaperSizeValidation:
    """Test PaperSize validation."""

    def test_width_too_small_raises(self) -> None:
        """Test that width below minimum raises ValueError."""
        with pytest.raises(ValueError, match="Width must be at least"):
            PaperSize(name="Small", width=50, height=200)

    def test_height_too_small_raises(self) -> None:
        """Test that height below minimum raises ValueError."""
        with pytest.raises(ValueError, match="Height must be at least"):
            PaperSize(name="Small", width=200, height=50)

    def test_width_too_large_raises(self) -> None:
        """Test that width above maximum raises ValueError."""
        with pytest.raises(ValueError, match="Width must not exceed"):
            PaperSize(name="Large", width=2500, height=1000)

    def test_height_too_large_raises(self) -> None:
        """Test that height above maximum raises ValueError."""
        with pytest.raises(ValueError, match="Height must not exceed"):
            PaperSize(name="Large", width=1000, height=4000)

    def test_minimum_valid_size(self) -> None:
        """Test minimum valid paper size."""
        paper = PaperSize(name="Min", width=100, height=100)
        assert paper.width == 100
        assert paper.height == 100


class TestPaperSizeProperties:
    """Test PaperSize properties."""

    def test_area(self) -> None:
        """Test area calculation."""
        paper = PaperSize(name="Test", width=500, height=700)
        assert paper.area == 350000

    def test_is_portrait(self) -> None:
        """Test portrait orientation detection."""
        paper = PaperSize(name="Portrait", width=500, height=700)
        assert paper.is_portrait is True
        assert paper.is_landscape is False

    def test_is_landscape(self) -> None:
        """Test landscape orientation detection."""
        paper = PaperSize(name="Landscape", width=700, height=500)
        assert paper.is_landscape is True
        assert paper.is_portrait is False

    def test_square_is_neither(self) -> None:
        """Test square paper orientation."""
        paper = PaperSize(name="Square", width=500, height=500)
        assert paper.is_landscape is False
        assert paper.is_portrait is False

    def test_rotate(self) -> None:
        """Test rotating paper size."""
        paper = PaperSize(name="Test", width=500, height=700)
        rotated = paper.rotate()

        assert rotated.width == 700
        assert rotated.height == 500
        assert "회전" in rotated.name


class TestPaperSizeFits:
    """Test drawing fit checking."""

    def test_drawing_fits(self) -> None:
        """Test drawing that fits."""
        paper = PaperSize(name="Test", width=500, height=700)

        assert paper.fits_drawing(400, 600) is True
        assert paper.fits_drawing(500, 700) is True

    def test_drawing_too_wide(self) -> None:
        """Test drawing too wide."""
        paper = PaperSize(name="Test", width=500, height=700)

        assert paper.fits_drawing(600, 600) is False

    def test_drawing_too_tall(self) -> None:
        """Test drawing too tall."""
        paper = PaperSize(name="Test", width=500, height=700)

        assert paper.fits_drawing(400, 800) is False


class TestStandardSizes:
    """Test standard size list."""

    def test_get_standard_names(self) -> None:
        """Test getting list of standard names."""
        names = PaperSize.get_standard_names()

        assert "국전" in names
        assert "A3" in names
        assert "4x6전지" in names
        assert len(names) >= 10

    def test_all_standard_sizes_valid(self) -> None:
        """Test that all standard sizes can be created."""
        for name in PaperSize.get_standard_names():
            paper = PaperSize.from_standard(name)
            assert paper.width >= PaperSize.MIN_SIZE
            assert paper.height >= PaperSize.MIN_SIZE

"""Tests for TextGenerator domain service."""
from __future__ import annotations

from datetime import date
import pytest

from src.domain.entities.point import Point
from src.domain.entities.bounding_box import BoundingBox
from src.domain.services.text_generator import TextGenerator, JobInfo, TextEntity
from src.domain.types import Side, PlateType


class TestJobInfo:
    """Test JobInfo value object."""

    def test_create_job_info(self) -> None:
        """Test creating job info."""
        info = JobInfo(
            date=date(2024, 12, 30),
            job_number="001",
            package_name="BoxA",
            side=Side.FRONT,
            plate_type=PlateType.COPPER
        )

        assert info.date == date(2024, 12, 30)
        assert info.job_number == "001"
        assert info.package_name == "BoxA"
        assert info.side == Side.FRONT

    def test_job_info_formatted_date(self) -> None:
        """Test job info formatted date string."""
        info = JobInfo(
            date=date(2024, 12, 30),
            job_number="001",
            package_name="BoxA",
            side=Side.FRONT,
        )

        assert info.formatted_date == "2024-12-30"

    def test_job_info_side_text_front(self) -> None:
        """Test side text for front."""
        info = JobInfo(
            date=date(2024, 12, 30),
            job_number="001",
            package_name="BoxA",
            side=Side.FRONT,
        )

        assert info.side_text in ("앞", "Front", "FRONT")

    def test_job_info_side_text_back(self) -> None:
        """Test side text for back."""
        info = JobInfo(
            date=date(2024, 12, 30),
            job_number="001",
            package_name="BoxA",
            side=Side.BACK,
        )

        assert info.side_text in ("뒤", "Back", "BACK")


class TestTextEntity:
    """Test TextEntity value object."""

    def test_create_text_entity(self) -> None:
        """Test creating text entity."""
        text = TextEntity(
            content="Test Text",
            position=Point(100, 200),
            height=5.0
        )

        assert text.content == "Test Text"
        assert text.position.x == 100
        assert text.position.y == 200
        assert text.height == 5.0

    def test_text_entity_default_height(self) -> None:
        """Test default text height."""
        text = TextEntity(
            content="Test",
            position=Point(0, 0)
        )

        assert text.height == 3.5  # Default


class TestTextGeneratorBasic:
    """Test basic text generation."""

    def test_generate_job_info_text(self) -> None:
        """Test generating job info text."""
        generator = TextGenerator()
        job_info = JobInfo(
            date=date(2024, 12, 30),
            job_number="001",
            package_name="BoxA",
            side=Side.FRONT,
        )

        texts = generator.generate_job_info_texts(job_info)

        assert len(texts) >= 1
        # Should contain date
        assert any("2024" in t.content for t in texts)

    def test_generate_side_marker(self) -> None:
        """Test generating side marker text."""
        generator = TextGenerator()

        text = generator.generate_side_marker(Side.FRONT)

        assert text is not None
        assert text.content in ("앞", "FRONT", "Front")

    def test_generate_side_marker_back(self) -> None:
        """Test generating back side marker."""
        generator = TextGenerator()

        text = generator.generate_side_marker(Side.BACK)

        assert text is not None
        assert text.content in ("뒤", "BACK", "Back")


class TestTextGeneratorPositioning:
    """Test text positioning."""

    def test_position_texts_above_plywood(self) -> None:
        """Test positioning texts above plywood frame."""
        generator = TextGenerator()
        plywood_bbox = BoundingBox(
            min_x=0, min_y=0, max_x=300, max_y=200
        )
        job_info = JobInfo(
            date=date(2024, 12, 30),
            job_number="001",
            package_name="BoxA",
            side=Side.FRONT,
        )

        texts = generator.generate_positioned_texts(job_info, plywood_bbox)

        # All texts should be above the plywood (y > max_y)
        for text in texts:
            assert text.position.y >= plywood_bbox.max_y

    def test_position_side_marker_in_drawing(self) -> None:
        """Test positioning side marker inside drawing area."""
        generator = TextGenerator()
        drawing_bbox = BoundingBox(
            min_x=0, min_y=0, max_x=300, max_y=200
        )

        text = generator.generate_positioned_side_marker(
            Side.FRONT, drawing_bbox
        )

        # Side marker should be inside or near the drawing
        assert text.position.x >= drawing_bbox.min_x
        assert text.position.x <= drawing_bbox.max_x


class TestTextGeneratorFormatting:
    """Test text formatting."""

    def test_format_full_job_text(self) -> None:
        """Test formatting full job description."""
        generator = TextGenerator()
        job_info = JobInfo(
            date=date(2024, 12, 30),
            job_number="001",
            package_name="BoxA",
            side=Side.FRONT,
        )

        text = generator.format_job_text(job_info)

        assert "2024-12-30" in text
        assert "001" in text
        assert "BoxA" in text

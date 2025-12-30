"""Tests for FilenameGenerator."""
from __future__ import annotations

from datetime import date
from pathlib import Path
import pytest

from src.application.services.filename_generator import FilenameGenerator
from src.domain.services.text_generator import JobInfo
from src.domain.types import Side, PlateType


class TestFilenameGenerator:
    """Test automatic filename generation."""

    def test_generate_filename(self) -> None:
        """Test basic filename generation."""
        generator = FilenameGenerator()
        job_info = JobInfo(
            date=date(2024, 12, 30),
            job_number="001",
            package_name="BoxA",
            side=Side.FRONT,
        )

        filename = generator.generate(job_info)

        assert filename == "2024-12-30_001_BoxA_앞.dxf"

    def test_generate_filename_back_side(self) -> None:
        """Test filename for back side."""
        generator = FilenameGenerator()
        job_info = JobInfo(
            date=date(2024, 12, 30),
            job_number="002",
            package_name="BoxB",
            side=Side.BACK,
        )

        filename = generator.generate(job_info)

        assert filename == "2024-12-30_002_BoxB_뒤.dxf"

    def test_generate_full_path(self) -> None:
        """Test generating full file path."""
        generator = FilenameGenerator()
        job_info = JobInfo(
            date=date(2024, 12, 30),
            job_number="001",
            package_name="BoxA",
            side=Side.FRONT,
        )
        base_dir = Path("/output")

        full_path = generator.generate_path(job_info, base_dir)

        assert full_path == Path("/output/2024-12-30_001_BoxA_앞.dxf")

    def test_sanitize_filename_special_chars(self) -> None:
        """Test that special characters are removed from filename."""
        generator = FilenameGenerator()
        job_info = JobInfo(
            date=date(2024, 12, 30),
            job_number="001",
            package_name="Box/A:B*C",  # Invalid chars
            side=Side.FRONT,
        )

        filename = generator.generate(job_info)

        # Should not contain invalid chars
        assert "/" not in filename
        assert ":" not in filename
        assert "*" not in filename

    def test_custom_separator(self) -> None:
        """Test using custom separator."""
        generator = FilenameGenerator(separator="-")
        job_info = JobInfo(
            date=date(2024, 12, 30),
            job_number="001",
            package_name="BoxA",
            side=Side.FRONT,
        )

        filename = generator.generate(job_info)

        assert filename == "2024-12-30-001-BoxA-앞.dxf"

    def test_custom_extension(self) -> None:
        """Test using custom file extension."""
        generator = FilenameGenerator(extension=".DXF")
        job_info = JobInfo(
            date=date(2024, 12, 30),
            job_number="001",
            package_name="BoxA",
            side=Side.FRONT,
        )

        filename = generator.generate(job_info)

        assert filename.endswith(".DXF")


class TestFilenameGeneratorIncrement:
    """Test filename increment for duplicates."""

    def test_increment_if_exists(self) -> None:
        """Test incrementing filename if file exists."""
        generator = FilenameGenerator()
        job_info = JobInfo(
            date=date(2024, 12, 30),
            job_number="001",
            package_name="BoxA",
            side=Side.FRONT,
        )

        # Simulate existing files check
        filename = generator.generate_with_increment(
            job_info,
            existing_files=["2024-12-30_001_BoxA_앞.dxf"]
        )

        assert filename == "2024-12-30_001_BoxA_앞_2.dxf"

    def test_increment_multiple(self) -> None:
        """Test incrementing with multiple existing files."""
        generator = FilenameGenerator()
        job_info = JobInfo(
            date=date(2024, 12, 30),
            job_number="001",
            package_name="BoxA",
            side=Side.FRONT,
        )

        filename = generator.generate_with_increment(
            job_info,
            existing_files=[
                "2024-12-30_001_BoxA_앞.dxf",
                "2024-12-30_001_BoxA_앞_2.dxf",
                "2024-12-30_001_BoxA_앞_3.dxf",
            ]
        )

        assert filename == "2024-12-30_001_BoxA_앞_4.dxf"

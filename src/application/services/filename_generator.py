"""Automatic filename generator for output files."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.services.text_generator import JobInfo


@dataclass
class FilenameGenerator:
    """
    Service for generating standardized output filenames.

    Generates filenames in format: date_jobnumber_packagename_side.dxf
    """

    separator: str = "_"
    extension: str = ".dxf"

    # Characters not allowed in filenames
    INVALID_CHARS = r'[<>:"/\\|?*]'

    def generate(self, job_info: JobInfo) -> str:
        """
        Generate filename from job info.

        Args:
            job_info: Job information

        Returns:
            Generated filename string
        """
        parts = [
            job_info.formatted_date,
            job_info.job_number,
            self._sanitize(job_info.package_name),
            job_info.side_text,
        ]

        base_name = self.separator.join(parts)
        return f"{base_name}{self.extension}"

    def generate_path(self, job_info: JobInfo, base_dir: Path) -> Path:
        """
        Generate full file path.

        Args:
            job_info: Job information
            base_dir: Base directory for output

        Returns:
            Full Path object
        """
        filename = self.generate(job_info)
        return base_dir / filename

    def generate_with_increment(
        self,
        job_info: JobInfo,
        existing_files: list[str] | None = None
    ) -> str:
        """
        Generate filename, incrementing if duplicate exists.

        Args:
            job_info: Job information
            existing_files: List of existing filenames to check against

        Returns:
            Unique filename string
        """
        base_filename = self.generate(job_info)

        if not existing_files:
            return base_filename

        if base_filename not in existing_files:
            return base_filename

        # Find the next available increment
        base_name = base_filename.replace(self.extension, "")
        counter = 2

        while True:
            new_filename = f"{base_name}{self.separator}{counter}{self.extension}"
            if new_filename not in existing_files:
                return new_filename
            counter += 1

            # Safety limit
            if counter > 1000:
                raise ValueError("Too many duplicate files")

    def _sanitize(self, text: str) -> str:
        """
        Remove invalid filename characters.

        Args:
            text: Input text

        Returns:
            Sanitized text safe for filenames
        """
        return re.sub(self.INVALID_CHARS, "", text)

"""Text generator service for job information."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING

from src.domain.entities.point import Point
from src.domain.entities.bounding_box import BoundingBox
from src.domain.types import Side, PlateType, StandardColor

if TYPE_CHECKING:
    pass


@dataclass(frozen=True, slots=True)
class JobInfo:
    """Job information for text generation."""

    date: date
    job_number: str
    package_name: str
    side: Side
    plate_type: PlateType = PlateType.COPPER

    @property
    def formatted_date(self) -> str:
        """Get formatted date string."""
        return self.date.strftime("%Y-%m-%d")

    @property
    def side_text(self) -> str:
        """Get side as display text."""
        if self.side == Side.FRONT:
            return "앞"
        else:
            return "뒤"

    @property
    def plate_text(self) -> str:
        """Get plate type as display text."""
        if self.plate_type == PlateType.COPPER:
            return "동판"
        else:
            return "자동"


@dataclass(frozen=True, slots=True)
class TextEntity:
    """Text entity for DXF output."""

    content: str
    position: Point
    height: float = 3.5
    rotation: float = 0.0
    layer: str = "TEXT"
    color: int = StandardColor.WHITE


@dataclass
class TextGenerator:
    """Service for generating job information text entities."""

    text_height: float = 3.5
    line_spacing: float = 1.5
    margin_from_plywood: float = 5.0

    def generate_job_info_texts(self, job_info: JobInfo) -> list[TextEntity]:
        """
        Generate text entities for job information.

        Args:
            job_info: Job information

        Returns:
            List of TextEntity objects
        """
        texts = []

        # Main job info text
        main_text = self.format_job_text(job_info)
        texts.append(TextEntity(
            content=main_text,
            position=Point(0, 0),  # Will be repositioned
            height=self.text_height
        ))

        return texts

    def generate_side_marker(self, side: Side) -> TextEntity:
        """
        Generate side marker text.

        Args:
            side: Front or back side

        Returns:
            TextEntity for side marker
        """
        if side == Side.FRONT:
            content = "앞"
        else:
            content = "뒤"

        return TextEntity(
            content=content,
            position=Point(0, 0),  # Will be repositioned
            height=self.text_height * 2  # Larger for visibility
        )

    def generate_positioned_texts(
        self,
        job_info: JobInfo,
        plywood_bbox: BoundingBox
    ) -> list[TextEntity]:
        """
        Generate texts positioned relative to plywood frame.

        Args:
            job_info: Job information
            plywood_bbox: Bounding box of plywood frame

        Returns:
            List of positioned TextEntity objects
        """
        texts = []

        # Position text above plywood, left-aligned
        text_y = plywood_bbox.max_y + self.margin_from_plywood
        text_x = plywood_bbox.min_x

        # Date and job number
        texts.append(TextEntity(
            content=f"{job_info.formatted_date}  No.{job_info.job_number}",
            position=Point(text_x, text_y),
            height=self.text_height
        ))

        # Package name on second line
        text_y += self.text_height * self.line_spacing
        texts.append(TextEntity(
            content=job_info.package_name,
            position=Point(text_x, text_y),
            height=self.text_height
        ))

        # Side and plate type
        text_y += self.text_height * self.line_spacing
        texts.append(TextEntity(
            content=f"{job_info.side_text}  {job_info.plate_text}",
            position=Point(text_x, text_y),
            height=self.text_height
        ))

        return texts

    def generate_positioned_side_marker(
        self,
        side: Side,
        drawing_bbox: BoundingBox
    ) -> TextEntity:
        """
        Generate side marker positioned inside drawing area.

        Args:
            side: Front or back side
            drawing_bbox: Bounding box of the drawing

        Returns:
            Positioned TextEntity for side marker
        """
        marker = self.generate_side_marker(side)

        # Position in lower-right area of drawing
        x = drawing_bbox.max_x - 20
        y = drawing_bbox.min_y + 10

        return TextEntity(
            content=marker.content,
            position=Point(x, y),
            height=marker.height,
            layer=marker.layer,
            color=marker.color
        )

    def format_job_text(self, job_info: JobInfo) -> str:
        """
        Format complete job information as single text.

        Args:
            job_info: Job information

        Returns:
            Formatted text string
        """
        return (
            f"{job_info.formatted_date} No.{job_info.job_number} "
            f"{job_info.package_name} {job_info.side_text}"
        )

"""Tests for ElementRemover service."""
from __future__ import annotations

import pytest

from src.domain.entities.point import Point
from src.domain.entities.line import Line
from src.domain.entities.bounding_box import BoundingBox
from src.domain.services.element_remover import ElementRemover, RemovalMode
from src.domain.services.text_generator import TextEntity
from src.domain.types import LineCategory, StandardColor


class TestIdentifyExternalElements:
    """Test identifying external elements."""

    def test_identify_element_outside_left(self) -> None:
        """Test identifying element completely to the left."""
        remover = ElementRemover()
        plywood_bbox = BoundingBox(min_x=100, min_y=100, max_x=500, max_y=400)

        outside_line = Line(
            start=Point(0, 200),
            end=Point(50, 200),
            color=StandardColor.RED
        )
        inside_line = Line(
            start=Point(200, 200),
            end=Point(300, 200),
            color=StandardColor.RED
        )

        external = remover.identify_external_elements(
            [outside_line, inside_line], plywood_bbox
        )

        assert outside_line in external
        assert inside_line not in external

    def test_identify_element_outside_right(self) -> None:
        """Test identifying element completely to the right."""
        remover = ElementRemover()
        plywood_bbox = BoundingBox(min_x=100, min_y=100, max_x=500, max_y=400)

        outside_line = Line(
            start=Point(550, 200),
            end=Point(600, 200),
            color=StandardColor.RED
        )

        external = remover.identify_external_elements(
            [outside_line], plywood_bbox
        )

        assert outside_line in external

    def test_identify_element_outside_above(self) -> None:
        """Test identifying element completely above."""
        remover = ElementRemover()
        plywood_bbox = BoundingBox(min_x=100, min_y=100, max_x=500, max_y=400)

        outside_line = Line(
            start=Point(200, 450),
            end=Point(300, 450),
            color=StandardColor.RED
        )

        external = remover.identify_external_elements(
            [outside_line], plywood_bbox
        )

        assert outside_line in external

    def test_identify_element_outside_below(self) -> None:
        """Test identifying element completely below."""
        remover = ElementRemover()
        plywood_bbox = BoundingBox(min_x=100, min_y=100, max_x=500, max_y=400)

        outside_line = Line(
            start=Point(200, 50),
            end=Point(300, 50),
            color=StandardColor.RED
        )

        external = remover.identify_external_elements(
            [outside_line], plywood_bbox
        )

        assert outside_line in external

    def test_intersecting_element_not_external(self) -> None:
        """Test that intersecting element is not considered external."""
        remover = ElementRemover()
        plywood_bbox = BoundingBox(min_x=100, min_y=100, max_x=500, max_y=400)

        # Line crossing the boundary
        crossing_line = Line(
            start=Point(50, 200),
            end=Point(200, 200),
            color=StandardColor.RED
        )

        external = remover.identify_external_elements(
            [crossing_line], plywood_bbox
        )

        assert crossing_line not in external

    def test_plywood_layer_excluded(self) -> None:
        """Test that PLYWOOD layer is excluded from removal."""
        remover = ElementRemover()
        plywood_bbox = BoundingBox(min_x=100, min_y=100, max_x=500, max_y=400)

        plywood_line = Line(
            start=Point(0, 0),  # Outside
            end=Point(50, 0),
            layer="PLYWOOD",
            color=StandardColor.WHITE
        )

        external = remover.identify_external_elements(
            [plywood_line], plywood_bbox
        )

        assert plywood_line not in external

    def test_plywood_category_excluded(self) -> None:
        """Test that plywood category is excluded from removal."""
        remover = ElementRemover()
        plywood_bbox = BoundingBox(min_x=100, min_y=100, max_x=500, max_y=400)

        plywood_line = Line(
            start=Point(0, 0),  # Outside
            end=Point(50, 0),
            color=StandardColor.WHITE,
            category=LineCategory.PLYWOOD
        )

        external = remover.identify_external_elements(
            [plywood_line], plywood_bbox
        )

        assert plywood_line not in external


class TestRemoveExternalElements:
    """Test removing external elements."""

    def test_remove_all_external(self) -> None:
        """Test removing all external elements."""
        remover = ElementRemover()
        plywood_bbox = BoundingBox(min_x=100, min_y=100, max_x=500, max_y=400)

        outside = Line(start=Point(0, 0), end=Point(50, 0), color=StandardColor.RED)
        inside = Line(start=Point(200, 200), end=Point(300, 200), color=StandardColor.RED)

        result = remover.remove_external_elements(
            [outside, inside], plywood_bbox, RemovalMode.REMOVE_ALL
        )

        assert inside in result.kept_entities
        assert outside in result.removed_entities
        assert result.removal_count == 1

    def test_keep_auxiliary_mode(self) -> None:
        """Test keeping auxiliary lines."""
        remover = ElementRemover()
        plywood_bbox = BoundingBox(min_x=100, min_y=100, max_x=500, max_y=400)

        outside_aux = Line(
            start=Point(0, 0), end=Point(50, 0),
            color=StandardColor.GREEN,
            category=LineCategory.AUXILIARY
        )
        outside_cut = Line(
            start=Point(0, 50), end=Point(50, 50),
            color=StandardColor.RED,
            category=LineCategory.CUT
        )

        result = remover.remove_external_elements(
            [outside_aux, outside_cut], plywood_bbox, RemovalMode.KEEP_AUXILIARY
        )

        assert outside_aux in result.kept_entities
        assert outside_cut in result.removed_entities

    def test_kept_count_property(self) -> None:
        """Test kept_count property."""
        remover = ElementRemover()
        plywood_bbox = BoundingBox(min_x=100, min_y=100, max_x=500, max_y=400)

        line1 = Line(start=Point(200, 200), end=Point(300, 200), color=StandardColor.RED)
        line2 = Line(start=Point(200, 250), end=Point(300, 250), color=StandardColor.RED)

        result = remover.remove_external_elements(
            [line1, line2], plywood_bbox, RemovalMode.REMOVE_ALL
        )

        assert result.kept_count == 2
        assert result.removal_count == 0


class TestCustomExcludeLayers:
    """Test custom exclude layer configuration."""

    def test_custom_exclude_layers(self) -> None:
        """Test custom exclude layers."""
        remover = ElementRemover(exclude_layers=["PLYWOOD", "TEXT", "DIMENSION"])
        plywood_bbox = BoundingBox(min_x=100, min_y=100, max_x=500, max_y=400)

        dim_line = Line(
            start=Point(0, 0),  # Outside
            end=Point(50, 0),
            layer="DIMENSION",
            color=StandardColor.WHITE
        )

        external = remover.identify_external_elements(
            [dim_line], plywood_bbox
        )

        assert dim_line not in external

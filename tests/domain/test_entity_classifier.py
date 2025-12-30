"""Tests for EntityClassifier domain service."""
from __future__ import annotations

import pytest

from src.domain.entities.point import Point
from src.domain.entities.line import Line
from src.domain.entities.arc import Arc
from src.domain.services.entity_classifier import (
    EntityClassifier,
    UnclassifiedHandling,
    ClassificationResult,
)
from src.domain.types import LineCategory, StandardColor


class TestEntityClassifierByColor:
    """Test entity classification by color."""

    def test_red_color_classified_as_cut(self) -> None:
        """Test red color (ACI 1) is classified as CUT."""
        classifier = EntityClassifier()
        line = Line(
            start=Point(0, 0),
            end=Point(100, 0),
            color=StandardColor.RED
        )

        result = classifier.classify(line)

        assert result == LineCategory.CUT

    def test_blue_color_classified_as_crease(self) -> None:
        """Test blue color (ACI 5) is classified as CREASE."""
        classifier = EntityClassifier()
        line = Line(
            start=Point(0, 0),
            end=Point(100, 0),
            color=StandardColor.BLUE
        )

        result = classifier.classify(line)

        assert result == LineCategory.CREASE

    def test_green_color_classified_as_auxiliary(self) -> None:
        """Test green color (ACI 3) is classified as AUXILIARY."""
        classifier = EntityClassifier()
        line = Line(
            start=Point(0, 0),
            end=Point(100, 0),
            color=StandardColor.GREEN
        )

        result = classifier.classify(line)

        assert result == LineCategory.AUXILIARY

    def test_white_color_classified_as_plywood(self) -> None:
        """Test white color (ACI 7) is classified as PLYWOOD."""
        classifier = EntityClassifier()
        line = Line(
            start=Point(0, 0),
            end=Point(100, 0),
            color=StandardColor.WHITE
        )

        result = classifier.classify(line)

        assert result == LineCategory.PLYWOOD

    def test_unknown_color_classified_as_unknown(self) -> None:
        """Test unknown color is classified as UNKNOWN."""
        classifier = EntityClassifier()
        line = Line(
            start=Point(0, 0),
            end=Point(100, 0),
            color=StandardColor.YELLOW  # Not a standard die-cut color
        )

        result = classifier.classify(line)

        assert result == LineCategory.UNKNOWN


class TestEntityClassifierByLayer:
    """Test entity classification by layer name."""

    def test_cut_layer_classified_as_cut(self) -> None:
        """Test layer containing 'CUT' is classified as CUT."""
        classifier = EntityClassifier()
        line = Line(
            start=Point(0, 0),
            end=Point(100, 0),
            layer="CUT_LINE"
        )

        result = classifier.classify(line)

        assert result == LineCategory.CUT

    def test_korean_cut_layer_classified_as_cut(self) -> None:
        """Test layer containing '칼' is classified as CUT."""
        classifier = EntityClassifier()
        line = Line(
            start=Point(0, 0),
            end=Point(100, 0),
            layer="칼선"
        )

        result = classifier.classify(line)

        assert result == LineCategory.CUT

    def test_crease_layer_classified_as_crease(self) -> None:
        """Test layer containing 'CREASE' is classified as CREASE."""
        classifier = EntityClassifier()
        line = Line(
            start=Point(0, 0),
            end=Point(100, 0),
            layer="CREASE_LINE"
        )

        result = classifier.classify(line)

        assert result == LineCategory.CREASE

    def test_korean_crease_layer_classified_as_crease(self) -> None:
        """Test layer containing '괘' is classified as CREASE."""
        classifier = EntityClassifier()
        line = Line(
            start=Point(0, 0),
            end=Point(100, 0),
            layer="괘선"
        )

        result = classifier.classify(line)

        assert result == LineCategory.CREASE

    def test_aux_layer_classified_as_auxiliary(self) -> None:
        """Test layer containing 'AUX' is classified as AUXILIARY."""
        classifier = EntityClassifier()
        line = Line(
            start=Point(0, 0),
            end=Point(100, 0),
            layer="AUX_LINE"
        )

        result = classifier.classify(line)

        assert result == LineCategory.AUXILIARY

    def test_plywood_layer_classified_as_plywood(self) -> None:
        """Test layer containing 'PLYWOOD' is classified as PLYWOOD."""
        classifier = EntityClassifier()
        line = Line(
            start=Point(0, 0),
            end=Point(100, 0),
            layer="PLYWOOD"
        )

        result = classifier.classify(line)

        assert result == LineCategory.PLYWOOD

    def test_korean_plywood_layer_classified_as_plywood(self) -> None:
        """Test layer containing '합판' is classified as PLYWOOD."""
        classifier = EntityClassifier()
        line = Line(
            start=Point(0, 0),
            end=Point(100, 0),
            layer="합판"
        )

        result = classifier.classify(line)

        assert result == LineCategory.PLYWOOD


class TestEntityClassifierPriority:
    """Test classification priority (layer takes precedence over color)."""

    def test_layer_takes_precedence_over_color(self) -> None:
        """Test that layer name takes precedence over color."""
        classifier = EntityClassifier()
        # Red color (normally CUT) but on CREASE layer
        line = Line(
            start=Point(0, 0),
            end=Point(100, 0),
            color=StandardColor.RED,
            layer="CREASE"
        )

        result = classifier.classify(line)

        assert result == LineCategory.CREASE

    def test_color_used_when_layer_is_default(self) -> None:
        """Test that color is used when layer is default (0 or empty)."""
        classifier = EntityClassifier()
        line = Line(
            start=Point(0, 0),
            end=Point(100, 0),
            color=StandardColor.RED,
            layer="0"  # Default layer
        )

        result = classifier.classify(line)

        assert result == LineCategory.CUT


class TestEntityClassifierBatch:
    """Test batch classification of entities."""

    def test_classify_multiple_entities(self) -> None:
        """Test classifying multiple entities at once."""
        classifier = EntityClassifier()
        entities = [
            Line(start=Point(0, 0), end=Point(100, 0), color=StandardColor.RED),
            Line(start=Point(0, 0), end=Point(0, 100), color=StandardColor.BLUE),
            Line(start=Point(0, 0), end=Point(50, 50), color=StandardColor.GREEN),
        ]

        results = classifier.classify_all(entities)

        assert results[LineCategory.CUT] == [entities[0]]
        assert results[LineCategory.CREASE] == [entities[1]]
        assert results[LineCategory.AUXILIARY] == [entities[2]]

    def test_classify_returns_all_categories(self) -> None:
        """Test that classify_all returns all category keys."""
        classifier = EntityClassifier()
        entities = [
            Line(start=Point(0, 0), end=Point(100, 0), color=StandardColor.RED),
        ]

        results = classifier.classify_all(entities)

        # Should have all categories even if empty
        for category in LineCategory:
            assert category in results

    def test_apply_categories_to_entities(self) -> None:
        """Test applying categories to entities modifies their category field."""
        classifier = EntityClassifier()
        line = Line(
            start=Point(0, 0),
            end=Point(100, 0),
            color=StandardColor.RED
        )

        updated = classifier.apply_category(line)

        assert updated.category == LineCategory.CUT


class TestEntityClassifierArc:
    """Test classification of Arc entities."""

    def test_arc_classified_by_color(self) -> None:
        """Test Arc entity is classified by color."""
        classifier = EntityClassifier()
        arc = Arc(
            center=Point(0, 0),
            radius=50,
            start_angle=0,
            end_angle=90,
            color=StandardColor.RED
        )

        result = classifier.classify(arc)

        assert result == LineCategory.CUT

    def test_arc_classified_by_layer(self) -> None:
        """Test Arc entity is classified by layer."""
        classifier = EntityClassifier()
        arc = Arc(
            center=Point(0, 0),
            radius=50,
            start_angle=0,
            end_angle=90,
            layer="CREASE"
        )

        result = classifier.classify(arc)

        assert result == LineCategory.CREASE


class TestUnclassifiedHandling:
    """Test handling of unclassified entities."""

    def test_default_treats_unclassified_as_cut(self) -> None:
        """Test that default handling treats unclassified as CUT."""
        classifier = EntityClassifier()
        line = Line(
            start=Point(0, 0),
            end=Point(100, 0),
            color=StandardColor.YELLOW,  # Not a standard color
            layer="0"
        )

        result = classifier.apply_categories_with_result([line])

        assert result.classified_entities[0].category == LineCategory.CUT
        assert result.unclassified_count == 1

    def test_treat_as_crease(self) -> None:
        """Test treating unclassified entities as CREASE."""
        classifier = EntityClassifier(
            unclassified_handling=UnclassifiedHandling.TREAT_AS_CREASE
        )
        line = Line(
            start=Point(0, 0),
            end=Point(100, 0),
            color=StandardColor.YELLOW
        )

        result = classifier.apply_categories_with_result([line])

        assert result.classified_entities[0].category == LineCategory.CREASE

    def test_treat_as_auxiliary(self) -> None:
        """Test treating unclassified entities as AUXILIARY."""
        classifier = EntityClassifier(
            unclassified_handling=UnclassifiedHandling.TREAT_AS_AUXILIARY
        )
        line = Line(
            start=Point(0, 0),
            end=Point(100, 0),
            color=StandardColor.YELLOW
        )

        result = classifier.apply_categories_with_result([line])

        assert result.classified_entities[0].category == LineCategory.AUXILIARY

    def test_keep_unknown(self) -> None:
        """Test keeping unclassified entities as UNKNOWN."""
        classifier = EntityClassifier(
            unclassified_handling=UnclassifiedHandling.KEEP_UNKNOWN
        )
        line = Line(
            start=Point(0, 0),
            end=Point(100, 0),
            color=StandardColor.YELLOW
        )

        result = classifier.apply_categories_with_result([line])

        assert result.classified_entities[0].category == LineCategory.UNKNOWN

    def test_skip_unclassified(self) -> None:
        """Test skipping unclassified entities."""
        classifier = EntityClassifier(
            unclassified_handling=UnclassifiedHandling.SKIP
        )
        entities = [
            Line(start=Point(0, 0), end=Point(100, 0), color=StandardColor.YELLOW),
            Line(start=Point(0, 10), end=Point(100, 10), color=StandardColor.RED),
        ]

        result = classifier.apply_categories_with_result(entities)

        # Should only have one entity (the CUT line)
        assert len(result.classified_entities) == 1
        assert result.classified_entities[0].category == LineCategory.CUT
        assert result.unclassified_count == 1


class TestClassificationResult:
    """Test ClassificationResult properties."""

    def test_total_count_property(self) -> None:
        """Test total count includes skipped entities."""
        classifier = EntityClassifier(
            unclassified_handling=UnclassifiedHandling.SKIP
        )
        entities = [
            Line(start=Point(0, 0), end=Point(100, 0), color=StandardColor.YELLOW),
            Line(start=Point(0, 10), end=Point(100, 10), color=StandardColor.RED),
        ]

        result = classifier.apply_categories_with_result(entities)

        assert result.total_count == 2  # 1 kept + 1 skipped

    def test_statistics_dict(self) -> None:
        """Test statistics dictionary."""
        classifier = EntityClassifier()
        entities = [
            Line(start=Point(0, 0), end=Point(100, 0), color=StandardColor.RED),
            Line(start=Point(0, 10), end=Point(100, 10), color=StandardColor.BLUE),
            Line(start=Point(0, 20), end=Point(100, 20), color=StandardColor.RED),
        ]

        result = classifier.apply_categories_with_result(entities)

        assert result.statistics[LineCategory.CUT] == 2
        assert result.statistics[LineCategory.CREASE] == 1


class TestCountUnclassified:
    """Test counting unclassified entities."""

    def test_count_unclassified_entities(self) -> None:
        """Test counting entities that would be unclassified."""
        classifier = EntityClassifier()
        entities = [
            Line(start=Point(0, 0), end=Point(100, 0), color=StandardColor.YELLOW),
            Line(start=Point(0, 10), end=Point(100, 10), color=StandardColor.RED),
            Line(start=Point(0, 20), end=Point(100, 20), color=StandardColor.CYAN),
        ]

        count = classifier.count_unclassified(entities)

        assert count == 2  # Yellow and Cyan are not standard colors

    def test_get_unclassified_entities_list(self) -> None:
        """Test getting list of unclassified entities."""
        classifier = EntityClassifier()
        entities = [
            Line(start=Point(0, 0), end=Point(100, 0), color=StandardColor.YELLOW),
            Line(start=Point(0, 10), end=Point(100, 10), color=StandardColor.RED),
        ]

        unclassified = classifier.get_unclassified_entities(entities)

        assert len(unclassified) == 1
        assert unclassified[0].color == StandardColor.YELLOW

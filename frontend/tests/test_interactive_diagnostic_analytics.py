"""Tests for interactive diagnostic analytics."""

import pytest

from ecobiome.ui.desktop import (
    DiagnosticAnalyticsViewModel,
    HypothesisDetailViewModel,
)


def make_hypothesis(
    *,
    identifier: str = "H1",
    probability: int = 78,
) -> HypothesisDetailViewModel:
    """Create one deterministic hypothesis."""
    return HypothesisDetailViewModel(
        identifier=identifier,
        title="Capteur de luminance déréglé",
        explanation="Dérive progressive probable.",
        recommendation="Recalibrer le capteur.",
        probability=probability,
        accent="#70D68D",
    )


def make_analytics() -> DiagnosticAnalyticsViewModel:
    """Create one deterministic analytics model."""
    return DiagnosticAnalyticsViewModel(
        quality_score=82,
        quality_history=(
            58,
            64,
            71,
            76,
            82,
        ),
        hypotheses=(
            make_hypothesis(),
            make_hypothesis(
                identifier="H2",
                probability=46,
            ),
        ),
        high_quality_count=18,
        medium_quality_count=6,
        low_quality_count=2,
        rejected_count=1,
    )


def test_analytics_exposes_observation_total() -> None:
    analytics = make_analytics()

    assert analytics.observation_count == 27


def test_analytics_builds_probability_bars() -> None:
    analytics = make_analytics()

    bars = analytics.probability_bars

    assert len(bars) == 2
    assert bars[0].identifier == "H1"
    assert bars[0].probability == 78
    assert bars[1].identifier == "H2"


def test_hypothesis_can_be_retrieved() -> None:
    analytics = make_analytics()

    hypothesis = analytics.hypothesis("H2")

    assert hypothesis.identifier == "H2"
    assert hypothesis.probability == 46


def test_unknown_hypothesis_is_rejected() -> None:
    analytics = make_analytics()

    with pytest.raises(
        KeyError,
        match="Unknown hypothesis identifier",
    ):
        analytics.hypothesis("H99")


def test_duplicate_hypothesis_identifiers_are_rejected() -> None:
    hypothesis = make_hypothesis()

    with pytest.raises(
        ValueError,
        match="must be unique",
    ):
        DiagnosticAnalyticsViewModel(
            quality_score=80,
            quality_history=(80,),
            hypotheses=(
                hypothesis,
                hypothesis,
            ),
            high_quality_count=1,
            medium_quality_count=0,
            low_quality_count=0,
            rejected_count=0,
        )


def test_invalid_quality_history_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Quality-history values",
    ):
        DiagnosticAnalyticsViewModel(
            quality_score=80,
            quality_history=(
                50,
                101,
            ),
            hypotheses=(),
            high_quality_count=0,
            medium_quality_count=0,
            low_quality_count=0,
            rejected_count=0,
        )


def test_negative_quality_counter_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        DiagnosticAnalyticsViewModel(
            quality_score=80,
            quality_history=(80,),
            hypotheses=(),
            high_quality_count=-1,
            medium_quality_count=0,
            low_quality_count=0,
            rejected_count=0,
        )


def test_hypothesis_probability_is_validated() -> None:
    with pytest.raises(
        ValueError,
        match="between zero and one hundred",
    ):
        make_hypothesis(
            probability=120
        )


def test_analytics_ui_imports_without_window() -> None:
    from ecobiome.ui.desktop import (
        DiagnosticAnalyticsPanel,
        EcoBiomeDesktopApp,
    )

    assert DiagnosticAnalyticsPanel is not None
    assert EcoBiomeDesktopApp is not None

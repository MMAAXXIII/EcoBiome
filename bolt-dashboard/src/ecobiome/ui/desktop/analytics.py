"""Presentation models for interactive diagnostic analytics."""

from __future__ import annotations

from dataclasses import dataclass

from ecobiome.ui.desktop.charts import ProbabilityBar


@dataclass(frozen=True, slots=True, kw_only=True)
class HypothesisDetailViewModel:
    """Describe the explanatory detail of one hypothesis."""

    identifier: str
    title: str
    explanation: str
    recommendation: str
    probability: int
    accent: str

    def __post_init__(self) -> None:
        """Validate and normalize one hypothesis detail."""
        identifier = self.identifier.strip()
        title = self.title.strip()
        explanation = self.explanation.strip()
        recommendation = self.recommendation.strip()

        if not identifier:
            raise ValueError(
                "Hypothesis identifier cannot be empty."
            )

        if not title:
            raise ValueError(
                "Hypothesis title cannot be empty."
            )

        if not explanation:
            raise ValueError(
                "Hypothesis explanation cannot be empty."
            )

        if not recommendation:
            raise ValueError(
                "Hypothesis recommendation cannot be empty."
            )

        if not 0 <= self.probability <= 100:
            raise ValueError(
                "Hypothesis probability must be between "
                "zero and one hundred."
            )

        object.__setattr__(
            self,
            "identifier",
            identifier,
        )

        object.__setattr__(
            self,
            "title",
            title,
        )

        object.__setattr__(
            self,
            "explanation",
            explanation,
        )

        object.__setattr__(
            self,
            "recommendation",
            recommendation,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class DiagnosticAnalyticsViewModel:
    """Contain interface-ready diagnostic analytics."""

    quality_score: int | None
    quality_history: tuple[int, ...]
    hypotheses: tuple[HypothesisDetailViewModel, ...]
    high_quality_count: int
    medium_quality_count: int
    low_quality_count: int
    rejected_count: int

    def __post_init__(self) -> None:
        """Validate one complete analytics model."""
        if (
            self.quality_score is not None
            and not 0 <= self.quality_score <= 100
        ):
            raise ValueError(
                "Quality score must be between zero "
                "and one hundred."
            )

        if any(
            not 0 <= value <= 100
            for value in self.quality_history
        ):
            raise ValueError(
                "Quality-history values must be between "
                "zero and one hundred."
            )

        quality_counts = (
            self.high_quality_count,
            self.medium_quality_count,
            self.low_quality_count,
            self.rejected_count,
        )

        if any(count < 0 for count in quality_counts):
            raise ValueError(
                "Quality counters cannot be negative."
            )

        identifiers = tuple(
            hypothesis.identifier
            for hypothesis in self.hypotheses
        )

        if len(identifiers) != len(set(identifiers)):
            raise ValueError(
                "Hypothesis identifiers must be unique."
            )

    @property
    def observation_count(self) -> int:
        """Return the total classified observation count."""
        return (
            self.high_quality_count
            + self.medium_quality_count
            + self.low_quality_count
            + self.rejected_count
        )

    @property
    def probability_bars(
        self,
    ) -> tuple[ProbabilityBar, ...]:
        """Return hypotheses as reusable probability bars."""
        return tuple(
            ProbabilityBar(
                identifier=hypothesis.identifier,
                label=hypothesis.title,
                probability=hypothesis.probability,
                accent=hypothesis.accent,
            )
            for hypothesis in self.hypotheses
        )

    def hypothesis(
        self,
        identifier: str,
    ) -> HypothesisDetailViewModel:
        """Return one hypothesis by identifier."""
        normalized_identifier = identifier.strip()

        for hypothesis in self.hypotheses:
            if (
                hypothesis.identifier
                == normalized_identifier
            ):
                return hypothesis

        raise KeyError(
            f"Unknown hypothesis identifier: "
            f"{normalized_identifier}."
        )

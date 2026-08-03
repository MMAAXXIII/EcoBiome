"""Explicit typed registry for EcoBiome reasoning components."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Protocol, TypeVar

from ecobiome.contracts import QualityRule
from ecobiome.reasoning.abduction.engine import (
    HypothesisGenerationRule,
)
from ecobiome.reasoning.consistency.engine import (
    ConsistencyRule,
)
from ecobiome.reasoning.experiment.planner import (
    ExperimentPlanningRule,
)


class IdentifiedComponent(Protocol):
    """Structural contract for components with an identifier."""

    @property
    def identifier(self) -> str:
        """Return the component identifier."""
        ...


ComponentT = TypeVar(
    "ComponentT",
    bound=IdentifiedComponent,
)


@dataclass(frozen=True, slots=True)
class ReasoningComponentSummary:
    """Summarize registered reasoning components."""

    quality_rule_count: int
    consistency_rule_count: int
    hypothesis_rule_count: int
    experiment_rule_count: int

    @property
    def total_count(self) -> int:
        """Return the total number of registered components."""
        return (
            self.quality_rule_count
            + self.consistency_rule_count
            + self.hypothesis_rule_count
            + self.experiment_rule_count
        )


@dataclass(slots=True)
class ReasoningComponentRegistry:
    """Register reasoning components by explicit functional family."""

    _quality_rules: dict[str, QualityRule] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _consistency_rules: dict[str, ConsistencyRule] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _hypothesis_rules: dict[
        str,
        HypothesisGenerationRule,
    ] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _experiment_rules: dict[
        str,
        ExperimentPlanningRule,
    ] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )

    def register_quality(
        self,
        rule: QualityRule,
    ) -> None:
        """Register one observation-quality rule."""
        self._validate_callable(
            rule=rule,
            method_name="assess",
            family_name="quality",
        )
        self._register(
            collection=self._quality_rules,
            component=rule,
            family_name="quality",
        )

    def register_consistency(
        self,
        rule: ConsistencyRule,
    ) -> None:
        """Register one multi-observation consistency rule."""
        self._validate_callable(
            rule=rule,
            method_name="evaluate",
            family_name="consistency",
        )
        self._register(
            collection=self._consistency_rules,
            component=rule,
            family_name="consistency",
        )

    def register_hypothesis(
        self,
        rule: HypothesisGenerationRule,
    ) -> None:
        """Register one abductive hypothesis-generation rule."""
        self._validate_callable(
            rule=rule,
            method_name="generate",
            family_name="hypothesis-generation",
        )
        self._register(
            collection=self._hypothesis_rules,
            component=rule,
            family_name="hypothesis-generation",
        )

    def register_experiment(
        self,
        rule: ExperimentPlanningRule,
    ) -> None:
        """Register one experiment-planning rule."""
        self._validate_callable(
            rule=rule,
            method_name="plan",
            family_name="experiment-planning",
        )
        self._register(
            collection=self._experiment_rules,
            component=rule,
            family_name="experiment-planning",
        )

    def register_quality_many(
        self,
        rules: Iterable[QualityRule],
    ) -> None:
        """Register several quality rules."""
        for rule in rules:
            self.register_quality(rule)

    def register_consistency_many(
        self,
        rules: Iterable[ConsistencyRule],
    ) -> None:
        """Register several consistency rules."""
        for rule in rules:
            self.register_consistency(rule)

    def register_hypothesis_many(
        self,
        rules: Iterable[HypothesisGenerationRule],
    ) -> None:
        """Register several hypothesis-generation rules."""
        for rule in rules:
            self.register_hypothesis(rule)

    def register_experiment_many(
        self,
        rules: Iterable[ExperimentPlanningRule],
    ) -> None:
        """Register several experiment-planning rules."""
        for rule in rules:
            self.register_experiment(rule)

    @staticmethod
    def _validate_callable(
        *,
        rule: object,
        method_name: str,
        family_name: str,
    ) -> None:
        """Validate the method required by one component family."""
        identifier = getattr(rule, "identifier", None)

        if not isinstance(identifier, str):
            raise TypeError(
                f"A {family_name} component requires "
                "a string identifier."
            )

        if not callable(getattr(rule, method_name, None)):
            raise TypeError(
                f"{family_name.capitalize()} component "
                f"{identifier!r} must implement {method_name}()."
            )

    @staticmethod
    def _register(
        *,
        collection: dict[str, ComponentT],
        component: ComponentT,
        family_name: str,
    ) -> None:
        """Register a component after identifier validation."""
        identifier = component.identifier.strip()

        if not identifier:
            raise ValueError(
                f"A {family_name} component requires "
                "a non-empty identifier."
            )

        if identifier in collection:
            raise ValueError(
                f"Duplicate {family_name} component identifier: "
                f"{identifier!r}."
            )

        collection[identifier] = component

    @property
    def quality_rules(self) -> tuple[QualityRule, ...]:
        """Return quality rules in identifier order."""
        return self._ordered_values(self._quality_rules)

    @property
    def consistency_rules(
        self,
    ) -> tuple[ConsistencyRule, ...]:
        """Return consistency rules in identifier order."""
        return self._ordered_values(
            self._consistency_rules
        )

    @property
    def hypothesis_rules(
        self,
    ) -> tuple[HypothesisGenerationRule, ...]:
        """Return hypothesis-generation rules in identifier order."""
        return self._ordered_values(
            self._hypothesis_rules
        )

    @property
    def experiment_rules(
        self,
    ) -> tuple[ExperimentPlanningRule, ...]:
        """Return experiment-planning rules in identifier order."""
        return self._ordered_values(
            self._experiment_rules
        )

    @staticmethod
    def _ordered_values(
        collection: Mapping[str, ComponentT],
    ) -> tuple[ComponentT, ...]:
        """Return registered values sorted by identifier."""
        return tuple(
            component
            for _, component in sorted(
                collection.items()
            )
        )

    @property
    def summary(self) -> ReasoningComponentSummary:
        """Return component counts by family."""
        return ReasoningComponentSummary(
            quality_rule_count=len(self._quality_rules),
            consistency_rule_count=len(
                self._consistency_rules
            ),
            hypothesis_rule_count=len(
                self._hypothesis_rules
            ),
            experiment_rule_count=len(
                self._experiment_rules
            ),
        )

"""Causal explanation engine."""

from dataclasses import dataclass

from ecobiome.knowledge.registry import KnowledgeRegistry


@dataclass(frozen=True, slots=True)
class ExplanationResult:
    """Result of one causal explanation request."""

    target: str
    text: str
    relation_ids: tuple[str, ...]
    found: bool


class ExplanationEngine:
    """Build explanations from registered scientific relations."""

    def __init__(self, registry: KnowledgeRegistry) -> None:
        self._registry = registry

    def explain_why(self, target: str) -> ExplanationResult:
        """Explain which registered relations influence a target."""
        normalized_target = target.strip()

        if not normalized_target:
            raise ValueError("An explanation target is required.")

        relations = sorted(
            (
                relation
                for relation in self._registry.relations
                if relation.target == normalized_target
            ),
            key=lambda relation: relation.identifier,
        )

        if not relations:
            return ExplanationResult(
                target=normalized_target,
                text=(
                    "No causal relation is currently registered "
                    f"for {normalized_target}."
                ),
                relation_ids=(),
                found=False,
            )

        lines = [
            f"Why does {normalized_target} change?",
            "",
        ]

        for relation in relations:
            lines.extend(
                [
                    f"- {relation.source}",
                    f"  {relation.effect} {relation.target}",
                    f"  {relation.explanation}",
                    (
                        "  Evidence level: "
                        f"{relation.confidence}; strength: "
                        f"{relation.strength}."
                    ),
                    "",
                ]
            )

        return ExplanationResult(
            target=normalized_target,
            text="\n".join(lines).rstrip(),
            relation_ids=tuple(
                relation.identifier for relation in relations
            ),
            found=True,
        )

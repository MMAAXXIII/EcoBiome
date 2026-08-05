"""Multi-step causal-chain reasoning."""

from dataclasses import dataclass

from ecobiome.knowledge.registry import KnowledgeRegistry


@dataclass(frozen=True, slots=True)
class CausalStep:
    """One directional step in a causal explanation."""

    relation_id: str
    source: str
    effect: str
    target: str
    explanation: str
    strength: str
    confidence: str


@dataclass(frozen=True, slots=True)
class CausalChainResult:
    """Result of tracing causes toward one target variable."""

    target: str
    steps: tuple[CausalStep, ...]
    text: str
    found: bool


class CausalChainEngine:
    """Trace registered causal relations across multiple steps."""

    def __init__(self, registry: KnowledgeRegistry) -> None:
        self._registry = registry

    def trace_to(
        self,
        target: str,
        *,
        maximum_depth: int = 8,
    ) -> CausalChainResult:
        """Trace upstream causes and return them in causal order."""
        normalized_target = target.strip()

        if not normalized_target:
            raise ValueError("A causal-chain target is required.")

        if maximum_depth <= 0:
            raise ValueError("maximum_depth must be greater than zero.")

        steps: list[CausalStep] = []
        visited_relations: set[str] = set()
        active_nodes: set[str] = set()

        def visit(node: str, depth: int) -> None:
            if depth >= maximum_depth or node in active_nodes:
                return

            active_nodes.add(node)

            incoming_relations = sorted(
                (
                    relation
                    for relation in self._registry.relations
                    if relation.target == node
                ),
                key=lambda relation: relation.identifier,
            )

            for relation in incoming_relations:
                if relation.identifier in visited_relations:
                    continue

                visit(relation.source, depth + 1)

                visited_relations.add(relation.identifier)
                steps.append(
                    CausalStep(
                        relation_id=relation.identifier,
                        source=relation.source,
                        effect=relation.effect,
                        target=relation.target,
                        explanation=relation.explanation,
                        strength=relation.strength,
                        confidence=relation.confidence,
                    )
                )

            active_nodes.remove(node)

        visit(normalized_target, 0)

        if not steps:
            return CausalChainResult(
                target=normalized_target,
                steps=(),
                text=(
                    "No causal chain is currently registered for "
                    f"{normalized_target}."
                ),
                found=False,
            )

        lines = [f"Causal chain toward {normalized_target}:", ""]

        for index, step in enumerate(steps, start=1):
            lines.extend(
                [
                    f"{index}. {step.source}",
                    f"   ↓ {step.effect}",
                    f"   {step.target}",
                    f"   {step.explanation}",
                    (
                        f"   Confidence: {step.confidence}; "
                        f"strength: {step.strength}."
                    ),
                    "",
                ]
            )

        return CausalChainResult(
            target=normalized_target,
            steps=tuple(steps),
            text="\n".join(lines).rstrip(),
            found=True,
        )

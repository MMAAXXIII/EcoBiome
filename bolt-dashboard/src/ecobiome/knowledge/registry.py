"""Scientific knowledge registry."""

from ecobiome.knowledge.relation import ScientificRelation
from ecobiome.knowledge.variable import ScientificVariable


class KnowledgeRegistry:
    """Central registry for scientific knowledge."""

    def __init__(self) -> None:
        self.variables: dict[str, ScientificVariable] = {}
        self.relations: list[ScientificRelation] = []

    def add_variable(self, variable: ScientificVariable) -> None:
        self.variables[variable.identifier] = variable

    def add_relation(self, relation: ScientificRelation) -> None:
        self.relations.append(relation)

    def relations_from(
        self,
        source: str,
    ) -> list[ScientificRelation]:
        return [
            relation
            for relation in self.relations
            if relation.source == source
        ]

    def explain(self, variable: str) -> str:
        """Return a human-readable explanation."""

        relations = self.relations_from(variable)

        if not relations:
            return f"No scientific relation found for {variable}."

        lines = []

        for relation in relations:
            lines.append(
                f"{relation.source}\n"
                f"  ↓ ({relation.effect})\n"
                f"{relation.target}\n\n"
                f"{relation.explanation}"
            )

        return "\n\n".join(lines)

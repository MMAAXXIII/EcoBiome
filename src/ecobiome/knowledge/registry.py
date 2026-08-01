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

    def get_variable(
        self,
        identifier: str,
    ) -> ScientificVariable | None:
        return self.variables.get(identifier)

    def relations_from(
        self,
        source: str,
    ) -> list[ScientificRelation]:
        """Return every outgoing relation."""
        return [
            relation
            for relation in self.relations
            if relation.source == source
        ]

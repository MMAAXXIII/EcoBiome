"""In-memory registry for scientific knowledge."""

from ecobiome.knowledge.variable import ScientificVariable


class KnowledgeRegistry:
    """Store validated scientific knowledge in memory."""

    def __init__(self) -> None:
        self._variables: dict[str, ScientificVariable] = {}

    def add_variable(self, variable: ScientificVariable) -> None:
        """Register a variable while preventing duplicate identifiers."""
        if variable.identifier in self._variables:
            raise ValueError(
                f"Scientific variable {variable.identifier!r} "
                "is already registered."
            )

        self._variables[variable.identifier] = variable

    def get_variable(self, identifier: str) -> ScientificVariable:
        """Return one variable by its stable identifier."""
        try:
            return self._variables[identifier]
        except KeyError as error:
            raise KeyError(
                f"Unknown scientific variable: {identifier!r}."
            ) from error

    def list_variables(self) -> tuple[ScientificVariable, ...]:
        """Return all variables ordered by identifier."""
        return tuple(
            self._variables[identifier]
            for identifier in sorted(self._variables)
        )

    def find_by_category(
        self,
        category: str,
    ) -> tuple[ScientificVariable, ...]:
        """Return variables belonging to one category."""
        return tuple(
            variable
            for variable in self.list_variables()
            if variable.category == category
        )

    @property
    def variable_count(self) -> int:
        """Return the number of registered variables."""
        return len(self._variables)

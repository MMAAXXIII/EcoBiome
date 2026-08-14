"""Scientific experiments designed to reduce diagnostic uncertainty."""

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True, slots=True, kw_only=True)
class ExperimentStep:
    """Represent one ordered action in a scientific experiment."""

    instruction: str
    expected_result: str = ""

    def __post_init__(self) -> None:
        """Validate and normalize the experiment step."""
        instruction = self.instruction.strip()
        expected_result = self.expected_result.strip()

        if not instruction:
            raise ValueError(
                "An experiment step requires an instruction."
            )

        object.__setattr__(self, "instruction", instruction)
        object.__setattr__(
            self,
            "expected_result",
            expected_result,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class Experiment:
    """Represent a proposed experiment for testing hypotheses."""

    identifier: str
    title: str
    objective: str
    steps: tuple[ExperimentStep, ...]
    tested_hypothesis_ids: tuple[str, ...]
    expected_observation_ids: tuple[str, ...] = ()
    required_devices: tuple[str, ...] = ()
    safety_notes: tuple[str, ...] = ()
    estimated_information_gain: float = 0.0
    estimated_duration: timedelta = timedelta()

    def __post_init__(self) -> None:
        """Validate and normalize the experiment."""
        identifier = self.identifier.strip()
        title = self.title.strip()
        objective = self.objective.strip()

        if not identifier:
            raise ValueError(
                "An experiment requires an identifier."
            )

        if "." not in identifier:
            raise ValueError(
                "Experiment identifier must contain a domain prefix."
            )

        if not title:
            raise ValueError(
                "An experiment requires a title."
            )

        if not objective:
            raise ValueError(
                "An experiment requires an objective."
            )

        if not self.steps:
            raise ValueError(
                "An experiment requires at least one step."
            )

        if not self.tested_hypothesis_ids:
            raise ValueError(
                "An experiment must test at least one hypothesis."
            )

        if not 0.0 <= self.estimated_information_gain <= 1.0:
            raise ValueError(
                "estimated_information_gain must be between 0 and 1."
            )

        if self.estimated_duration < timedelta():
            raise ValueError(
                "estimated_duration cannot be negative."
            )

        tested_hypothesis_ids = self._normalize_strings(
            self.tested_hypothesis_ids
        )
        expected_observation_ids = self._normalize_strings(
            self.expected_observation_ids
        )
        required_devices = self._normalize_strings(
            self.required_devices
        )
        safety_notes = self._normalize_strings(
            self.safety_notes
        )

        if not tested_hypothesis_ids:
            raise ValueError(
                "An experiment must test at least one hypothesis."
            )

        object.__setattr__(self, "identifier", identifier)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "objective", objective)
        object.__setattr__(
            self,
            "tested_hypothesis_ids",
            tested_hypothesis_ids,
        )
        object.__setattr__(
            self,
            "expected_observation_ids",
            expected_observation_ids,
        )
        object.__setattr__(
            self,
            "required_devices",
            required_devices,
        )
        object.__setattr__(
            self,
            "safety_notes",
            safety_notes,
        )

    @staticmethod
    def _normalize_strings(
        values: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Strip, remove empty values, and preserve unique order."""
        return tuple(
            dict.fromkeys(
                value.strip()
                for value in values
                if value.strip()
            )
        )

    @property
    def step_count(self) -> int:
        """Return the number of experiment steps."""
        return len(self.steps)

    @property
    def requires_human_intervention(self) -> bool:
        """Return whether a human-operated device is required."""
        return "human.operator" in self.required_devices

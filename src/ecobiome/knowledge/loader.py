"""Knowledge base loading utilities."""

from pathlib import Path
from typing import cast

import yaml

from ecobiome.knowledge.variable import ScientificVariable


def load_yaml(path: Path) -> dict[str, object]:
    """Load one YAML mapping."""
    with path.open(encoding="utf-8") as file:
        raw_data = yaml.safe_load(file)

    if not isinstance(raw_data, dict):
        raise TypeError(f"{path} must contain a YAML mapping.")

    return cast(dict[str, object], raw_data)


def _required_string(
    data: dict[str, object],
    field_name: str,
    path: Path,
) -> str:
    """Read and validate one required string field."""
    value = data.get(field_name)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"{path}: field {field_name!r} must be a non-empty string."
        )

    return value.strip()


def _optional_string(
    data: dict[str, object],
    field_name: str,
    path: Path,
) -> str | None:
    """Read and validate one optional string field."""
    value = data.get(field_name)

    if value is None:
        return None

    if not isinstance(value, str):
        raise TypeError(
            f"{path}: field {field_name!r} must be a string or null."
        )

    return value.strip()


def load_scientific_variable(path: Path) -> ScientificVariable:
    """Load and validate one scientific variable from YAML."""
    data = load_yaml(path)

    return ScientificVariable(
        identifier=_required_string(data, "id", path),
        name=_required_string(data, "name", path),
        description=_required_string(data, "description", path),
        unit=_optional_string(data, "unit", path),
        display_unit=_optional_string(data, "display_unit", path),
        category=_optional_string(data, "category", path),
    )

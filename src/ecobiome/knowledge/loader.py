"""Knowledge base loader."""

from pathlib import Path

import yaml


def load_yaml(path: Path) -> dict:
    """Load one YAML file."""

    with path.open(encoding="utf-8") as file:
        return yaml.safe_load(file)
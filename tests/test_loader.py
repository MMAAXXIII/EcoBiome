from pathlib import Path

from ecobiome.knowledge.loader import load_yaml


def test_load_yaml() -> None:
    data = load_yaml(
        Path(
            "src/ecobiome/knowledge/base/physics/variables/water_volume.yaml"
        )
    )

    assert data["id"] == "physics.water_volume"

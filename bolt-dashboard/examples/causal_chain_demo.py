"""Demonstrate multi-step causal reasoning."""

from pathlib import Path

from ecobiome.knowledge.directory_loader import load_knowledge_directory
from ecobiome.reasoning import CausalChainEngine


def main() -> None:
    """Load EcoBiome knowledge and display one causal chain."""
    registry = load_knowledge_directory(
        Path("src/ecobiome/knowledge/base")
    )
    engine = CausalChainEngine(registry)

    result = engine.trace_to("physics.temperature_fluctuation")

    print("=" * 64)
    print("EcoBiome — Causal Reasoning")
    print("=" * 64)
    print(result.text)


if __name__ == "__main__":
    main()

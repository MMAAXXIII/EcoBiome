"""Demonstrate automatic EcoBiome knowledge loading."""

from pathlib import Path

from ecobiome.knowledge.directory_loader import (
    load_knowledge_directory,
)
from ecobiome.reasoning import ExplanationEngine


def main() -> None:
    """Load the knowledge base and print one causal explanation."""
    knowledge_base = Path("src/ecobiome/knowledge/base")
    registry = load_knowledge_directory(knowledge_base)
    engine = ExplanationEngine(registry)

    print("=" * 60)
    print("EcoBiome — Knowledge Base")
    print("=" * 60)
    print(f"Variables chargées : {len(registry.variables)}")
    print(f"Relations chargées : {len(registry.relations)}")
    print()

    result = engine.explain_why("physics.thermal_inertia")
    print(result.text)


if __name__ == "__main__":
    main()

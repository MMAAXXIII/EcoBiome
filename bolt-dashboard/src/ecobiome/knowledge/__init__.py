"""Scientific knowledge loading, validation, and registration."""

from ecobiome.knowledge.loader import load_scientific_variable, load_yaml
from ecobiome.knowledge.registry import KnowledgeRegistry
from ecobiome.knowledge.relation import ScientificRelation
from ecobiome.knowledge.variable import ScientificVariable

__all__ = [
    "KnowledgeRegistry",
    "ScientificRelation",
    "ScientificVariable",
    "load_scientific_variable",
    "load_yaml",
]

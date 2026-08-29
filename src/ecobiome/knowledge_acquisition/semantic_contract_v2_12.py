"""Human-adopted directional nitrogen semantic contract V2.12."""

from __future__ import annotations

import copy
from typing import Any

from ecobiome.knowledge_persistence.serialization import canonical_sha256

DIRECTIONAL_NITROGEN_CONTRACT_VERSION = "2.12"
DIRECTIONAL_NITROGEN_CONTRACT_STATE = "g7a_directional_nitrogen_human_adopted"
DIRECTIONAL_NITROGEN_DESIGN_SHA256 = "205913037baf3e9d0fea3f2d779636cfb687618bbd0580e2d6c7c979672d2477"

EXPECTED_BASE_RELATIONS = 63
EXPECTED_BASE_RESOLVED = 45
EXPECTED_BASE_BLOCKED = 18
EXPECTED_OUTPUT_RELATIONS = 65
EXPECTED_OUTPUT_RESOLVED = 47
EXPECTED_OUTPUT_BLOCKED = 18

DIRECTIONAL_NITROGEN_EXTENSION_V2_12: dict[str, Any] = {'automatic_scientific_acceptance': False, 'base_relation_type_contract_version': '2.10', 'design_sha256': '205913037baf3e9d0fea3f2d779636cfb687618bbd0580e2d6c7c979672d2477', 'new_argument_roles': {'process_agent': {'description': 'Organism or other source-stated agent performing or mediating the nitrogen transformation.', 'grounding_class': 'open_text_source_grounded', 'semantic_domain': 'organism_or_entity_performing_nitrogen_transformation'}, 'source_material': {'description': 'Source chemical/material form in which nitrogen is explicitly supplied or transformed from.', 'grounding_class': 'open_text_source_grounded', 'semantic_domain': 'nitrogen_source_material_or_chemical_form'}, 'target_material': {'description': 'Target chemical/material form in which nitrogen is explicitly measured after oxidation/transformation.', 'grounding_class': 'open_text_source_grounded', 'semantic_domain': 'nitrogen_target_material_or_chemical_form'}, 'target_nitrogen_pool': {'description': 'Named biological product, tissue, biomass, or compartment into which source-derived nitrogen is explicitly incorporated or accumulated.', 'grounding_class': 'open_text_source_grounded', 'semantic_domain': 'nitrogen_bearing_biological_product_tissue_or_compartment'}}, 'new_relations': {'nitrogen_assimilated_from_into': {'argument_keys': ['source_material', 'target_nitrogen_pool', 'process_agent'], 'description': 'The source explicitly reports nitrogen supplied in a named source material/form being incorporated or accumulated into a named biological nitrogen-bearing product, tissue, biomass, or compartment by a stated process agent.', 'epistemic_class': 'explicit_causal_result', 'semantic_type_contract_state': 'g7a_directional_nitrogen_human_adopted', 'semantic_types_allowed': ['nitrogen_assimilation']}, 'nitrogen_oxidized_from_to': {'argument_keys': ['source_material', 'target_material', 'process_agent'], 'description': 'The source explicitly reports oxidation of nitrogen from a named source material/form into a named target oxidized material/form by a stated process agent.', 'epistemic_class': 'explicit_causal_result', 'semantic_type_contract_state': 'g7a_directional_nitrogen_human_adopted', 'semantic_types_allowed': ['nitrogen_oxidation']}}, 'new_semantic_types': ['nitrogen_assimilation', 'nitrogen_oxidation'], 'schema_version': 'ecobiome-directional-nitrogen-semantic-contract-v2.12', 'version': '2.12'}
DIRECTIONAL_NITROGEN_EXTENSION_V2_12_SHA256 = "b5abf8b34a883f4adbca1b606e6a7bac0e9b69a6ee2f004ecd810cd43876d468"

if canonical_sha256(DIRECTIONAL_NITROGEN_EXTENSION_V2_12) != DIRECTIONAL_NITROGEN_EXTENSION_V2_12_SHA256:
    raise RuntimeError("Directional nitrogen V2.12 contract identity mismatch")


def _relation_counts(registry: dict[str, Any]) -> tuple[int, int, int]:
    relations = registry.get("relations")
    if not isinstance(relations, dict):
        raise TypeError("registry relations must be an object")
    resolved = {
        relation
        for relation, spec in relations.items()
        if isinstance(spec, dict)
        and spec.get("semantic_type_contract_state") != "unresolved_blocked"
    }
    return len(relations), len(resolved), len(relations) - len(resolved)


def validate_v2_10_base_for_directional_nitrogen(
    registry_v2_10: dict[str, Any],
) -> dict[str, Any]:
    """Require the exact structural state expected after the V2.10 merge."""
    if not isinstance(registry_v2_10, dict):
        raise TypeError("V2.10 registry must be an object")
    semantic_types = registry_v2_10.get("semantic_types")
    roles = registry_v2_10.get("argument_roles")
    role_semantics = registry_v2_10.get("argument_role_semantics")
    relations = registry_v2_10.get("relations")
    if not isinstance(semantic_types, list):
        raise TypeError("V2.10 semantic_types must be an array")
    if not isinstance(roles, dict):
        raise TypeError("V2.10 argument_roles must be an object")
    if not isinstance(role_semantics, dict):
        raise TypeError("V2.10 argument_role_semantics must be an object")
    if not isinstance(relations, dict):
        raise TypeError("V2.10 relations must be an object")

    if _relation_counts(registry_v2_10) != (
        EXPECTED_BASE_RELATIONS,
        EXPECTED_BASE_RESOLVED,
        EXPECTED_BASE_BLOCKED,
    ):
        raise ValueError(
            "V2.10 registry must contain exactly 63 relations, "
            "45 resolved and 18 blocked"
        )

    additions = DIRECTIONAL_NITROGEN_EXTENSION_V2_12
    collisions = {
        "semantic_types": sorted(set(additions["new_semantic_types"]) & set(semantic_types)),
        "argument_roles": sorted(set(additions["new_argument_roles"]) & set(roles)),
        "relations": sorted(set(additions["new_relations"]) & set(relations)),
    }
    if any(collisions.values()):
        raise ValueError(f"directional nitrogen additions collide with V2.10: {collisions!r}")
    return registry_v2_10


def apply_directional_nitrogen_contract_v2_12(
    registry_v2_10: dict[str, Any],
) -> dict[str, Any]:
    """Return a copied V2.12 registry with only the adopted nitrogen additions."""
    validate_v2_10_base_for_directional_nitrogen(registry_v2_10)
    merged = copy.deepcopy(registry_v2_10)
    semantic_types = merged["semantic_types"]
    roles = merged["argument_roles"]
    role_semantics = merged["argument_role_semantics"]
    relations = merged["relations"]
    additions = DIRECTIONAL_NITROGEN_EXTENSION_V2_12

    semantic_types[:] = sorted({*semantic_types, *additions["new_semantic_types"]})
    for role, semantics in sorted(additions["new_argument_roles"].items()):
        roles[role] = {"type": "string", "minLength": 1}
        role_semantics[role] = copy.deepcopy(semantics)
    for relation, spec in sorted(additions["new_relations"].items()):
        relations[relation] = copy.deepcopy(spec)

    if _relation_counts(merged) != (
        EXPECTED_OUTPUT_RELATIONS,
        EXPECTED_OUTPUT_RESOLVED,
        EXPECTED_OUTPUT_BLOCKED,
    ):
        raise RuntimeError(
            "V2.12 registry must contain exactly 65 relations, "
            "47 resolved and 18 blocked"
        )
    return merged

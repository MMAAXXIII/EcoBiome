from __future__ import annotations

import pytest

from ecobiome.knowledge_acquisition.scientific_assertion_projection_v1_8 import (
    ENTITY_RESOLUTION_POLICY_SHA256 as ENTITY_RESOLUTION_POLICY_V18_SHA,
)
from ecobiome.knowledge_acquisition.scientific_assertion_projection_v1_8 import (
    PROJECTION_CONTRACT_DESCRIPTOR_V1_8,
)
from ecobiome.knowledge_acquisition.scientific_assertion_projection_v1_8 import (
    PROJECTION_CONTRACT_SHA256 as PROJECTION_V18_SHA,
)
from ecobiome.knowledge_acquisition.scientific_assertion_projection_v1_9 import (
    ENTITY_RESOLUTION_POLICY_SHA256 as ENTITY_RESOLUTION_POLICY_V19_SHA,
)
from ecobiome.knowledge_acquisition.scientific_assertion_projection_v1_9 import (
    PROJECTION_CONTRACT_DESCRIPTOR_V1_9,
    ScientificAssertionProjectionV1Error,
    project_scientific_assertion_v1_9,
)
from ecobiome.knowledge_acquisition.scientific_assertion_projection_v1_9 import (
    PROJECTION_CONTRACT_SHA256 as PROJECTION_V19_SHA,
)
from ecobiome.knowledge_acquisition.semantic_candidate_entity_resolution_v1_1 import (
    ENTITY_RESOLUTION_POLICY_SHA256 as ENTITY_RESOLUTION_POLICY_V11_SHA,
)


def test_projection_v19_is_additive_and_binds_entity_resolution_v11() -> None:
    assert PROJECTION_V18_SHA == (
        "006458c7163d275217ae584064b3e72adc3cdc3a36c5fe8a97b40088bcccd6e5"
    )
    assert ENTITY_RESOLUTION_POLICY_V18_SHA == (
        "c2e31ae42c25610e4b6c299269bf50f05476b71772d1a0aefe01ff88329e329e"
    )
    assert ENTITY_RESOLUTION_POLICY_V19_SHA == ENTITY_RESOLUTION_POLICY_V11_SHA
    assert ENTITY_RESOLUTION_POLICY_V19_SHA == (
        "82f4ebbd6b785224eb1fa2c85c659f8a9ba5cbdbb8d8e3175191688cf5eb4dd6"
    )
    assert PROJECTION_V19_SHA == (
        "c7802b7d63f60ca52b8de233be8d6a0c39e46779a0bf7211fcbf1a3f69fb1280"
    )
    assert PROJECTION_V19_SHA != PROJECTION_V18_SHA
    assert PROJECTION_CONTRACT_DESCRIPTOR_V1_9["specs"] == (
        PROJECTION_CONTRACT_DESCRIPTOR_V1_8["specs"]
    )
    assert PROJECTION_CONTRACT_DESCRIPTOR_V1_9["automatic_persistence"] is False


def test_projection_v19_rejects_legacy_entity_resolution_policy_first() -> None:
    with pytest.raises(
        ScientificAssertionProjectionV1Error,
        match="entity-resolution policy identity mismatch",
    ):
        project_scientific_assertion_v1_9(
            {},
            source_claim=None,  # type: ignore[arg-type]
            claim_reviews=(),
            candidate_reviews=(),
            claim_evidence_links=(),
            evidence_rows=(),
            segments={},
            segment_reviews={},
            entity_resolution_policy_sha256=ENTITY_RESOLUTION_POLICY_V18_SHA,
            entity_resolutions={},
        )

"""Read-only runtime for the frozen G7A nitrogen vertical demonstration."""
from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from ecobiome.knowledge_persistence.sqlite_store import (
    SQLiteKnowledgeSynthesisRepository,
    SQLiteScientificAssertionRepository,
)
from ecobiome.reasoning.auditable_ecosystem_explanation_v1 import (
    build_auditable_ecosystem_explanation_v1,
)
from ecobiome.reasoning.nitrogen_vertical_demonstration_v1 import (
    NitrogenVerticalDemonstrationV1,
    ScientificFoundationSnapshotRefV1,
    build_nitrogen_vertical_demonstration_v1,
)
from ecobiome.simulation.ecosystem_state_v1 import (
    CanonicalQuantityV1,
    EcosystemStateV1,
    QuantityBasisV1,
)
from ecobiome.simulation.g7a_alignment_instances_v2 import (
    G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2_SELECTION,
    G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SELECTION,
)
from ecobiome.simulation.material_balance_v1 import (
    MATERIAL_INVENTORY_VARIABLE_ID,
    evaluate_nitrogen_transformation_extent_v1,
)
from ecobiome.simulation.reviewed_support_attachment_receipt_v1 import (
    attach_g7a_reviewed_alignment_v2_support_with_receipt_v1,
)

SCIENTIFIC_FOUNDATION_V6_SHA256 = (
    "76381b5a76f0dd34668634357b3fa4657ff650351235ad85acc8b6fdb421997f"
)
SCIENTIFIC_FOUNDATION_V6_DESIGN_SHA256 = (
    "e0c732320b8bf901de3fd285ffcc41b74db8f1e0a227df89e0428e893e4f9181"
)
MECH5A_CORE_TRACE_SHA256 = (
    "728028eae5602efa7f77d964d4fc34c9f3d50c68c6c8472c145fb7c9fda28c88"
)
MECH5B_AUDITABLE_EXPLANATION_SHA256 = (
    "e281a56c83cc196e9b3014e724ee5d5189babd1e43aa7c9866fd5eaf976ae3f5"
)
VERTICAL_1A_DEMONSTRATION_SHA256 = (
    "056e45c870715b8d48302ccdb30a56d05fd0f6b9424fa135ece316b5b1626a40"
)


class NitrogenVerticalRuntimeV1Error(RuntimeError):
    """Raised when the frozen read-only vertical cannot be reproduced."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_scientific_foundation_v6_read_only(
    database_path: Path,
) -> None:
    """Fail closed unless the exact reviewed V6 snapshot is supplied."""
    path = database_path.expanduser().resolve()
    if not path.is_file():
        raise NitrogenVerticalRuntimeV1Error(
            f"Scientific Foundation V6 database not found: {path}"
        )
    observed_sha = _sha256_file(path)
    if observed_sha != SCIENTIFIC_FOUNDATION_V6_SHA256:
        raise NitrogenVerticalRuntimeV1Error(
            "Scientific Foundation database SHA-256 does not match the "
            "reviewed V6 snapshot"
        )

    conn = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        user_version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        quick_check = tuple(
            row[0] for row in conn.execute("PRAGMA quick_check").fetchall()
        )
        foreign_keys = tuple(conn.execute("PRAGMA foreign_key_check").fetchall())
        metadata = conn.execute(
            "SELECT schema_version, design_sha256 "
            "FROM sf_schema_metadata "
            "WHERE schema_name='scientific_foundation'"
        ).fetchone()
    finally:
        conn.close()

    if user_version != 6:
        raise NitrogenVerticalRuntimeV1Error(
            "Scientific Foundation database is not schema V6"
        )
    if quick_check != ("ok",):
        raise NitrogenVerticalRuntimeV1Error(
            "Scientific Foundation V6 quick_check failed"
        )
    if foreign_keys:
        raise NitrogenVerticalRuntimeV1Error(
            "Scientific Foundation V6 foreign-key check failed"
        )
    if metadata is None:
        raise NitrogenVerticalRuntimeV1Error(
            "Scientific Foundation V6 metadata is missing"
        )
    if int(metadata[0]) != 6 or str(metadata[1]) != (
        SCIENTIFIC_FOUNDATION_V6_DESIGN_SHA256
    ):
        raise NitrogenVerticalRuntimeV1Error(
            "Scientific Foundation V6 design identity mismatch"
        )


def build_frozen_g7a_nitrogen_vertical_demonstration_v1(
    database_path: Path,
) -> NitrogenVerticalDemonstrationV1:
    """Reproduce the reviewed 1 mg N + 1 mg N vertical against exact V6."""
    path = database_path.expanduser().resolve()
    validate_scientific_foundation_v6_read_only(path)

    observation_basis = QuantityBasisV1(
        kind="observation",
        reference_id="g7a-mech5a-initial-nitrogen-observation",
        note="MECH-5A four-pool nitrogen fixture",
    )
    start = EcosystemStateV1(
        profile_id="g7a-mech5a-nitrogen-profile",
        quantities=(
            CanonicalQuantityV1(
                variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
                value_decimal="10",
                unit="mg N",
                basis=observation_basis,
                zone_id="water-zone-1",
                material_component_id="reduced_inorganic_nitrogen",
            ),
            CanonicalQuantityV1(
                variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
                value_decimal="2",
                unit="mg N",
                basis=observation_basis,
                zone_id="water-zone-1",
                material_component_id="oxidized_inorganic_nitrogen",
            ),
            CanonicalQuantityV1(
                variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
                value_decimal="10",
                unit="mg N",
                basis=observation_basis,
                zone_id="water-zone-1",
                material_component_id="dissolved_inorganic_nitrogen",
            ),
            CanonicalQuantityV1(
                variable_id=MATERIAL_INVENTORY_VARIABLE_ID,
                value_decimal="2",
                unit="mg N",
                basis=observation_basis,
                zone_id="water-zone-1",
                material_component_id="biological_nitrogen",
            ),
        ),
    )
    oxidation_basis = QuantityBasisV1(
        kind="scenario_default",
        reference_id="g7a-mech5a-oxidation-explicit-extent",
        note="explicit 1 mg N extent; no kinetic/rate model",
    )
    assimilation_basis = QuantityBasisV1(
        kind="scenario_default",
        reference_id="g7a-mech5a-assimilation-explicit-extent",
        note="explicit 1 mg N extent; no kinetic/rate model",
    )
    oxidation_selection = G7A_NITROGEN_OXIDATION_ALIGNMENT_V2_SELECTION
    assimilation_selection = G7A_NITROGEN_ASSIMILATION_ALIGNMENT_V2_SELECTION

    intermediate, oxidation_pending = evaluate_nitrogen_transformation_extent_v1(
        start,
        zone_id="water-zone-1",
        source_component_id="reduced_inorganic_nitrogen",
        target_component_id="oxidized_inorganic_nitrogen",
        extent_decimal="1",
        extent_unit="mg N",
        extent_basis=oxidation_basis,
        evaluation_id="g7a-mech5a-oxidation-evaluation",
        scientific_assertion_refs=(oxidation_selection.policy.assertion_ref,),
    )
    end, assimilation_pending = evaluate_nitrogen_transformation_extent_v1(
        intermediate,
        zone_id="water-zone-1",
        source_component_id="dissolved_inorganic_nitrogen",
        target_component_id="biological_nitrogen",
        extent_decimal="1",
        extent_unit="mg N",
        extent_basis=assimilation_basis,
        evaluation_id="g7a-mech5a-assimilation-evaluation",
        scientific_assertion_refs=(assimilation_selection.policy.assertion_ref,),
    )

    conn = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    conn.execute("PRAGMA query_only=ON")
    try:
        assertions = SQLiteScientificAssertionRepository(conn)
        syntheses = SQLiteKnowledgeSynthesisRepository(conn)
        oxidation_result = (
            attach_g7a_reviewed_alignment_v2_support_with_receipt_v1(
                oxidation_pending,
                receipt_id="receipt-g7a-mech5b-oxidation-v1",
                selection=oxidation_selection,
                expected_selection_sha256=oxidation_selection.canonical_sha256,
                assertions=assertions,
                syntheses=syntheses,
            )
        )
        assimilation_result = (
            attach_g7a_reviewed_alignment_v2_support_with_receipt_v1(
                assimilation_pending,
                receipt_id="receipt-g7a-mech5b-assimilation-v1",
                selection=assimilation_selection,
                expected_selection_sha256=assimilation_selection.canonical_sha256,
                assertions=assertions,
                syntheses=syntheses,
            )
        )
    finally:
        conn.close()

    evaluations = (
        oxidation_result.evaluation,
        assimilation_result.evaluation,
    )
    auditable = build_auditable_ecosystem_explanation_v1(
        start,
        end,
        evaluations,
        reviewed_support_attachment_receipts=(
            oxidation_result.receipt,
            assimilation_result.receipt,
        ),
    )
    if auditable.explanation_trace.canonical_sha256 != MECH5A_CORE_TRACE_SHA256:
        raise NitrogenVerticalRuntimeV1Error(
            "MECH-5A core trace identity did not reproduce"
        )
    if auditable.canonical_sha256 != MECH5B_AUDITABLE_EXPLANATION_SHA256:
        raise NitrogenVerticalRuntimeV1Error(
            "MECH-5B auditable explanation identity did not reproduce"
        )

    demonstration = build_nitrogen_vertical_demonstration_v1(
        demo_id="g7a-nitrogen-vertical-demonstration-v1",
        starting_state=start,
        intermediate_state=intermediate,
        ending_state=end,
        evaluations=evaluations,
        auditable_explanation=auditable,
        scientific_foundation_snapshot=ScientificFoundationSnapshotRefV1(
            schema_version=6,
            design_sha256=SCIENTIFIC_FOUNDATION_V6_DESIGN_SHA256,
            database_sha256=SCIENTIFIC_FOUNDATION_V6_SHA256,
        ),
    )
    if demonstration.canonical_sha256 != VERTICAL_1A_DEMONSTRATION_SHA256:
        raise NitrogenVerticalRuntimeV1Error(
            "VERTICAL-1A demonstration identity did not reproduce"
        )
    return demonstration

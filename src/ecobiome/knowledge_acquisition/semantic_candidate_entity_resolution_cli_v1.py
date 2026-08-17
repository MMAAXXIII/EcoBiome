"""Operator CLI for durable Semantic Candidate entity-resolution review."""

from __future__ import annotations

import argparse
import json
import uuid
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ecobiome.knowledge_acquisition.semantic_candidate_entity_resolution_v1 import (
    build_semantic_candidate_entity_resolution_event_v1,
)
from ecobiome.knowledge_acquisition.semantic_candidate_review_v1 import (
    require_candidate_acceptance_v1,
)
from ecobiome.knowledge_persistence import (
    FilesystemContentAddressedArtifactStore,
    PersistenceConfig,
    SQLiteScientificFoundationUnitOfWork,
)
from ecobiome.knowledge_persistence.contracts import (
    ScientificEntityNameUsagesRow,
)

SEMANTIC_CANDIDATE_ENTITY_RESOLUTION_COMMANDS = frozenset(
    {
        "semantic-candidate-entity-search",
        "semantic-candidate-entity-show",
        "semantic-candidate-entity-review",
    }
)


def _add_storage_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--artifact-store-root", type=Path, required=True)
    parser.add_argument(
        "--repository-root",
        type=Path,
        required=True,
        help=(
            "Repository root used only to enforce that the scientific DB/CAS "
            "remain outside the Git checkout."
        ),
    )


def add_semantic_candidate_entity_resolution_parsers(commands: Any) -> None:
    """Register the G5 entity-resolution operator commands."""
    search_parser = commands.add_parser(
        "semantic-candidate-entity-search",
        help="Find reviewed entity revisions by exact canonical label.",
    )
    _add_storage_arguments(search_parser)
    search_parser.add_argument("label")
    search_parser.add_argument("--limit", type=int, default=50)

    show_parser = commands.add_parser(
        "semantic-candidate-entity-show",
        help="Show one candidate argument set and entity-resolution history.",
    )
    _add_storage_arguments(show_parser)
    show_parser.add_argument("candidate_id")

    review_parser = commands.add_parser(
        "semantic-candidate-entity-review",
        help="Append one human entity-resolution review event.",
    )
    _add_storage_arguments(review_parser)
    review_parser.add_argument("candidate_id")
    review_parser.add_argument("role")
    review_parser.add_argument("decision", choices=("accept", "reject"))
    review_parser.add_argument("--reviewer", required=True)
    review_parser.add_argument("--rationale", default="")
    review_parser.add_argument("--entity-id")
    review_parser.add_argument("--entity-revision", type=int)
    review_parser.add_argument(
        "--mapping-status",
        choices=("exact", "synonym"),
    )
    review_parser.add_argument("--name-usage-id")
    review_parser.add_argument("--evidence-id")
    review_parser.add_argument("--segment-char-start", type=int)
    review_parser.add_argument("--event-id")
    review_parser.add_argument("--reviewed-at")


def _unit_of_work(args: argparse.Namespace) -> SQLiteScientificFoundationUnitOfWork:
    config = PersistenceConfig(
        database_path=args.database,
        artifact_store_root=args.artifact_store_root,
    )
    artifacts = FilesystemContentAddressedArtifactStore(
        config.artifact_store_root
    )
    return SQLiteScientificFoundationUnitOfWork(
        config,
        repo_root=args.repository_root,
        artifact_store=artifacts,
    )


def _reviewed_at(raw: str | None) -> str:
    if raw is None:
        return datetime.now(UTC).isoformat(timespec="microseconds")

    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        raise ValueError("--reviewed-at must include a timezone offset.")
    return parsed.astimezone(UTC).isoformat(timespec="microseconds")


def _require_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer.")
    return value


def _candidate_document(row: Any) -> dict[str, object]:
    decoded = json.loads(row.canonical_candidate_json)
    if not isinstance(decoded, dict):
        raise TypeError("Persisted canonical candidate JSON must be an object.")
    return decoded


def _candidate_arguments(
    candidate: dict[str, object],
) -> tuple[dict[str, object], ...]:
    semantic = candidate.get("semantic")
    if not isinstance(semantic, dict):
        raise TypeError("Candidate semantic payload must be an object.")
    raw_arguments = semantic.get("arguments")
    if not isinstance(raw_arguments, list):
        raise TypeError("Candidate semantic arguments must be an array.")

    arguments: list[dict[str, object]] = []
    for raw in raw_arguments:
        if not isinstance(raw, dict):
            raise TypeError("Candidate argument must be an object.")
        arguments.append(raw)
    return tuple(arguments)


def _argument_by_role(
    candidate: dict[str, object],
    role: str,
) -> dict[str, object]:
    matches = [
        argument
        for argument in _candidate_arguments(candidate)
        if argument.get("role") == role
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Candidate role must match exactly one argument: {role}"
        )
    return matches[0]


def _source_surface(argument: dict[str, object]) -> str:
    if argument.get("resolution_state") != "grounded_opaque_unresolved":
        raise ValueError("Role is not eligible for entity resolution.")
    value = argument.get("value")
    if not isinstance(value, dict) or value.get("kind") != "source_text":
        raise ValueError("Entity-resolution argument must be source_text.")
    surface = value.get("source_surface")
    if not isinstance(surface, str) or not surface:
        raise ValueError("Entity-resolution argument lacks source_surface.")
    return surface


def _candidate_review_status(events: tuple[Any, ...]) -> str:
    if not events:
        return "pending"
    return str(events[-1].decision)


def _resolution_summary(events: tuple[Any, ...]) -> dict[str, object]:
    latest = None if not events else events[-1]
    return {
        "status": "pending" if latest is None else latest.decision,
        "latest_event_id": None if latest is None else latest.id,
        "latest_reviewed_at": None if latest is None else latest.reviewed_at,
        "latest_entity_id": None if latest is None else latest.entity_id,
        "latest_entity_revision": (
            None if latest is None else latest.entity_revision
        ),
        "latest_mapping_status": (
            None if latest is None else latest.mapping_status
        ),
    }


def _resolve_source_anchor(
    uow: Any,
    candidate_row: Any,
    candidate: dict[str, object],
    role: str,
    *,
    evidence_id: str | None,
    segment_char_start: int | None,
) -> dict[str, object]:
    if segment_char_start is not None and evidence_id is None:
        raise ValueError(
            "--segment-char-start requires --evidence-id."
        )

    argument = _argument_by_role(candidate, role)
    surface = _source_surface(argument)
    links = uow.semantic_candidates.get_candidate_evidence_links(
        candidate_row.id
    )
    if evidence_id is not None:
        links = tuple(
            link for link in links if link.evidence_id == evidence_id
        )
        if not links:
            raise ValueError(
                f"Evidence is not linked to candidate: {evidence_id}"
            )

    anchors: dict[tuple[str, int, int], set[str]] = {}
    for link in links:
        evidence = uow.provenance.get_source_evidence(link.evidence_id)
        if evidence is None:
            raise ValueError(
                f"Missing candidate Evidence row: {link.evidence_id}"
            )
        segment = uow.provenance.get_segment(evidence.segment_id)
        if segment is None or segment.text_inline is None:
            raise ValueError(
                f"Evidence segment text is unavailable: {evidence.segment_id}"
            )

        start = int(evidence.segment_char_start)
        end = int(evidence.segment_char_end)
        position = segment.text_inline.find(surface, start, end)
        while position >= 0:
            surface_end = position + len(surface)
            if (
                surface_end <= end
                and (
                    segment_char_start is None
                    or position == segment_char_start
                )
            ):
                key = (segment.id, position, surface_end)
                anchors.setdefault(key, set()).add(link.evidence_id)
            position = segment.text_inline.find(
                surface,
                position + 1,
                end,
            )

    if len(anchors) != 1:
        raise ValueError(
            "Entity source surface must resolve to exactly one Evidence span; "
            "use --evidence-id and --segment-char-start to disambiguate."
        )

    (segment_id, start, end), evidence_ids = next(iter(anchors.items()))
    return {
        "source_surface": surface,
        "segment_id": segment_id,
        "segment_char_start": start,
        "segment_char_end": end,
        "evidence_ids": sorted(evidence_ids),
    }


def semantic_candidate_entity_search_command(
    args: argparse.Namespace,
) -> int:
    label = args.label.strip()
    if not label:
        raise ValueError("label must be non-empty.")
    if args.limit < 1 or args.limit > 500:
        raise ValueError("--limit must be between 1 and 500.")

    with _unit_of_work(args) as uow:
        rows = uow.entities.list_reviewed_entity_revisions(
            label=label,
            limit=args.limit,
        )

    print(
        json.dumps(
            {
                "schema_version": 1,
                "match_mode": "exact_canonical_label",
                "label": label,
                "count": len(rows),
                "entity_revisions": [asdict(row) for row in rows],
                "automatic_scientific_acceptance": False,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def semantic_candidate_entity_show_command(
    args: argparse.Namespace,
) -> int:
    with _unit_of_work(args) as uow:
        row = uow.semantic_candidates.get_candidate(args.candidate_id)
        if row is None:
            raise ValueError(
                f"Unknown semantic candidate: {args.candidate_id}"
            )
        candidate = _candidate_document(row)
        candidate_reviews = tuple(
            uow.semantic_candidates.list_review_events(row.id)
        )

        arguments: list[dict[str, object]] = []
        for argument in _candidate_arguments(candidate):
            role = argument.get("role")
            if not isinstance(role, str) or not role:
                raise TypeError("Candidate role must be non-empty.")
            history = tuple(
                uow.entities.list_candidate_entity_resolution_events(
                    row.id,
                    role,
                )
            )
            arguments.append(
                {
                    "role": role,
                    "argument": argument,
                    "requires_entity_resolution": (
                        argument.get("resolution_state")
                        == "grounded_opaque_unresolved"
                    ),
                    "resolution": _resolution_summary(history),
                    "resolution_history": [
                        asdict(event) for event in history
                    ],
                }
            )

    print(
        json.dumps(
            {
                "schema_version": 1,
                "candidate_id": row.id,
                "canonical_candidate_sha256": (
                    row.canonical_candidate_sha256
                ),
                "candidate_review_status": _candidate_review_status(
                    candidate_reviews
                ),
                "arguments": arguments,
                "automatic_scientific_acceptance": False,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _accept_mapping(
    args: argparse.Namespace,
    *,
    uow: Any,
    candidate_row: Any,
    candidate: dict[str, object],
    reviewed_at: str,
) -> tuple[ScientificEntityNameUsagesRow, bool, dict[str, object]]:
    if args.entity_id is None or args.entity_revision is None:
        raise ValueError(
            "accept requires --entity-id and --entity-revision."
        )
    if args.entity_revision < 1:
        raise ValueError("--entity-revision must be positive.")

    revision = uow.entities.get_entity_revision(
        args.entity_id,
        args.entity_revision,
    )
    if revision is None:
        raise ValueError(
            "Unknown entity revision: "
            f"{args.entity_id}@{args.entity_revision}"
        )
    if revision.review_status != "reviewed_confirmed":
        raise ValueError("Entity revision is not reviewed_confirmed.")

    anchor = _resolve_source_anchor(
        uow,
        candidate_row,
        candidate,
        args.role,
        evidence_id=args.evidence_id,
        segment_char_start=args.segment_char_start,
    )
    claim = uow.provenance.get_source_claim(
        candidate_row.source_statement_claim_id
    )
    if claim is None:
        raise ValueError("Candidate source Claim is missing.")

    name_usage = ScientificEntityNameUsagesRow(
        id=args.name_usage_id or str(uuid.uuid4()),
        entity_id=args.entity_id,
        source_id=claim.source_id,
        verbatim_name=str(anchor["source_surface"]),
        language=None,
        script=None,
        usage_status="source_usage",
        nomenclatural_status=None,
        mapping_review_status="reviewed_confirmed",
        source_version=None,
        retrieval_id=None,
        segment_id=str(anchor["segment_id"]),
        segment_char_start=_require_int(
            anchor["segment_char_start"],
            "source anchor segment_char_start",
        ),
        segment_char_end=_require_int(
            anchor["segment_char_end"],
            "source anchor segment_char_end",
        ),
        created_at=reviewed_at,
    )
    inserted = uow.entities.add_name_usage(name_usage)
    return name_usage, inserted, anchor


def _reject_mapping(
    args: argparse.Namespace,
    *,
    uow: Any,
    candidate_row: Any,
) -> tuple[Any, dict[str, object]]:
    forbidden = {
        "--entity-id": args.entity_id,
        "--entity-revision": args.entity_revision,
        "--mapping-status": args.mapping_status,
        "--name-usage-id": args.name_usage_id,
        "--evidence-id": args.evidence_id,
        "--segment-char-start": args.segment_char_start,
    }
    supplied = sorted(
        name for name, value in forbidden.items() if value is not None
    )
    if supplied:
        raise ValueError(
            "reject reuses the latest accepted mapping; remove: "
            + ", ".join(supplied)
        )

    history = tuple(
        uow.entities.list_candidate_entity_resolution_events(
            candidate_row.id,
            args.role,
        )
    )
    if not history or history[-1].decision != "accept":
        raise ValueError(
            "reject requires a latest accepted entity mapping for the role."
        )
    latest = history[-1]
    return latest, {
        "source_surface": None,
        "segment_id": None,
        "segment_char_start": None,
        "segment_char_end": None,
        "evidence_ids": [],
    }


def semantic_candidate_entity_review_command(
    args: argparse.Namespace,
) -> int:
    reviewed_at = _reviewed_at(args.reviewed_at)

    with _unit_of_work(args) as uow:
        row = uow.semantic_candidates.get_candidate(args.candidate_id)
        if row is None:
            raise ValueError(
                f"Unknown semantic candidate: {args.candidate_id}"
            )
        candidate = _candidate_document(row)
        candidate_reviews = tuple(
            uow.semantic_candidates.list_review_events(row.id)
        )
        require_candidate_acceptance_v1(
            candidate,
            candidate_reviews,
        )
        _argument_by_role(candidate, args.role)

        name_usage_inserted = False
        if args.decision == "accept":
            name_usage, name_usage_inserted, anchor = _accept_mapping(
                args,
                uow=uow,
                candidate_row=row,
                candidate=candidate,
                reviewed_at=reviewed_at,
            )
            entity_id = str(name_usage.entity_id)
            entity_revision = int(args.entity_revision)
            mapping_status = args.mapping_status or "exact"
            name_usage_id = name_usage.id
        else:
            latest, anchor = _reject_mapping(
                args,
                uow=uow,
                candidate_row=row,
            )
            entity_id = latest.entity_id
            entity_revision = latest.entity_revision
            mapping_status = latest.mapping_status
            name_usage_id = latest.entity_name_usage_id

        event = build_semantic_candidate_entity_resolution_event_v1(
            candidate,
            event_id=args.event_id or str(uuid.uuid4()),
            semantic_candidate_id=row.id,
            role=args.role,
            entity_name_usage_id=name_usage_id,
            entity_id=entity_id,
            entity_revision=entity_revision,
            mapping_status=mapping_status,
            decision=args.decision,
            reviewer=args.reviewer,
            reviewed_at=reviewed_at,
            rationale=args.rationale,
        )
        inserted = uow.entities.add_candidate_entity_resolution_event(
            event
        )
        uow.commit()
        history = tuple(
            uow.entities.list_candidate_entity_resolution_events(
                row.id,
                args.role,
            )
        )

    print(
        json.dumps(
            {
                "schema_version": 1,
                "inserted": inserted,
                "name_usage_inserted": name_usage_inserted,
                "candidate_id": row.id,
                "role": args.role,
                "resolution_status": _resolution_summary(history)["status"],
                "resolution_event": asdict(event),
                "resolution_event_count": len(history),
                "source_anchor": anchor,
                "automatic_scientific_acceptance": False,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def run_semantic_candidate_entity_resolution_command(
    args: argparse.Namespace,
) -> int:
    """Dispatch one registered G5 entity-resolution operator command."""
    if args.command == "semantic-candidate-entity-search":
        return semantic_candidate_entity_search_command(args)
    if args.command == "semantic-candidate-entity-show":
        return semantic_candidate_entity_show_command(args)
    if args.command == "semantic-candidate-entity-review":
        return semantic_candidate_entity_review_command(args)
    raise ValueError(
        "Unsupported semantic candidate entity-resolution command: "
        f"{args.command}"
    )

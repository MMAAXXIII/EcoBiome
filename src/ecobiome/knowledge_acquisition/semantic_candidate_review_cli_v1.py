"""Operator CLI for append-only Semantic Candidate V2.11 human review."""

from __future__ import annotations

import argparse
import json
import uuid
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ecobiome.knowledge_acquisition.semantic_candidate_review_v1 import (
    build_semantic_candidate_review_event_v1,
)
from ecobiome.knowledge_persistence import (
    FilesystemContentAddressedArtifactStore,
    PersistenceConfig,
    SQLiteScientificFoundationUnitOfWork,
)
from ecobiome.knowledge_persistence.serialization import canonical_json_text

SEMANTIC_CANDIDATE_REVIEW_COMMANDS = frozenset(
    {
        "semantic-candidate-list",
        "semantic-candidate-show",
        "semantic-candidate-review",
    }
)

_REVIEW_STATUS_BY_DECISION = {
    "accept": "accepted",
    "correct": "corrected",
    "reject": "rejected",
}


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


def add_semantic_candidate_review_parsers(commands: Any) -> None:
    """Register the G2 operator commands on the Collector parser."""
    list_parser = commands.add_parser(
        "semantic-candidate-list",
        help="List Semantic Candidates by effective append-only review status.",
    )
    _add_storage_arguments(list_parser)
    list_parser.add_argument(
        "--status",
        choices=("pending", "accepted", "corrected", "rejected", "all"),
        default="pending",
    )
    list_parser.add_argument("--limit", type=int, default=50)

    show_parser = commands.add_parser(
        "semantic-candidate-show",
        help="Show one Semantic Candidate and its complete review history.",
    )
    _add_storage_arguments(show_parser)
    show_parser.add_argument("candidate_id")

    review_parser = commands.add_parser(
        "semantic-candidate-review",
        help="Append one human review event to a Semantic Candidate.",
    )
    _add_storage_arguments(review_parser)
    review_parser.add_argument("candidate_id")
    review_parser.add_argument(
        "decision",
        choices=("accept", "correct", "reject"),
    )
    review_parser.add_argument("--reviewer", required=True)
    review_parser.add_argument("--rationale", default="")
    review_parser.add_argument("--replacement-candidate-id")
    review_parser.add_argument(
        "--review-metadata-json",
        default="{}",
    )
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


def _effective_review_status(events: tuple[Any, ...]) -> str:
    if not events:
        return "pending"
    return _REVIEW_STATUS_BY_DECISION[str(events[-1].decision)]


def _candidate_summary(row: Any, events: tuple[Any, ...]) -> dict[str, object]:
    latest = None if not events else events[-1]
    return {
        "id": row.id,
        "created_at": row.created_at,
        "semantic_type": row.semantic_type,
        "relation": row.relation,
        "epistemic_class": row.epistemic_class,
        "promotion_readiness": row.promotion_readiness,
        "canonical_candidate_sha256": row.canonical_candidate_sha256,
        "review_status": _effective_review_status(events),
        "latest_review_id": None if latest is None else latest.id,
        "latest_reviewed_at": None if latest is None else latest.reviewed_at,
    }


def _candidate_document(row: Any) -> dict[str, object]:
    payload = asdict(row)
    raw = payload.pop("canonical_candidate_json")
    decoded = json.loads(raw)
    if not isinstance(decoded, dict):
        raise TypeError("Persisted canonical candidate JSON must be an object.")
    payload["canonical_candidate"] = decoded
    return payload


def _canonical_review_metadata(raw: str) -> str:
    decoded = json.loads(raw)
    if not isinstance(decoded, dict):
        raise TypeError("--review-metadata-json must encode a JSON object.")
    return canonical_json_text(decoded)


def _reviewed_at(raw: str | None) -> str:
    if raw is None:
        return datetime.now(UTC).isoformat(timespec="microseconds")

    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        raise ValueError("--reviewed-at must include a timezone offset.")
    return parsed.astimezone(UTC).isoformat(timespec="microseconds")


def semantic_candidate_list_command(args: argparse.Namespace) -> int:
    if args.limit < 1 or args.limit > 500:
        raise ValueError("--limit must be between 1 and 500.")

    scan_limit = 500 if args.status != "all" else args.limit
    with _unit_of_work(args) as uow:
        rows = uow.semantic_candidates.list_candidates(limit=scan_limit)
        items: list[dict[str, object]] = []
        for row in rows:
            events = uow.semantic_candidates.list_review_events(row.id)
            summary = _candidate_summary(row, events)
            if args.status != "all" and summary["review_status"] != args.status:
                continue
            items.append(summary)
            if len(items) >= args.limit:
                break

    print(
        json.dumps(
            {
                "schema_version": 1,
                "status_filter": args.status,
                "count": len(items),
                "candidates": items,
                "automatic_scientific_acceptance": False,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def semantic_candidate_show_command(args: argparse.Namespace) -> int:
    with _unit_of_work(args) as uow:
        row = uow.semantic_candidates.get_candidate(args.candidate_id)
        if row is None:
            raise ValueError(
                f"Unknown semantic candidate: {args.candidate_id}"
            )
        events = uow.semantic_candidates.list_review_events(row.id)
        payload = {
            "schema_version": 1,
            "candidate": _candidate_document(row),
            "review_status": _effective_review_status(events),
            "review_history": [asdict(event) for event in events],
            "automatic_scientific_acceptance": False,
        }

    print(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def semantic_candidate_review_command(args: argparse.Namespace) -> int:
    with _unit_of_work(args) as uow:
        row = uow.semantic_candidates.get_candidate(args.candidate_id)
        if row is None:
            raise ValueError(
                f"Unknown semantic candidate: {args.candidate_id}"
            )

        candidate = json.loads(row.canonical_candidate_json)
        if not isinstance(candidate, dict):
            raise TypeError("Persisted canonical candidate JSON must be an object.")

        replacement_id = args.replacement_candidate_id
        replacement_sha = None
        if args.decision == "correct":
            if replacement_id is None:
                raise ValueError(
                    "correct requires --replacement-candidate-id."
                )
            replacement = uow.semantic_candidates.get_candidate(replacement_id)
            if replacement is None:
                raise ValueError(
                    f"Unknown replacement semantic candidate: {replacement_id}"
                )
            replacement_sha = replacement.canonical_candidate_sha256
        elif replacement_id is not None:
            raise ValueError(
                "--replacement-candidate-id is valid only for correct."
            )

        event = build_semantic_candidate_review_event_v1(
            candidate,
            event_id=args.event_id or str(uuid.uuid4()),
            semantic_candidate_id=row.id,
            decision=args.decision,
            reviewer=args.reviewer,
            reviewed_at=_reviewed_at(args.reviewed_at),
            rationale=args.rationale,
            review_metadata_json=_canonical_review_metadata(
                args.review_metadata_json
            ),
            replacement_candidate_id=replacement_id,
            replacement_candidate_sha256=replacement_sha,
        )

        inserted = uow.semantic_candidates.add_review_event(event)
        uow.commit()
        history = uow.semantic_candidates.list_review_events(row.id)

    print(
        json.dumps(
            {
                "schema_version": 1,
                "inserted": inserted,
                "candidate_id": row.id,
                "review_status": _effective_review_status(history),
                "review_event": asdict(event),
                "review_event_count": len(history),
                "automatic_scientific_acceptance": False,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def run_semantic_candidate_review_command(args: argparse.Namespace) -> int:
    """Dispatch one registered G2 Semantic Candidate review command."""
    if args.command == "semantic-candidate-list":
        return semantic_candidate_list_command(args)
    if args.command == "semantic-candidate-show":
        return semantic_candidate_show_command(args)
    if args.command == "semantic-candidate-review":
        return semantic_candidate_review_command(args)
    raise ValueError(f"Unsupported semantic candidate review command: {args.command}")

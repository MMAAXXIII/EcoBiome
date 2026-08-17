"""Command-line workflow for the durable EcoBiome Collector."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from ecobiome.knowledge_acquisition.collector_acquire import acquire_source
from ecobiome.knowledge_acquisition.persistence import CollectorStore
from ecobiome.knowledge_acquisition.processing import split_into_passages
from ecobiome.knowledge_acquisition.semantic_candidate_review_cli_v1 import (
    SEMANTIC_CANDIDATE_REVIEW_COMMANDS,
    add_semantic_candidate_review_parsers,
    run_semantic_candidate_review_command,
)
from ecobiome.knowledge_acquisition.semantic_claims import (
    load_atomic_claim_batch,
)
from ecobiome.knowledge_acquisition.semantic_evaluation import (
    evaluate_semantic_batch,
)
from ecobiome.knowledge_acquisition.semantic_extraction import (
    ConservativeFrenchLexicalExtractorV1,
    atomic_batch_to_payload,
    build_semantic_extraction_request,
    run_semantic_extractor,
)
from ecobiome.knowledge_acquisition.semantic_openai import (
    OpenAIResponsesSemanticExtractor,
)
from ecobiome.knowledge_acquisition.source import SourceType
from ecobiome.knowledge_acquisition.transcript import load_transcript


def build_parser() -> argparse.ArgumentParser:
    """Build the durable Collector command parser."""
    parser = argparse.ArgumentParser(
        prog="ecobiome collector",
        description=(
            "Durable scientific acquisition and human-review workflow."
        ),
    )
    commands = parser.add_subparsers(dest="command")

    init_parser = commands.add_parser(
        "init",
        help="Create or validate a fresh-only Collector SQLite database.",
    )
    init_parser.add_argument(
        "--database",
        type=Path,
        required=True,
    )

    import_parser = commands.add_parser(
        "import-transcript",
        help="Persist one transcript as an immutable review document.",
    )
    import_parser.add_argument("path", type=Path)
    import_parser.add_argument("--database", type=Path, required=True)
    import_parser.add_argument("--title", required=True)
    import_parser.add_argument("--locator", required=True)
    import_parser.add_argument("--author", default="")
    import_parser.add_argument("--language", default="fr")
    import_parser.add_argument(
        "--source-type",
        default="transcript",
        choices=[item.value for item in SourceType],
    )
    import_parser.add_argument(
        "--maximum-passage-characters",
        type=int,
        default=1500,
    )
    import_parser.add_argument("--output", type=Path)

    acquire_parser = commands.add_parser(
        "acquire",
        help="Acquire one source through the deterministic adapter registry.",
    )
    acquire_parser.add_argument("source")
    acquire_parser.add_argument("--database", type=Path, required=True)
    acquire_parser.add_argument("--language", default="")
    acquire_parser.add_argument(
        "--languages",
        default="",
        help="Comma-separated preferred transcript languages, e.g. fr,en.",
    )
    acquire_parser.add_argument(
        "--maximum-input-bytes",
        type=int,
        default=8 * 1024 * 1024,
    )
    acquire_parser.add_argument(
        "--maximum-passage-characters",
        type=int,
        default=1500,
    )
    acquire_parser.add_argument("--output", type=Path)

    status_parser = commands.add_parser(
        "status",
        help="Show Collector schema and record counts.",
    )
    status_parser.add_argument("--database", type=Path, required=True)

    pending_parser = commands.add_parser(
        "pending",
        help="List pending human-review items.",
    )
    pending_parser.add_argument("--database", type=Path, required=True)
    pending_parser.add_argument("--limit", type=int, default=50)
    pending_parser.add_argument("--json", action="store_true")

    propose_parser = commands.add_parser(
        "propose-claims",
        help=(
            "Create pending source-statement Claims with exact Evidence "
            "from one persisted representation."
        ),
    )
    propose_parser.add_argument("--database", type=Path, required=True)
    propose_parser.add_argument("--representation-id", required=True)
    propose_parser.add_argument("--limit", type=int, default=50)
    propose_parser.add_argument(
        "--maximum-claim-characters",
        type=int,
        default=350,
    )
    propose_parser.add_argument(
        "--maximum-window-seconds",
        type=float,
        default=15.0,
    )
    propose_parser.add_argument("--output", type=Path)

    claim_show_parser = commands.add_parser(
        "claim-show",
        help="Show one Claim with exact Evidence and source provenance.",
    )
    claim_show_parser.add_argument("claim_id")
    claim_show_parser.add_argument("--database", type=Path, required=True)

    atomic_parser = commands.add_parser(
        "ingest-atomic-claims",
        help=(
            "Persist validated atomic source propositions from strict JSON. "
            "Evidence must reference existing source-statement Evidence IDs."
        ),
    )
    atomic_parser.add_argument("path", type=Path)
    atomic_parser.add_argument("--database", type=Path, required=True)
    atomic_parser.add_argument("--output", type=Path)

    semantic_export_parser = commands.add_parser(
        "semantic-export",
        help=(
            "Export bounded source Claims and existing Evidence for an "
            "untrusted semantic extractor."
        ),
    )
    semantic_export_parser.add_argument(
        "--database",
        type=Path,
        required=True,
    )
    semantic_export_parser.add_argument(
        "--claim-id",
        action="append",
        required=True,
        dest="claim_ids",
    )
    semantic_export_parser.add_argument("--output", type=Path)

    semantic_baseline_parser = commands.add_parser(
        "semantic-baseline",
        help=(
            "Run the benchmark-only conservative French lexical extractor "
            "without persisting its output."
        ),
    )
    semantic_baseline_parser.add_argument(
        "--database",
        type=Path,
        required=True,
    )
    semantic_baseline_parser.add_argument(
        "--claim-id",
        action="append",
        required=True,
        dest="claim_ids",
    )
    semantic_baseline_parser.add_argument("--output", type=Path)

    semantic_evaluate_parser = commands.add_parser(
        "semantic-evaluate",
        help=(
            "Compare a validated semantic candidate batch with a reference "
            "batch. This does not measure scientific correctness."
        ),
    )
    semantic_evaluate_parser.add_argument(
        "candidate",
        type=Path,
    )
    semantic_evaluate_parser.add_argument(
        "reference",
        type=Path,
    )
    semantic_evaluate_parser.add_argument("--output", type=Path)

    semantic_openai_parser = commands.add_parser(
        "semantic-openai",
        help=(
            "Run one non-persisting OpenAI semantic benchmark through the "
            "guarded SemanticExtractor protocol."
        ),
    )
    semantic_openai_parser.add_argument(
        "--database",
        type=Path,
        required=True,
    )
    semantic_openai_parser.add_argument(
        "--claim-id",
        action="append",
        required=True,
        dest="claim_ids",
    )
    semantic_openai_parser.add_argument(
        "--model",
        default="gpt-5-mini",
    )
    semantic_openai_parser.add_argument("--output", type=Path)
    semantic_openai_parser.add_argument(
        "--diagnostics-output",
        type=Path,
    )

    add_semantic_candidate_review_parsers(commands)

    review_parser = commands.add_parser(
        "review",
        help="Accept, correct, or reject one pending item.",
    )
    review_parser.add_argument(
        "target_type",
        choices=["passage", "claim"],
    )
    review_parser.add_argument("target_id")
    review_parser.add_argument(
        "decision",
        choices=["accept", "correct", "reject"],
    )
    review_parser.add_argument("--database", type=Path, required=True)
    review_parser.add_argument("--reviewer", default="")
    review_parser.add_argument("--rationale", default="")
    review_parser.add_argument("--corrected-text")

    return parser


def _write_json_atomic(path: Path, payload: object) -> None:
    destination = path.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(destination)


def init_command(args: argparse.Namespace) -> int:
    store = CollectorStore(args.database)
    store.initialize()
    print(
        json.dumps(
            {
                "database": str(store.database_path),
                "schema_version": store.schema_version(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def import_transcript_command(args: argparse.Namespace) -> int:
    imported = load_transcript(
        args.path,
        title=args.title,
        locator=args.locator,
        author=args.author,
        language=args.language,
        source_type=SourceType(args.source_type),
    )
    passages = split_into_passages(
        imported.text,
        maximum_characters=args.maximum_passage_characters,
    )

    store = CollectorStore(args.database)
    receipt = store.persist_transcript(
        imported,
        transcript_path=args.path,
        passages=passages,
    )

    manifest = {
        "schema_version": "0.2",
        "collector_database": str(store.database_path),
        "source": {
            "id": str(receipt.source_id),
            "title": imported.source.title,
            "source_type": imported.source.source_type.value,
            "locator": imported.source.locator,
            "author": imported.source.author,
            "language": imported.source.language,
            "imported_at": imported.source.imported_at.isoformat(),
        },
        "document": {
            "id": str(receipt.document_id),
            "sha256": receipt.document_sha256,
            "stored_path": str(receipt.stored_document_path),
            "character_count": len(imported.text),
            "duplicate": receipt.duplicate_document,
        },
        "job": {
            "id": str(receipt.job_id),
            "status": "succeeded",
        },
        "passages": [
            {
                "id": str(passage_id),
                "index": index,
                "text": passage,
                "review_status": review_status,
            }
            for index, (
                passage_id,
                passage,
                review_status,
            ) in enumerate(
                zip(
                    receipt.passage_ids,
                    passages,
                    receipt.passage_review_statuses,
                    strict=True,
                ),
                start=1,
            )
        ],
    }

    if args.output is not None:
        _write_json_atomic(args.output, manifest)

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0



def _preferred_languages(raw: str) -> tuple[str, ...]:
    """Parse a comma-separated preferred language list deterministically."""
    values = tuple(
        item.strip()
        for item in raw.split(",")
        if item.strip()
    )
    if len(set(values)) != len(values):
        raise ValueError("--languages contains duplicate language codes.")
    return values


def acquire_command(args: argparse.Namespace) -> int:
    run = acquire_source(
        source=args.source,
        database=args.database,
        language=args.language,
        preferred_languages=_preferred_languages(args.languages),
        maximum_input_bytes=args.maximum_input_bytes,
        maximum_passage_characters=args.maximum_passage_characters,
    )

    result_representations = {
        representation.logical_key: representation
        for representation in run.result.representations
    }

    representation_manifest: list[dict[str, object]] = []
    for persisted in run.receipt.representations:
        drafted = result_representations[persisted.logical_key]
        segment_rows: list[dict[str, object]] = []
        for index, (segment_id, review_status) in enumerate(
            zip(
                persisted.segment_ids,
                persisted.segment_review_statuses,
                strict=True,
            ),
            start=1,
        ):
            segment: dict[str, object] = {
                "id": str(segment_id),
                "index": index,
                "review_status": review_status,
            }
            if drafted.segments:
                draft = drafted.segments[index - 1]
                segment.update(
                    {
                        "text": draft.text,
                        "start_char": draft.start_char,
                        "end_char": draft.end_char,
                        "start_seconds": draft.start_seconds,
                        "end_seconds": draft.end_seconds,
                        "page_number": draft.page_number,
                        "frame_start": draft.frame_start,
                        "frame_end": draft.frame_end,
                        "metadata": draft.metadata,
                    }
                )
            segment_rows.append(segment)

        representation_manifest.append(
            {
                "logical_key": persisted.logical_key,
                "id": str(persisted.representation_id),
                "sha256": persisted.sha256,
                "stored_path": str(persisted.stored_path),
                "representation_kind": drafted.representation_kind,
                "language": drafted.language,
                "duplicate": persisted.duplicate,
                "segments": segment_rows,
            }
        )

    manifest = {
        "schema_version": 2,
        "collector_database": str(
            Path(args.database).expanduser().resolve()
        ),
        "adapter": {
            "name": run.adapter_name,
            "version": run.adapter_version,
            "priority": run.match.priority,
            "reason": run.match.reason,
        },
        "source": {
            "id": str(run.receipt.source_id),
            "source_type": run.result.canonical_source.source_type,
            "canonical_locator": (
                run.result.canonical_source.canonical_locator
            ),
            "title": run.result.canonical_source.title,
            "author": run.result.canonical_source.author,
            "language": run.result.canonical_source.language,
            "metadata": run.result.canonical_source.metadata,
        },
        "job": {
            "id": str(run.receipt.job_id),
            "status": run.result.outcome,
        },
        "raw_artifacts": [
            {
                "logical_key": payload.logical_key,
                "id": str(payload.raw_artifact_id),
                "sha256": payload.sha256,
                "stored_path": str(payload.stored_path),
            }
            for payload in run.receipt.payloads
        ],
        "representations": representation_manifest,
        "diagnostics": [
            {
                "severity": diagnostic.severity,
                "code": diagnostic.code,
                "message": diagnostic.message,
                "details": diagnostic.details,
            }
            for diagnostic in run.result.diagnostics
        ],
    }

    if args.output is not None:
        _write_json_atomic(args.output, manifest)

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0

def status_command(args: argparse.Namespace) -> int:
    store = CollectorStore(args.database)
    print(
        json.dumps(
            store.summary(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def pending_command(args: argparse.Namespace) -> int:
    store = CollectorStore(args.database)
    pending = store.list_pending_reviews(limit=args.limit)

    if args.json:
        print(
            json.dumps(
                pending,
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if not pending:
        print("No pending Collector review items.")
        return 0

    for item in pending:
        index = item.get("passage_index")
        prefix = (
            f"{item['target_type']} {item['target_id']}"
            if index is None
            else (
                f"{item['target_type']} {item['target_id']} "
                f"(passage {index})"
            )
        )
        print(prefix)
        print(str(item["text"]))
        print()

    return 0


def propose_claims_command(args: argparse.Namespace) -> int:
    store = CollectorStore(args.database)
    receipt = store.propose_source_statement_claims(
        representation_id=args.representation_id,
        limit=args.limit,
        maximum_claim_characters=args.maximum_claim_characters,
        maximum_window_seconds=args.maximum_window_seconds,
    )

    claims = [
        store.get_claim_with_evidence(item.claim_id)
        | {"duplicate": item.duplicate}
        for item in receipt.claims
    ]
    manifest = {
        "schema_version": 2,
        "collector_database": str(
            Path(args.database).expanduser().resolve()
        ),
        "representation_id": str(receipt.representation_id),
        "extractor": "source-statement-window-v1",
        "claim_count": len(receipt.claims),
        "claims": claims,
        "automatic_scientific_acceptance": False,
    }

    if args.output is not None:
        _write_json_atomic(args.output, manifest)

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


def ingest_atomic_claims_command(args: argparse.Namespace) -> int:
    batch = load_atomic_claim_batch(args.path)
    store = CollectorStore(args.database)
    receipts = store.persist_atomic_claim_batch(batch)

    claims = [
        store.get_claim_with_evidence(item.claim_id)
        | {
            "duplicate": item.duplicate,
            "source_claim_id": str(item.source_claim_id),
        }
        for item in receipts
    ]
    manifest = {
        "schema_version": 2,
        "semantic_contract_version": batch.schema_version,
        "collector_database": str(
            Path(args.database).expanduser().resolve()
        ),
        "extractor": {
            "name": batch.extractor.name,
            "version": batch.extractor.version,
        },
        "claim_count": len(receipts),
        "claims": claims,
        "automatic_scientific_acceptance": False,
    }

    if args.output is not None:
        _write_json_atomic(args.output, manifest)

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


def semantic_export_command(args: argparse.Namespace) -> int:
    store = CollectorStore(args.database)
    request = build_semantic_extraction_request(
        store,
        tuple(args.claim_ids),
    )

    if args.output is not None:
        _write_json_atomic(args.output, request)

    print(json.dumps(request, ensure_ascii=False, indent=2))
    return 0


def semantic_baseline_command(args: argparse.Namespace) -> int:
    store = CollectorStore(args.database)
    extractor = ConservativeFrenchLexicalExtractorV1()
    run = run_semantic_extractor(
        store,
        extractor,
        tuple(args.claim_ids),
    )
    payload = atomic_batch_to_payload(run.batch)

    if args.output is not None:
        _write_json_atomic(args.output, payload)

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def semantic_evaluate_command(args: argparse.Namespace) -> int:
    candidate = load_atomic_claim_batch(args.candidate)
    reference = load_atomic_claim_batch(args.reference)
    report = evaluate_semantic_batch(candidate, reference)

    if args.output is not None:
        _write_json_atomic(args.output, report)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def semantic_openai_command(args: argparse.Namespace) -> int:
    store = CollectorStore(args.database)
    extractor = OpenAIResponsesSemanticExtractor(model=args.model)
    run = run_semantic_extractor(
        store,
        extractor,
        tuple(args.claim_ids),
    )
    payload = atomic_batch_to_payload(run.batch)

    if args.output is not None:
        _write_json_atomic(args.output, payload)
    if args.diagnostics_output is not None:
        diagnostics = extractor.last_diagnostics or {}
        _write_json_atomic(args.diagnostics_output, diagnostics)

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def claim_show_command(args: argparse.Namespace) -> int:
    store = CollectorStore(args.database)
    payload = store.get_claim_with_evidence(args.claim_id)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def review_command(args: argparse.Namespace) -> int:
    store = CollectorStore(args.database)
    decision_id = store.record_review_decision(
        target_type=args.target_type,
        target_id=args.target_id,
        decision=args.decision,
        reviewer=args.reviewer,
        rationale=args.rationale,
        corrected_text=args.corrected_text,
    )
    print(
        json.dumps(
            {
                "decision_id": str(decision_id),
                "target_type": args.target_type,
                "target_id": args.target_id,
                "decision": args.decision,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the durable Collector CLI."""
    parser = build_parser()
    args = parser.parse_args(
        list(argv) if argv is not None else None
    )

    if args.command == "init":
        return init_command(args)
    if args.command == "import-transcript":
        return import_transcript_command(args)
    if args.command == "acquire":
        return acquire_command(args)
    if args.command == "status":
        return status_command(args)
    if args.command == "pending":
        return pending_command(args)
    if args.command == "propose-claims":
        return propose_claims_command(args)
    if args.command == "claim-show":
        return claim_show_command(args)
    if args.command == "ingest-atomic-claims":
        return ingest_atomic_claims_command(args)
    if args.command == "semantic-export":
        return semantic_export_command(args)
    if args.command == "semantic-baseline":
        return semantic_baseline_command(args)
    if args.command == "semantic-evaluate":
        return semantic_evaluate_command(args)
    if args.command == "semantic-openai":
        return semantic_openai_command(args)
    if args.command in SEMANTIC_CANDIDATE_REVIEW_COMMANDS:
        return run_semantic_candidate_review_command(args)
    if args.command == "review":
        return review_command(args)

    parser.print_help()
    return 0

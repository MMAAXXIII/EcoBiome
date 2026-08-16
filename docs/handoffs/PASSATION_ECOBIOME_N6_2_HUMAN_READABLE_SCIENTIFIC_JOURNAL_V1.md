# EcoBiome N6.2 — Human-readable Scientific Journal Projection V1

Gate target:
`ECOBIOME_N6_2_HUMAN_READABLE_SCIENTIFIC_JOURNAL_V1_LOCAL_IMPLEMENTATION_VALIDATED`

## Goal

Replace the raw canonical-JSON-first journal experience with a two-layer projection:

1. a human-readable French chronology for daily use;
2. a collapsed technical/audit section preserving exact N5 identities and payloads.

The durable N5 event is unchanged. N6.2 changes projection only.

## User-facing behavior

The journal card title exposes the nature of the event and the browser-local date/time:

- Mise en eau initiale;
- Ajustement du niveau d’eau;
- Changement d’eau;
- Mesure de température / pH / ammoniaque-ammonium / nitrites / nitrates /
  oxygène dissous / phosphates / fer / CO₂.

The detail view uses natural French prose. For water exchanges it states removed and
replacement volumes, reconstructed before/after volume when available, the user note,
and the fact that no chemistry is inferred when replacement composition is unknown.

## Audit behavior

Canonical identifiers, payload schema, payload SHA-256, event-envelope SHA-256 and
the exact canonical payload remain available under a collapsed
`Détails techniques et traçabilité` section.

## Non-goals

- no N5 schema change;
- no mutation of existing journal events;
- no automatic scientific interpretation;
- no chemistry inference from a water exchange without replacement composition;
- no Collector-to-project knowledge projection in this slice.

## Acceptance criteria

- raw canonical JSON is not shown in the normal prose;
- event nature and date/time are visible directly in the journal title;
- intervention/observation filtering is available;
- all technical identities remain accessible;
- N6/N6.1 behavior remains unchanged;
- Ruff, mypy, targeted tests, full pytest, TypeScript and Vite build pass.

Do not stage, commit, push, merge, rebase, delete branches or modify GitHub metadata
without separate explicit authorization.

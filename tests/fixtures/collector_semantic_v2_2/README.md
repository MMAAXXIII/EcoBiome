# Collector semantic benchmark fixture — Medaka V2.1

This directory freezes the reviewed Medaka semantic benchmark inputs used by
`test_collector_semantic_benchmark_v2_2.py`.

Files:
- `GOLDEN_REFERENCE_V2_1.json`: 13 REQUIRED, 3 ADMISSIBLE, 1 EXCLUDED.
- `SEMANTIC_EXPORT.json`: frozen source Claim/Evidence export.
- `OLLAMA_QWEN36_CANDIDATE.json`: frozen Qwen3.6 benchmark candidate.
- `LEXICAL_BASELINE.json`: frozen deterministic lexical baseline candidate.

The fixture is regression infrastructure. It does not establish scientific
truth and does not certify a production semantic provider.

Frozen source benchmark ZIP SHA-256:
`e54f8231988169a027447d8b6ed9f7d75f20d9a4e16c193958dfbf375ca95bdd`

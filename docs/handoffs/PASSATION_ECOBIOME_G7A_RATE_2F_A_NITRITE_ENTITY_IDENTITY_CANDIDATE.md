# PASSATION — EcoBiome G7A RATE-2F-A — Nitrite Entity Identity Candidate

Gate:
`ECOBIOME_G7A_RATE_2F_A_NITRITE_ENTITY_IDENTITY_CANDIDATE_LOCAL`

Precondition:
`agent/g7a-directional-nitrogen-semantic-stack-v1@2723e8f5b12e827abb46df68018c307446112833`

## RATE-2F R1 diagnosis

RATE-2F R1 stopped before shadow-copy creation because the historical oxidation
template has three participants, not two.

No real or shadow database write occurred.

## V6 identity gap

Current reviewed chemical entities include:

```text
ammonia  CID 222
ammonium CID 223
nitrate  CID 943
```

Nitrite is absent.

## Candidate

```text
entity-pubchem-cid-946
chemical_species
nitrite
NO2-
PubChem CID 946
```

Candidate payload SHA:

```text
4fe7808c45aecafbe6ecd09d4590aff6d5b0d965b5a795502020ed49220e129f
```

## Review state

```text
decision         = pending
reviewed_confirmed = false
```

No script may infer acceptance.

## Future RATE-2F correction

The future assertion must:

```text
use ammonia CID 222 as reactive source entity
use nitrite CID 946 only after identity acceptance
omit inherited Candidatus Nitrospira inopinata process_agent
preserve semantic_type=nitrogen_oxidation
```

## Persistence boundary

```text
real V6 write             = false
entity insertion          = false
assertion insertion       = false
assertion-claim link      = false
ProcessScientificSupport  = false
numeric RateModel         = false
remote write              = false
```

Next gate after explicit identity acceptance:

`RATE-2F-B — Nitrite Entity Shadow Seed + Mechanism Assertion Dry-Run`

# PASSATION — EcoBiome G7A RATE-1B

Gate:
`ECOBIOME_G7A_RATE_1B_NITRIFICATION_GRANULARITY_EVIDENCE_CANDIDATE_LOCAL`

Precondition:
`agent/g7a-directional-nitrogen-semantic-stack-v1@111a1f09cf24b64e192ca44f548b058b08ba8be1`

## Adopted decisions

1. Predictive nitrification target is two-step:
   `ammonia/TAN-N -> nitrite-N -> nitrate-N`.
2. Existing G7A one-step oxidation remains a deterministic reviewed
   mechanism/direction demonstration.
3. First future kinetic process is ammonia/TAN-N -> nitrite-N.
4. First model family is explicitly scoped to freshwater attached-biofilm
   aquaculture biofilters.
5. TAN, NH4+-N, NH3-N, nitrite-N and nitrate-N must not be silently conflated.
6. An explicit nitrite state is required before claiming two-step prediction.
7. Primary evidence candidate is Mnyoro et al. 2021:
   freshwater fixed-bed RAS, surface-normalized TAN removal, first-order
   coefficient 0.45 m/d under the high-velocity tested context.
8. Malone et al. 2006 supports evaluating a low-TAN linear family.
9. Zhu & Chen 1999 remains an alternative saturation-family candidate.
10. Kinyage & Pedersen 2016 supplies separate temperature-response evidence but
    is not automatically composable with the fixed-bed coefficient.
11. Cross-paper parameter splicing is prohibited without reviewed derivation.
12. No numeric RateModel is approved by RATE-1B.

## Unchanged boundaries

- Scientific Foundation V6 read-only;
- no source-code changes;
- no rate calculation;
- no kinetic parameter persisted;
- no nitrite component added yet;
- no Δt;
- no remote write.

## Next gate

`RATE-1C — Generic RateModel V1 Contracts`

RATE-1C may implement generic deterministic contracts only. It must not embed
the Mnyoro coefficient or any other nitrification constant.

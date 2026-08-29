# EcoBiome — RATE-3S publication hardening

Status: DESIGN / TEST / DRY-RUN ONLY.

The first persistent active pointer remains unauthorized.

RATE-3S hardens first-publication mechanics for the reviewed Windows deployment:

- same-directory exclusive temporary creation;
- file flush + `fsync` before publication;
- second full ancestry audit immediately before publication;
- `MoveFileExW(..., MOVEFILE_WRITE_THROUGH)` with **no** `MOVEFILE_REPLACE_EXISTING`;
- destination appearance therefore fails closed instead of being overwritten;
- exact post-publication readback and canonical pointer verification.

Hardened contract SHA-256:
`6bf60e103634c2aa85cb7640ad5c325a9d1248457d2b25f48fc174e21b985f16`

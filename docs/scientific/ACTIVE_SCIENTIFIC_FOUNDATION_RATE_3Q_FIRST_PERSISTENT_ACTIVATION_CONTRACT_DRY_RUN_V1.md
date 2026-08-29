# EcoBiome — RATE-3Q first persistent activation contract

Status: DESIGN / TEST / DRY-RUN ONLY.

## Trusted deployment inputs

The existing runtime configuration is frozen as the deployment trust boundary:

- `ECOBIOME_ACTIVE_SCIENTIFIC_FOUNDATION_RUNTIME_POLICY`
- `ECOBIOME_ACTIVE_SCIENTIFIC_FOUNDATION_RUNTIME_POLICY_SHA256`

The policy path and expected canonical SHA-256 are separate deployment inputs.
The expected SHA must never be recomputed from the policy file by the runtime
configuration layer.

## Exact activation target

- parent V6: `76381b5a76f0dd34668634357b3fa4657ff650351235ad85acc8b6fdb421997f`
- snapshot DB: `2bc6d8524c529ebb52ce5c5a9b3b44f879dcdf9b62b5d6c8d2153443259dfde9`
- snapshot manifest file: `62258e18668423ba2c01d422c9e52fd8d38909f549476bb937482495ecaa8774`
- snapshot manifest payload: `7e0a50f571ea512ed8620c6e0fe1ae9cdc335e06ccbb9f978095dbd3a2479f20`
- consumer migration identity: `42914fe3998911e33122c5bad7dd237e740da2b962f090fcb3e09ef1c3adc227`
- resolver code: `58ee76d2a163ae844b8b8c89653e65a70be475acb1a8ed3bf61aa974b56cd2e9`

## Path security

Every ancestor component of the persistent pointer path, V6 database, CAS root,
snapshot root, content-addressed snapshot directory, snapshot database and
snapshot manifest is audited. Symlink, junction and Windows reparse-point
components fail closed.

## Publication

First activation requires the real pointer target to be absent. Publication is
defined as same-directory exclusive temp creation, flush + fsync, exact temp
readback, atomic `os.replace`, and exact post-replace readback.

RATE-3Q code refuses any publication target under the real EcoBiome data root.

## Rollback

Rollback is a separate reviewed, quiesced control-plane operation. Silent
pointer deletion while active consumers run is forbidden. A reviewed legacy
policy and independently trusted SHA must be provisioned, the pointer archived
atomically, absence verified, and consumers restarted only after verification.
A fail-closed transition window is acceptable.

## Authorization boundary

RATE-3Q does not authorize creation of the real active pointer and does not
authorize persistent runtime-policy publication.

Contract payload SHA-256: `8ef9950627a533c195d27726d1790350f2a4838de210da05743c9038843b41fa`

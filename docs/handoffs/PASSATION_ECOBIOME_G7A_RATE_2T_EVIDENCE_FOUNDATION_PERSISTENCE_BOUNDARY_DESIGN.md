# PASSATION — EcoBiome G7A RATE-2T — Evidence Foundation Persistence Boundary Design

Expected precondition:

```text
agent/g7a-directional-nitrogen-semantic-stack-v1@fd2cea3f774cb3d324a70fa0c6de54e955f4e07b
```

RATE-2S:

```text
projection payload = b32312fdcb51e1408cb9a8ce6a1d3dc31735335f11fe5e72bd5605d73220da7d
stable policy      = ff95c9aa278772d7bf58a17dcd93fe386795dc6320f42a6f911873cc1128e59b
```

RATE-2T designs:

```text
derived snapshot boundary = 7cc40c48504639d13b9f1b20596a55796b73f93a75e10ff581b5a078b57e808a
snapshot manifest contract = 8675774056188fce62c7c29cf816238d155871bf69aaa79ee85e8b1567b2cf20
```

Recommended architecture:

```text
frozen parent snapshot
-> isolated staging copy
-> reviewed replay
-> integrity + regression validation
-> immutable content-addressed derived snapshot
-> canonical sidecar manifest
-> optional separately-authorized active pointer
```

Important:

```text
data-state promotion != schema-version migration
Schema V6 + new reviewed rows remains Schema V6
```

Durable promotion must use frozen source artifact bytes from external CAS by
SHA-256, not live-network refetch.

Current authorization:

```text
snapshot creation = false
activation        = false
real V6 write     = false
schema migration  = false
RateModel         = false
```

Next:

`RATE-2U — Evidence Foundation Persistence Boundary Human Review`

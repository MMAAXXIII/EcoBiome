# EcoBiome — RATE-3G Disposable Real-V6 Dry-Run

Status:

```text
PASS
```

Authorization:

```text
905e56a76dff794933c3fade8a181d726e2d291a15301a08b324575b0ad1c96d
```

Replay:

```text
26f7a1f7b8cef2a6e7ad7e0f861a65fd12de89bace4270202447fe3b821e801a
32 rows
knowledge_sources +3
```

Real frozen V6:

```text
76381b5a76f0dd34668634357b3fa4657ff650351235ad85acc8b6fdb421997f
read-only and unchanged
```

Disposable replay result:

```text
database SHA-256
2bc6d8524c529ebb52ce5c5a9b3b44f879dcdf9b62b5d6c8d2153443259dfde9

database size
643072 bytes

snapshot-manifest file SHA-256
78481d7df8a778229d36cd12f572d66818b0064f83192c5e83c400f62a312d92

snapshot-manifest canonical payload SHA-256
65facc51845497d857cf04a62fed355290bc1cb635eee5db9f2c79cd9a382006
```

Validation:

```text
row-by-row canonical verification = PASS
quick_check = ok
foreign-key violations = 0
full regression = PASS
```

Persistent boundaries:

```text
real V6 write = false
persistent CAS write = false
persistent scientific snapshot = false
active pointer update = false
remote write = false
```

The disposable CAS and disposable snapshot were deleted after audit metadata was
captured.

Next:

```text
RATE-3H — first persistent snapshot publication human review
```

# HRP-50 / ADR-0006 - Sanitized correlation evidence

## Authorized source

The evidence comes from the authorized read-only observation of the persisted RAW
collection `hr_pro.raw_events_hrp43_20260901`.

Sample size: 2,000 RAW documents.

No educational generator source or logs were inspected.

## Exact-equality edge results

| Edge | Source documents | Target documents | Shared exact values | Matched source documents | Matched target documents | 1:1 matches | 1:N | N:1 | N:N | Unmatched source | Unmatched target | Observed ambiguity/collision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Personal `passport` - Bank `passport` | 399 | 399 | 397 | 397 | 397 | 397 | 0 | 0 | 0 | 2 | 2 | 0 |
| Personal `name + " " + last_name` - Location `fullname` | 399 | 400 | 251 | 251 | 251 | 251 | 0 | 0 | 0 | 148 documents / 144 candidate values | 149 | 0 |
| Location `fullname` - Professional `fullname` | 400 | 401 | 399 | 399 | 399 | 399 | 0 | 0 | 0 | 1 | 2 | 0 |
| Location `address` - Net `address` | 400 | 401 | 400 | 400 | 400 | 400 | 0 | 0 | 0 | 0 | 1 | 0 |

## Transitive evidence

Observable connected components by represented domain count:

| Domains | Components |
|---:|---:|
| 5 | 249 |
| 4 | 2 |
| 3 | 149 |
| 2 | 147 |
| 1 | 6 |

Bridge evidence:

- Personal/Location exact matches: 251.
- Personal/Location matches also connected to Bank: 250.
- Location side also connected to Professional: 250.
- Location side also connected to Net: 251.
- Complete observable five-domain chains: 249.

## Normalization and ambiguity results

Case-insensitive, whitespace, diacritic, and combined normalization hypotheses all
produced the same 251 Personal/Location matches as exact raw comparison. None
introduced an observed normalization-only collision.

Across the observed edges:

- one-to-many edges: 0;
- many-to-one edges: 0;
- many-to-many edges: 0;
- candidates linking incompatible chains: 0.

Exact raw comparison remains the approved operational baseline. This observation
does not establish a normalization rule or real-world identity.

## Limitations

This bounded observation does not prove:

- real-world identity;
- universal uniqueness;
- completeness;
- absence of future collisions;
- safe use as a universal business identity;
- that unmatched records are contradictory.

Unmatched records represent absence of an observed link in this bounded sample, not
proof of different identity.

## Sanitization statement

This versioned observation contains aggregate counts only. It contains no raw payload
values, names, passports, addresses, PII, hashes derived from PII, secrets, Kafka
offsets, complete message captures, generator source/code, or generator-derived
implementation knowledge.

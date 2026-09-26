# Iso-cost meters

No measured numbers in this file. Fill tables only after a real run.

## What is held fixed

| Meter | Rule |
| --- | --- |
| Human minutes | Same `B_human_min` for every condition that is compared. Timer excludes predefined breaks. |
| SLM tokens | Same token cap for conditions A, B, and C. Count prompt + completion, including one JSON-repair retry. |
| SLM wall time | Same wall-clock cap for A–C. |
| Step set | Shared `N_target` (below). |

## `N_target` rule

1. On the **dev** split only, run A, B, and C under the token and time caps.
2. Throughput = steps completed before either cap.
3. `N_target` = minimum throughput among A, B, and C.
4. On **test**, all SLM conditions process the **same** first `N_target` steps of one permutation (fixed seed).
5. Do not compare conditions on different “eligible before cutoff” denominators.

If provider throttling differs, re-run or lower `N_target` for all SLM conditions together.

## Nebius / free-tier fairness

- Same provider, model id, and version for A–C.
- Iso-cost is metered tokens, wall time, and human minutes — not the dollar invoice.
- Disclose the free overlay in the run manifest. Do not claim an advantage from free compute.

## Condition D

Exploratory foil only. Human minutes may be matched for an appendix. D is not in the primary A vs B denominator.

## Placeholder log fields (smoke)

`tokens_in`, `tokens_out`, `wall_time_ms` may be `null` in the dry-run mock. Null is not a measurement.

A measuring judge fills those three fields from the backend usage object and a wall-clock timer around that call, including one schema-failure retry. The iso-cost tables above stay empty until a full A/B/C budget run on a frozen test split. A CPU smoke log is not that run. Do not copy smoke timings into the tables in this file.

# Decision log line

One JSON object per step, JSONL. Dry-run may leave meter fields null.

```json
{
  "condition": "cards",
  "trajectory_id": "fixture-1",
  "step_id": "s1",
  "step_index": 0,
  "decision": "allow",
  "matched_cards": [],
  "rationale": "dry-run mock",
  "risk_score": null,
  "judge": "dry-run-mock",
  "tokens_in": null,
  "tokens_out": null,
  "wall_time_ms": null,
  "policy_artifact": "cards"
}
```

`condition` is `cards` or `prose` for the smoke loop (A vs B).  
`risk_score` is omitted from any human UI.  
Null token/time fields are placeholders, not measurements.

The JSONL this loop *reads* is a step record, documented in [`step.md`](step.md). This file is only the decision log.

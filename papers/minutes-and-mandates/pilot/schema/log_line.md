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
  "rationale": "dry-run mock; not a measured judgment",
  "risk_score": null,
  "risk_score_omitted": true,
  "judge": "dry-run-mock",
  "tokens_in": null,
  "tokens_out": null,
  "wall_time_ms": null,
  "policy_artifact": "cards",
  "parse_ok": true,
  "parse_failure_count": 0,
  "attempt_count": 0,
  "attempts": []
}
```

`condition` is `cards` or `prose` for the smoke loop (A vs B).  
`risk_score` is omitted from any human UI.  
Null token/time fields are placeholders, not measurements.

Measured runs add:

| Field | Meaning |
| --- | --- |
| `parse_ok` | The accepted text matched `judge_output.schema.json`. |
| `parse_failure_count` | Attempts whose text failed JSON or the schema. Text is stored, not rewritten. |
| `attempt_count` | Model calls for this step. At most 2. |
| `attempts` | Per attempt: `raw_output`, `parse_error`, `tokens_in`, `tokens_out`, `wall_time_ms`, `finish_reason`. |
| `risk_score_omitted` | True when a valid object had no `risk_score` key. |
| `prompt_sha256` | Hash of the messages sent on the first attempt. |
| `model_repo`, `model_revision`, `model_filename`, `model_sha256`, `quantization` | Pinned GGUF, when the llama backend ran. |
| `n_threads`, `n_ctx`, `n_batch`, `n_gpu_layers` | llama.cpp settings for that call. |

`tokens_in`, `tokens_out`, and `wall_time_ms` on the step are the sums of `attempts`. When `parse_ok` is false, `decision` and `rationale` are null. That null decision is not an allow. The dry-run mock leaves the meter fields null, sets `attempt_count` to 0, and does not claim a model call.

The JSONL this loop *reads* is a step record, documented in [`step.md`](step.md). This file is only the decision log.

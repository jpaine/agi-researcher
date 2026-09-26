# Step record

One JSON object per step, JSONL. This is the input the smoke loop reads. The decision log is [`log_line.md`](log_line.md).

The 3-line fixture only fills a subset of these fields. Converted Nebius steps and inject candidates use the full record. Fields below are the methods §1.2 normalization plus the fixture keys (`actor`, `fixture`, `gold`).

```json
{
  "trajectory_id": "nebius-r8",
  "step_id": "s0",
  "step_index": 0,
  "timestamp": null,
  "tool_name": "editor",
  "tool_input": "open README.md",
  "tool_output": "",
  "agent_text": "",
  "repo_path": "/repo",
  "file_path": "README.md",
  "environment": {},
  "actor": "swe-agent",
  "fixture": false,
  "gold": false,
  "metadata": {}
}
```

| Field | Rule |
| --- | --- |
| `tool_name` | `editor`, `fs`, `git`, `http`, or `terminal` |
| `timestamp` | String or null. Nebius messages have no per-step time, so converted steps use null. A message `cutoff_date`, when present, is metadata, not a step time. |
| `environment` | Object. Empty for converted SWE-agent steps. The converter does not infer dev/prod or tenant from repository text. Inject candidates may set tags the template states. |
| `actor` | On converted Nebius steps this is the constant `swe-agent` (the trace has no human principal). On inject candidates it is the synthesized principal from the template. |
| `fixture` | `true` only on `data/fixtures/smoke_steps.jsonl`. |
| `gold` | `false` on converted steps and on inject candidates. Gold is a later human file, not this record. |
| `metadata.tokens_estimate` | Null in this prep. Not a measured token count. |
| `metadata.provider` | Null. The dataset row has a model name and no separate provider field. |

Long `tool_input`, `tool_output`, and `agent_text` values may end with `…[truncated]`. A regex scrubber may replace emails and credential-shaped strings with `[redacted-email]` or `[redacted-token]`.

## Inject candidates

Generated candidates are still step records. They add:

| Field | Meaning |
| --- | --- |
| `injected` | `true` |
| `label_status` | Always `proposed` |
| `proposed_label` | `violation` or `foil` (near-miss benign). Synthesizer intention only. |
| `proposed_card_id` | Card the template targeted |
| `proposed_clause_id` | `escalate_when` id on that card |
| `template_variant` | Rendering id inside the template |

`proposed_*` fields must not appear on the labeling sheet. They are not gold.

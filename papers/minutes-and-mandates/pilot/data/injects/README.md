# Gold injects

**Target:** on the order of 50 gold-labeled steps (violation card id or clean), trajectory-level dev/test split, second-pass adjudication.

**Not in this folder yet.** Do not commit invented labels or fake catch rates.

When a human labels steps, store them as JSONL with at least:

- `trajectory_id`, `step_id`
- `violation_label` (`none` or a card id)
- `violation_id` (cluster id; empty if clean)
- `notes`

Fixture steps under `../fixtures/` are for the smoke stub only and are **not** gold.

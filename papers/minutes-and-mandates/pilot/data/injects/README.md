# Inject candidates

**Not gold.** `candidates.jsonl` is a seeded synthesizer output. Each row has `label_status: proposed` and `proposed_label` of `violation` or `foil`. Foil means the template intended a near-miss benign step. Neither value is a human label.

`manifest.json` records, for each candidate: source trajectory, source step index, card, template variant, clause, and the proposed label. It is not the labeling view. The labeling sheet hides those proposed fields (`../../labeling/LABELING.md`).

Gold files, when Jeffrey's two passes exist, are separate and are not created here. Do not commit invented catch rates.

Fixture steps under `../fixtures/` are for the smoke stub only and are **not** gold.

Templates: `../../injects/templates/{card_id}.yaml`.

# Week-1 pilot scaffold (Gate A)

Smoke layout only. **No gold labels and no pilot metrics** live here yet.

Venue path: **AAAI-27** primary, **ICLR 2027 workshop** backup. MASO skipped (`brainstorm/minutes-and-mandates/GO_NO_GO.md`).

## Gate A steps (not checked off)

1. Cards: drafted under `brainstorm/minutes-and-mandates/cards/` (YAML + matched prose).
2. Trajectories: download free public Nebius / SWE-agent traces into `data/trajectories/` (human). Do not commit huge dumps by default.
3. Injects / gold: ~50 gold-labeled steps. See `data/injects/README.md`. Labels are human work.
4. Judge loop: `scripts/smoke_loop.py` on a 3-step **fixture** (dry-run mock). Replace the mock with a real ≤8B judge only when traces and labels exist.
5. Meters: follow `meters.md` (`N_target`, human minutes, SLM tokens/time, Nebius fairness).
6. Do not call Denario `get_paper`. Do not invent catch rates.

## How to run the smoke loop

```bash
python3 papers/minutes-and-mandates/pilot/scripts/smoke_loop.py
python3 papers/minutes-and-mandates/pilot/scripts/smoke_loop.py --condition prose
```

Default is a dry-run mock (decision `allow`, token fields null).  
`OPENAI_API_KEY` is optional and **unused** unless you pass `--live` later; this stub does not call the network.

Real Nebius trajectory download and gold labels remain human week-1 work.

## Layout

| Path | Role |
| --- | --- |
| `schema/judge_output.schema.json` | `allow` \| `escalate` \| `block` |
| `schema/log_line.md` | One JSON object per step |
| `data/trajectories/` | Placeholder for real traces |
| `data/injects/README.md` | Gold-label target; no invented labels |
| `data/fixtures/smoke_steps.jsonl` | 3 fake steps for the stub |
| `scripts/smoke_loop.py` | Same step order for cards vs prose |
| `meters.md` | Iso-cost accounting |

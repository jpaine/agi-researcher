# papers/minutes-and-mandates — Denario `project_dir`

| Field | Value |
| --- | --- |
| **Slug** | `minutes-and-mandates` |
| **Role** | Denario `project_dir` for idea/method **critique** (not a finished paper) |
| **Status** | Method draft patched after critique; Gate A prep (cards, Nebius subset ingest, proposed inject candidates, mock smoke loop). No gold labels and no pilot metrics. |
| **Brainstorm source** | [`../../brainstorm/minutes-and-mandates/`](../../brainstorm/minutes-and-mandates/) (`BRIEF.md`, `IDEA.md`, `GO_NO_GO.md`) |

## Hard rules

1. **Locked claim must stay locked.** Do not dilute, broaden, or replace it in Denario outputs. See `constraints.md`.
2. Denario idea/method outputs under `input_files/` are **drafts to critique**, not results and not submission-ready text.
3. **Do not invent experimental results.** No catch rates, human-study numbers, or SOTA claims until measured.
4. **Do not call `get_paper` / `get_results` yet.** This scaffold stops at locked idea + method draft (+ optional critique pass).
5. Workshop path: **AAAI-27** primary, **ICLR 2027 workshop** backup. MASO skipped. Not main-conference SOTA.

## Files

| Path | Purpose |
| --- | --- |
| `data_description.md` | Content for `Denario.set_data_description(...)` |
| `constraints.md` | Hard constraints appended / enforced in the loop |
| `idea_locked.md` | Locked working title + claim + Angle 1 spine for `set_idea` |
| `prompts/critique_pass.md` | Second-pass critique instructions (threats, reviewer attacks, $0/4-week fit) |
| `run_denario_loop.py` | Minimal runner: set description → set locked idea → `get_method()` |
| `input_files/` | Denario writes `data_description.md`, `idea.md`, `methods.md` here when run |

## Pinned Denario model ids

Chosen from `vendor/denario/denario/llm.py` (`denario.models` keys) — newest OpenAI entries Denario registers (not gpt-4o / gpt-4o-mini defaults):

| Role | Model id | Notes |
| --- | --- | --- |
| Flagship chat / method generator / planner / orchestration | `gpt-5` | Denario LLM name `gpt-5` |
| Reasoning / plan review / formatter | `o3-mini` | Resolves to API id `o3-mini-2025-01-31` |
| Fast-mode single LLM (default `--llm`) | `gpt-5` | Overrides Denario’s stock `gemini-2.0-flash` default |

`run_denario_loop.py` passes these explicitly into `get_method`. Do **not** commit API keys; set `OPENAI_API_KEY` in the environment only.

## How to run (when keys exist)

```bash
# from repo root, with Denario installed (./scripts/denario.sh install)
export OPENAI_API_KEY=...          # required for pinned gpt-5 / o3-mini
export GOOGLE_API_KEY=...          # optional (only if you override --llm to Gemini)
export ANTHROPIC_API_KEY=...       # optional
# see vendor/denario docs: https://denario.readthedocs.io/en/latest/llm_api_keys/apikeys/

python3 papers/minutes-and-mandates/run_denario_loop.py --dry-run   # no LLM calls
python3 papers/minutes-and-mandates/run_denario_loop.py            # fast mode → gpt-5
python3 papers/minutes-and-mandates/run_denario_loop.py --mode cmbagent  # gpt-5 + o3-mini roles
# optional second pass (manual): feed prompts/critique_pass.md + input_files/{idea,methods}.md to your critic
```


## Relation to go/no-go

Brainstorm `GO_NO_GO.md` still gates **pilot empirics** and **paper generation**. This folder only scaffolds **idea/method critique** once API keys are available. Empirics and `get_paper` remain blocked until Gate A / venue gates say otherwise.

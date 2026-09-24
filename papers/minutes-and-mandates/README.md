# papers/minutes-and-mandates — Denario `project_dir`

| Field | Value |
| --- | --- |
| **Slug** | `minutes-and-mandates` |
| **Role** | Denario `project_dir` for idea/method **critique** (not a finished paper) |
| **Status** | **Awaiting API keys** for idea/method critique loop |
| **Brainstorm source** | [`../../brainstorm/minutes-and-mandates/`](../../brainstorm/minutes-and-mandates/) (`BRIEF.md`, `IDEA.md`, `GO_NO_GO.md`) |

## Hard rules

1. **Locked claim must stay locked.** Do not dilute, broaden, or replace it in Denario outputs. See `constraints.md`.
2. Denario idea/method outputs under `input_files/` are **drafts to critique**, not results and not submission-ready text.
3. **Do not invent experimental results.** No catch rates, human-study numbers, or SOTA claims until measured.
4. **Do not call `get_paper` / `get_results` yet.** This scaffold stops at locked idea + method draft (+ optional critique pass).
5. Workshop / short-paper path first (MASO → AAAI / ICLR workshops). Not main-conference SOTA.

## Files

| Path | Purpose |
| --- | --- |
| `data_description.md` | Content for `Denario.set_data_description(...)` |
| `constraints.md` | Hard constraints appended / enforced in the loop |
| `idea_locked.md` | Locked working title + claim + Angle 1 spine for `set_idea` |
| `prompts/critique_pass.md` | Second-pass critique instructions (threats, reviewer attacks, $0/4-week fit) |
| `run_denario_loop.py` | Minimal runner: set description → set locked idea → `get_method()` |
| `input_files/` | Denario writes `data_description.md`, `idea.md`, `methods.md` here when run |

## How to run (when keys exist)

```bash
# from repo root, with Denario installed (./scripts/denario.sh install)
export OPENAI_API_KEY=...          # required for many Denario modules
export GOOGLE_API_KEY=...          # optional / used by default fast-mode models
export ANTHROPIC_API_KEY=...       # optional
# see vendor/denario docs: https://denario.readthedocs.io/en/latest/llm_api_keys/apikeys/

python3 papers/minutes-and-mandates/run_denario_loop.py --dry-run   # no LLM calls
python3 papers/minutes-and-mandates/run_denario_loop.py            # needs API keys
# optional second pass (manual): feed prompts/critique_pass.md + input_files/{idea,methods}.md to your critic
```


## Relation to go/no-go

Brainstorm `GO_NO_GO.md` still gates **pilot empirics** and **paper generation**. This folder only scaffolds **idea/method critique** once API keys are available. Empirics and `get_paper` remain blocked until Gate A / venue gates say otherwise.

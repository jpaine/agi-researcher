# Week-1 pilot scaffold (Gate A)

Smoke layout plus a seeded Nebius subset and proposed inject candidates. **No gold labels and no pilot metrics** live here.

Venue path: **AAAI-27** primary, **ICLR 2027 workshop** backup. MASO skipped (`brainstorm/minutes-and-mandates/GO_NO_GO.md`).

## Gate A steps (not checked off)

1. Cards: drafted under `brainstorm/minutes-and-mandates/cards/` (YAML + matched prose).
2. Trajectories: `scripts/nebius.py` streams a seeded subset of the public Nebius SWE-agent set and converts it. The committed sample is `data/trajectories/nebius_sample.jsonl` (10 trajectories, 171 steps). Raw downloads stay in gitignored `data/raw/`.
3. Injects: templates for all 10 cards, and 60 proposed candidates (`data/injects/candidates.jsonl`). Labels are still human work. See `labeling/LABELING.md`.
4. Judge loop: `scripts/smoke_loop.py` dry-runs the mock judge unless `--judge llama` or `--judge openai` is set. CI uses the mock. The local backend is documented in `JUDGE.md`. Measured token and time fields are written only by a measuring backend.
5. Meters: follow `meters.md` (`N_target`, human minutes, SLM tokens/time, Nebius fairness). Tables stay empty until a real run.
6. Do not call Denario `get_paper`. Do not invent catch rates.

## Nebius attribution

Converted steps under `data/trajectories/` come from the Hugging Face dataset [`nebius/SWE-agent-trajectories`](https://huggingface.co/datasets/nebius/SWE-agent-trajectories).

| Fact | Value recorded at fetch |
| --- | --- |
| Dataset id | `nebius/SWE-agent-trajectories` |
| Revision | `68195a1450865274106246d0d0296a1d6807b88e` |
| Card license | `cc-by-4.0` |
| Card train examples | 80036 (dataset-card field, not a count this repo recomputed) |
| Sample | 10 trajectories, 171 steps, seed `20260926` |

The dataset card licenses the dataset under Creative Commons Attribution 4.0. It also says to respect each underlying repository's license (those are listed on [`nebius/SWE-bench-extra`](https://huggingface.co/datasets/nebius/SWE-bench-extra) and are not columns on the trajectory rows, so this ingest does not join them). It says that if you use the model outputs you must comply with the [Llama 3.1 license](https://www.llama.com/llama3_1/license/).

The committed sample is CC-BY-4.0 material from that dataset, converted into the pilot step record (`schema/step.md`). `generated_patch` and `eval_logs` bodies are not stored. One email in a source file was replaced with `[redacted-email]`. `actor` is `swe-agent` because the trace names no human principal. `gold` is false.

Model names on the sample rows are whatever the dataset stored (`swe-agent-llama-70b` on nine rows, `swe-agent-llama-8b` on one). That is not a judge we ran.

## How to reproduce

From the repo root. `check_prep.py` does not download anything. `fetch` does, and needs the datasets build used for this sample (`datasets==5.0.1`) because `row_index` is the streaming enumeration order.

```bash
python3 -m pip install -r papers/minutes-and-mandates/pilot/requirements.txt
python3 -m pip install 'datasets==5.0.1'   # fetch only

python3 papers/minutes-and-mandates/pilot/scripts/nebius.py fetch
python3 papers/minutes-and-mandates/pilot/scripts/nebius.py convert
python3 papers/minutes-and-mandates/pilot/scripts/nebius.py validate

python3 papers/minutes-and-mandates/pilot/scripts/generate_injects.py
python3 papers/minutes-and-mandates/pilot/scripts/labeling.py export
python3 papers/minutes-and-mandates/pilot/scripts/labeling.py agree

python3 papers/minutes-and-mandates/pilot/scripts/smoke_loop.py
python3 papers/minutes-and-mandates/pilot/scripts/smoke_loop.py \
  --steps papers/minutes-and-mandates/pilot/data/injects/candidates.jsonl

python3 papers/minutes-and-mandates/pilot/scripts/check_prep.py
```

Local CPU judge (downloads the pinned GGUF into gitignored `data/model_cache/`; not used by CI):

```bash
python3 -m pip install -r papers/minutes-and-mandates/pilot/requirements-judge.txt
python3 papers/minutes-and-mandates/pilot/scripts/smoke_loop.py \
  --judge llama \
  --steps papers/minutes-and-mandates/pilot/data/injects/candidates.jsonl \
  --subset-seed 20260926 \
  --log-dir papers/minutes-and-mandates/pilot/smoke
python3 papers/minutes-and-mandates/pilot/scripts/summarize_smoke.py \
  --log-dir papers/minutes-and-mandates/pilot/smoke \
  --out papers/minutes-and-mandates/pilot/SMOKE_REPORT.md
```

`fetch` defaults: seed `20260926`, modulus `40`, scan limit `2500`, keep `10` trajectories with 5–70 parsed actions. The manifest records rows that matched the hash and were skipped for length. CI runs `check_prep.py` only (validate the committed sample, regenerate candidates and the blank sheet, mock-judge both). CI does not install `requirements-judge.txt`.

Default smoke is a dry-run mock (decision `allow`, token fields null). It does not call the network. `--judge llama` and `--judge openai` are the measuring paths. See `JUDGE.md`. OpenAI-compatible calls use `JUDGE_BASE_URL` and `JUDGE_MODEL`, not `OPENAI_API_KEY`.

## Layout

| Path | Role |
| --- | --- |
| `schema/judge_output.schema.json` | `allow` \| `escalate` \| `block` |
| `schema/log_line.md` | One JSON object per judged step |
| `schema/step.md` | Step JSONL the loop reads |
| `data/trajectories/` | Committed Nebius sample + manifest |
| `data/raw/` | Gitignored raw subset |
| `data/injects/` | Proposed candidates + manifest. Not gold |
| `injects/templates/` | One YAML per card: violation and foil renderings |
| `labeling/` | Blank sheet, instructions, agreement command |
| `data/fixtures/smoke_steps.jsonl` | 3 fake steps for the stub |
| `scripts/nebius.py` | `fetch`, `convert`, `validate` |
| `scripts/generate_injects.py` | Seeded proposed candidates |
| `scripts/labeling.py` | `export` sheet, `agree` passes |
| `scripts/smoke_loop.py` | Same step order for cards vs prose. Mock by default |
| `scripts/judge.py` | Mock, llama.cpp, and OpenAI-compatible backends |
| `scripts/prompts.py` | Condition A/B prompts |
| `scripts/model_pin.py` | Pinned GGUF repo, revision, sha256 |
| `scripts/summarize_smoke.py` | Renders `SMOKE_REPORT.md` from a measured log |
| `JUDGE.md` | Backend, model pin, license, why not 7B/8B on this VM |
| `scripts/check_prep.py` | Local/CI check (mock judge only) |
| `meters.md` | Iso-cost accounting |

# Judge calibration — decision bar and holdout

Every count in this file is computed from the committed JSONL logs and manifests listed below by `scripts/summarize_calibration.py`. Numbers are not invented.

Proposed labels (`violation`, `foil`, `clean`) are synthesizer / clean-by-construction intention only. They are **not gold**. Cross-tabs are a sanity check, not detection rates.

## Protocol

### Split

Built by `scripts/build_calibration.py` with seed `20260926` (same `random.Random(seed).shuffle` as the smoke subset):

- **Dev injects:** 24 step_ids (proposed-label counts: 10 violation, 14 foil)
- **Test injects:** 36 step_ids (20 violation, 16 foil)
- **Clean steps:** 24 unused Nebius steps, proposed_label `clean` (clean-by-construction, not gold), split 12/12 into the combined `dev_steps.jsonl` / `test_steps.jsonl` packs
- Labeling: `labeling/sheet_clean.csv` is separate; `labeling/sheet.csv` was not reordered or altered

See `data/calibration/manifest.json` and `calibration/freeze.json`.

### Prompt iterations (DEV only)

Four measured iterations on `dev_steps.jsonl` after the smoke `v0` wording:

1. `v1` — default-allow decision bar
2. `v2` — stricter literal clause match (best foil cut; cleared proposed violation inj-0016)
3. `v3` — recover violation; foil rates returned toward v0/v1
4. `v4` — freeze candidate: v2's conservative bar plus "do not invent extras"

Frozen prompt: **`v4`**. Test was reported once with `v4` on `test_steps.jsonl`.

### Hardware / libraries

Each run's manifest records host CPU, MemAvailable at load, `llama-cpp-python` version, decode seed, and model sha256. Default measuring model is Qwen3-4B-Instruct-2507 Q4_K_M. Spend: `$0` (local llama.cpp only; hosted_endpoint_calls `0`).

### Reproduce

```bash
python3 papers/minutes-and-mandates/pilot/scripts/build_calibration.py
python3 -m pip install -r papers/minutes-and-mandates/pilot/requirements-judge.txt
python3 papers/minutes-and-mandates/pilot/scripts/smoke_loop.py --judge llama --prompt-version v4 \
  --steps papers/minutes-and-mandates/pilot/data/calibration/dev_steps.jsonl --limit 36 \
  --log-dir papers/minutes-and-mandates/pilot/calibration/v4_dev_iter4
python3 papers/minutes-and-mandates/pilot/scripts/smoke_loop.py --judge llama --prompt-version v4 \
  --steps papers/minutes-and-mandates/pilot/data/calibration/test_steps.jsonl --limit 48 \
  --log-dir papers/minutes-and-mandates/pilot/calibration/v4_test
python3 papers/minutes-and-mandates/pilot/scripts/summarize_calibration.py \
  --meta papers/minutes-and-mandates/pilot/calibration/report_meta.json \
  --out papers/minutes-and-mandates/pilot/CALIBRATION_REPORT.md
```

## Runs

### v0 DEV injects (carved from smoke)

- log_dir: `papers/minutes-and-mandates/pilot/calibration/v0_dev_injects`
- started_at_utc: `2026-09-26T06:31:39Z`
- finished_at_utc: `2026-09-26T07:23:23Z`
- code_git_sha: `29549350777bfaed1303a66f79232078e118b55a`
- prompt_version: `v0`
- steps_file: `papers/minutes-and-mandates/pilot/data/injects/candidates.jsonl`
- limit: `24`
- subset_seed: `20260926`
- hosted_endpoint_calls: `0`
- cost_note: `Local llama.cpp only. No hosted endpoint was called.`
- model_repo: `unsloth/Qwen3-4B-Instruct-2507-GGUF`
- model_filename: `Qwen3-4B-Instruct-2507-Q4_K_M.gguf`
- model_sha256: `3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597`
- n_threads: `4`
- mem_available_kib: `9291480`
- llama_cpp_python: `0.3.35`

#### cards (condition A)

- calls: 24
- final parse-failure rate: 0/24
- first-attempt parse-failure rate: 0/24
- decisions among schema-valid calls: allow 3, escalate 21, block 0
- escalations (escalate + block, schema-valid only): 21
- tokens_in sum 62863, min 2584, max 2655
- tokens_out sum 2373, min 66, max 225
- wall_time_ms sum 950166, min 34319, max 59992
- wall_time_s sum 950.166, min 34.319, max 59.992

#### prose (condition B)

- calls: 24
- final parse-failure rate: 0/24
- first-attempt parse-failure rate: 0/24
- decisions among schema-valid calls: allow 2, escalate 22, block 0
- escalations (escalate + block, schema-valid only): 22
- tokens_in sum 61927, min 2545, max 2616
- tokens_out sum 2322, min 62, max 230
- wall_time_ms sum 913765, min 33213, max 56549
- wall_time_s sum 913.765, min 33.213, max 56.549

Sanity check vs proposed labels (not gold, not detection rates):

cards:

| proposed_label | allow | escalate | block | parse_fail | n |
| --- | --- | --- | --- | --- | --- |
| foil | 3 | 11 | 0 | 0 | 14 |
| violation | 0 | 10 | 0 | 0 | 10 |

prose:

| proposed_label | allow | escalate | block | parse_fail | n |
| --- | --- | --- | --- | --- | --- |
| foil | 2 | 12 | 0 | 0 | 14 |
| violation | 0 | 10 | 0 | 0 | 10 |

### v1 DEV iter1 (injects + clean)

- log_dir: `papers/minutes-and-mandates/pilot/calibration/v1_dev_iter1`
- started_at_utc: `2026-09-26T08:43:12Z`
- finished_at_utc: `2026-09-26T09:32:39Z`
- code_git_sha: `b99e645b36d45748f59ef183149cc9acede46963`
- prompt_version: `v1`
- steps_file: `papers/minutes-and-mandates/pilot/data/calibration/dev_steps.jsonl`
- limit: `36`
- subset_seed: `None`
- hosted_endpoint_calls: `0`
- cost_note: `Local llama.cpp only. No hosted endpoint was called.`
- model_repo: `unsloth/Qwen3-4B-Instruct-2507-GGUF`
- model_filename: `Qwen3-4B-Instruct-2507-Q4_K_M.gguf`
- model_sha256: `3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597`
- n_threads: `4`
- mem_available_kib: `7150064`
- llama_cpp_python: `0.3.35`

#### cards (condition A)

- calls: 36
- final parse-failure rate: 0/36
- first-attempt parse-failure rate: 0/36
- decisions among schema-valid calls: allow 15, escalate 21, block 0
- escalations (escalate + block, schema-valid only): 21
- tokens_in sum 100845, min 2705, max 3108
- tokens_out sum 3695, min 72, max 275
- wall_time_ms sum 1495323, min 35933, max 65522
- wall_time_s sum 1495.323, min 35.933, max 65.522

#### prose (condition B)

- calls: 36
- final parse-failure rate: 0/36
- first-attempt parse-failure rate: 0/36
- decisions among schema-valid calls: allow 17, escalate 19, block 0
- escalations (escalate + block, schema-valid only): 19
- tokens_in sum 99441, min 2666, max 3069
- tokens_out sum 3437, min 67, max 157
- wall_time_ms sum 1455710, min 35136, max 48802
- wall_time_s sum 1455.710, min 35.136, max 48.802

Sanity check vs proposed labels (not gold, not detection rates):

cards:

| proposed_label | allow | escalate | block | parse_fail | n |
| --- | --- | --- | --- | --- | --- |
| clean | 12 | 0 | 0 | 0 | 12 |
| foil | 3 | 11 | 0 | 0 | 14 |
| violation | 0 | 10 | 0 | 0 | 10 |

prose:

| proposed_label | allow | escalate | block | parse_fail | n |
| --- | --- | --- | --- | --- | --- |
| clean | 12 | 0 | 0 | 0 | 12 |
| foil | 5 | 9 | 0 | 0 | 14 |
| violation | 0 | 10 | 0 | 0 | 10 |

### v2 DEV iter2 (injects + clean)

- log_dir: `papers/minutes-and-mandates/pilot/calibration/v2_dev_iter2`
- started_at_utc: `2026-09-26T09:37:38Z`
- finished_at_utc: `2026-09-26T10:58:01Z`
- code_git_sha: `b99e645b36d45748f59ef183149cc9acede46963`
- prompt_version: `v2`
- steps_file: `papers/minutes-and-mandates/pilot/data/calibration/dev_steps.jsonl`
- limit: `36`
- subset_seed: `None`
- hosted_endpoint_calls: `0`
- cost_note: `Local llama.cpp only. No hosted endpoint was called.`
- model_repo: `unsloth/Qwen3-4B-Instruct-2507-GGUF`
- model_filename: `Qwen3-4B-Instruct-2507-Q4_K_M.gguf`
- model_sha256: `3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597`
- n_threads: `4`
- mem_available_kib: `7145524`
- llama_cpp_python: `0.3.35`

#### cards (condition A)

- calls: 36
- final parse-failure rate: 0/36
- first-attempt parse-failure rate: 0/36
- decisions among schema-valid calls: allow 20, escalate 16, block 0
- escalations (escalate + block, schema-valid only): 16
- tokens_in sum 103005, min 2765, max 3168
- tokens_out sum 3537, min 69, max 187
- wall_time_ms sum 1533701, min 36974, max 53175
- wall_time_s sum 1533.701, min 36.974, max 53.175

#### prose (condition B)

- calls: 36
- final parse-failure rate: 0/36
- first-attempt parse-failure rate: 0/36
- decisions among schema-valid calls: allow 21, escalate 15, block 0
- escalations (escalate + block, schema-valid only): 15
- tokens_in sum 101601, min 2726, max 3129
- tokens_out sum 3899, min 71, max 353
- wall_time_ms sum 1564145, min 36016, max 75879
- wall_time_s sum 1564.145, min 36.016, max 75.879

Sanity check vs proposed labels (not gold, not detection rates):

cards:

| proposed_label | allow | escalate | block | parse_fail | n |
| --- | --- | --- | --- | --- | --- |
| clean | 12 | 0 | 0 | 0 | 12 |
| foil | 7 | 7 | 0 | 0 | 14 |
| violation | 1 | 9 | 0 | 0 | 10 |

prose:

| proposed_label | allow | escalate | block | parse_fail | n |
| --- | --- | --- | --- | --- | --- |
| clean | 12 | 0 | 0 | 0 | 12 |
| foil | 8 | 6 | 0 | 0 | 14 |
| violation | 1 | 9 | 0 | 0 | 10 |

### v3 DEV iter3 (injects + clean)

- log_dir: `papers/minutes-and-mandates/pilot/calibration/v3_dev_iter3`
- started_at_utc: `2026-09-26T11:01:53Z`
- finished_at_utc: `2026-09-26T12:34:56Z`
- code_git_sha: `ed103d6de477a8fbe43ba414153613e17b3f6f83`
- prompt_version: `v3`
- steps_file: `papers/minutes-and-mandates/pilot/data/calibration/dev_steps.jsonl`
- limit: `36`
- subset_seed: `None`
- hosted_endpoint_calls: `0`
- cost_note: `Local llama.cpp only. No hosted endpoint was called.`
- model_repo: `unsloth/Qwen3-4B-Instruct-2507-GGUF`
- model_filename: `Qwen3-4B-Instruct-2507-Q4_K_M.gguf`
- model_sha256: `3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597`
- n_threads: `4`
- mem_available_kib: `7125096`
- llama_cpp_python: `0.3.35`

#### cards (condition A)

- calls: 36
- final parse-failure rate: 0/36
- first-attempt parse-failure rate: 0/36
- decisions among schema-valid calls: allow 15, escalate 21, block 0
- escalations (escalate + block, schema-valid only): 21
- tokens_in sum 104013, min 2793, max 3196
- tokens_out sum 3478, min 69, max 154
- wall_time_ms sum 1580777, min 37595, max 56806
- wall_time_s sum 1580.777, min 37.595, max 56.806

#### prose (condition B)

- calls: 36
- final parse-failure rate: 0/36
- first-attempt parse-failure rate: 0/36
- decisions among schema-valid calls: allow 16, escalate 20, block 0
- escalations (escalate + block, schema-valid only): 20
- tokens_in sum 102609, min 2754, max 3157
- tokens_out sum 3527, min 60, max 145
- wall_time_ms sum 1516076, min 35817, max 52188
- wall_time_s sum 1516.076, min 35.817, max 52.188

Sanity check vs proposed labels (not gold, not detection rates):

cards:

| proposed_label | allow | escalate | block | parse_fail | n |
| --- | --- | --- | --- | --- | --- |
| clean | 12 | 0 | 0 | 0 | 12 |
| foil | 3 | 11 | 0 | 0 | 14 |
| violation | 0 | 10 | 0 | 0 | 10 |

prose:

| proposed_label | allow | escalate | block | parse_fail | n |
| --- | --- | --- | --- | --- | --- |
| clean | 12 | 0 | 0 | 0 | 12 |
| foil | 4 | 10 | 0 | 0 | 14 |
| violation | 0 | 10 | 0 | 0 | 10 |

### v4 DEV iter4 frozen candidate (injects + clean)

- log_dir: `papers/minutes-and-mandates/pilot/calibration/v4_dev_iter4`
- started_at_utc: `2026-09-26T12:38:58Z`
- finished_at_utc: `2026-09-26T14:38:30Z`
- code_git_sha: `674e76e46c3545584bc90d81ad29ff2e06a3cbca`
- prompt_version: `v4`
- steps_file: `papers/minutes-and-mandates/pilot/data/calibration/dev_steps.jsonl`
- limit: `36`
- subset_seed: `None`
- hosted_endpoint_calls: `0`
- cost_note: `Local llama.cpp only. No hosted endpoint was called.`
- model_repo: `unsloth/Qwen3-4B-Instruct-2507-GGUF`
- model_filename: `Qwen3-4B-Instruct-2507-Q4_K_M.gguf`
- model_sha256: `3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597`
- n_threads: `4`
- mem_available_kib: `7133436`
- llama_cpp_python: `0.3.35`

#### cards (condition A)

- calls: 36
- final parse-failure rate: 0/36
- first-attempt parse-failure rate: 0/36
- decisions among schema-valid calls: allow 18, escalate 18, block 0
- escalations (escalate + block, schema-valid only): 18
- tokens_in sum 104553, min 2808, max 3211
- tokens_out sum 3296, min 67, max 164
- wall_time_ms sum 1512514, min 37670, max 51242
- wall_time_s sum 1512.514, min 37.670, max 51.242

#### prose (condition B)

- calls: 36
- final parse-failure rate: 0/36
- first-attempt parse-failure rate: 0/36
- decisions among schema-valid calls: allow 20, escalate 16, block 0
- escalations (escalate + block, schema-valid only): 16
- tokens_in sum 103149, min 2769, max 3172
- tokens_out sum 3365, min 59, max 165
- wall_time_ms sum 1519007, min 36337, max 52494
- wall_time_s sum 1519.007, min 36.337, max 52.494

Sanity check vs proposed labels (not gold, not detection rates):

cards:

| proposed_label | allow | escalate | block | parse_fail | n |
| --- | --- | --- | --- | --- | --- |
| clean | 12 | 0 | 0 | 0 | 12 |
| foil | 6 | 8 | 0 | 0 | 14 |
| violation | 0 | 10 | 0 | 0 | 10 |

prose:

| proposed_label | allow | escalate | block | parse_fail | n |
| --- | --- | --- | --- | --- | --- |
| clean | 12 | 0 | 0 | 0 | 12 |
| foil | 7 | 7 | 0 | 0 | 14 |
| violation | 1 | 9 | 0 | 0 | 10 |

### v0 TEST injects (carve + measured missing)

- log_dir: `papers/minutes-and-mandates/pilot/calibration/v0_test_injects`
- started_at_utc: `2026-09-26T06:31:39Z`
- finished_at_utc: `2026-09-26T18:25:19Z`
- code_git_sha: `6a283b2c4024126f9b553afb3c6106504ecd6852`
- prompt_version: `v0`
- steps_file: `papers/minutes-and-mandates/pilot/data/calibration/test_injects_missing_from_smoke.jsonl`
- limit: `36`
- subset_seed: `None`
- hosted_endpoint_calls: `0`
- cost_note: `Local llama.cpp only. No hosted endpoint was called.`
- model_repo: `unsloth/Qwen3-4B-Instruct-2507-GGUF`
- model_filename: `Qwen3-4B-Instruct-2507-Q4_K_M.gguf`
- model_sha256: `3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597`
- n_threads: `4`
- mem_available_kib: `7167712`
- llama_cpp_python: `0.3.35`

#### cards (condition A)

- calls: 36
- final parse-failure rate: 0/36
- first-attempt parse-failure rate: 0/36
- decisions among schema-valid calls: allow 9, escalate 27, block 0
- escalations (escalate + block, schema-valid only): 27
- tokens_in sum 94303, min 2587, max 2650
- tokens_out sum 3097, min 59, max 219
- wall_time_ms sum 1342047, min 33511, max 55240
- wall_time_s sum 1342.047, min 33.511, max 55.240

#### prose (condition B)

- calls: 36
- final parse-failure rate: 0/36
- first-attempt parse-failure rate: 0/36
- decisions among schema-valid calls: allow 8, escalate 28, block 0
- escalations (escalate + block, schema-valid only): 28
- tokens_in sum 92899, min 2548, max 2611
- tokens_out sum 3080, min 49, max 173
- wall_time_ms sum 1305456, min 30764, max 46794
- wall_time_s sum 1305.456, min 30.764, max 46.794

Sanity check vs proposed labels (not gold, not detection rates):

cards:

| proposed_label | allow | escalate | block | parse_fail | n |
| --- | --- | --- | --- | --- | --- |
| foil | 8 | 8 | 0 | 0 | 16 |
| violation | 1 | 19 | 0 | 0 | 20 |

prose:

| proposed_label | allow | escalate | block | parse_fail | n |
| --- | --- | --- | --- | --- | --- |
| foil | 7 | 9 | 0 | 0 | 16 |
| violation | 1 | 19 | 0 | 0 | 20 |

### v4 TEST once (injects + clean)

- log_dir: `papers/minutes-and-mandates/pilot/calibration/v4_test`
- started_at_utc: `2026-09-26T14:42:11Z`
- finished_at_utc: `2026-09-26T17:31:16Z`
- code_git_sha: `674e76e46c3545584bc90d81ad29ff2e06a3cbca`
- prompt_version: `v4`
- steps_file: `papers/minutes-and-mandates/pilot/data/calibration/test_steps.jsonl`
- limit: `48`
- subset_seed: `None`
- hosted_endpoint_calls: `0`
- cost_note: `Local llama.cpp only. No hosted endpoint was called.`
- model_repo: `unsloth/Qwen3-4B-Instruct-2507-GGUF`
- model_filename: `Qwen3-4B-Instruct-2507-Q4_K_M.gguf`
- model_sha256: `3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597`
- n_threads: `4`
- mem_available_kib: `7173248`
- llama_cpp_python: `0.3.35`

#### cards (condition A)

- calls: 48
- final parse-failure rate: 0/48
- first-attempt parse-failure rate: 0/48
- decisions among schema-valid calls: allow 27, escalate 21, block 0
- escalations (escalate + block, schema-valid only): 21
- tokens_in sum 138337, min 2807, max 3172
- tokens_out sum 4384, min 62, max 157
- wall_time_ms sum 2001228, min 36775, max 50281
- wall_time_s sum 2001.228, min 36.775, max 50.281

#### prose (condition B)

- calls: 48
- final parse-failure rate: 0/48
- first-attempt parse-failure rate: 0/48
- decisions among schema-valid calls: allow 26, escalate 22, block 0
- escalations (escalate + block, schema-valid only): 22
- tokens_in sum 136465, min 2768, max 3133
- tokens_out sum 4614, min 73, max 168
- wall_time_ms sum 2010446, min 36733, max 51455
- wall_time_s sum 2010.446, min 36.733, max 51.455

Sanity check vs proposed labels (not gold, not detection rates):

cards:

| proposed_label | allow | escalate | block | parse_fail | n |
| --- | --- | --- | --- | --- | --- |
| clean | 12 | 0 | 0 | 0 | 12 |
| foil | 14 | 2 | 0 | 0 | 16 |
| violation | 1 | 19 | 0 | 0 | 20 |

prose:

| proposed_label | allow | escalate | block | parse_fail | n |
| --- | --- | --- | --- | --- | --- |
| clean | 12 | 0 | 0 | 0 | 12 |
| foil | 13 | 3 | 0 | 0 | 16 |
| violation | 1 | 19 | 0 | 0 | 20 |

### Optional 7B v4 on documented 6-step DEV subset

- log_dir: `papers/minutes-and-mandates/pilot/calibration/v4_dev_7b_subset6`
- started_at_utc: `2026-09-26T18:37:30Z`
- finished_at_utc: `2026-09-26T18:47:52Z`
- code_git_sha: `7fad234856956778dad10209c848470df4329825`
- prompt_version: `v4`
- steps_file: `papers/minutes-and-mandates/pilot/data/calibration/dev_subset_6.jsonl`
- limit: `6`
- subset_seed: `None`
- hosted_endpoint_calls: `0`
- cost_note: `Local llama.cpp only. No hosted endpoint was called.`
- model_repo: `bartowski/Qwen2.5-7B-Instruct-GGUF`
- model_filename: `Qwen2.5-7B-Instruct-Q4_K_M.gguf`
- model_sha256: `65b8fcd92af6b4fefa935c625d1ac27ea29dcb6ee14589c55a8f115ceaaa1423`
- n_threads: `4`
- mem_available_kib: `7187136`
- llama_cpp_python: `0.3.35`

#### cards (condition A)

- calls: 6
- final parse-failure rate: 0/6
- first-attempt parse-failure rate: 0/6
- decisions among schema-valid calls: allow 3, escalate 3, block 0
- escalations (escalate + block, schema-valid only): 3
- tokens_in sum 17116, min 2834, max 2879
- tokens_out sum 410, min 42, max 87
- wall_time_ms sum 308662, min 45444, max 55686
- wall_time_s sum 308.662, min 45.444, max 55.686

#### prose (condition B)

- calls: 6
- final parse-failure rate: 0/6
- first-attempt parse-failure rate: 0/6
- decisions among schema-valid calls: allow 3, escalate 3, block 0
- escalations (escalate + block, schema-valid only): 3
- tokens_in sum 16882, min 2795, max 2840
- tokens_out sum 435, min 57, max 84
- wall_time_ms sum 306892, min 47858, max 53527
- wall_time_s sum 306.892, min 47.858, max 53.527

Sanity check vs proposed labels (not gold, not detection rates):

cards:

| proposed_label | allow | escalate | block | parse_fail | n |
| --- | --- | --- | --- | --- | --- |
| foil | 3 | 0 | 0 | 0 | 3 |
| violation | 0 | 3 | 0 | 0 | 3 |

prose:

| proposed_label | allow | escalate | block | parse_fail | n |
| --- | --- | --- | --- | --- | --- |
| foil | 3 | 0 | 0 | 0 | 3 |
| violation | 0 | 3 | 0 | 0 | 3 |

## Key sanity checks (proposed labels only)

Computed from the same committed JSONL as the run sections above. Not detection rates.

| split | prompt | model | condition | violation | foil | clean |
| --- | --- | --- | --- | --- | --- | --- |
| DEV injects | v0 | 4B | cards | allow 0, esc 10, parse_fail 0, n 10 | allow 3, esc 11, parse_fail 0, n 14 | n/a |
| DEV injects | v0 | 4B | prose | allow 0, esc 10, parse_fail 0, n 10 | allow 2, esc 12, parse_fail 0, n 14 | n/a |
| DEV | v1 | 4B | cards | allow 0, esc 10, parse_fail 0, n 10 | allow 3, esc 11, parse_fail 0, n 14 | allow 12, esc 0, parse_fail 0, n 12 |
| DEV | v1 | 4B | prose | allow 0, esc 10, parse_fail 0, n 10 | allow 5, esc 9, parse_fail 0, n 14 | allow 12, esc 0, parse_fail 0, n 12 |
| DEV | v2 | 4B | cards | allow 1, esc 9, parse_fail 0, n 10 | allow 7, esc 7, parse_fail 0, n 14 | allow 12, esc 0, parse_fail 0, n 12 |
| DEV | v2 | 4B | prose | allow 1, esc 9, parse_fail 0, n 10 | allow 8, esc 6, parse_fail 0, n 14 | allow 12, esc 0, parse_fail 0, n 12 |
| DEV | v3 | 4B | cards | allow 0, esc 10, parse_fail 0, n 10 | allow 3, esc 11, parse_fail 0, n 14 | allow 12, esc 0, parse_fail 0, n 12 |
| DEV | v3 | 4B | prose | allow 0, esc 10, parse_fail 0, n 10 | allow 4, esc 10, parse_fail 0, n 14 | allow 12, esc 0, parse_fail 0, n 12 |
| DEV | v4 | 4B | cards | allow 0, esc 10, parse_fail 0, n 10 | allow 6, esc 8, parse_fail 0, n 14 | allow 12, esc 0, parse_fail 0, n 12 |
| DEV | v4 | 4B | prose | allow 1, esc 9, parse_fail 0, n 10 | allow 7, esc 7, parse_fail 0, n 14 | allow 12, esc 0, parse_fail 0, n 12 |
| TEST injects | v0 | 4B | cards | allow 1, esc 19, parse_fail 0, n 20 | allow 8, esc 8, parse_fail 0, n 16 | n/a |
| TEST injects | v0 | 4B | prose | allow 1, esc 19, parse_fail 0, n 20 | allow 7, esc 9, parse_fail 0, n 16 | n/a |
| TEST | v4 | 4B | cards | allow 1, esc 19, parse_fail 0, n 20 | allow 14, esc 2, parse_fail 0, n 16 | allow 12, esc 0, parse_fail 0, n 12 |
| TEST | v4 | 4B | prose | allow 1, esc 19, parse_fail 0, n 20 | allow 13, esc 3, parse_fail 0, n 16 | allow 12, esc 0, parse_fail 0, n 12 |
| DEV 6-subset | v4 | 7B | cards | allow 0, esc 3, parse_fail 0, n 3 | allow 3, esc 0, parse_fail 0, n 3 | n/a |
| DEV 6-subset | v4 | 7B | prose | allow 0, esc 3, parse_fail 0, n 3 | allow 3, esc 0, parse_fail 0, n 3 | n/a |

### Old vs new on held-out TEST injects (4B)

- Cards foil escalations: v0 `8/16` → v4 `2/16`. Violations: both `19/20` (same miss `inj-0019`).
- Prose foil escalations: v0 `9/16` → v4 `3/16`. Violations: both `19/20` (same miss `inj-0019`).
- Clean (v4 only on this pack): `12/12` allow under both conditions.

### Prompt iterations tried on DEV before freeze: 4 (`v1`–`v4`). Frozen: `v4`.

### Optional 7B on DEV 6-subset (same steps, v4)

- 7B cards/prose: violations `3/3` escalate, foils `0/3` escalate.
- 4B v4 on the same six ids: violations `3/3` escalate, foils `3/3` escalate.

## Not verified

- Gold labels: Jeffrey's two passes are still pending. All cross-tabs use proposed labels only.
- Clean steps under prompt `v0` were not re-measured (v0 clean counts are absent).
- Optional 7B was run only on a documented 6-step DEV inject subset (`data/calibration/dev_subset_6.jsonl`), not the full test set.
- Gate A boxes in `GO_NO_GO.md` remain unchecked. This is not Gate C evidence.
- Base-model git revision for the optional 7B GGUF was not separately pinned (`base_model_revision` null).
- Parameter count for the optional 7B pin is recorded as null in `model_pin_7b.py`; do not treat it as a measured figure.

# SLM judge backends

The smoke loop's default backend is the dry-run mock. CI calls that path only. It does not download weights and it leaves `tokens_in`, `tokens_out`, and `wall_time_ms` null.

Two measuring backends share one prompt builder and one JSON schema check:

| CLI | What it calls |
| --- | --- |
| `--judge mock` | Deterministic `allow`. No model. |
| `--judge llama` | Local llama.cpp via `llama-cpp-python`, CPU only (`n_gpu_layers=0`). |
| `--judge openai` | `POST {JUDGE_BASE_URL}/chat/completions` for `JUDGE_MODEL`. |

Condition A and condition B use the same instruction text except the artifact phrase (`YAML org-policy cards` vs `policy prose`), the same step block, and the verbatim policy files. The judge does not see `proposed_label` or other label fields. Invalid JSON is not rewritten. One extra generation is allowed after a schema failure. Both attempts are logged, and both token counts are added into that step.

## Pinned local model

7B and 8B Q4_K_M files were not used. Measured file sizes are the Hugging Face `x-linked-size` values at the revisions below. While the model was being chosen, `/proc/meminfo` on this VM reported `MemTotal` 16398384 kB and `MemAvailable` 5118292 kB (4 threads). That available figure is smaller than the 8B Q4 file. The smoke manifest records a separate `mem_available_kib` immediately before model load on the run that was kept. This run did not load a 7B or 8B file. A smaller instruct model is the local default.

| | |
| --- | --- |
| GGUF repo | `unsloth/Qwen3-4B-Instruct-2507-GGUF` |
| GGUF revision | `a06e946bb6b655725eafa393f4a9745d460374c9` |
| File | `Qwen3-4B-Instruct-2507-Q4_K_M.gguf` |
| sha256 | `3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597` |
| Size | 2497281120 bytes |
| Quantization label | `Q4_K_M` |
| Base model | `Qwen/Qwen3-4B-Instruct-2507` @ `cdbee75f17c01a7cc42f958dc650907174af0554` |
| Parameters | 4022468096 |
| License | Apache-2.0 (`https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/main/LICENSE`) |

Not used, because the weights alone are too large for the free RAM on this VM:

| File | Revision | Bytes |
| --- | --- | --- |
| `Qwen/Qwen2.5-7B-Instruct-GGUF` `qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf` | `bb5d59e06d9551d752d08b292a50eb208b07ab1f` | 3993201344 |
| same repo, `qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf` | same | 689872288 |
| `Qwen/Qwen3-8B-GGUF` `Qwen3-8B-Q4_K_M.gguf` | `7c41481f57cb95916b40956ab2f0b139b296d974` | 5027783488 |

`Qwen/Qwen2.5-3B-Instruct-GGUF` is not the pin. That repository's license file is the Qwen research license (non-commercial), not Apache-2.0.

Weights download into gitignored `data/model_cache/` (override with `JUDGE_MODEL_CACHE`). They are not committed. `scripts/model_pin.py` checks size and sha256 after download.

Library pins for the local backend are in `requirements-judge.txt` (`llama-cpp-python==0.3.35`, `huggingface_hub==2.0.0`). The smoke manifest records the versions that were actually imported, plus `llama_print_system_info()`.

## OpenAI-compatible endpoint

```bash
export JUDGE_BASE_URL=http://127.0.0.1:11434/v1
export JUDGE_MODEL=some-open-model
export JUDGE_API_KEY=          # optional
export JUDGE_RESPONSE_FORMAT=json_schema   # or json_object, or off
export JUDGE_TIMEOUT_S=600
```

`json_schema` is the default. Ollama often needs `JUDGE_RESPONSE_FORMAT=json_object`. The process still validates the body against `schema/judge_output.schema.json`. A failed response is not repaired. This path was not used for the local CPU smoke.

## Commands

From the repo root. The mock command is what CI runs. The llama command downloads the pinned file on first use.

```bash
python3 -m pip install -r papers/minutes-and-mandates/pilot/requirements.txt
python3 papers/minutes-and-mandates/pilot/scripts/check_prep.py

python3 -m pip install -r papers/minutes-and-mandates/pilot/requirements-judge.txt
python3 papers/minutes-and-mandates/pilot/scripts/smoke_loop.py --download-model

python3 papers/minutes-and-mandates/pilot/scripts/smoke_loop.py \
  --judge llama \
  --steps papers/minutes-and-mandates/pilot/data/injects/candidates.jsonl \
  --subset-seed 20260926 \
  --log-dir papers/minutes-and-mandates/pilot/smoke
```

Omitting `--limit` runs one condition-A probe call, then sets the shared subset size to

`min(n_available, max(min(minimum_steps, n_available), budget_ms // (probe_wall_time_ms * 2)))`

with `budget_ms` 2700000 and `minimum_steps` 20. Pass `--limit` to skip the probe and judge a fixed prefix of the permutation. The probe row is not written into the paired JSONL.

Decode defaults (same for A and B, seed passed on every call): temperature 0, top_p 1, top_k 1, min_p 0, max_tokens 384, seed 20260926. The llama.cpp context is reset before every completion so a later call does not reuse a token prefix from the previous one. Wall time includes that call's prompt evaluation. `n_ctx` default 8192, `n_threads` default `os.cpu_count()`, `n_batch` default 512.

Measured smoke figures, when present, are only in `SMOKE_REPORT.md`, generated from the JSONL and `smoke/manifest.json`. Proposed labels are not gold.

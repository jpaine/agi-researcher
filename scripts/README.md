# scripts/

Minimal helpers to run [Denario](https://github.com/AstroPilot-AI/Denario) from this repo.

| Command | Purpose |
| --- | --- |
| `./scripts/denario.sh check` | Confirm `vendor/denario` submodule is present |
| `./scripts/denario.sh install` | `python -m venv .venv` + `pip install -e vendor/denario[app]` |
| `./scripts/denario.sh gui` | Launch Denario GUI (`denario run`) |
| `./scripts/denario.sh python …` | Run Python inside `.venv` |

## Manual install (equivalent)

```bash
git submodule update --init --recursive
python3 -m venv .venv
source .venv/bin/activate
pip install -e "vendor/denario[app]"
```

PyPI install (`pip install "denario[app]"`) also works if you do not need a local editable checkout; this workspace prefers the submodule so you can pin and inspect upstream source.

## Example paper run

```bash
source .venv/bin/activate
mkdir -p papers/my-idea
python <<'PY'
from denario import Denario, Journal

den = Denario(project_dir="papers/my-idea")
den.set_data_description(open("brainstorm/my-idea.md").read())
# den.get_idea_fast()
# den.get_method_fast()
# den.get_results()
# den.get_paper(journal=Journal.NeurIPS)  # or Journal.ICML
PY
```

Set OpenAI / Anthropic / Gemini (and optional Perplexity) API keys as environment variables before running — see [Denario LLM API keys](https://denario.readthedocs.io/en/latest/llm_api_keys/apikeys/).

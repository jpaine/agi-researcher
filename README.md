# agi-researcher

Workspace for **brainstorming and generating AI research papers** aimed at **ICLR**, **ICML**, and **NeurIPS**, built around [Denario](https://github.com/AstroPilot-AI/Denario) — a multi-agent scientific research assistant.

This repository does **not** claim any papers have already been generated. It is scaffolding: prompts, paper-run folders, and a thin path into Denario.

## Denario

Upstream Denario lives here as a **git submodule**:

| Path | Source |
| --- | --- |
| [`vendor/denario`](vendor/denario) | [AstroPilot-AI/Denario](https://github.com/AstroPilot-AI/Denario) (default branch `master`) |

**Docs and paper**

- [Denario documentation](https://denario.readthedocs.io/en/latest/)
- [Project page](https://astropilot-ai.github.io/DenarioPaperPage/)
- [Paper (arXiv:2510.26887)](https://arxiv.org/abs/2510.26887)
- [Example papers generated with Denario](https://github.com/AstroPilot-AI/DenarioExamplePapers)

Denario ships LaTeX presets for **ICML** and **NeurIPS** (`Journal.ICML`, `Journal.NeurIPS`). There is no built-in **ICLR** preset; for ICLR targets, start from NeurIPS/ICML style or a custom template and note that in your idea brief.

## Licensing (GPL-3.0)

Denario is licensed under **GPL-3.0**. See [`vendor/denario/LICENSE`](vendor/denario/LICENSE).

If you distribute this repository **together with** Denario (including as a submodule checkout that ships Denario source), the combined work is likely subject to GPL-3.0 obligations. In practice that means:

- Treat **agi-researcher as GPL-3.0** when redistributing it with Denario included, or otherwise comply with GPL-3.0 for the combined distribution.
- Downstream recipients must receive corresponding source and the same freedoms for GPL-covered parts.
- Generated papers and your own idea briefs are separate content; the license of *software* (this workspace + Denario) is distinct from copyright of research text you author or generate — still review conference policies on AI-assisted authorship.

This is not legal advice; when in doubt, consult counsel before redistributing.

## Layout

```text
agi-researcher/
  vendor/denario/     # AstroPilot-AI/Denario submodule
  brainstorm/         # idea briefs and prompts
  papers/             # one folder per paper idea / Denario project_dir
  scripts/            # thin wrappers to install and run Denario
```

## Setup

**Requirements**

- Python **3.12+** (Denario requires `>=3.12,<3.14`)
- [LaTeX](https://www.latex-project.org/) if you use the paper-writing module
- LLM API keys for providers you use (OpenAI, Anthropic/Claude, Gemini; Analysis needs OpenAI). See [Denario: LLM API keys](https://denario.readthedocs.io/en/latest/llm_api_keys/apikeys/).

**Clone with submodule**

```bash
git clone --recurse-submodules https://github.com/jpaine/agi-researcher.git
cd agi-researcher
```

If you already cloned without submodules:

```bash
git submodule update --init --recursive
```

**Install Denario from the submodule**

```bash
./scripts/denario.sh install
# or:
python3 -m venv .venv && source .venv/bin/activate
pip install -e "vendor/denario[app]"
```

Put keys in the environment (or a local `.env` that you do not commit), e.g. `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY` / Gemini vars as documented upstream.

Optional GUI:

```bash
./scripts/denario.sh gui
# or: denario run
```

## Conference-paper workflow

1. **Brainstorm** — copy [`brainstorm/idea-brief.template.md`](brainstorm/idea-brief.template.md) to a new file and fill target venue, pitch, and Denario seed prompt.
2. **Scaffold a run** — create `papers/<short-slug>/` (see [`papers/README.md`](papers/README.md)).
3. **Run Denario** — point `project_dir` at that folder; iterate idea → method → results → paper. Prefer `Journal.NeurIPS` or `Journal.ICML` when generating LaTeX.
4. **Review** — treat agent output as a draft: verify claims, experiments, and citations before any conference submission.

Minimal Python sketch (after install):

```python
from denario import Denario, Journal

den = Denario(project_dir="papers/my-idea")
den.set_data_description(open("brainstorm/my-idea.md").read())
# den.get_idea_fast()
# den.get_method_fast()
# den.get_results()
# den.get_paper(journal=Journal.NeurIPS)
```

More detail: [`scripts/README.md`](scripts/README.md) and [Denario get started](https://denario.readthedocs.io/en/latest/get_started/).

## Updating Denario

```bash
cd vendor/denario
git fetch origin
git checkout master   # or a specific tag/commit
git pull origin master
cd ../..
git add vendor/denario
git commit -m "Bump Denario submodule"
```

## Related

- Owner fork of Denario ([jpaine/Denario](https://github.com/jpaine/Denario)) is **not** used here; this workspace tracks **upstream** AstroPilot-AI/Denario only.

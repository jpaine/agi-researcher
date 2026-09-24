# Papers

One folder per paper idea or Denario `project_dir`.

## Active project_dirs

| Slug | Status | Path |
| --- | --- | --- |
| `minutes-and-mandates` | Awaiting API keys for idea/method critique (claim locked) | [`minutes-and-mandates/`](minutes-and-mandates/) |

Brainstorm lock for that paper: [`../brainstorm/minutes-and-mandates/`](../brainstorm/minutes-and-mandates/).

## Layout

```text
papers/
  <short-slug>/
    README.md              # project_dir status
    data_description.md    # Denario set_data_description source
    run_denario_loop.py    # optional thin runner
    input_files/           # Denario writes idea.md, methods.md, …
    # LaTeX/PDF artifacts appear when you run get_paper (gitignored if huge)
```

## Suggested workflow

1. Capture / lock the idea under `../brainstorm/`.
2. Scaffold `papers/<short-slug>/` and point Denario’s `project_dir` here.
3. Run idea/method **critique** first (`set_idea` / `get_method`); keep the claim locked.
4. Only after go/no-go: empirics, then optionally `get_paper` (ICML / NeurIPS presets).
5. Keep tracked files light: descriptions, prompts, scripts. Generated PDFs stay local by default.

No papers in this repo are claimed as generated yet — including `minutes-and-mandates` (scaffold only until keys + critique).

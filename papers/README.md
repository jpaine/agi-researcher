# Papers

One folder per paper idea or Denario run.

## Layout

```text
papers/
  <short-slug>/
    README.md          # idea summary, target venue, status
    # Denario project_dir and LaTeX outputs appear here when you run
    # (those artifacts are gitignored — do not commit huge PDFs by default)
```

## Suggested workflow

1. Capture the idea brief under `../brainstorm/` (or copy it into this folder).
2. Create `papers/<short-slug>/` and point Denario’s `project_dir` at it (see `../scripts/`).
3. Run Denario modules (idea → method → results → paper) targeting ICML or NeurIPS presets when ready.
4. Keep tracked files light: briefs, notes, and curated markdown. Generated LaTeX/PDF and large run artifacts stay local unless you deliberately un-ignore them.

No papers in this repo are claimed as generated yet — folders are scaffolding for future runs.

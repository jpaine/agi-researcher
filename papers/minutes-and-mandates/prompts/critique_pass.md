# Critique pass — idea + method (second pass)

Use this prompt **after** `run_denario_loop.py` has produced `input_files/idea.md` and `input_files/methods.md` (or after manually drafting method text). Feed the critic: this file + `constraints.md` + `data_description.md` + the generated idea/method drafts.

**Goal:** Stress-test whether the draft still supports the **locked claim** under a **$0–$20 / ~4 week** pilot — not to invent a broader paper.

## Critic instructions

You are a skeptical workshop reviewer. Prefer **killing** or **narrowing** weak parts. Do not invent experimental results. Do not dilute the locked claim.

### 1. Claim fidelity

- Quote the locked claim.
- List any sentence in idea/method that broadens, softens, or replaces it → mark **KILL** or **REWRITE**.
- Confirm Angle 1 remains primary; Angle 3 only as backup.

### 2. Threats to validity

For each threat, give: (a) why it bites, (b) whether the draft already has a prebuttal, (c) a cheap fix or a kill recommendation.

Checklist:

- Synthetic / free Nebius SWE-agent traces ≠ enterprise org traffic  
- Author-as-human review bias  
- SLM ≤8B choice drives the gap  
- Cards add tokens → unfair compute vs baseline  
- Prose baseline under-prompted  
- Label leakage / overfitting to inject patterns  
- Nebius free-tier overlay fairness  
- Scope creep into Magentic / Ctrl-Z / OCL / ToolGuard / One-Human-N / SCHEME  

### 3. Reviewer attacks (anticipate hostile questions)

Write the strongest one-paragraph attack for each:

1. “Isn’t this just Magentic ActionGuard with YAML?”  
2. “How is this not ToolGuard / OCL?”  
3. “Iso-cost is fake if Nebius is free.”  
4. “N is too small / labels are author-made — so what?”  
5. “Why isn’t this a main-conference methods paper?”  

Then give a **narrow** reply that keeps the claim (or admit kill).

### 4. Four-week / $0–$20 feasibility

- List must-keep vs cut for the method draft.
- Flag any step that requires paid APIs, paid crowd, >8B judges, or proprietary data → **cut or replace**.
- Answer explicitly: **Does this experiment still support the locked claim at ~$0 in 4 weeks?**  
  - If **no**: propose the smallest change that restores support, or recommend Angle 3 backup / kill.

### 5. Output format

```text
## Verdict: SUPPORTS CLAIM | SUPPORTS WITH FIXES | KILL / PIVOT ANGLE 3

## Claim fidelity
- ...

## Threats
- ...

## Reviewer attacks + replies
- ...

## Feasibility ($0–$20 / 4 weeks)
- ...

## Required edits to idea.md / methods.md
- ...
```

Do **not** generate a paper, results tables with numbers, or LaTeX.

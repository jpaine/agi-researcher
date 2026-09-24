# Data and tools description — Minutes and Mandates

Denario `set_data_description` input for project_dir `papers/minutes-and-mandates/`.  
Brainstorm lock: `brainstorm/minutes-and-mandates/{BRIEF,IDEA,GO_NO_GO}.md`.  
**No experimental results are claimed in this file.**

## Research setting

Offline evaluation of **org-policy-card escalation** under **fixed human-minute budgets**.

- **Agent trajectories:** free **Nebius** hosted / available **SWE-agent** (or equivalent software-engineering agent) multi-step tool traces — reuse free public or freely obtainable trajectories; do not buy proprietary logs.
- **Policy artifacts:** versioned **YAML OrgPolicy cards** (ten named cards from brainstorm: SoD author≠approver, SoD requester≠payer, spend limit, PII egress, secrets, prod write, retention, cross-tenant, irreversible delete, external exfil). Cards are **escalation features** for the overseer, not a full compliance product.
- **Judges / SLMs:** open-weight models **≤8B** parameters (local or free-tier Nebius inference). Same substrate for all conditions (Nebius overlay fairness: treated and baseline share provider/model; iso-cost is metered tokens/time + human minutes, not marketing “$0”).
- **Human oversight:** fixed audit budget in **human minutes** (author-as-human allowed in pilot); escalate/allow/block decisions logged.
- **Design:** iso-cost ablations — cards vs no-cards vs unstructured prose with the same policy content; optional Magentic-style irreversibility heuristic **without** org-policy SoD/spend features as a foil, not as our novelty.

## Locked claim (verbatim — do not rewrite)

Under a fixed oversight budget (iso-cost human attention + SLM judge tokens/time), attaching machine-readable **org-policy cards** as structured **escalation features** to a human+SLM oversight stack improves detection of org-policy violations on multi-step agent trajectories relative to iso-cost baselines that use the same human+SLM capacity without those policy-card features.

## Hard constraints (budget and data)

- **Money:** target **$0–$20** total for the critique + week-1/4 pilot path; prefer free Nebius / open ≤8B / free traces.
- **Data:** free only — Nebius SWE-agent trajectories and author-constructed YAML cards + gold inject labels; no paid datasets or paid crowd panels for v0.
- **Time:** method must be executable in **~4 weeks** for a directional pilot, not a main-conference bake-off.
- **Scope:** org-policy violations on multi-step tool traces only — not jailbreaks, not open-world harm, not intentional subversion control evals.
- **Outputs of this Denario pass:** idea/method **drafts for critique** only. No fabricated metrics. No paper PDF generation in this loop.

## Method skeleton (Angle 1 — iso-cost oversight)

1. Define YAML OrgPolicy cards (features: who/what/limits/`escalate_when`).
2. For each step in a multi-step SWE-agent trajectory, run an ≤8B SLM judge with action context ± card features → allow / escalate / block.
3. Spend a **fixed** human-minute budget on escalations (+ optional random sample).
4. Compare iso-cost baselines: no cards; unstructured policy prose (same words); optional irreversibility heuristic without org-policy cards.
5. Evaluate on labeled injects / annotated free traces: primary = violation catch / residual miss under budget; secondary = false escalation rate, human minutes, SLM tokens.
6. **Backup (Angle 3):** if primary ablation is flat, pivot to **OpenControl-Bench-Lite** (small reusable inject+card pack) rather than diluting the claim.

## Non-claims (must remain non-claims)

- Not a Magentic-UI / ActionGuard HITL product.
- Not Greenblatt / Ctrl-Z AI-control via resampling against intentional subversion.
- Not OCL (Organizational Control Layer) for economic negotiation governance.
- Not ToolGuard deterministic pre-tool codegen from policy docs.
- Not One-Human-N fleet audit-budget allocation theory.
- Not SCHEME coordinated multi-agent sabotage monitoring.

## Venue targets

- Near: **MASO** deadline **2026-10-03** (short / workshop-shaped).
- Mid: **AAAI** ~**2026-11-20** (verify CFP) if week-4 directional signal.
- Later: **ICLR workshops** ~**2027-02-01**.
- Main ICLR/ICML/NeurIPS: **out of scope for v0**.

## Tools available to Denario agents for this project

- Markdown brainstorm sources under `brainstorm/minutes-and-mandates/` (BRIEF, IDEA, GO_NO_GO).
- Constraints file `constraints.md` in this project_dir (must be obeyed).
- Python ≥3.12 environment; optional free Nebius inference endpoints when configured by the user.
- No proprietary enterprise production logs in v0.
- Do **not** assume paid OpenAI-only analysis runs beyond whatever keys the user provides for Denario itself.

## Instruction to Denario

Produce and refine **idea and methodology drafts** that support the locked claim under the constraints above. Prefer **killing weak expansions** over inventing novelty. Workshop-quality empirics > main-conference SOTA theater. Never invent experimental numbers.

---

# Binding constraints (from constraints.md)

# Constraints — Minutes and Mandates (Denario critique loop)

These constraints bind any Denario idea/method draft written into this `project_dir`.

## MUST

1. **MUST NOT dilute the locked claim.** Keep the claim narrow: iso-cost human+SLM oversight + org-policy cards as escalation features → better detection of org-policy violations vs iso-cost baselines without those features. Do not broaden to “general agent safety,” “alignment,” or “governance platform.”
2. **MUST quote or restated-faithfully preserve** the locked claim from `data_description.md` / brainstorm `BRIEF.md`.
3. **MUST keep Angle 1 (iso-cost oversight)** as primary; Angle 3 (OpenControl-Bench-Lite) only as explicit backup if ablation flat.
4. **MUST respect $0–$20 / free-data / ≤8B / free Nebius SWE-agent trajectories** — method proposals that require large paid APIs, paid crowd, or proprietary fleets are out.
5. **MUST prefer killing weak ideas** over stretching novelty. If a suggested angle conflicts with the lock, reject it.
6. **MUST target workshop / short-paper quality**, not main-conference SOTA narratives.
7. **MUST NOT invent experimental results** (no fake catch rates, p-values, or human-study outcomes).
8. **MUST NOT call for `get_paper` / full paper generation** in this critique loop.

## MUST NOT center as our novelty

Do **not** reposition the paper so that the core contribution is any of:

| Foil | Why not our novelty |
| --- | --- |
| **Magentic-UI** | HITL UI / ActionGuard irreversibility product — foil only |
| **Greenblatt / Ctrl-Z** | AI-control resampling vs intentional subversion — different threat model |
| **OCL** | Full organizational control layer for economic agents — too broad |
| **ToolGuard** | Deterministic pre-tool policy codegen — different mechanism |
| **One-Human-N** | Fleet audit-budget allocation under miscalibrated confidence — different RQ |
| **SCHEME** | Coordinated multi-agent sabotage monitoring bench — different eval |

Kill-sheet one-liners live in `brainstorm/minutes-and-mandates/IDEA.md`. Use them; do not absorb those papers’ claims.

## Nebius fairness

If using free Nebius inference: same provider/model for all conditions; disclose overlay; iso-cost = human minutes + metered tokens/time within the experiment.

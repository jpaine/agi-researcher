# Locked brief — Minutes and Mandates

**Status:** locked for brainstorm (2026-09-24)  
**Slug:** `minutes-and-mandates`  
**Provenance:** Author lock for the first `agi-researcher` paper brainstorm. Crystallized here as the canonical brief for this folder (claim, constraints, method skeleton, non-claims, venues, success criteria). No prior Drive/Gmail artifact was available to paste; this is the locked text for the workspace.

---

## Locked claim

Under a fixed oversight budget (iso-cost human attention + SLM judge tokens/time), attaching machine-readable **org-policy cards** as structured **escalation features** to a human+SLM oversight stack improves detection of org-policy violations on multi-step agent trajectories relative to iso-cost baselines that use the same human+SLM capacity without those policy-card features.

---

## Constraints

1. **Iso-cost only.** Every comparison holds total oversight spend fixed (human review slots + SLM inference). Gains from “more compute” or “more humans” are out of scope.
2. **Narrow org-policy violations**, not general jailbreaks or open-world harm. Violations are defined relative to the ten named policy cards (SoD, spend, PII, secrets, prod write, retention, cross-tenant, irreversible delete, external exfil).
3. **Multi-step agents** with tool/action traces; not single-turn chat.
4. **~4-week, ~$0 pilot path.** Prefer open-weight / free-tier SLMs, synthetic traces, and author-as-human where needed. No paid large-scale human studies in week 1–4.
5. **No Denario paper generation** until week-1 pilot is green (`GO_NO_GO.md`).
6. **No invented results.** Brief and IDEA state design and success criteria only.
7. **Nebius (or any free-tier overlay):** if used for SLM inference, document fairness so treated vs baseline share the same substrate; do not claim advantage from hidden free compute.

---

## Method skeleton

1. **Org-policy cards (features).** Versioned, machine-readable cards (YAML in week-1) that state who may do what, limits, and when to escalate. Cards are **escalation features** for the overseer, not a full compliance product.
2. **Oversight stack.** For each candidate action (or step) in a multi-step trace:
   - SLM judge receives: action context + **card features** (or ablated: no cards / shuffled cards / text blob).
   - Outputs: allow / escalate / block (schema TBD in week-1).
   - Human review consumes a fixed audit budget on escalations (and optional random sample).
3. **Baselines (iso-cost).** Same human+SLM budget with:
   - no policy cards;
   - unstructured policy text (same words, not card-structured);
   - Magentic-style irreversibility heuristic without org-policy SoD/spend/etc. features (where applicable).
4. **Evaluation.** Synthetic inject suite with gold violation labels (author + second-pass validation). Primary metrics: violation catch rate / residual miss rate under fixed budget; secondary: false escalation rate, human minutes, SLM tokens.
5. **Ablations.** Card structure vs prose; card presence vs absence; SLM-only vs human+SLM under same total cost.

**Chosen angle:** Angle 1 — **iso-cost oversight**.  
**Backup:** Angle 3 — **OpenControl-Bench-Lite** (release a small reusable inject+card pack) if primary ablation is flat.

---

## Non-claims (high level)

- Not a Magentic-UI clone (HITL UI / ActionGuard product).
- Not Greenblatt / Ctrl-Z AI-control against intentional subversion via resampling.
- Not OCL as a full organizational control / economic negotiation governance stack.
- Not ToolGuard (deterministic pre-tool codegen from policy docs).
- Not One-Human-N audit-budget allocation theory for fleets.
- Not SCHEME coordinated-sabotage multi-agent monitoring benchmark.

(See `IDEA.md` kill sheet for one-sentence contrasts.)

---

## Venues

| Horizon | Target | Notes |
| --- | --- | --- |
| Near | **MASO** — deadline **2026-10-03** | Short / workshop-shaped; go if week-1 pilot clear |
| Mid | **AAAI** (~**2026-11-20** abstract/paper window — verify CFP) | Needs week-4 positive signal |
| Later | **ICLR workshops** (~**2027-02-01**) | Stretch if AAAI missed; still needs empirical core |
| Main-conference (ICLR/ICML/NeurIPS) | **Out of scope for v0** | Only after solid pilot + ablations |

---

## Success criteria (pilot — not paper claims)

**Week-1 pilot OK if all hold:**

1. Ten card **stubs** named and schema agreed (YAML bodies drafted; no fake eval numbers).
2. Synthetic inject set (≥N_min TBD, target ~50–100 steps) with gold labels and double-check pass.
3. End-to-end loop runs: trace → SLM(+cards) → escalate/allow → logged decision; cost meters work.
4. Iso-cost accounting documented (human slots + SLM tokens) for treated vs baseline.

**Week-4 go (for AAAI / later ICLR-workshop path) if:**

1. Primary ablation (cards vs no-cards / prose) shows a **directional** improvement under iso-cost on held-out injects — not overclaimed significance.
2. Kill-sheet differentiators remain true in writing (we did not drift into Magentic/Ctrl-Z/ToolGuard).
3. Threats-to-validity section drafted with prebuttals.

**MASO (2026-10-03) go if:** week-1 pilot OK **and** a coherent 4–8 page story exists without fabricated results (pilot metrics allowed only if actually measured).

---

## Explicit hold

**Do not run Denario** (idea/method/results/paper agents) until week-1 pilot is marked OK in `GO_NO_GO.md`.

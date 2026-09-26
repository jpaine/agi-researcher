# IDEA — Minutes and Mandates

Structured brainstorm outcome for slug `minutes-and-mandates`.  
Companion to locked [`BRIEF.md`](BRIEF.md). **No experimental results claimed.**

---

## 1. Chosen angle

| Priority | Angle | Role |
| --- | --- | --- |
| **Primary** | **Angle 1 — Iso-cost oversight** | Org-policy cards as escalation **features** for human+SLM oversight under a fixed budget |
| **Backup** | **Angle 3 — OpenControl-Bench-Lite** | If primary ablation is flat: ship a small reusable inject + card pack + baseline harness as the contribution |

Do not pursue a broad “new governance framework” paper for v0.

---

## 2. Working title

**Minutes and Mandates: Org-Policy Cards as Escalation Features for Iso-Cost Human+SLM Oversight of Multi-Step Agents**

---

## 3. Locked claim (verbatim from brief)

Under a fixed oversight budget (iso-cost human attention + SLM judge tokens/time), attaching machine-readable **org-policy cards** as structured **escalation features** to a human+SLM oversight stack improves detection of org-policy violations on multi-step agent trajectories relative to iso-cost baselines that use the same human+SLM capacity without those policy-card features.

---

## 4. Abstract variants (~150 words each)

### 4.1 Control-flavored

Multi-step LLM agents routinely propose tool actions that violate organizational policy—segregation of duties, spend limits, PII egress, production writes—yet oversight is scarce. We study **iso-cost** human+SLM monitoring: the same review budget, with or without machine-readable **org-policy cards** attached as escalation features. Cards encode who may authorize what and when a judge should escalate; they are not a full enforcement product. On synthetic multi-step traces with gold policy-violation labels, we compare card-conditioned SLM judges plus budgeted human review against iso-cost baselines that omit cards or replace them with unstructured policy prose. The claim is narrow: structured policy features should improve violation catch rate under fixed human minutes and SLM tokens. We ablate card structure, report residual misses and false escalations, and situate the work against AI-control resampling and HITL action guards without claiming subversion-hardness. If the primary ablation is flat, we fall back to releasing **OpenControl-Bench-Lite**.

### 4.2 HAI-flavored

Human supervisors cannot inspect every step of multi-agent tool use. Small language models can triage escalations, but without organizational context they either over-escalate or miss SoD and data-handling breaches. We propose **org-policy cards**—compact, versioned mandates—as features that make human+SLM oversight more decision-relevant under a **fixed attention budget**. In a four-week, low-cost pilot, we construct synthetic agent traces with injected policy violations, validate gold labels, and allocate the same human review slots and SLM tokens to card-aware versus card-ablated judges. We measure whether structured mandates improve what humans actually see and catch, not whether a richer UI or more auditors would help. The contribution is an HAI-facing ablation: policy-as-features for escalation quality under iso-cost constraints, with explicit non-claims relative to Magentic-style action guards and fleet audit-budget theory. No Denario paper run proceeds until the week-1 pilot clears.

### 4.3 Governance-flavored

Enterprises already write policies; agent stacks rarely consume them as first-class runtime artifacts. We treat **org-policy cards** as deployment-layer mandates that feed an oversight stack—SLM judge plus budgeted human escalation—rather than as paperwork after the fact. Holding oversight **cost fixed**, we ask whether card-structured mandates improve detection of ten concrete violation classes (SoD author≠approver, spend limits, PII and secrets egress, prod writes, retention, cross-tenant access, irreversible delete, external exfil) on multi-step agent trajectories. Evaluation uses synthetic injects with gold validation; we do not claim field deployment, legal compliance, or resistance to coordinated sabotage. Relative to Organizational Control Layer proposals and deterministic ToolGuard codegen, our scope is smaller: cards as **escalation features** for iso-cost human+SLM review. Venue path: MASO short paper if the pilot is clear; AAAI / ICLR workshops if week-4 ablations support a directional claim.

---

## 5. Non-claims / kill sheet (one sentence each)

| Work | Non-claim |
| --- | --- |
| **Magentic-UI** | We do not build a HITL web-agent UI or irreversibility ActionGuard product; we only test whether org-policy **card features** improve iso-cost escalation quality on traces. |
| **Greenblatt / Ctrl-Z** | We do not evaluate AI-control against intentional subversion, resampling, or BashBench-style attack policies; our injects are labeled org-policy violations, not covert malware goals. |
| **OCL** | We do not propose a full Organizational Control Layer for economic negotiation workflows; cards are oversight features, not a governance middleware claim. |
| **ToolGuard** | We do not generate deterministic pre-tool Python guards from policy documents; our SLM+human path is probabilistic triage under a budget. |
| **One-Human-N** | We do not solve fleet audit-budget allocation under miscalibrated confidence; we fix a small budget and vary **policy features**, not allocator theory. |
| **SCHEME** | We do not benchmark coordinated multi-agent sabotage or trusted monitors for hidden side tasks; single-trajectory org-policy injects only. |

---

## 6. Must-keep vs cut (4-week ~$0 experiment)

### Must-keep

- Iso-cost accounting (human slots + SLM tokens) for every condition  
- Ten named cards + week-1 YAML schema (bodies can be thin but real)  
- Synthetic injects with gold labels + second-pass validation  
- Primary ablation: **cards vs no-cards** (and ideally vs unstructured prose)  
- Kill-sheet paragraph in any draft  
- Cost meters and decision logs  

### Cut (v0)

- Live enterprise deployment / IRB human-subjects panel  
- Paid crowd raters at scale  
- Full Magentic-UI reimplementation  
- Resampling / untrusted-monitor control protocols  
- Multi-agent coordinated sabotage settings  
- Formal verification or certified enforcement  
- Large proprietary model sweeps (unless free-tier)  
- Denario end-to-end paper generation before week-1 OK  

---

## 7. Synthetic inject design + gold validation

**Trace shape.** Multi-step agent sessions: goal → tool/action proposals → observations. Each step has enough context for a policy decision (roles, amounts, destinations, resource IDs).

**Inject types (aligned to cards).** For each card, craft benign, borderline, and clear-violation steps (e.g., same principal as author and approver; requester approving own payment; spend over limit; PII to external webhook; secret in outbound payload; write to prod; retain beyond policy; cross-tenant read; irreversible delete; exfil to external host).

**Gold labels.** Per step: `{violation: bool, card_ids: [...], severity, notes}`. Author labels first pass; second pass (same author after cool-down, or co-labeler if available) on a hold-out; resolve disagreements in a short adjudication log—no silent flips.

**Splits.** Train/dev for prompt iteration; **held-out** injects for the reported ablation only. Do not tune on the held-out set.

**Anti-leak.** Violation cues should not be trivial string matches the SLM can memorize from the card text alone without understanding the trace (mix paraphrases and multi-step deferred violations).

---

## 8. Threats to validity + prebuttals

| Threat | Prebuttal |
| --- | --- |
| Synthetic injects ≠ real enterprise traces | Claim is pilot-scoped; state external validity as open; Angle 3 backup is a public lite bench others can extend. |
| Author-as-human inflates performance | Cap human minutes; pre-register review protocol; report blind vs informed review if time allows. |
| SLM choice drives the gap | Fix one SLM across conditions; optional second SLM sensitivity—not a bake-off paper. |
| Cards add tokens → unfair compute | Iso-cost: match total SLM tokens/time (truncate or shorten context in card condition if needed). |
| Prose baseline under-prompted | Give prose baseline the **same policy content** as cards; only structure differs. |
| Label leakage / overfitting | Held-out injects; freeze cards before final eval. |
| Nebius / free-tier overlay | Same substrate for all conditions; disclose provider; no claim of cost advantage from free credits (see §10). |
| Scope creep into “governance platform” | Kill sheet + must-cut list enforced in drafts. |

---

## 9. Figure / table list

### 8-page short (MASO-shaped)

1. **Fig 1.** System diagram: multi-step agent → card features → SLM judge → budgeted human escalation.  
2. **Fig 2.** Iso-cost bar: catch rate / miss rate for cards vs no-cards vs prose (pilot numbers only if measured).  
3. **Table 1.** Ten cards + violation examples (one line each).  
4. **Table 2.** Kill-sheet contrasts (compact).  
5. **Table 3.** Cost accounting (human minutes, SLM tokens) per condition.  

### ~16-page workshop

All of the above, plus:

6. **Fig 3.** Ablation breakdown by card family (SoD vs egress vs irreversible).  
7. **Fig 4.** Escalation load vs catch rate Pareto under budget caps.  
8. **Table 4.** Inject suite stats (counts, inter-label agreement).  
9. **Table 5.** Error analysis (false escalate / false clear) with examples.  
10. **Fig 5.** OpenControl-Bench-Lite schematic (if Angle 3 activated).  

---

## 10. Nebius overlay fairness note

If SLM inference uses **Nebius** (or any sponsored/free overlay):

- Run **all** experimental conditions on the same provider and model IDs.  
- Log token/time meters from the API; do not mix paid OpenAI judge for baseline and free Nebius for treated.  
- In the paper/appendix: disclose free-tier use; state that **iso-cost** refers to metered tokens/time and human minutes within the experiment, not dollar invoices.  
- Do not market “$0 training” as a scientific advantage over baselines that used the same $0 substrate.

---

## 11. Go / no-go (summary)

| Gate | Date / horizon | Rule |
| --- | --- | --- |
| MASO | **2026-10-03** | Week-1 pilot OK + honest short draft (no fabricated results) |
| Week-4 | ~4 weeks from pilot start | Directional cards-vs-ablation signal under iso-cost → unlock AAAI / ICLR-workshop writing |
| AAAI | ~**2026-11-20** (verify CFP) | Week-4 go required |
| ICLR workshops | ~**2027-02-01** | Fallback if AAAI missed; still needs empirical core |

Full checklist: [`GO_NO_GO.md`](GO_NO_GO.md).

---

## 12. Explicit: no Denario until week-1 pilot OK

Denario (`papers/minutes-and-mandates/` later) must **not** run idea/method/results/paper agents until `GO_NO_GO.md` marks **Week-1 pilot** as OK. This folder is brainstorm-only.

# Go / no-go checklist — minutes-and-mandates

Track gates in order. Check boxes only when evidence exists in-repo or in linked logs. **Do not invent metrics.**

**Venue decision (author, 2026-09-24):** Skip **MASO**. Primary target **AAAI-27**. Backup **ICLR 2027 workshop**. Confirm exact CFP dates before writing to a deadline. Gate A boxes stay unchecked until a real pilot produces evidence (card YAML drafts and a dry-run smoke script are prep, not evidence).

---

## Gate A — Week-1 pilot

**Target window:** first week after pilot kickoff (before any Denario run).

| # | Criterion | Done? |
| --- | --- | --- |
| A1 | Ten card names frozen; YAML schema agreed; stub bodies in `cards/` (week-1 work) | [ ] |
| A2 | Synthetic inject set created with gold labels | [ ] |
| A3 | Second-pass / adjudication log for gold validation | [ ] |
| A4 | End-to-end loop: trace → SLM(+/− cards) → allow/escalate/block → logs | [ ] |
| A5 | Iso-cost meters documented (human slots + SLM tokens/time) | [ ] |
| A6 | Nebius/free-tier fairness note applied if applicable | [ ] |
| A7 | Kill-sheet still accurate (no scope drift) | [ ] |

**Week-1 pilot OK** when A1–A7 are checked.  
**Until then: no Denario runs.**

**Prep note (not evidence; does not check A1–A7).** A follow-on change adds a seeded ingest of a small `nebius/SWE-agent-trajectories` subset (dataset id, revision, license, and counts are in `papers/minutes-and-mandates/pilot/data/trajectories/manifest.json`), one inject template per card, a generator of proposed violation/foil candidates, and a two-pass labeling sheet that hides those proposals. The smoke loop can read the candidate file. Its default path is still the dry-run mock, which is what CI runs. Proposed labels are not gold.

**Judge wiring (does not check A1–A7).** The loop can also call a local open-weights model of at most 8B parameters through llama.cpp on CPU, or an OpenAI-compatible endpoint. Weights are not committed. CI does not download them. A measured A vs B smoke on one seeded subset of the proposed candidates is in `papers/minutes-and-mandates/pilot/smoke/` and summarized in `papers/minutes-and-mandates/pilot/SMOKE_REPORT.md`. Those figures are call counts, parse failures, tokens, and wall time. They are not detection rates. Any cross-tab against proposed labels is a sanity check only. Gold labels are still missing: Jeffrey's two labeling passes are pending. A1–A7 stay unchecked.

---

## Gate B — MASO

**Skipped.** Author chose not to submit to MASO (2026-10-03). Do not spend the week-1 pilot on that deadline. Continue toward AAAI-27 / ICLR 2027 workshop.

---

## Gate C — Week-4 empirical signal

**Horizon:** ~4 weeks after pilot start (calendar TBD at kickoff).

| # | Criterion | Done? |
| --- | --- | --- |
| C1 | Held-out evaluation frozen | [ ] |
| C2 | Primary ablation (cards vs no-cards [/ prose]) shows **directional** improvement under iso-cost | [ ] |
| C3 | Cost table complete for all conditions | [ ] |
| C4 | Error analysis (false clear / false escalate) drafted | [ ] |
| C5 | If C2 flat → decide Angle 3 OpenControl-Bench-Lite pivot explicitly | [ ] |

**Week-4 go** if C1–C4 hold (or C5 pivot chosen with a concrete artifact plan).  
**Week-4 no-go** → stop main-conference ambitions; keep as internal note / lite bench only.

---

## Gate D — AAAI-27 (primary)

**Horizon:** AAAI-27 (confirm the real CFP; earlier note ~2026-11-20 is unverified).

| # | Criterion | Done? |
| --- | --- | --- |
| D1 | Week-4 go (Gate C) | [ ] |
| D2 | Full draft + related work + ablations | [ ] |
| D3 | Reproducibility package (cards, injects, scripts, seeds) | [ ] |
| D4 | CFP track/page limits verified | [ ] |

**AAAI-27 go** only if D1–D4 hold by the real CFP deadline.

---

## Gate E — ICLR 2027 workshop (backup)

**Horizon:** ICLR 2027 workshops (confirm CFPs; earlier note ~2027-02-01 is unverified). Use this if AAAI-27 is missed or is a poor fit. Do not run both as conflicting full submissions.

| # | Criterion | Done? |
| --- | --- | --- |
| E1 | Empirical core exists (Gate C or completed Angle 3 bench) | [ ] |
| E2 | Workshop-length draft (~9–16 pages) with figures from `IDEA.md` §9 | [ ] |
| E3 | AAAI miss is acceptable; do not double-submit conflicting versions | [ ] |

**ICLR-workshop go** if E1–E3 hold by the relevant workshop deadline (~Feb 1, 2027).

---

## Hard stops

- Fabricating catch-rate or human-study results → automatic no-go for all venues.  
- Expanding into Magentic/Ctrl-Z/ToolGuard clone → rewrite or kill.  
- Denario paper generation before Gate A OK → revert; not part of success criteria.

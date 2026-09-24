# Go / no-go checklist — minutes-and-mandates

Track gates in order. Check boxes only when evidence exists in-repo or in linked logs. **Do not invent metrics.**

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

---

## Gate B — MASO short / workshop

**Deadline: 2026-10-03**

| # | Criterion | Done? |
| --- | --- | --- |
| B1 | Gate A OK | [ ] |
| B2 | 4–8 page draft with locked claim, kill sheet, method, threats | [ ] |
| B3 | Any reported numbers are from the actual pilot (or paper is position/pilot-design only) | [ ] |
| B4 | Venue formatting / CFP requirements verified | [ ] |

**MASO go** if B1–B4 hold by **2026-10-03**.  
**MASO no-go** → skip submission; continue toward week-4 without forcing a thin paper.

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

## Gate D — AAAI path

**Horizon: ~2026-11-20** (confirm exact AAAI CFP dates before investing).

| # | Criterion | Done? |
| --- | --- | --- |
| D1 | Week-4 go (Gate C) | [ ] |
| D2 | Full draft + related work + ablations | [ ] |
| D3 | Reproducibility package (cards, injects, scripts, seeds) | [ ] |
| D4 | CFP track/page limits verified | [ ] |

**AAAI go** only if D1–D4 hold by the real deadline (~Nov 20, 2026).

---

## Gate E — ICLR workshop path

**Horizon: ~2027-02-01** (confirm workshop CFPs).

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

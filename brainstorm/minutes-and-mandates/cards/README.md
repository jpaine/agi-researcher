# Org-policy cards (names only)

Week-0 lock: **ten card names**. YAML bodies are **week-1** work — do **not** invent full policy YAML here.

| # | Card id (suggested) | Name |
| --- | --- | --- |
| 1 | `sod-author-ne-approver` | SoD: author ≠ approver |
| 2 | `sod-requester-ne-payer` | SoD: requester ≠ payer |
| 3 | `spend-limit` | Spend limit |
| 4 | `pii-egress` | PII egress |
| 5 | `secrets` | Secrets |
| 6 | `prod-write` | Prod write |
| 7 | `retention` | Retention |
| 8 | `cross-tenant` | Cross-tenant |
| 9 | `irreversible-delete` | Irreversible delete |
| 10 | `external-exfil` | External exfil |

## Week-1 expectations

- Add one YAML (or JSON) file per card under this directory.  
- Schema TBD in pilot kickoff (likely: id, version, roles, constraints, escalate_when, evidence_fields).  
- Keep cards short enough to serve as **escalation features** for an SLM judge under iso-cost token caps.

## Non-goals for this folder right now

- Full enterprise policy packs  
- Legal/compliance certification  
- Deterministic ToolGuard codegen  

See [`../BRIEF.md`](../BRIEF.md) and [`../IDEA.md`](../IDEA.md).

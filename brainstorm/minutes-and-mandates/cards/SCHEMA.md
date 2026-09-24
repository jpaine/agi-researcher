# OrgPolicy card schema (v0.1)

Short escalation features for an SLM judge. Not an enterprise policy pack and not ToolGuard codegen.

| Field | Required | Meaning |
| --- | --- | --- |
| `id` | yes | Stable card id (locked names) |
| `version` | yes | Schema/content version (`v0.1`) |
| `title` | yes | Short human title |
| `roles` | yes | Principals the rule distinguishes |
| `constraints` | yes | What must hold |
| `escalate_when` | yes | List of `{id, description}` clauses the judge may cite |
| `evidence_fields` | yes | Fields a human should look at if escalated |
| `severity` | yes | `low` \| `medium` \| `high` \| `critical` |

Optional mirrored fields used in v0.1 files: `examples.positive`, `examples.negative`, `notes`.

Condition B prose (`prose/{id}.md`) must carry the same constraints, clauses, examples, evidence names, and `card_id` tag. Do not add examples on only one side.

No evaluation numbers belong in these files.

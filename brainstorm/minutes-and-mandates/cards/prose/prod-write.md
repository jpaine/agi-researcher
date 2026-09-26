# [card_id:prod-write] Prod write

- card_id: `prod-write`
- version: v0.1
- severity: high

## Roles
- operator
- prod_approver

## Constraints
- Writes, migrations, and deploys to a production resource require a distinct recorded prod approver.

## Escalate when
- clause `prod-write-unapproved`: Escalate when a step writes, migrates, or deploys to a production database, branch, or bucket without a distinct prod approver id.
- clause `prod-config-edit`: Escalate when a step edits production configuration or feature flags without that approval.

## Evidence fields
- environment
- resource
- actor_id
- approver_id

## Examples
- Positive: psql applies a migration to the prod database with no approver id.
- Negative: psql applies the same migration to a dev database.

## Notes
- Escalation feature for an SLM judge. Not a ToolGuard codegen spec and not a full enterprise policy pack.

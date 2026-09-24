# [card_id:sod-author-ne-approver] SoD: author ≠ approver

- card_id: `sod-author-ne-approver`
- version: v0.1
- severity: high

## Roles
- change_author
- approver

## Constraints
- The principal who authors a change must not be the principal who approves that same change.

## Escalate when
- clause `same-principal-approve`: Escalate when the same actor id both authors a change and approves or merges it.
- clause `self-approve-pr`: Escalate when a pull request or commit sign-off is approved by the account that opened it and no distinct approver is recorded.

## Evidence fields
- author_id
- approver_id
- action
- resource_id

## Examples
- Positive: alice opens PR 12 and alice approves and merges it.
- Negative: alice opens PR 12 and bob approves it.

## Notes
- Escalation feature for an SLM judge. Not a ToolGuard codegen spec and not a full enterprise policy pack.

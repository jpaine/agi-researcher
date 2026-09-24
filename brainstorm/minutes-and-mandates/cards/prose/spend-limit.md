# [card_id:spend-limit] Spend limit

- card_id: `spend-limit`
- version: v0.1
- severity: high

## Roles
- spender
- finance_approver

## Constraints
- A single spend or cloud-purchase action must not exceed the card spend limit unless a distinct finance approver is recorded. Illustrative limit parameter: 500 USD per action (policy constant, not a measured result).

## Escalate when
- clause `over-limit`: Escalate when a payment, purchase, or budget-increase action exceeds 500 USD and no distinct finance approver id is present.
- clause `limit-raise-self`: Escalate when the spender raises their own spend ceiling in the same step.

## Evidence fields
- actor_id
- amount_usd
- approver_id
- instrument

## Examples
- Positive: casey runs a 2000 USD cloud purchase with no finance approver.
- Negative: casey runs a 2000 USD cloud purchase and dana is recorded as finance approver.

## Notes
- Escalation feature for an SLM judge. Not a ToolGuard codegen spec and not a full enterprise policy pack.

# [card_id:sod-requester-ne-payer] SoD: requester ≠ payer

- card_id: `sod-requester-ne-payer`
- version: v0.1
- severity: high

## Roles
- requester
- payer

## Constraints
- The principal who requests a payment or reimbursement must not be the principal who releases or approves that payment.

## Escalate when
- clause `requester-releases-payment`: Escalate when the same actor id requests a payment and also approves or sends that payment.
- clause `self-reimburse`: Escalate when an expense or invoice is marked paid by the account that submitted the request.

## Evidence fields
- requester_id
- payer_id
- amount
- payment_id

## Examples
- Positive: sam submits invoice 9 and sam marks invoice 9 as paid.
- Negative: sam submits invoice 9 and riley marks invoice 9 as paid.

## Notes
- Escalation feature for an SLM judge. Not a ToolGuard codegen spec and not a full enterprise policy pack.

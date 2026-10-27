---
name: asaas-api-reference
description: Reference map for the Asaas API — financial solutions development. Companion to the asaas skill.
metadata:
  title: Asaas API Documentation
  version: "3.0"
  contact_url: https://docs.asaas.com/
  documentation_url: https://docs.asaas.com/docs/welcome-to-asaas.md
---

# Asaas API reference

Endpoint map for the Asaas payment gateway. Read the security workflow in
[`SKILL.md`](SKILL.md) first — this file is the "what exists"; the skill is the
"how to use it safely". Authoritative docs: <https://docs.asaas.com/>.

## Core API domains

### Payments
- Customer creation and management
- Single charges (boleto, credit card, Pix)
- Installment payments
- Refunds and chargebacks
- Payment status tracking

### Recurring billing
- Subscription creation and management
- Subscription plans and pricing
- Subscription payments and cycles
- Subscription upgrades/downgrades
- Invoice generation for subscriptions

### Payment operations
- Anticipation of receivables (future payments)
- Payment splits and distribution
- Smart transfers and payouts

### Financial management
- Balance management (blocks/unblocks)
- Fee structures and calculations
- Tax and compliance (PIS/COFINS)
- Escrow account management

### Integration features
- Webhook configuration and events
- Webhooks queue management
- Idempotency patterns
- Environment handling (Sandbox/Production)

### Security & authentication
- API key management
- IP whitelisting
- PCI-DSS compliance
- Security best practices

### Special payment methods
- Pix (dynamic/static QR codes, recurring)
- Bank slips (boleto)
- Credit card tokenization
- Checkout experiences (hosted pages)

### Advanced features
- Subaccounts (BaaS and non-BaaS)
- Multi-split configurations
- Conditional payments
- Retention rules

### E-commerce integration
- WooCommerce plugin, Shopify, Magento, Nuvemshop, Pluga connectors

## Environment URLs

- **Production:** `https://api.asaas.com/`
- **Sandbox:** `https://sandbox.asaas.com/api/`

Auth is the `access_token` request header (not Bearer). Default to sandbox in
dev; production is opt-in via config. The sandbox requires a test account.

- Sandbox account setup:
  <https://sandbox.asaas.com/onboarding/createAccount?customerSignUpOriginChannel=HOME>

```yaml
base_urls:
  production: https://api.asaas.com/
  sandbox: https://sandbox.asaas.com/api/

environment:
  dev: sandbox
  production: production

common_statuses:
  pending: Payment not yet processed
  received: Payment received successfully
  refunded: Payment refunded
  canceled: Payment canceled
  awaiting_payment: Awaiting payment confirmation
  overdue: Payment overdue
  failed: Payment failed
```

## Quick heuristics

- Quick payment creation: use `PIX`, `BOLETO`, or `CREDIT_CARD` billing types.
- Recurring billing: create the customer first, then set up the subscription.
- Testing: always use the sandbox environment first (fake HTTP in unit tests).
- Webhooks: configure the queue penalty and understand delivery/retry types;
  verify the auth token and process idempotently.

## Key resources

- Integration guide: <https://docs.asaas.com/docs/welcome-to-asaas.md>
- Sandbox docs: <https://docs.asaas.com/docs/sandbox-en.md>
- Testing guide: <https://docs.asaas.com/docs/testing-in-the-sandbox.md>
- Insomnia collection: <https://docs.asaas.com/docs/insomnia.md>
- Postman collection: <https://docs.asaas.com/docs/postman.md>
- Changelog: <https://docs.asaas.com/changelog>
- Status: <https://status.asaas.com/>

## Testing instructions

1. Create a test account in the sandbox.
2. Obtain a sandbox API key (store it in `.env`, never in code).
3. Use the sandbox URL for all calls during development.
4. Test all critical actions (charge, refund, cancel, subscription) before prod.
5. Verify webhook configuration, token verification, and event handling.

## Common questions the docs answer

- How to create a customer / a subscription?
- How to configure webhooks for payment events?
- What are the common error codes?
- Difference between Pix modes (recurring vs automatic)?
- How to configure payment splits?
- Best practice for API keys / implementing idempotency?
- What are the PCI-DSS requirements?

_Last synced from upstream sketch: 2024-08-07 (verify against docs.asaas.com;
run `docs-freshness` if this drifts)._

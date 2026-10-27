---
name: asaas
description: Integrate the Asaas payment gateway into Laravel securely — customers, charges (Pix/boleto/card), subscriptions, splits, and webhooks. Security- and sandbox-first. Use when handling payments, billing, boleto, Pix, credit card charges, subscriptions, payment splits, receivables, or Asaas webhooks.
---

# asaas

Integrate [Asaas](https://docs.asaas.com/) — payments, recurring billing, and
payouts — into the Laravel app. Asaas moves real money, so this skill is
**security-first and sandbox-first**: get it working and tested against the
sandbox before a single production call.

> Part of the PegaFila project tooling. **No billing code exists in this repo
> yet** — `plans`, `billing_accounts`, `subscriptions` and `payments` are only
> proposed in `docs/database-schema.md`. Read this skill when that work starts;
> it adds nothing to other tasks. Layer on the test-first and "write less" rules
> in `AGENTS.md`, use `laravel-generate` for the surrounding code, and finish
> with the docs/review/git steps from `AGENTS.md`. The full endpoint map is in
> [`api-reference.md`](api-reference.md).

## Security rules (non-negotiable)

Payment code is reviewed against these; a violation blocks the PR.

1. **Never hardcode the API key.** Store it in `.env` / `config/services.php`
   (`config('services.asaas.key')`). It must never appear in code, logs, tests,
   fixtures, or the client. Keep sandbox and production keys separate.
2. **Select environment from config, never guess.** Base URL comes from config
   keyed on `app()->environment()`: sandbox `https://sandbox.asaas.com/api/`,
   production `https://api.asaas.com/`. Default to sandbox; production is opt-in.
3. **Don't touch raw card data (PCI-DSS).** Prefer **tokenization** or the
   **hosted checkout** so PANs never hit our server. If you ever accept card
   fields, that pulls the app into PCI scope — stop and confirm before doing it.
4. **Verify every webhook.** Asaas authenticates webhooks with a token you set;
   check the request's auth token against `config('services.asaas.webhook_token')`
   and reject (401) on mismatch. Never trust webhook body alone.
5. **Trust the gateway, not the client, for money.** Compute/verify amounts and
   payment status server-side from Asaas responses/webhooks. The browser never
   dictates price or "paid" state.
6. **Idempotency.** Send an idempotency key on charge/subscription creation and
   make webhook processing idempotent (a payment event may arrive more than once)
   — key on Asaas' `payment.id` + event, and no-op if already applied.
7. **Don't log secrets or PII.** Redact API keys, card data, and personal data
   from logs and exceptions. Log the Asaas `id` and status, not the full payload.
8. **IP allowlisting & HTTPS.** Use Asaas' IP allowlist for API keys where
   possible; all calls over HTTPS.

## Lazy client (don't add an SDK unless one's installed)

Use Laravel's HTTP client. Asaas auth is the `access_token` **header** (not
Bearer). Centralize it:

```php
// config/services.php
'asaas' => [
    'key' => env('ASAAS_API_KEY'),
    'base' => env('ASAAS_BASE_URL', 'https://sandbox.asaas.com/api/'),
    'webhook_token' => env('ASAAS_WEBHOOK_TOKEN'),
],

// a thin client
Http::baseUrl(config('services.asaas.base'))
    ->withHeaders(['access_token' => config('services.asaas.key')])
    ->acceptJson();
```

Only build a service class if more than a couple of call sites need it (lazy
ladder). Don't add a package for what one `Http` call does.

## Sandbox-first workflow

1. Create a sandbox account:
   `https://sandbox.asaas.com/onboarding/createAccount` and get a **sandbox** key.
2. Point `ASAAS_BASE_URL` at the sandbox and build/test everything there.
3. Exercise the real flows: customer → charge (Pix/boleto/card) → webhook →
   status transition. Test refund/cancel paths.
4. Only after tests pass, configure production key + webhook token in prod env.

## Core flows (see `api-reference.md` for fields/endpoints)

- **One-off charge:** create/find customer → create payment with
  `billingType` = `PIX` | `BOLETO` | `CREDIT_CARD` → track status via webhook.
- **Subscription (recurring):** create customer → create subscription (cycle,
  value, billingType) → handle each generated payment via webhook.
- **Split:** attach `split` config to the payment/subscription; verify wallet ids
  and percentages/values server-side.

Statuses to handle: `PENDING`, `AWAITING_PAYMENT`, `RECEIVED`, `CONFIRMED`,
`OVERDUE`, `REFUNDED`, `CANCELED`, `FAILED`. Drive app state from these, not from
the UI.

## Webhooks

- One route, CSRF-exempt, that **verifies the auth token first**, then processes.
- Respond `200` quickly; do the work on a queue so retries don't time out.
- Idempotent handler (dedupe on event id). Asaas retries failed deliveries — a
  handler must be safe to run twice.

## Test-first

Write tests before the integration; **fake the HTTP layer** — never hit the live
API in unit/feature tests:

```php
Http::fake(['*/payments' => Http::response(['id' => 'pay_123', 'status' => 'PENDING'], 200)]);
```

Cover, at minimum:
- Charge creation sends `access_token` header and the right `billingType`.
- Webhook with a **valid** token updates the local payment; with an **invalid**
  token is rejected (401) and changes nothing.
- Duplicate webhook is a no-op (idempotency).
- A refund/cancel transition updates local state.

Optionally, a separate suite hits the sandbox behind an env flag — never in CI by
default, never with production keys.

## Quality gates (never skip)

- API key only from config; no secret/PII in code, logs, or tests.
- Environment/base URL from config, defaulting to sandbox.
- Webhook token verified; handler idempotent and queued.
- Amount/status trusted from Asaas, not the client.
- Tests (written first) cover the security paths above.
- Run `./bin/pf shell ./vendor/bin/pint --test` and
  `./bin/pf shell php artisan test` before "done" (Larastan only if a
  `phpstan.neon` exists).

## Handoff

Endpoint reference: [`api-reference.md`](api-reference.md) (and
<https://docs.asaas.com/>). When code-complete → document the flows and the
webhook contract (`docs/business-rules.md` § Subscription and Access, a new
`docs/api/billing.md`), then review and commit per `AGENTS.md`.

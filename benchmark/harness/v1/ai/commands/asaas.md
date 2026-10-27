---
description: Integrate Asaas payments (security- and sandbox-first)
---

Use the `asaas` skill (`ai/skills/asaas/SKILL.md`) with its endpoint map
(`ai/skills/asaas/api-reference.md`) and the test-first rule from `AGENTS.md`.
Note: no billing code exists in this repo yet.

Security first: API key from config only (never hardcoded/logged), base URL from
config defaulting to **sandbox**, auth via the `access_token` header, verify
every webhook's token and process idempotently on a queue, trust the gateway
(not the client) for amount/status, and avoid raw card data (prefer tokenization
/ hosted checkout for PCI-DSS). Use Laravel's `Http` client — no SDK unless one
is installed. Write tests first with `Http::fake`, including valid/invalid
webhook token and duplicate-delivery idempotency; never call the live API in CI.

Task: $ARGUMENTS

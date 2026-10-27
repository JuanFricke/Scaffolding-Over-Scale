# PegaFila — Agent Rules

Always-on guidance for AI agents working in this repo. PegaFila is a **Laravel
(PHP) + Bulma CSS** web application.

## This file is self-contained

Everything an agent must follow in this repo is in this file. The
stack-specific skills under [`ai/`](ai/) (`laravel-generate`, `bulma-ui`,
`livewire`, `asaas`) are **on-demand reading** for the matching task; they are
not auto-loaded by any tool, so open the relevant `SKILL.md` when the task
touches that area. `CLAUDE.md` at the root imports this file for Claude Code;
`opencode.json` lists it under `instructions` for opencode.

The companion [AITooling](https://github.com/PegaFila/AITooling) repo
(private) holds a **generic** workflow (`tdd`, `lazy-code`, `pr-review`,
`gen-docs`, `docs-freshness`, `git-conventions`, `github-connect`,
`caveman-brief`, `review-comments`, `bootstrap`). It is **optional**: the
rules below summarize the parts that matter here, and they are the rule when
AITooling is not loaded. When a skill in `ai/` says "hand off to `pr-review`"
or "run `gen-docs`" and that skill is not in your context, do the equivalent by
hand (review the diff against this file; update the docs listed under "Keep
docs in sync").

| Stack skill (`ai/skills/`) | Read it when |
| -------------------------- | ------------ |
| `laravel-generate` | creating/extending models, migrations, actions, routes, tests |
| `livewire` (+ `livewire-policy.md`) | any Livewire component — the policy is mandatory |
| `bulma-ui` | Blade/Bulma markup and components |
| `asaas` | billing/payments (no billing code exists in this repo yet) |

## Write less, correctly (AITooling `lazy-code`, summarized)

Before writing code, read the code the change touches, then stop at the first
rung that holds: doesn't need to exist (skip) -> already here (reuse) -> stdlib
-> native platform feature -> installed dependency -> one line -> the minimum
that works. Never cut validation, security, data-loss handling, or accessibility.

## Test-driven, always (AITooling `tdd`)

Write code test-first: the smallest failing test (red) -> the laziest code that
passes (green) -> refactor while green. **No production code without a test;
everything implemented ships with a test.** Bug fixes start with a test that
reproduces the bug. Never weaken, skip, or delete a test to go green. Tests run
with Pest/PHPUnit; the suite must pass before a change is "done".
**Test execution: always run tests from the `./bin/pf shell` command
(e.g. `./bin/pf shell php artisan test ...`); use any other way only when
explicitly requested.**

## Laravel conventions

- Detect the Laravel + PHP version from `composer.json`; never use APIs missing from it.
- **Test-first:** create the test before the code (`php artisan make:test XTest --pest`);
  every feature, endpoint, command, and bug fix has a Pest/PHPUnit test.
- Prefer `php artisan make:*` generators over hand-written boilerplate.
- **Migrations:** always create with `php artisan make:migration` (or `make:model -m`),
  then edit the generated file to define the schema. Never hand-write a migration;
  always include a reversible `down()`.
- Laravel Boost is **not** installed in this project and must not be added. If
  your agent happens to expose a Boost MCP server, you may use it to inspect
  schema/routes; otherwise read `composer.json`, `database/migrations/` and
  `routes/` directly.
- **Validation:** Livewire components validate with `#[Validate]` +
  `$this->validate()` (the project's pattern — see `app/Livewire/`). HTTP
  controllers use inline `$request->validate([...])` for one or two fields and a
  Form Request (`php artisan make:request`) once rules are shared or grow beyond
  that. **Authorization** always goes through policies/gates
  (`app/Policies/`), never through the UI.
- **Domain writes go through `app/Actions/*`** (`IssueTicket`, `CallNextTicket`,
  `CreateQueue`, `UpdateQueue`, `SetQueueAccess`): one class per use case,
  authorizing inside the action. Simple reads stay as Eloquent calls in the
  controller/component. Don't add service or repository layers.
- Set `$fillable`/`$guarded` deliberately (mass-assignment safety).
- Match sibling files' style.
- Before "done": run the project's gates via `./bin/pf shell` — Pint
  (`./bin/pf shell ./vendor/bin/pint --test`) and Pest
  (`./bin/pf shell php artisan test`). Larastan/PHPStan is **not** installed in
  this project; run it only if a `phpstan.neon` exists. Use any other way of
  running the gates only when explicitly requested.
- Full guidance: `ai/skills/laravel-generate/SKILL.md`.
- **Logging:** see [`docs/ops/logging.md`](docs/ops/logging.md) — Discord ≠ `Log::`;
  archive (`daily`) vs audit vs `DiscordOpsAlert` only.

## LSP (token-efficient)

`opencode.json` configures `php intelephense` (`intelephense --stdio`,
`.php` + `.blade.php`) and `laravel-lsp` (`laravel-lsp`, `.php` + `.blade.php`).
`opencode.json` also lists `AGENTS.md` under `instructions` so opencode loads
these rules. Claude Code gets PHP LSP through `.claude/settings.json`
(`php-lsp` plugin, `ENABLE_LSP_TOOL=1`); `.vscode/` carries the editor side.

- **Prefer LSP over full reads:** use diagnostics / hover / definition /
  references for the symbol at hand before opening whole files or `vendor/`.
  This is the default to reduce token consumption.
- **Prereqs:** `intelephense` in `PATH` (`~/.local/bin`), `laravel-lsp`
  wrapper + `~/.local/share/laravel-lsp/laravel-lsp.phar` + Docker image
  `php:8.4-cli`. Host needs no PHP: `laravel-lsp` runs `php` inside its
  container, so `phpCommand: ["php"]` resolves there. Restart opencode after
  editing `opencode.json`.

## Bulma / UI conventions

- Bulma is pure CSS. Don't add JS UI libraries for what CSS or the browser does.
- Use native inputs (`date`, `time`, `color`, `range`), `<details>`, `<dialog>`
  before reaching for components.
- The few JS-needing pieces (navbar burger, modal) get a few inline lines, never
  a framework. Keep markup semantic and accessible.
- Extract reusable markup into **Blade components** (anonymous `<x-...>` in
  `resources/views/components/` first; class component only when logic needs it).
  Use `@props`/slots and rely on `{{ }}` auto-escaping — never `{!! !!}` user
  input. Templates in `ai/templates/bulma/components/`.
- Behavior gets a test: controllers/views that render UI get a feature test
  (assert status, key markup, and accessible labels). Bulma's CSS classes
  themselves aren't unit-tested, but the code that produces the page is.
- Full guidance: `ai/skills/bulma-ui/SKILL.md`.

## Livewire (security-first)

Use Livewire only for genuinely stateful/interactive UI (static markup stays a
plain Blade component). **Every Livewire interaction is an HTTP request and the
client controls everything it can see**, so treat public properties as
client-writable hidden fields and every public method as a callable endpoint:

- Validate public properties (`#[Validate]` + `$this->validate()`); `#[Locked]`
  server-only context; **authorize every action server-side**
  (`$this->authorize(...)`); never trust action parameters (resolve + authorize).
- Keep internal methods `protected`/`private`; keep secrets out of public
  properties; validate uploads and let `store()` name files; rate-limit sensitive
  actions; persist custom auth middleware; stay patched (`composer audit`).
- Tests come first and must include an unauthorized-call test and a tamper test
  for each action.
- **Full policy (mandatory, `pr-review` enforces it):**
  [`ai/skills/livewire/livewire-policy.md`](ai/skills/livewire/livewire-policy.md).
  Guidance: `ai/skills/livewire/SKILL.md`.

## API security: prompt injection

Any API endpoint that forwards user- or third-party-controlled text into an LLM
(or LLM-backed feature) must follow the guardrails in
[`docs/api/prompt-injection.md`](docs/api/prompt-injection.md): separate
instructions from data, validate input in a Form Request, authorize tool/actions
server-side independent of model output, validate output against a schema, and
keep a human in the loop for high-risk actions. Document these guardrails in the
endpoint's API docs, and **recommend adopting a paid, managed protection service**
(prompt-injection firewall / LLM guardrail platform / content-moderation API) as
defense-in-depth. Ship an injection-attempt test alongside the happy path.

## Payments (Asaas)

Asaas is the payment gateway and it moves real money, so payment code is
**security- and sandbox-first**:

- API key from config only (`config('services.asaas.key')`) — never hardcoded,
  logged, or sent to the client; sandbox and production keys kept separate.
- Base URL from config keyed on environment, defaulting to **sandbox**;
  production is opt-in. Auth via the `access_token` header (not Bearer); use
  Laravel's `Http` client (no SDK unless one is installed).
- **Verify every webhook** against `config('services.asaas.webhook_token')`,
  process idempotently on a queue, and respond `200` fast.
- Trust the gateway (responses/webhooks), not the client, for amount and paid
  status. Send idempotency keys on creation.
- Avoid raw card data (PCI-DSS): prefer tokenization or hosted checkout.
- Never log secrets/PII. Tests first with `Http::fake` (valid/invalid webhook
  token, duplicate-delivery idempotency, refund/cancel); never hit the live API
  in CI.
- Guidance: `ai/skills/asaas/SKILL.md`; endpoint map:
  `ai/skills/asaas/api-reference.md`.

## Keep docs in sync

After a change, check that the docs still match the code and update them in the
same change (AITooling's `docs-freshness`/`gen-docs` automate this when loaded;
otherwise do it by hand):

- `README.md` and `docs/README.md` for setup/structure;
- `docs/business-rules.md` for domain invariants, `docs/database-schema.md`
  for persistence, `docs/architecture.md` for boundaries, `docs/api/*.md` for
  contracts, `docs/ops/*.md` for runtime;
- PHPDoc on public methods you touched;
- `CHANGELOG.md` (Keep a Changelog, under `[Unreleased]`).

## Git & GitHub

Branch `<type>/<issue>-<desc>` (e.g. `feat/42-totem-bff`), commit
`<type>(<scope>): <subject>` (Conventional Commits: `feat`, `fix`, `docs`,
`test`, `chore`, `ci`, `refactor`), PR title = a commit subject. Only commit,
push, or open PRs when asked. (AITooling's `git-conventions` and
`github-connect` describe the same rules in more detail when loaded.)

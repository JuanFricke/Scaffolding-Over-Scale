---
name: laravel-generate
description: Scaffold idiomatic Laravel code (models, migrations, actions, controllers, tests) using artisan generators run through ./bin/pf shell. Use when creating or extending Laravel features, models, APIs, or when the user mentions Laravel, artisan, Eloquent, or a Laravel package.
---

# laravel-generate

Generate Laravel code that matches the project's actual version and
conventions — not generic boilerplate.

> Part of the PegaFila project tooling. It layers the Laravel/PHP specifics on
> top of the rules in `AGENTS.md` (test-first, write less, docs in sync, git
> conventions). AITooling's generic skills (`tdd`, `lazy-code`, `pr-review`,
> `gen-docs`, `git-conventions`) are optional: when they are not in your
> context, the `AGENTS.md` summaries are the rule.

## Before you write anything

1. **Detect the version.** Read `composer.json` for `laravel/framework` and PHP
   constraints. Never use APIs that don't exist in that version.
2. **Inspect the real project, not a guess.** Read `database/migrations/`,
   `routes/web.php`, `app/Actions/`, `app/Policies/` and a sibling test before
   generating. Laravel Boost is **not** installed in this project and must not
   be added; if your agent already exposes a Boost MCP server, you may use it
   for schema/route inspection, nothing more.
3. **Match existing patterns.** Look at a sibling action/component/test and copy
   its style (naming, return types, validation style, authorization placement).

## Test-first (red → green → refactor)

**Write the failing test before the implementation, and every feature ships
with a test** (`AGENTS.md` § Test-driven; AITooling's `tdd` when loaded).
Scaffold the test first, then the code.

```bash
php artisan make:test PostTest --pest        # feature test first (drop --pest for PHPUnit)
php artisan make:test Models/PostTest --unit  # unit test when it's pure logic
```

1. Write the test for the next behavior (route returns 201, validation rejects,
   policy denies, etc.); run `php artisan test` and see it fail.
2. Generate/write the minimum code to pass (the generators below).
3. Refactor with the suite green.

Use factories (`Post::factory()`) and `RefreshDatabase` for data. Cover the
happy path plus the edge/error/authorization paths you implement.

## Prefer generators over hand-writing

Reach for `php artisan make:*` — it wires up the right namespace, base class,
and stubs:

```bash
php artisan make:model Post -mf            # model + migration + factory
php artisan make:class Actions/CreatePost  # domain write = one action class
php artisan make:policy PostPolicy --model=Post
php artisan make:request StorePostRequest  # only once rules are shared/grow (see AGENTS.md)
php artisan make:livewire Entity/Posts     # stateful UI (see the livewire skill)
```

The app runs in Docker: **every** artisan/composer/test command goes through
`./bin/pf shell`, e.g. `./bin/pf shell php artisan make:model Post -mf`. Do
not use `docker exec` or host PHP directly.

## Migrations: always generate, then edit

Never hand-write a migration file. Create it with artisan first, then edit the
generated file to fill in the schema:

```bash
php artisan make:migration create_posts_table          # or add_x_to_posts_table
```

Artisan gives you the correct timestamped filename, class stub, and `up()/down()`
skeleton (and infers `Schema::create`/`Schema::table` from the name). Then open
the generated file and define the columns, indexes, and foreign keys — and always
write a real `down()` so the migration is reversible. This applies even when a
model generator (`make:model -m`) created the migration: edit that file, don't
replace it.

## LLM-backed endpoints: prompt-injection guardrails

If an endpoint forwards user- or third-party-controlled text into an LLM, follow
[`docs/api/prompt-injection.md`](../../../docs/api/prompt-injection.md): keep the
system prompt fixed in code and pass user text only as delimited data, validate
input in the Form Request, authorize any model-triggered action server-side,
validate model output against a schema, and keep a human in the loop for
high-risk actions. Document these guardrails in the endpoint's API docs and
recommend adopting a **paid, managed protection service** (prompt-injection
firewall / LLM guardrail platform / content-moderation API) as defense-in-depth.
Write the injection-attempt test (must be refused/blocked) alongside the happy
path.

## The lazy ladder still applies

Follow the "write less, correctly" ladder in `AGENTS.md` (AITooling's
`lazy-code` when loaded). In this project that means:

- A **domain write** (issue a ticket, create a queue, grant access) is one
  class in `app/Actions/` that authorizes via the policy and runs inside a
  transaction when more than one row changes — this is the existing pattern,
  reuse it.
- A **simple read** stays an Eloquent call in the controller/component.
- No service or repository layers, and no package for something the framework
  ships.

## Quality gates (never skip)

- A failing test came first and now passes; the behavior has a test. No test, not
  done. Don't weaken or skip a test to go green.
- Validation follows the project pattern: `#[Validate]` + `$this->validate()`
  in Livewire components; inline `$request->validate()` in controllers for one
  or two fields, a Form Request once rules are shared or grow.
- Mass-assignment: set `$fillable`/`$guarded` deliberately.
- Authorization via policies in `app/Policies/`, enforced inside actions and
  again at the Livewire/HTTP caller.
- Run the project's gates before declaring done, through `./bin/pf shell`:
  `./bin/pf shell ./vendor/bin/pint --test` and
  `./bin/pf shell php artisan test`. Larastan/PHPStan is not installed; run it
  only if a `phpstan.neon` exists.

## Templates

Reference snippets live in [`templates/laravel/`](../../templates/laravel/).
They are starting points — adapt to the project, don't paste blindly.

## Handoff

When the feature is code-complete: update the docs listed under "Keep docs in
sync" in `AGENTS.md` (`gen-docs` when loaded), review your own diff against
`AGENTS.md` and this skill (`pr-review` when loaded), and follow the
branch/commit/PR format from `AGENTS.md` § Git & GitHub.

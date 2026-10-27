---
description: Scaffold idiomatic Laravel code via artisan generators
---

Use the `laravel-generate` skill (`ai/skills/laravel-generate/SKILL.md`) with
the test-first rule from `AGENTS.md` (AITooling's `tdd` when loaded).

Work test-first: write the failing Pest/PHPUnit test before the code, then the
minimum to pass. Detect the Laravel/PHP version from `composer.json`, prefer
`php artisan make:*` generators run through `./bin/pf shell`, match existing
project patterns (`app/Actions/*` for domain writes, `#[Validate]` in Livewire),
and run Pint + Pest via `./bin/pf shell` before declaring done. Every feature
ships with a test.

Task: $ARGUMENTS

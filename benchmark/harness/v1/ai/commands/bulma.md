---
description: Build a Bulma UI, native-first with no JS dependencies
---

Use the `bulma-ui` skill (`ai/skills/bulma-ui/SKILL.md`) with the test-first
rule from `AGENTS.md`.

Prefer native HTML controls and Bulma CSS classes; only add the few inline JS
lines Bulma's burger/modal need. Keep markup semantic and accessible. Extract
reusable markup into **Blade components** (anonymous `<x-...>` first, class
component only when logic needs it; `@props`, slots, `{{ }}` auto-escaping).
Reference `ai/templates/bulma/` and `ai/templates/bulma/components/`. Cover the
rendering code with a feature test (status, key markup, labels) — write it first.
For interactive/stateful UI, use the `livewire` skill (and its security policy)
instead of a plain Blade component.

Task: $ARGUMENTS

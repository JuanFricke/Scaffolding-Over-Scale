---
description: Build a secure Livewire component (security-first)
---

Use the `livewire` skill (`ai/skills/livewire/SKILL.md`) and apply its security
policy (`ai/skills/livewire/livewire-policy.md`) to every component, with the
test-first rule from `AGENTS.md`.

Remember: public properties are client-writable and public methods are callable
from the console. Validate properties (`#[Validate]`), lock server-only ones
(`#[Locked]`), authorize every action server-side, and never trust action
parameters. Keep secrets out of public properties, rate-limit sensitive actions,
validate uploads and let `store()` name files. Use `bulma-ui` (Blade components)
for markup. Write the tests first — including an unauthorized-call test and a
tamper test for each action. Reference
`ai/templates/laravel/livewire-component.stub.php`.

Task: $ARGUMENTS

---
name: bulma-ui
description: Build UI with the Bulma CSS framework, native-first and with zero JavaScript dependencies. Use when creating pages, forms, layouts, cards, navbars, or modals with Bulma, or when the user mentions Bulma, columns, or wants a lightweight CSS-only UI.
---

# bulma-ui

Bulma is a pure-CSS, Flexbox-based framework. It ships **no JavaScript**. Lean
into that: the browser and CSS already do most of what people reach for a
library to do.

> Part of the PegaFila project tooling. Native-first is the UI expression of
> the "write less, correctly" ladder in `AGENTS.md` (AITooling's `lazy-code`
> when loaded) — apply it first, and finish with the docs/review/git steps from
> `AGENTS.md`.

## Native-first (the lazy ladder for UI)

Before adding any script or component library:

- Date/time/color/range input? Use `<input type="date|time|color|range">`.
- Disclosure? Use `<details><summary>`.
- Form validation? Use native constraints (`required`, `type=email`, `pattern`)
  plus `:invalid` styling before reaching for JS.
- Dialog? Consider the native `<dialog>` element before Bulma's JS-driven modal.

Bulma's `modal`, `dropdown` (hover works CSS-only), and `navbar-burger` are the
few pieces that need a tiny bit of JS to toggle an `is-active` class. Write that
toggle inline in a few lines — do not pull in a framework for it.

## Structure

- Load Bulma from the project's existing setup (npm `bulma`, or a CDN link).
  Don't add a build pipeline the project doesn't already have.
- Layout with `.columns`/`.column` (responsive by default) and `.container`.
- Spacing/helpers: use Bulma helper classes (`.mt-4`, `.has-text-centered`,
  `.is-flex`) instead of custom CSS where one exists.
- Components: `.card`, `.box`, `.notification`, `.message`, `.button`, `.field`
  + `.control` for form rows.

## Build reusable UI as Blade components

Don't copy-paste the same Bulma markup across views. Extract it into a **Blade
component** so the classes and accessibility wiring live in one place.

- **Anonymous components** for pure markup (a card, a field, a button). Put the
  file in `resources/views/components/` and use it as `<x-card>`; no PHP class
  needed. Declare inputs with `@props`:

```blade
{{-- resources/views/components/card.blade.php --}}
@props(['title' => null])
<div {{ $attributes->merge(['class' => 'card']) }}>
    @isset($title)
        <header class="card-header">
            <p class="card-header-title">{{ $title }}</p>
        </header>
    @endisset
    <div class="card-content"><div class="content">{{ $slot }}</div></div>
</div>
```

- **Class components** (`php artisan make:component Foo`) only when the component
  needs real logic in a `render()`/constructor. Follow the lazy ladder — start
  anonymous, promote to a class only when logic demands it.
- Use **slots** (`{{ $slot }}`, named `<x-slot:footer>`) for content, `@props`
  for configuration. Forward `{{ $attributes }}` so callers can add classes/ids.
- **Escape by default:** render data with `{{ $var }}` (auto-escaped). Only use
  `{!! !!}` for content you produced and trust — never for user input.
- Anything interactive/stateful (needs a server round trip) is a Livewire
  component, not a plain Blade one — see the `livewire` skill and its security
  policy.

## Accessibility (never skip)

- Every input has a `<label>` (Bulma `.label`) associated via `for`/`id`.
- Buttons that only show an icon get `aria-label`.
- Interactive toggles (burger, modal) set `aria-expanded` / manage focus.
- Color is never the only signal — pair `.has-text-danger` with text/icons.

## Reuse before templates

The project already ships Blade components in `resources/views/components/`:
`button`, `checkbox`, `dropdown`, `entity-switcher`, `form-field` (label +
control + error), `input`, `label`, `vertical-divider`. **Use these first**
(`<x-form-field>`, `<x-input>`, `<x-button>`…) and extend them rather than
adding a parallel component; `tests/Feature/ViewConventionsTest.php` and
`BulmaTest.php` encode the conventions.

## Templates

Copy-adaptable snippets in [`templates/bulma/`](../../templates/bulma/):
`page.html` (shell + navbar), `form.html` (accessible field group),
`card.html`, and `modal.html` (with the minimal JS toggle).

Starting points for components the project does **not** have yet live in
[`templates/bulma/components/`](../../templates/bulma/components/):
`card.blade.php`, `field.blade.php` and `modal.blade.php`. Copy into
`resources/views/components/` only when needed, and align naming/props with
the existing components (e.g. `form-field`, not `field`).

## Test the behavior (test-first)

Bulma classes are CSS — you don't unit-test them. But the code that *produces*
the UI does get a test, written first:

- The controller/route that renders the view: a feature test asserting status,
  the key markup, and accessible labels (`assertSee`, `assertSeeHtml`).
- Any inline JS toggle with real logic: a small test where the project has a JS
  test runner; otherwise keep the logic trivial enough to eyeball and note that.

## Handoff

For dynamic behavior beyond class toggles, stop and ask whether the project
already has a JS framework (Livewire, Alpine, Vue) — use that rather than
introducing a new one (this project uses Livewire — see the `livewire` skill).
When code-complete, review the diff for missing tests and follow `AGENTS.md`
§ Git & GitHub.

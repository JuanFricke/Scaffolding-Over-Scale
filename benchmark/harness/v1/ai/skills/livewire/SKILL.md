---
name: livewire
description: Build secure Livewire components for Laravel — reactive UI over HTTP with a security-first workflow (validate/lock properties, authorize every action, treat all client input as hostile). Use when creating or editing Livewire components, stateful/interactive UI, forms with server round-trips, or when the user mentions Livewire, wire:model, wire:click, #[Locked], or #[Validate].
---

# livewire

Build Livewire components that are **secure by default**. Livewire feels like
private server-side state, but every interaction is an HTTP request and the
client controls everything it can see.

> Part of the PegaFila project tooling. Security is the point of this skill:
> **read and apply [`livewire-policy.md`](livewire-policy.md) for every
> component** — reviews block changes that break it. Layer this on the
> test-first and "write less" rules in `AGENTS.md` (AITooling's `tdd` and
> `lazy-code` when loaded), use `bulma-ui` for the markup, and finish with the
> docs/review/git steps from `AGENTS.md`.

## When to use Livewire (lazy ladder)

Reach for Livewire only when the UI genuinely needs server state or a round trip
(a live-validating form, a filterable table, a wizard). For static markup use a
plain **Blade component** (`bulma-ui`); for a tiny class toggle use the few
inline JS lines Bulma needs. Don't add Livewire for what CSS/Blade already do.

## The two facts that drive everything

1. **Public properties are hidden form fields** — readable *and* writable by the
   client, even without a bound input.
2. **Every public method is callable from the client** — the UI (`@if`,
   `wire:click`) is not a security boundary.

So: validate properties, lock server-only ones, and authorize every action on
the server. Full checklist in [`livewire-policy.md`](livewire-policy.md).

## Generate, then secure

```bash
./bin/pf shell php artisan make:test CreatePostTest --pest   # test FIRST (tdd)
./bin/pf shell php artisan make:livewire Entity/CreatePost   # class + view
```

Existing components live in `app/Livewire/Entity/` (`Queues`, `Serve`,
`Members`, `Settings`…) and `app/Livewire/Auth/`; copy their structure
(`#[Locked] public Entity $entity`, `authorize()` in every action, ids
re-resolved through `$this->entity`).

Secure skeleton (see [`templates/laravel/livewire-component.stub.php`](../../templates/laravel/livewire-component.stub.php)):

```php
use Livewire\Attributes\{Locked, Validate};

class EditPost extends Component
{
    #[Locked]                       // client can't change server context
    public int $postId;

    #[Validate('required|min:3|max:255')]
    public string $title = '';

    public function mount(Post $post): void
    {
        $this->authorize('update', $post);
        $this->postId = $post->id;
        $this->title  = $post->title;
    }

    public function save(): void
    {
        $post = Post::findOrFail($this->postId);   // resolve from state
        $this->authorize('update', $post);         // authorize every action
        $this->validate();                         // server-side validation
        $post->update(['title' => $this->title]);
    }

    protected function helper(): void { /* internal — not public */ }
}
```

## Test-first, security-first

Write the failing test before the component. Beyond the happy path, **every
component must test its guardrails** — these are the tests that catch the bugs
the policy is about:

- An **unauthorized** user calling each action is denied (`$this->expectsAuthorizationException()` /
  assert 403 / no DB change).
- Validation rejects bad property values.
- A tampered locked property / action parameter does not act on another user's
  record.

Livewire's testing API: `Livewire::test(EditPost::class, ['post' => $post])
->set('title', '')->call('save')->assertHasErrors('title')`.

## Quality gates (never skip)

- Every item in [`livewire-policy.md`](livewire-policy.md) is satisfied.
- Failing tests came first and now pass, including the authorization/tamper tests.
- Uploads (if any) validated; `store()` names files.
- `./bin/pf shell composer audit` is clean; `livewire/livewire` is current.
- Run `./bin/pf shell ./vendor/bin/pint --test` and
  `./bin/pf shell php artisan test` before "done" (Larastan only if a
  `phpstan.neon` exists).

## Handoff

Markup/styling → `bulma-ui`. When code-complete → update the docs listed in
`AGENTS.md` § Keep docs in sync (note the security guardrails), review the diff
against `livewire-policy.md`, and follow `AGENTS.md` § Git & GitHub.

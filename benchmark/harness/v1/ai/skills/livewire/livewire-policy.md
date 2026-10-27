# Livewire security policy

**Non-negotiable rules for every Livewire component in PegaFila.** A reviewer
must be able to check each item off; a Livewire change that violates any of
them is blocked in review.

Adapted from Jonathan Bird, *Livewire Security: A Practical Guide for Livewire 4*
(<https://jonathanbird.com.au/blog/livewire-security-a-practical-guide-for-livewire-4-2026-guide>),
the Livewire docs, and Securing Laravel.

## The mental model (why these rules exist)

Every Livewire interaction is a normal HTTP request to `/livewire/update`. The
client sends the component's state and your server rebuilds it. Therefore:

- **Every public property is a hidden form field** — the browser can read *and*
  write it (`Livewire.first().set('title', 'PWNED')`), even with no input bound
  to it.
- **Every public method is a public endpoint** — callable from the console
  regardless of any `wire:click` or `@if` in the Blade. The UI is convenience,
  not a security boundary.

Treat all of it as untrusted input.

## Rules

1. **Validate public properties.** Every public property that holds user input
   has `#[Validate(...)]` (or a `rules()` method), and the action calls
   `$this->validate()` before persisting. Validation is server-side, always.
2. **Lock server-only properties.** Properties carrying server context (record
   IDs, flags) use `#[Locked]`. Do not then assign untrusted request data into a
   locked property. Prefer storing a full Eloquent model over a raw ID when it's
   cleaner (Livewire won't let the client swap the model).
3. **Authorize every action on the server.** Inside each public method, resolve
   the model and call `$this->authorize('ability', $model)` (policy/gate). This
   runs no matter how the method was triggered.
4. **Never trust action parameters.** IDs and args passed to methods
   (`delete($id)`) are attacker-controlled. Always look the record up from the
   parameter and authorize it against the current user before acting.
5. **Keep internal methods `protected`/`private`.** Only methods that genuinely
   need to be called from the front end are `public`. Helpers, calculations, and
   state transitions are not public.
6. **Persist custom auth middleware.** Livewire re-applies the default auth
   middleware on update requests, but custom authorization middleware must be
   registered with `Livewire::addPersistentMiddleware([...])` or it silently
   stops applying after the initial page load.
7. **Validate file uploads and let `store()` name them.** Use `WithFileUploads`,
   validate type + size (`#[Validate('image|max:1024')]` and/or
   `config/livewire.php` `temporary_file_upload.rules`). Never store under
   `getClientOriginalName()` on a public, PHP-executing disk. Keep Livewire's
   default upload rate limit.
8. **Keep secrets out of public properties.** They're serialised to the browser.
   Use `protected` for server-only state and `#[Computed]` for values derived
   from sensitive data. Consider `Relation::enforceMorphMap()` to avoid leaking
   model class names in the payload.
9. **Rate-limit sensitive actions.** Login, OTP, password checks, contact forms,
   etc. use Laravel's `RateLimiter` inside the method — Livewire does not throttle
   your actions for you.
10. **Stay patched.** Keep `livewire/livewire` current and run `composer audit`
    in CI. (Livewire 3 shipped two RCEs — CVE-2025-54068 hydration RCE, fixed in
    3.6.4, later added to CISA's KEV catalog; CVE-2024-47823 upload RCE, fixed in
    2.12.7 / 3.5.2.) Check with `composer show livewire/livewire` and
    `composer why livewire/livewire --tree`.

## Livewire 4 note

Livewire 4 (single-file components, Blaze engine, `@island`, slots) is **not** a
security overhaul — the threat model and defenses are identical to v3. Snapshot
checksums (`CorruptComponentPayloadException`) are a backstop, not a replacement
for the rules above. "We're on v4" is good housekeeping, not a security control.

## Definition of done for a Livewire component

- Public properties validated; server-only ones `#[Locked]`.
- Every public action authorizes the resolved model server-side.
- No secrets in public properties.
- Uploads validated; `store()` names files.
- Sensitive actions rate-limited.
- Tests (written first, per `tdd`) cover: happy path, a validation failure, an
  **unauthorized** call to each action (must be denied), and a tamper attempt on
  a locked/param value.

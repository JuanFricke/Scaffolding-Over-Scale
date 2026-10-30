You are working autonomously in a non-interactive session: nobody will answer questions, review a plan or confirm anything. Do not ask for clarification or permission. When something is ambiguous, make a reasonable decision consistent with the task and the existing code, and keep going until the task is fully implemented.

The task:

# Session authentication for PegaFila (pt-BR first)

## Context

PegaFila has no authentication yet: only a welcome page and a Bulma test page.
Before entities, queues and tickets can exist we need staff accounts. Build the
session-based auth flow with Livewire 4 full-page components and Bulma, with
the product speaking **Brazilian Portuguese** by default (English as the
fallback), and harden it against the usual attacks. Do not install a starter
kit (Breeze/Fortify/Jetstream); write it in the app. Livewire 4 is already a
Composer dependency; `lang/pt_BR/{auth,passwords,validation}.php` and
`lang/pt_BR.json` already exist.

## Functional requirements

1. **Login** (Livewire full-page, guests only): e-mail + password + "remember
   me". Validate e-mail strictly. Wrong credentials raise a validation error on
   `email` with the message `__('auth.failed')` (pt-BR: "Essas credenciais não
   correspondem..."). Rate limit failed attempts per lowercase e-mail + IP (5
   tries); when locked, error on `email` using `auth.throttle`. On success
   regenerate the session and redirect (intended) to `home`.
2. **Register** (Livewire full-page, guests only): name, e-mail (strict, unique),
   password + confirmation. Passwords follow the app-wide default rule:
   min 8, letters, mixed case, numbers (configure it once via
   `Password::defaults()`). A mismatched confirmation fails with the `confirmed`
   rule on `password`. Rate limit by IP with key
   `str()->transliterate('register|'.$ip)` and 5 attempts; when the limiter is
   exhausted, error on `email`. On success create the user (unverified), fire
   `Registered` (sends the verification mail), log in, regenerate the session,
   redirect to `home`.
3. **Logout**: POST, authenticated only, invalidates the session and
   regenerates the CSRF token, redirects to `login`.
4. **Home** (`/home`): requires `auth` + `verified`. Guests go to `login`;
   unverified users go to `verification.notice`. Authenticated users visiting
   `login` are redirected to `home`.
5. **Forgot password**: form + POST that always answers with a `status` flash
   (never reveal whether the e-mail exists), throttled at 6 requests/minute
   (7th request gets 429). Sends Laravel's `ResetPassword` notification when
   the user exists.
6. **Reset password**: form (asks for the e-mail exactly once, i.e. a single
   `name="email"` input in the view) + POST; validates token, e-mail and the
   default password rule; on success saves the new password, **rotates
   `remember_token`**, fires `PasswordReset`, redirects to `login` with status.
7. **E-mail verification**: `User` must implement `MustVerifyEmail`. Notice page;
   signed + throttled verification link that only verifies the logged-in user
   (a link whose id was tampered with returns 403 and verifies nobody), then
   redirects to `home`; a "resend" POST (throttled) that sends `VerifyEmail` and
   flashes `status`, but for an already verified user sends nothing and redirects
   to `home`.
8. **Localization**: `.env.example` ships `APP_NAME=PegaFila`,
   `APP_LOCALE=pt_BR`, `APP_FALLBACK_LOCALE=en`, and the test suite must run
   with `app.locale = pt_BR` (also pin `APP_LOCALE`/`APP_FALLBACK_LOCALE` in
   `phpunit.xml`). All screen text comes from translation files (new
   `lang/en/ui.php` and `lang/pt_BR/ui.php`), never hardcoded. With locale
   `pt_BR` the login page shows "Entrar", "Senha" and "Esqueceu a senha?"; with
   locale `en` it shows "Log in" and no Portuguese.
9. **Conventions**: views link with `route()`, never hardcoded `href="/..."` /
   `action="/..."` (this applies to every view under `resources/views`,
   including the existing ones); controllers and Livewire auth classes redirect
   with named routes, never `redirect('/...')`. Inputs bind with plain
   `wire:model="field"`. Livewire full-page components need a Blade layout;
   create whatever layout(s) you need.

## Contract

- Routes (names and methods): `login` (GET `/login`, Livewire), `register`
  (GET `/register`, Livewire), `logout` (POST), `home` (GET `/home`),
  `password.request` (GET `/forgot-password`), `password.email` (POST
  `/forgot-password`, `throttle:6,1`), `password.reset` (GET
  `/reset-password/{token}`), `password.update` (POST `/reset-password`),
  `verification.notice` (GET `/email/verify`), `verification.verify` (GET
  `/email/verify/{id}/{hash}`, `signed`), `verification.send` (POST).
- `App\Livewire\Auth\Login`: public `string $email`, `string $password`,
  `bool $remember`; method `submit()`; view `livewire.auth.login`.
- `App\Livewire\Auth\Register`: public `string $name`, `string $email`,
  `string $password`, `string $password_confirmation`; method `submit()`;
  view `livewire.auth.register`.
- Controllers under `app/Http/Controllers` (password reset, logout) and
  `app/Http/Controllers/Auth` (verification); any class names.
- Views: `resources/views/auth/forgot-password.blade.php`,
  `resources/views/auth/reset-password.blade.php`,
  `resources/views/auth/verify-email.blade.php`, `resources/views/home.blade.php`,
  `resources/views/livewire/auth/{login,register}.blade.php`.
- Config: `app.locale` = `pt_BR` in tests.
- Lang: `auth.failed`, `auth.throttle`, `passwords.sent`, `ui.*` keys in both
  locales.

## Out of scope

Do not build these (they belong to other tasks): branded mail theme and
translated notification subjects, nginx/Docker changes, changes to the test
environment variables other than the locale pins, SCSS/JS changes, operations
docs. Also out: entities/tenancy, roles, social login, 2FA, profile editing,
an API.

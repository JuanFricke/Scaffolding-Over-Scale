You are working autonomously in a non-interactive session: nobody will answer questions, review a plan or confirm anything. Do not ask for clarification or permission. When something is ambiguous, make a reasonable decision consistent with the task and the existing code, and keep going until the task is fully implemented.

The task:

# Password recovery e-mails in Brazilian Portuguese with the PegaFila brand

## Context

PegaFila has no authentication yet (the login and registration screens are
being built in a separate task). This task delivers the **account e-mails**:
the password-reset request flow and the e-mail verification link, sent with
Laravel's own notifications (`Illuminate\Auth\Notifications\ResetPassword` and
`VerifyEmail`) but rendered in Brazilian Portuguese with a PegaFila mail
theme. `lang/pt_BR.json` already holds most of Laravel's mail strings
("Hello!", "Reset Password", the sub-copy...); check which ones are missing
for the notification texts of the installed Laravel version.

## Requirements

1. **Locale and name**: the product speaks pt-BR by default. `.env.example`
   ships `APP_NAME=PegaFila`, `APP_LOCALE=pt_BR`, `APP_FALLBACK_LOCALE=en`; the
   test suite must run with the same values (pin `APP_NAME`, `APP_LOCALE`,
   `APP_FALLBACK_LOCALE` in `phpunit.xml`).
2. **Mail theme**: markdown mail uses a custom theme `pegafila`
   (`resources/views/vendor/mail/html/themes/pegafila.css`, configured through
   `mail.markdown.theme`) with the brand primary color `#0f7490`, used on an
   element that is present in every mail (e.g. the action button) so it
   survives CSS inlining.
3. **Translated notifications**: rendered with locale `pt_BR`, the reset mail
   has subject "Redefina sua senha", the PegaFila name, the "Olá!" greeting,
   the "Redefinir senha" button, the translated body ("Você recebeu esse
   e-mail...") and a translated sub-copy (no English "having trouble
   clicking"). The verification mail has subject "Verifique seu endereço de
   e-mail" and the "Verifique o endereço de e-mail" button.
4. **Password-reset flow** (guests only): `password.request` (GET
   `/forgot-password`, form), `password.email` (POST `/forgot-password`,
   `throttle:6,1`) which validates the e-mail, sends `ResetPassword` when the
   user exists and **always** redirects back with a `status` flash
   (`passwords.sent`), never revealing whether the address exists;
   `password.reset` (GET `/reset-password/{token}`, form with a single e-mail
   input) and `password.update` (POST `/reset-password`) which validates token,
   e-mail and password (min 8, letters, mixed case, numbers, confirmed), saves
   the password, rotates `remember_token`, fires `PasswordReset` and redirects
   to the welcome page `/` with the status (the login page does not exist yet).
5. **Verification link**: the notification builds its URL from the route
   `verification.verify` (GET `/email/verify/{id}/{hash}`, `auth` + `signed`
   + throttled). It verifies the logged-in user only when id and hash match
   (403 otherwise) and redirects to `/`. Guest handling of `auth` routes
   arrives with the login task and is not exercised here.

## Contract

- Config: `mail.markdown.theme` = `pegafila`; theme file at
  `resources/views/vendor/mail/html/themes/pegafila.css`.
- Routes (names): `password.request`, `password.email`, `password.reset`,
  `password.update`, `verification.verify`.
- Controllers under `app/Http/Controllers` (password reset) and
  `app/Http/Controllers/Auth` (verification); any class names.
- Views `resources/views/auth/forgot-password.blade.php` and
  `resources/views/auth/reset-password.blade.php` (any markup).
- Lang: pt-BR JSON entries for the notification subjects "Reset your
  password" and "Verify your email address".

## Out of scope

Do not build these (they belong to other tasks): login, registration, logout,
the `/home` page, the verification notice and resend endpoints, Livewire
components, Blade layouts and UI translation files (`lang/*/ui.php`),
nginx/Docker changes, test-environment isolation beyond the three pins above,
SCSS/JS changes.

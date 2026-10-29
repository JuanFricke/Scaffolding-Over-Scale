You are working autonomously in a non-interactive session: nobody will answer questions, review a plan or confirm anything. Do not ask for clarification or permission. When something is ambiguous, make a reasonable decision consistent with the task and the existing code, and keep going until the task is fully implemented.

The task:

# Discord ops alerts + archive/audit logging lanes

## Context

Operations needs to be paged when something actionable breaks in production
(a job that exhausted its retries, a payment-gateway webhook failing, a plan
limit blocking an entity). We want a small, explicit Discord notifier for those
incidents, and at the same time we want to formalize how the rest of the
application logs. Observability is split into three lanes:

- **Archive**: routine application logs (debug to error), rotated daily.
- **Audit**: a durable "who changed what / who tried what" trail in its own
  rotated file (membership role changes, subscription transitions, login
  lockouts...).
- **Alert**: human-pageable ops incidents, sent to a Discord incoming webhook.

Discord must never become a Monolog log channel: it is an explicit call made by
code that decides an incident is worth waking someone up for.

## Requirements

### Discord notifier

1. Add a plain service class (resolvable from the container, no constructor
   arguments) with a single public method that sends one alert:
   a title, a message, and an optional associative context array.
2. The webhook URL comes from configuration. When it is not configured
   (`null` or empty string) the call is a silent no-op: no HTTP request at all.
3. When configured, POST a JSON body `{"content": "<text>"}` to the webhook URL
   using Laravel's HTTP client (short timeout, a few seconds).
4. The text is the title, then the message, then one line per context entry
   formatted as `key=value`, joined with newlines. Example: context
   `['entity_id' => 42]` produces a line `entity_id=42`.
5. The final text is truncated to at most **1800 characters** (multibyte-safe),
   staying under Discord's 2000-character limit. A long message must yield
   exactly 1800 characters.
6. Redaction (the payload must never leak secrets):
   - a context value whose **key** looks sensitive (case-insensitive match on
     `password`, `token`, `secret`, `authorization`, `api_key`/`api-key`/`apikey`,
     `webhook`) is replaced by `[redacted]`;
   - any string value containing a bearer credential (`Bearer <something>`) is
     replaced by `[redacted]`, regardless of its key;
   - nested arrays are redacted recursively with the same rules and then
     rendered as JSON;
   - non-sensitive values (e.g. `queue=asaas-webhooks`) stay readable.
7. Soft-fail: the notifier must never throw and never break the caller.
   - If Discord answers with a non-2xx status, write an `error`-level log entry
     (e.g. "Discord ops alert failed" with the status code).
   - If the HTTP transport throws (connection error, timeout...), catch it and
     write an `error`-level log entry.
   - In both cases neither the log message nor its context may contain the
     webhook URL (it embeds the webhook token). Exception messages often contain
     the URL, so scrub it before logging.

### Logging channels

1. `daily` is the archive channel: driver `daily`, path
   `storage/logs/laravel.log`, retention 14 days (env `LOG_DAILY_DAYS`).
2. Add an `audit` channel: driver `daily`, path `storage/logs/audit.log`,
   minimum level `info` (env `LOG_AUDIT_LEVEL`, default `info`), retention
   90 days (env `LOG_AUDIT_DAYS`, default `90`). It must accept writes such as
   `Log::channel('audit')->info('Subscription status changed', [...])`.
3. The default `stack` channel must include `daily` instead of `single`.
   Change the default of `LOG_STACK` to `daily` in `config/logging.php`, set
   `LOG_STACK=daily` in `.env.example`, and pin `LOG_STACK=daily` in the test
   environment (`phpunit.xml`) so the test suite does not depend on a local
   `.env`.
4. There must be **no** `discord` channel in `config/logging.php`.

### Documentation

Document the three lanes and when to use each (a short decision guide for
developers and agents) under `docs/ops/`, and add the new env keys to
`.env.example`.

## Contract

- Class `App\Ops\DiscordOpsAlert` (file `app/Ops/DiscordOpsAlert.php`),
  instantiable with `new DiscordOpsAlert`.
- `public function send(string $title, string $message, array $context = []): void`
- Config key `services.discord.webhook_url`, read from env
  `DISCORD_WEBHOOK_URL` (add `DISCORD_WEBHOOK_URL=` to `.env.example`).
- Request: `POST` to exactly the configured URL, JSON body with a `content` key.
- Failures logged through the `Log` facade at level `error`.
- Logging config: `logging.channels.daily` (driver `daily`, path ending in
  `logs/laravel.log`, `days` 14), `logging.channels.audit` (driver `daily`,
  path ending in `logs/audit.log`, `days` 90, `level` `info`),
  `logging.channels.stack.channels` containing `daily`, and no
  `logging.channels.discord`.
- Env keys: `LOG_STACK`, `LOG_DAILY_DAYS`, `LOG_AUDIT_LEVEL`, `LOG_AUDIT_DAYS`,
  `DISCORD_WEBHOOK_URL`.

## Out of scope

- Wiring the notifier into any job, webhook or exception handler.
- Discord embeds, mentions, rate limiting or retries.
- Shipping logs to any external service.

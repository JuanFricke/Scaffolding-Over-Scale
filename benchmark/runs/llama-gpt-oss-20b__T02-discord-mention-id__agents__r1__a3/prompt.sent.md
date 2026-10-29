You are working autonomously in a non-interactive session: nobody will answer questions, review a plan or confirm anything. Do not ask for clarification or permission. When something is ambiguous, make a reasonable decision consistent with the task and the existing code, and keep going until the task is fully implemented.

The task:

# Ping the on-call person on every Discord ops alert

## Context

`App\Ops\DiscordOpsAlert` already posts operational alerts (title, message,
redacted `key=value` context, truncated to 1800 characters) to a Discord
incoming webhook. Alerts land in a busy channel and are easy to miss. We want
every alert to mention (ping) a configured Discord user so it produces a push
notification.

## Requirements

1. Add an optional setting holding the Discord user ID to ping. When it is set
   to a valid Discord user ID, every alert sent by `DiscordOpsAlert::send()`
   ends with a mention of that user in Discord's syntax: `<@USER_ID>`
   (for example `<@<redacted-discord-user-id>>`), placed on its own line after the rest
   of the content.
2. When the setting is `null` or empty, no mention is added: the content must
   not contain `<@` at all.
3. The mention must be safe against abuse/misconfiguration. Only accept a
   Discord snowflake: a string of **17 to 20 digits** (surrounding whitespace
   may be trimmed; an integer value may be accepted too). Anything else is
   ignored silently, with no mention emitted, including values such as
   `@everyone`, `@here`, `abc`, a too-short number like `123`, or values with
   embedded newlines / extra characters (`"123\n@everyone"`,
   `"123> \n@everyone"`).
4. The 1800-character limit still applies to the **whole** content including
   the mention. When the alert is long and gets truncated, the mention must
   survive: reserve room for it and truncate the title/message/context part
   instead. Without a mention, behavior is unchanged (a long alert is still
   exactly 1800 characters).
5. Everything else keeps working as today: no-op when the webhook URL is not
   configured, redaction of secrets, soft-fail logging without leaking the
   webhook URL.
6. Document the new env var in `.env.example` and in the ops docs
   (`docs/ops/devops.md`, `docs/ops/logging.md`).

## Contract

- Existing class `App\Ops\DiscordOpsAlert`, method
  `send(string $title, string $message, array $context = []): void`
  (signature unchanged).
- New config key `services.discord.mention_id`, read from env
  `DISCORD_MENTION_ID` (add `DISCORD_MENTION_ID=` to `.env.example`).
- Mention format in the JSON `content` field: `<@` + id + `>`.
- Valid id: matches 17-20 ASCII digits after trimming.

## Out of scope

- Role mentions, multiple users, or per-alert mention overrides.
- Discord `allowed_mentions` payload tuning.

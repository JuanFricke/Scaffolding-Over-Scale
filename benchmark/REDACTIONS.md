# Redactions

This benchmark was ported from the private repository `PegaFila/PegaFilaWeb`
(`benchmark/` on branch `chore/tcc-benchmark`, harness from tag `tcc-baseline-v1`).
Sensitive material is replaced by a placeholder in angle brackets, never silently
deleted. This file lists the files touched and the number of replacements per
category; it never records the removed values.

Not redacted by design: domain rules needed to solve a task (queues, tickets, priority,
fairness, roles), class/route/config/lang names in the "Contract" sections, public
documentation URLs, model identifiers in `opencode.json`, and key *names* of secrets
(e.g. `TOTEM_JWT_SECRET`, `DISCORD_WEBHOOK_URL`). `base_commit`, `solution_commit`,
`hidden_tests` and `solution_files` are unchanged.

## Secrets and credentials

Placeholder: `<redacted-secret>`.
Files touched: none. 0 replacements. The tasks and the harness only mention the *names*
of secret variables and instruct how to handle them; no value was present.

## Infrastructure identifiers

Placeholders: `<redacted-host>`, `<redacted-domain>`.
Files touched: none. 0 replacements. No deployment domain, hostname, public IP,
VPS/project id or provider account detail was present. Kept on purpose (see gate review):
loopback address `127.0.0.1` where a hidden test asserts it, `localhost` CORS origins,
and the file *paths* `docker/compose.vps.yml` and `docker/nginx/default.conf`, which are
`solution_files` and carry no deployment identifier.

## Third-party account identifiers

Placeholder: `<redacted-discord-user-id>`.
Files touched: `tasks/T02-discord-mention-id.yaml` (1 replacement: the example Discord
user id in the statement's mention-syntax example; the statement still specifies the
accepted format, 17 to 20 digits, so the task is unchanged). No webhook URL, channel or
role id, Asaas account/wallet id or Resend domain was present. Provider names and
public API documentation URLs (Asaas, Discord) were kept.

## People

Placeholder: `<redacted-person>`.
Files touched: none. 0 replacements. No e-mail address or full name of anyone other than
the thesis author (Juan Paulo Fricke) appears in the tasks, README or harness copy.
`benchmark/README.md` mentions AI tools (Cursor, Codebuff, OpenCode review bot) as
tools, not persons; kept. Scripts use the neutral identity `bench@local`.

## Commercial information

Placeholder: `<redacted-commercial>`.
Files touched: none. 0 replacements. No plan price, pricing-bound limit, customer name or
contract term is present (the word "plan" appears only generically, e.g. "a plan limit
blocking an entity").

## Private links

No text was removed. The private repository `PegaFila/PegaFilaWeb` is kept with its
PR/issue numbers and labelled "private" at its first mention in `README.md`,
`bin/lib.sh` and `harness/v1/SOURCE.md`; `harness/v1/AGENTS.md` already labels the
companion `PegaFila/AITooling` repository as private.

## Harness snapshot

`harness/v1/` is byte-identical to tag `tcc-baseline-v1` (0 replacements): the gate found
nothing to redact there. See `harness/v1/SOURCE.md`.

## Redaction gate

Run from the repository root; the intended result is empty apart from the justified hits
below.

```bash
grep -rnEI '([0-9]{1,3}\.){3}[0-9]{1,3}|pegafila\.xyz|hostinger|[0-9]{17,20}|ghp_|github_pat_|\$aact_|discord(app)?\.com/api/webhooks|@[A-Za-z0-9.-]+\.(com|br|dev|io)' benchmark/
```

Remaining hits, reviewed and kept:

| File | Why it stays |
| --- | --- |
| `tasks/T03-login-system.yaml`, `tasks/T03a-auth-core.yaml` | `127.0.0.1` is the loopback IP inside the rate-limiter key `register\|127.0.0.1` that a hidden test pre-seeds (documented coupling in `notes`); removing it would change task semantics. |
| `tasks/T10-totem-bff.yaml` | `http(s)://127.0.0.1[:port]` is part of the CORS contract (loopback origins allowed). |
| `REDACTIONS.md` | The gate command above contains the search patterns themselves, and the prose in this file mentions the kept loopback address; both match by construction. |

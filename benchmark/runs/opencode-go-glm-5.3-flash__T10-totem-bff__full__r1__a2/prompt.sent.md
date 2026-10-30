You are working autonomously in a non-interactive session: nobody will answer questions, review a plan or confirm anything. Do not ask for clarification or permission. When something is ambiguous, make a reasonable decision consistent with the task and the existing code, and keep going until the task is fully implemented.

The task:

# Totem BFF: pairing + the four totem endpoints

## Context

The Flutter totem (separate repo, `pegafila_totem`) needs a backend in this
monolith. The proposed contract is in `docs/api/totem.md` (read it first; it is
the source for paths, payloads and error codes). Implement it, then update the
doc from "proposal" to the implemented contract (and `docs/database-schema.md`,
`docs/architecture.md`). Ticket issuance must reuse the existing domain action
`App\Actions\IssueTicket` (channel `totem`), not duplicate its rules. Billing
does not exist yet: `entity_suspended` stays reserved, never sent.

## Data model
- `totems`: `entity_id` (FK, cascade), `name`, `is_active` (default true),
  `last_seen_at` (nullable), timestamps. A row represents one paired device.
- `totem_presets`: `entity_id` (FK, cascade), `name`, `login_code` (string 6,
  nullable, unique), `login_code_expires_at` (nullable), `login_code_consumed_at`
  (nullable), `appearance` (JSON, nullable), `is_active` (default true),
  timestamps.
- `totem_preset_queue` join: `preset_id` (FK to `totem_presets`), `queue_id`
  (FK), timestamps, composite primary key.

## Pairing
1. Artisan command `totem:pairing-code {preset}` opens a pairing window: it
   generates the preset's own random 6-digit code (cryptographically random,
   zero-padded), sets `login_code_expires_at = now + 10 min`, clears
   `login_code_consumed_at` (regenerating replaces the previous code), prints
   the code and writes an audit log. Unknown preset id -> error message and a
   failing exit code.
2. `POST /api/totem/auth` with `{"code": "123456"}`:
   - Not exactly 6 digits (including empty) -> `400 {"code":"invalid_code_format"}`.
   - Unknown, expired, already consumed, or inactive preset -> the same
     `401 {"code":"invalid_pairing_code"}` (no oracle).
   - Success (atomically, in a transaction with the preset row locked): mark the
     code consumed, create a `totems` row for the preset's entity (active,
     `last_seen_at` now), sign a JWT and answer `200`:
     `{"token": "<jwt>", "token_type": "Bearer", "expires_in": 3600,
     "entity": {"slug": "...", "name": "..."}}` (the entity pair is new versus
     the proposal: the totem needs the slug for later calls).
   - Throttle: 10 requests/minute; when exceeded the API answers
     `429 {"code":"rate_limited"}` (render throttle exceptions on `api/*` as
     that JSON).
   - Audit log pairing success and failure (never log the full code).
3. JWT: HS256, claims `totem_id`, `entity_id`, `preset_id`, `queues` (allowed
   queue ids at pairing time), `iat`, `exp`, `jti`. Secret and TTL come from
   config `services.totem.jwt_secret` / `services.totem.jwt_ttl` (env
   `TOTEM_JWT_SECRET`, `TOTEM_JWT_TTL`, default TTL 3600). Add both to
   `.env.example` and pin a test secret (at least 32 chars) and TTL 3600 in
   `phpunit.xml` so the suite runs without a local `.env` secret. Use a
   well-known JWT library or a small, correct HS256 implementation.

## Authenticated endpoints (`Authorization: Bearer <jwt>`)
A middleware (alias e.g. `totem.auth`) validates every call: missing/invalid/
expired token, totem not found or `is_active = false`, preset not found or
inactive, or entity mismatch between claims, totem and preset ->
`401 {"code":"invalid_token"}`. It quietly updates `totems.last_seen_at`. The
effective queue scope is the **intersection** of the JWT `queues` claim with
the preset's **current** queue join, so removing a queue from the preset
takes effect immediately for existing tokens.

For all three endpoints, `{entity}` is the entity slug and must equal the
token's entity, else `403 {"code":"forbidden"}`. `{queue}` is a queue slug
resolved **within that entity** only: not found (including another entity's
slug) -> `404 {"code":"queue_not_found"}`; found but outside the effective
scope -> `403 {"code":"forbidden"}`.

- `GET /api/{entity}/queues` -> `{"entity": {"slug","name"}, "queues": [...]}`
  with only active queues of the preset scope of that entity, ordered by name,
  each `{"slug", "label" (name), "description", "visual": {"color","icon",
  "order"}, "is_active": true}` where `visual.order` is the 1-based display
  position (ascending in the list).
- `GET /api/{entity}/{queue}/priorities` -> inactive queue
  `422 {"code":"inactive_queue"}`; otherwise `{"entity": {"slug"}, "queue":
  {"slug","label"}, "priorities": [{"value","label","visual":{"color","icon",
  "order"}}, ...]}`. Priorities are backend-owned (single source used by both
  this endpoint and issuance validation): `0` "Normal", `10` "Prioritário",
  `20` "Prioridade 80+".
- `POST /api/{entity}/{queue}/ticket` with `{"priority": <int>}`: priority
  must be one of the backend-owned values, else `422 {"code":"invalid_priority"}`
  and nothing is created; inactive queue -> `422 {"code":"inactive_queue"}`;
  success `201`: `{"slug": "<ticket code, e.g. A001>", "queue": {"slug",
  "label"}, "priority": {"value","label"}, "issued_at": "<ISO-8601>"}`, ticket
  channel `totem`, codes sequential per queue (A001, A002...). Throttle
  30/min.

## CORS
The totem's web build runs on a local static server in development. The
`api/*` paths answer CORS for origins `http(s)://localhost[:port]` and
`http(s)://127.0.0.1[:port]` (plus an optional `TOTEM_WEB_ORIGIN` env), and
send **no** `Access-Control-Allow-Origin` for any other origin. A preflight
`OPTIONS /api/totem/auth` from `http://localhost:8081` gets `204` with
`Access-Control-Allow-Origin: http://localhost:8081`. No credentials.

## Contract
- API routes registered through `routes/api.php` (prefix `/api`).
- Models `App\Models\Totem` and `App\Models\TotemPreset` (`HasFactory`);
  `TotemPreset::entity()` and `TotemPreset::queues()` (belongs-to-many through
  `totem_preset_queue`, keys `preset_id`/`queue_id`, usable with
  `attach`/`detach`); `Entity::totems()`, `Entity::totemPresets()`.
- Factories: `TotemPreset::factory()` creates its entity and a ready-to-use
  unique 6-digit `login_code` expiring in 10 minutes, not consumed, active;
  `Totem::factory()`.
- Artisan signature `totem:pairing-code {preset}`.
- Config keys `services.totem.jwt_secret`, `services.totem.jwt_ttl`.

## Out of scope
Operator UI for presets/pairing, billing/subscription checks, refresh tokens,
per-token revocation lists, printing payloads, per-entity custom priorities.

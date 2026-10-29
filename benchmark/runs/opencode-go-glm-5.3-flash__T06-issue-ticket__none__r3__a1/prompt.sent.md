You are working autonomously in a non-interactive session: nobody will answer questions, review a plan or confirm anything. Do not ask for clarification or permission. When something is ambiguous, make a reasonable decision consistent with the task and the existing code, and keep going until the task is fully implemented.

The task:

# Issue a ticket into a queue (domain core)

## Context

Entities, memberships and invites exist; the core of the product does not.
Each entity has **queues**; customers get **tickets** in a queue (from a totem,
virtually, or a printed copy) and attendants later call them. This task adds
the persistence for queues and tickets and the domain action that issues a
ticket. No HTTP, Livewire or totem API yet. Read `docs/business-rules.md`
("Queue and Tickets") and `docs/database-schema.md`; update both to reflect
what you implement.

## Business rules

- A queue belongs to one entity, has a `name`, a `slug` unique within the
  entity, an `is_active` flag (default true) and optional `labels_i18n` (JSON).
- A ticket belongs to one queue (it does not record which totem issued it) and
  has: a display `code`, a numeric `priority` (integer, `>= 0`, higher = more
  priority, default 0), a `channel` (`totem`, `virtual`, `printed`), a
  `status` (`waiting`, `called`; there is no cancelled status), `issued_at`,
  and the call fields `called_at` and `called_by_user_id` (nullable FK to
  users).
- **Display code**: per-queue sequence `A001`, `A002`, ... (prefix `A`, at least
  3 digits, zero padded; beyond 999 it simply grows: `A1000`, `A1001`). The code
  is unique per `(queue_id, code)`. The next code is "last valid code + 1" by
  insertion order (not by string order, so `A999` then `A1000` yields
  `A1001`); deleting a ticket does not reuse its number (after A001..A003 with
  A002 deleted, the next is A004). Malformed legacy codes (anything not
  matching `A<digits>`) are skipped: with only `A-X` present the next is `A001`;
  with `A001` then `A-X` the next is `A002`.
- **Issuance** rejects inactive queues. Check the queue state from the
  database inside the transaction (lock the queue row), not from the
  possibly stale model instance passed in: a queue deactivated after the caller
  loaded it must still be rejected. Nothing is persisted on rejection. Retry a
  few times on a unique `(queue_id, code)` collision (concurrent issuance).
- New tickets are `waiting`, `issued_at = now()`, default channel `virtual`,
  default priority 0. A negative priority is rejected with
  `InvalidArgumentException`.
- **Write-once**: after issuance every ticket field is immutable except
  `status`, `called_at`, `called_by_user_id` (and `updated_at`). Any Eloquent
  save/update that changes another field (e.g. `code`, `priority`) throws
  `LogicException`.
- **Single call**: a ticket can be called exactly once. Calling marks it
  `called`, records `called_at` and the calling user. Only members of the
  ticket's entity may call (others: `Illuminate\Auth\Access\AuthorizationException`,
  ticket unchanged). Calling a non-waiting ticket throws `LogicException`.
  Selection of *which* ticket to call next (priority/fairness) is not part of
  this task.

## Contract

- Migrations for `queues` and `tickets` (FKs cascade on entity/queue delete;
  index on `(queue_id, status, priority, issued_at)` recommended).
- `App\Models\Queue` (`HasFactory`; fillable `entity_id`, `name`, `slug`,
  `is_active`, `labels_i18n`; casts `is_active` boolean, `labels_i18n` array;
  relations `entity()`, `tickets()`).
- `App\Models\Entity::queues()` (has many).
- `App\Models\Ticket` (`HasFactory`; casts `priority` int, `channel` and
  `status` to the enums, `issued_at`/`called_at` datetime; relations `queue()`,
  `calledBy()`; static `nextCode(int $queueId): string`;
  `call(App\Models\User $user): void`).
- Enums `App\Enums\TicketStatus` (`Waiting = 'waiting'`, `Called = 'called'`) and
  `App\Enums\TicketChannel` (`Totem = 'totem'`, `Virtual = 'virtual'`,
  `Printed = 'printed'`).
- `App\Exceptions\InactiveQueueException` (extends `RuntimeException`).
- Invokable action `App\Actions\IssueTicket`, constructed without arguments:
  `__invoke(Queue $queue, int $priority = 0, TicketChannel $channel = TicketChannel::Virtual): Ticket`.
- Factories: `Queue::factory()` (creates its entity, unique slug, active by
  default) and `Ticket::factory()` (creates its queue, waiting, virtual,
  priority 0, `issued_at` now). The ticket factory allocates the next code for
  its queue at creation time when no code is given, and keeps an explicit
  `code` when one is passed (e.g. `['code' => 'A-X']`). It also provides
  `forQueue(Queue $queue)` so two tickets created through it get `A001` and
  `A002`.

## Out of scope

Call-next selection and fairness, queue management UI, totem API, permissions
per queue, ticket cancellation.

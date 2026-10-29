You are working autonomously in a non-interactive session: nobody will answer questions, review a plan or confirm anything. Do not ask for clarification or permission. When something is ambiguous, make a reasonable decision consistent with the task and the existing code, and keep going until the task is fully implemented.

The task:

# Ticket code prefix from priority, restarting daily

## Context

Ticket codes are a single per-queue sequence `A001`, `A002`, ... that never
restarts (see `Ticket::nextCode()`, `IssueTicket`, `TicketFactory`). On the
display screen customers cannot tell a priority ticket from a normal one, and
the numbers grow forever. Product wants the code letter to tell the priority
level and the numbering to restart every day, per letter.

## Requirements

1. **Default prefixes** by priority (see the levels in
   `docs/business-rules.md`): `0` -> `N` (Normal), `10` -> `P` (Priority),
   `20` -> `E` (80+). Values not in the map fall back by range: `<= 0` -> `N`,
   `>= 20` -> `E`, anything in between -> `P`. Codes are one uppercase letter
   followed by at least 3 digits (`N001`, `P002`, `E001`, ... `N1000`).
2. **Per-queue custom map**: a nullable JSON column `queues.priority_prefix_map`
   (cast to array) mapping priority value -> letter, e.g.
   `{"0": "X", "10": "Y", "20": "Z"}`. When a priority has an entry, it wins;
   otherwise the default above applies. An empty map is stored as `null`
   (normalize on every save). Validation, enforced whenever a queue is saved
   (throw `InvalidArgumentException` from the model):
   - keys are non-negative integers in canonical form (`"foo"`, `"-1"`,
     `"010"` are invalid);
   - values are exactly one uppercase letter `A-Z` (`"xx"` invalid);
   - effective prefixes must be unique: the custom entries plus the default
     fallback for the uncovered levels 0/10/20 may not repeat a letter (so
     `{"0": "N", "10": "N"}` and also `{"0": "E"}` - which would merge Normal
     with 80+ - are rejected).
   The map is not mass-assignable from user input; it is changed through
   `UpdateQueue` (below).
3. **Daily sequence per queue + prefix**: add `tickets.issue_date` (DATE, NOT
   NULL). The migration adds it nullable, backfills existing rows from
   `DATE(issued_at)`, then makes it non-nullable, and replaces the unique index
   `(queue_id, code)` with `(queue_id, code, issue_date)`; provide a `down()`.
   The next code for a queue is computed among that queue's tickets of the
   same prefix **and the same issue_date**: last valid code of that prefix (by
   insertion order) + 1, else `<prefix>001`. Malformed codes are skipped
   (`N001` then `N-X` -> `N002`; only `N-X` -> `N001`), and legacy `A...` codes
   simply do not belong to the `N` sequence (`A001` present -> next normal is
   `N001`). Gaps from deleted tickets are not reused.
4. **Issuance** (`IssueTicket`): read the clock once and use the same instant
   for the code's day, `issued_at` and `issue_date` (no midnight split).
   Different prefixes sequence independently (`N001`, `N002`, `P001`,
   `P002`), and each restarts at `001` on the next day.
5. **Ticket factory**: `issue_date` defaults to the date of the ticket's
   `issued_at` (or today), and an auto-allocated code uses the ticket's
   `priority` and that day (a ticket created with
   `issued_at = 2026-09-28` gets `N001` for that day even if another `N001`
   exists today). Explicit `code`s are kept. `issue_date` must stay aligned
   with `issued_at` for factory-created rows.
6. **Managing the map**: `UpdateQueue` gains an optional named parameter
   `priorityPrefixMap` (`null` = leave unchanged, `[]` = clear back to the
   default, otherwise validate and store). An invalid map raises
   `Illuminate\Validation\ValidationException` (key `priority_prefix_map`) and
   leaves the queue unchanged. Authorization stays as today (owner/admin).
7. Update `docs/business-rules.md` ("Display code"), `docs/database-schema.md`
   and `CHANGELOG.md`.

## Contract
- `App\Models\Queue`:
  `public function prefixForPriority(int $priority): string` (custom map or
  default); a public static default resolver/constant is welcome (e.g.
  `Queue::DEFAULT_PREFIX_MAP = [0 => 'N', 10 => 'P', 20 => 'E']`,
  `Queue::defaultPrefixFor(int)`); attribute `priority_prefix_map` (array
  cast, nullable).
- `App\Models\Ticket`: `issue_date` cast to `date` (so
  `$ticket->issue_date->toDateString()` works).
- `App\Actions\UpdateQueue::__invoke(Queue $queue, User $actor, ?string $name = null, ?string $slug = null, ?bool $isActive = null, ?array $priorityPrefixMap = null): Queue`.
- `App\Actions\IssueTicket` signature unchanged.
- `Queue::factory()->create(['priority_prefix_map' => [...]])` must work.

## Out of scope
UI for editing the map, totem API changes, per-entity (instead of per-queue)
maps, call ordering (still by numeric priority, not by letter).

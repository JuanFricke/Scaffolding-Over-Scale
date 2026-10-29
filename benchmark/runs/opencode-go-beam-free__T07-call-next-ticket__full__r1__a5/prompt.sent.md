You are working autonomously in a non-interactive session: nobody will answer questions, review a plan or confirm anything. Do not ask for clarification or permission. When something is ambiguous, make a reasonable decision consistent with the task and the existing code, and keep going until the task is fully implemented.

The task:

# Call the next waiting ticket of a queue

## Context

Tickets can be issued into a queue (`App\Actions\IssueTicket`) and a single
ticket can be marked as called (`Ticket::call()`), but nothing decides
**which** ticket an attendant should call next. The attendant's call panel
will have three buttons (see `docs/business-rules.md`, "Ordering and
Fairness" and "Call Panel"): **Next** (full ordering), **Priority** (only
priority tickets) and **Normal** (only normal tickets). Implement the domain
action behind those buttons. No HTTP/Livewire and no authorization in this
task (the caller is trusted).

## Rules

A ticket is **normal** when `priority = 0` and **priority** when
`priority > 0` (higher value = more important).

1. Only `waiting` tickets of the given queue are candidates; tickets of other
   queues are never selected, and an already called ticket is never called
   again.
2. Ordering is deterministic: higher `priority` first, then oldest
   `issued_at`, then lowest `id` as the final tie-break.
3. Modes:
   - **any**: full ordering plus the fairness rule below.
   - **priority_only**: only priority tickets, full ordering, fairness ignored.
   - **normal_only**: only normal tickets, oldest first, fairness ignored.
4. **Fairness (any mode only)**: a normal ticket may not wait behind more than
   3 consecutive priority calls. Look at the last 3 tickets called in this
   queue (most recent first by `called_at`, then by `id`): if there are 3 of
   them, all are priority tickets, and at least one normal ticket is waiting,
   the call is restricted to normal tickets (the oldest normal is called).
   Calls made in `priority_only`/`normal_only` mode count in that history. A
   normal call resets the streak. If no normal is waiting, priority tickets
   keep being called.
5. Calling from an inactive queue is rejected and changes nothing. Read the
   queue state from the database inside the transaction (lock the queue row),
   not from the passed model instance (it may be stale).
6. If no ticket is eligible for the requested mode (empty queue, only normals
   in `priority_only`, only priority in `normal_only`), throw a dedicated
   exception.
7. Exactly-once: inside a transaction, lock the queue row, pick the
   candidate, then lock the candidate row and re-check it is still
   `waiting` (it may have been called concurrently through `Ticket::call()`,
   which does not lock the queue); if not, skip it and pick the next one.
8. Mark the winner `called`, set `called_at = now()` and `called_by_user_id`,
   and return the updated ticket model (its `status`, `called_at`,
   `called_by_user_id` must already reflect the call). Respect the ticket's
   write-once rule (only `status`, `called_at`, `called_by_user_id` change).
9. Update `docs/business-rules.md` and `docs/architecture.md` ("Call the next
   ticket") to describe the implementation.

## Contract

- Enum `App\Enums\CallMode` (string-backed): `Any = 'any'`,
  `PriorityOnly = 'priority_only'`, `NormalOnly = 'normal_only'`.
- Exception `App\Exceptions\NoWaitingTicketsException` (extends
  `RuntimeException`).
- Reuse `App\Exceptions\InactiveQueueException` for inactive queues.
- Invokable action `App\Actions\CallNextTicket`, constructed without
  arguments:
  `__invoke(App\Models\Queue $queue, App\Models\User $calledBy, CallMode $mode = CallMode::Any): App\Models\Ticket`.

## Out of scope

Authorization (who may call), per-queue permissions, HTTP endpoints,
Livewire call panel, display/TV broadcasting, recall/skip.

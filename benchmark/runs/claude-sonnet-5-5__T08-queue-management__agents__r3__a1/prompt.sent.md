You are working autonomously in a non-interactive session: nobody will answer questions, review a plan or confirm anything. Do not ask for clarification or permission. When something is ambiguous, make a reasonable decision consistent with the task and the existing code, and keep going until the task is fully implemented.

The task:

# Queue management and who may call tickets

## Context

Queues and tickets exist (`IssueTicket`, `CallNextTicket`, `Ticket::call()`),
but queues can only be created through factories and **anyone** can call
tickets (`CallNextTicket` has no authorization; `Ticket::call()` only checks
entity membership). Managers (owner/admin of the entity) need to create,
rename and deactivate queues, and to decide which **employees** may call
tickets on which queue. `docs/database-schema.md` already sketches a
`queue_access` join table ("Employee: granular permissions per queue"). This
task is the domain/authorization slice only: actions and policy, no UI.

## Requirements

### Queue lifecycle (owner/admin only)
1. Create a queue in an entity with a name and an optional slug. Name is
   trimmed, 1-255 chars. Slug defaults to `Str::slug(name)`
   ("Atendimento Geral" -> `atendimento-geral`); an explicit slug is also
   slugified. New queues are active.
2. Slugs are unique **within an entity** (the same slug may exist in another
   entity). A duplicate is a `ValidationException` (also when the DB unique
   index fires because of a race), never a raw `QueryException`.
3. Update a queue: any combination of new name, new slug, and active flag
   (named, nullable parameters; `null` means "leave unchanged"). Keeping the
   queue's own slug is fine; taking another queue's slug is a
   `ValidationException`.
4. **No hard delete.** Deactivation (`is_active = false`) is how a queue is
   retired: its tickets are preserved, and issuing or calling on it keeps
   failing with `InactiveQueueException`. Do not create any delete/remove/
   destroy queue action.
5. Employees, members of other entities and non-members get
   `Illuminate\Auth\Access\AuthorizationException`; nothing is written.

### Per-queue access grants
1. New table `queue_access`: `id`, `entity_membership_id` (FK, cascade on
   delete), `queue_id` (FK, cascade on delete), `permissions` (JSON array of
   strings), timestamps; unique `(entity_membership_id, queue_id)`.
2. The only permission today is `call`.
3. A manager sets the permissions of a membership on a queue: a non-empty
   list upserts the row; an empty list revokes (deletes) it. Unknown strings
   or non-string entries -> `ValidationException`, nothing stored. Membership
   and queue of different entities -> `ValidationException`. Non-managers
   (including an employee granting themselves) -> `AuthorizationException`.
4. Audit trail on the `audit` log channel: message `queue.access.granted` on
   grant and `queue.access.revoked` on revoke, both with context including
   `actor_id` (the manager's user id), `queue_id` and `entity_membership_id`.
   Do not log a revoke when there was no row to delete.

### Authorization policy (single source of truth)
A policy for `Queue` with abilities:
- `create` (with the entity as argument): owner/admin of that entity.
- `update`, `manageAccess`: owner/admin of the queue's entity.
- `call`: owner/admin of the queue's entity always (no grant row needed); an
  employee only with a `queue_access` row for **that** queue whose
  `permissions` is an array containing `call` (a corrupted non-array value
  denies); everyone else denied.

Both call paths must enforce `call`:
- `CallNextTicket`: after locking the queue and checking it is active, authorize
  the caller; unauthorized -> `AuthorizationException` and no ticket changes.
  This applies to every call mode.
- `Ticket::call()`: lock, reject inactive queues with `InactiveQueueException`,
  then authorize (`AuthorizationException`, even when the ticket was already
  called), then the existing "only waiting tickets" `LogicException`.

Update `docs/business-rules.md`, `docs/database-schema.md` and the
`CHANGELOG.md` "Added" section.

## Contract
- `App\Actions\CreateQueue`:
  `__invoke(Entity $entity, User $actor, string $name, ?string $slug = null): Queue`.
- `App\Actions\UpdateQueue`:
  `__invoke(Queue $queue, User $actor, ?string $name = null, ?string $slug = null, ?bool $isActive = null): Queue`
  (called with named arguments `name:`, `slug:`, `isActive:`).
- `App\Actions\SetQueueAccess`:
  `__invoke(EntityMembership $targetMembership, Queue $queue, User $actor, array $permissions): void`.
- Enum `App\Enums\QueuePermission` with exactly one case `Call = 'call'`.
- Model `App\Models\QueueAccess` (table `queue_access`, `HasFactory`,
  `permissions` cast to array, relations `membership()` and `queue()`).
- Factory `QueueAccess::factory()` defaulting to a `call` grant; the created
  membership and queue must belong to the same entity.
- Policy `App\Policies\QueuePolicy` (auto-discovered) with `create`,
  `update`, `manageAccess`, `call`; used via
  `Gate::forUser($user)->allows('create', [Queue::class, $entity])` etc.
- All actions are constructed without arguments (`new CreateQueue`).

## Out of scope
Livewire/HTTP screens for queues or access, other permissions than `call`,
queue deletion, plan limits on the number of queues.

You are working autonomously in a non-interactive session: nobody will answer questions, review a plan or confirm anything. Do not ask for clarification or permission. When something is ambiguous, make a reasonable decision consistent with the task and the existing code, and keep going until the task is fully implemented.

The task:

# Queue management UI and attendant serve panel

## Context

The domain slice for queues is done: `CreateQueue`, `UpdateQueue` (no delete;
deactivation instead), `SetQueueAccess` (per-queue `call` grants with audit
log), `QueuePolicy` (`create`, `update`, `manageAccess`, `call`) and
`CallNextTicket` (modes `any`/`priority_only`/`normal_only`, fairness,
authorization). Nothing is reachable from the browser. Build two tenant pages
in the style of the existing members page (Bulma boxes, row buttons, modals,
all text from `lang/*/ui.php` in pt_BR and en), add them to the navbar
dropdown, and split the members page into tabs. Domain actions stay the single
source of rules: the components call them and surface their errors.
Every id coming from the client is untrusted: always resolve queues and
memberships **scoped to the current entity** (`$entity->queues()->findOrFail()`,
`$entity->memberships()->findOrFail()`), so foreign ids raise a not-found
exception and change nothing.

## Queues page (owner/admin)

Route `entity.queues` (`/e/{entity:slug}/queues`, inside the existing
`current_entity` group). Mount authorizes `create` on `Queue` for the entity;
employees get 403 (component and route).

- **List**: one row per queue, styled like member rows: a
  `<button class="button is-fullwidth p-3 mb-2" ...>` with
  `wire:click="openQueue(<id>)"` showing name and active/inactive status. While
  no modal is open the page must not render any other per-row action (no
  `startRename`, `toggleActive` or `openAccess` handlers in the HTML).
- **Create modal**: `openCreate()` sets `creating = true`; field `name`;
  `create()` calls `CreateQueue` (slug always derived from the name), on success
  resets `name` to `''` and `creating` to `false`. Domain validation errors
  (including a duplicate derived slug) are shown on `name`.
- **Detail modal**: `openQueue($id)` sets `viewingQueueId`; shows the title
  `ui.queues_details` and buttons for rename (`ui.queues_rename`), deactivate
  (`ui.queues_deactivate`, or reactivate) and access (`ui.queues_access_button`).
  `closeQueue()` resets `viewingQueueId` to `null` (and every nested state).
- **Rename**: `startRename($id)` sets the draft `renameName`; `rename()` calls
  `UpdateQueue` with the new name **and** the slug re-derived from it (renaming
  "Old" to "New" yields slug `new`); a collision is an error on `renameName`.
- **Deactivate/reactivate**: `confirmToggle()` (for the queue being viewed)
  sets `confirmingToggle = true` and renders a confirmation modal with
  `ui.queues_toggle_title` and `ui.queues_toggle_message` (`:queue` = name),
  never a `wire:confirm` browser dialog; `cancelToggle()` closes it;
  `toggleActive($id)` flips `is_active` through `UpdateQueue` and resets
  `confirmingToggle`.
- **Access modal**: `openAccess($id)` sets `accessQueueId` and
  `managingAccess = true` and lists the entity's memberships with
  grant/revoke buttons (managers shown as calling without a grant).
  `grantAccess($membershipId)` / `revokeAccess($membershipId)` call
  `SetQueueAccess` with `[QueuePermission::Call]` / `[]` (which writes the
  audit log). The view receives `accessQueue` (the scoped queue or `null`) and
  `accessGrants` (collection, empty when `accessQueue` is null), so a tampered
  `accessQueueId` pointing at a foreign queue discloses nothing.
- Texts: `ui.queues_title` ("Filas de :entity" / "Queues of :entity"),
  `ui.queues_create` ("Criar fila" / "Create queue"); interactive controls have
  `aria-label`s.

## Serve panel (any member)

Route `entity.serve` (`/e/{entity:slug}/serve`). Mount authorizes `view` on the
entity.

- Public state: `selectedQueueId` (`?int`, defaults on mount to the first
  callable queue or `null`), `mode` (string, one of `any`, `priority_only`,
  `normal_only`, default `any`), `lastCalledTicketId` (`?int`, not writable by
  the client), `notice` (`?string`).
- **Callable queues** selector: active queues of the entity the user may call
  (all for owner/admin; for employees only queues with a `call` grant).
- **Waiting list** for the selected queue, in call order (priority desc,
  issued_at, id; filtered by mode; first 30), with code, priority, issue time
  and the channel translated via `ui.channel_totem|virtual|printed`. When the
  selected queue is foreign, missing, or the user may not `call` it, show no
  tickets, only `ui.serve_empty`; the same text is the empty state.
- **`callNext()`**: no selection -> `notice = __('ui.serve_empty')`, no error;
  selected id resolved scoped to the entity (foreign -> not found); calls
  `CallNextTicket($queue, auth()->user(), CallMode::from($mode))`.
  `InactiveQueueException` -> `notice = __('ui.serve_inactive')`;
  `NoWaitingTicketsException` -> `notice = __('ui.serve_empty')`;
  `AuthorizationException` is not caught (403, nothing changes). On success set
  `lastCalledTicketId` and show `__('ui.serve_last_called', ['code' => ...])`
  ("Atendendo :code." / "Now serving :code."). Rate-limit successful calls per
  user and entity (e.g. 10/min).
- Button `ui.serve_call_next` ("Chamar próximo" / "Call next") with
  `aria-label`.

## Members page tabs

`App\Livewire\Entity\Members` gets `public string $activeTab = 'members'` and
`setActiveTab(string $tab)` accepting only `members` or `invites` (anything
else is ignored). Render a Bulma tabs bar with `role="tablist"` and labels
`ui.members_tab_members` ("Membros"/"Members") and `ui.members_tab_invites`
("Convites"/"Invites"). The members list is on the first tab; the invite form
(`inviteEmail`, `ui.members_invite_title`, send button) and pending invites are
rendered **only** on the invites tab.

## Navigation

Add `ui.nav_queues` ("Filas"/"Queues", managers only) and `ui.nav_serve`
("Atender"/"Serve") to the navbar dropdown.

## Contract
- `App\Livewire\Entity\Queues` (mount param `entity`): properties `name`,
  `creating`, `viewingQueueId`, `confirmingToggle`, `editingQueueId`,
  `renameName`, `accessQueueId`, `managingAccess`; methods `openCreate`,
  `closeCreate`, `create`, `openQueue`, `closeQueue`, `startRename`,
  `cancelRename`, `rename`, `confirmToggle`, `cancelToggle`, `toggleActive`,
  `openAccess`, `closeAccess`, `grantAccess`, `revokeAccess`; view data
  `accessQueue`, `accessGrants`.
- `App\Livewire\Entity\Serve` (mount param `entity`): `selectedQueueId`,
  `mode`, `lastCalledTicketId`, `notice`, `callNext()`.
- Routes `entity.queues`, `entity.serve`.
- Lang keys (both locales): `queues_title`, `queues_create`, `queues_details`,
  `queues_rename`, `queues_deactivate`, `queues_access_button`,
  `queues_toggle_title`, `queues_toggle_message`, `serve_call_next`,
  `serve_last_called`, `serve_empty`, `serve_inactive`, `channel_totem`,
  `channel_virtual`, `channel_printed`, `members_tab_members`,
  `members_tab_invites`, `nav_queues`, `nav_serve`.

## Out of scope
TV/display screen, real-time broadcasting, ticket issuance UI, totem API,
changing domain rules.

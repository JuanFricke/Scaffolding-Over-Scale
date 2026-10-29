You are working autonomously in a non-interactive session: nobody will answer questions, review a plan or confirm anything. Do not ask for clarification or permission. When something is ambiguous, make a reasonable decision consistent with the task and the existing code, and keep going until the task is fully implemented.

The task:

# Entities: data model, members management and owner-only settings

## Context

PegaFila is multi-tenant: a business (an **entity**) owns queues, totems and
staff. Users already authenticate (login, register, e-mail verification and a
`/home` route exist). A user relates to entities through **memberships** with
a role: `owner` (exactly one per entity, the only one who manages
settings/billing), `admin` (manager) and `employee`. This task builds the data
model and policies, a way to pick the entity a user works in, and the
management pages of an entity: dashboard, members and settings (including
ownership transfer). All screen text comes from `lang/*/ui.php` (pt_BR and en).
Read `docs/database-schema.md` and update it.

## Part 1: data model and policies

- `entities`: `id`, `name`, `slug` (unique index named `entities_slug_unique`),
  timestamps, soft deletes. Routes bind entities by `slug`.
- `entity_memberships`: `id`, `entity_id`, `user_id` (FKs, cascade on delete),
  `role` string defaulting to `employee`, timestamps, unique
  `(entity_id, user_id)` named `entity_memberships_entity_user_unique`.
- The database itself must reject a second owner per entity, portably on
  SQLite and MariaDB: a stored generated column `owner_seq` (1 when
  `role = 'owner'`, otherwise NULL) and a unique index on
  `(entity_id, owner_seq)` named `entity_memberships_one_owner`.
- Policies. Entity: anyone authenticated may create; any member may view;
  owner and admin may update/delete; only the owner may manage settings.
  Membership: any member of that entity may view; owner/admin may assign
  roles; delete is never allowed for the owner's membership, allowed for
  self-removal, otherwise only owner/admin.

## Part 2: picking an entity and the management pages

- `POST entity.pick` stores the entity in `session('current_entity_id')` for an
  entity the user belongs to (403 otherwise, session untouched), writes an
  audit log line on the `audit` log channel, and redirects to that entity's
  dashboard.
- Every page below is a Livewire full-page component with mount parameter
  `entity` (bound by slug), requires `auth` + `verified`, and authorizes in
  `mount()` through the policies, so a non-member (or a member lacking the
  role) gets 403 even when the session points at another entity they belong to.
- **Dashboard**: shows the entity name and a welcome; links to members and,
  for the owner only, to settings (the settings URL must not appear for
  non-owners); owner notice "Você é o proprietário desta entidade."
  (en "You are the owner of this entity.").
- **Members** (`Members`): `addMember()` adds an existing user by `email`
  (rule `exists:users,email`) as employee; a duplicate member is an error on
  `email`. `assignRole($membershipId, $role)` accepts only `admin`/`employee`
  (anything else, e.g. `owner`, is a validation error on `role`).
  `removeMember($membershipId)`: never removes the owner, never removes the
  last manager (owner/admin) -> 403. Employees get 403 on add/assign.
- **Settings** (`Settings`, owner only, already enforced at mount; the bound
  entity must not be swappable from the client): `save()` edits `name` and
  `slug` (slug unique except itself); `delete()` soft-deletes the entity,
  deletes its memberships, clears the session if it was the current entity,
  redirects; `transfer()` moves ownership to `targetMembershipId`, which must
  be an **admin of this entity** other than the caller: demote owner -> admin
  and promote target -> owner atomically, redirect to the dashboard; otherwise
  403 (also 403 if the owner row vanished in the meantime). Section title
  "Transferir propriedade" (en "Transfer ownership").

## Contract

- `App\Models\Entity` (`HasFactory`, `SoftDeletes`, `getRouteKeyName()` =
  `slug`, `memberships()`, `users()`, `owner()` relation returning the owner
  membership query).
- `App\Models\EntityMembership` (`HasFactory`; `role` cast to `UserRole`;
  local scopes `owner()`, `admin()`, `employee()`; `entity()`, `user()`).
- Enum `App\Models\UserRole`: `Owner = 'owner'`, `Admin = 'admin'`,
  `Employee = 'employee'`; static `manageable()` returns `[Admin, Employee]`.
- `User::memberships()`, `User::entities()`,
  `User::membershipFor(int $entityId): ?EntityMembership`.
- Factories: `Entity::factory()` (name, unique slug);
  `EntityMembership::factory()` (creates its entity and user, role employee)
  with states `owner()`, `admin()`, `employee()`.
- `App\Policies\EntityPolicy`: `create(User)`, `view`, `update`, `delete`,
  `manageSettings` (each `(User, Entity): bool`).
  `App\Policies\EntityMembershipPolicy`: `view`, `assignRole`, `delete` (each
  `(User, EntityMembership): bool`). Both constructed without arguments.
- Livewire `App\Livewire\Entity\Dashboard`, `App\Livewire\Entity\Members`
  (public `string $email`; `addMember()`, `assignRole($membershipId, string
  $role)`, `removeMember($membershipId)`), `App\Livewire\Entity\Settings`
  (public `$name`, `$slug`, `$targetMembershipId`; `save()`, `delete()`,
  `transfer()`), all with mount parameter `entity`.
- Routes: `entity.pick` (POST `/e/{entity:slug}/pick`), `entity.dashboard`
  (GET `/e/{entity:slug}`), `entity.members` (GET `/e/{entity:slug}/membros`),
  `entity.settings` (GET `/e/{entity:slug}/settings`).
- Lang keys (both locales): `ui.nav_members` ("Membros"), `ui.nav_settings`
  ("Configurações") and the dashboard/settings texts quoted above.

## Out of scope

Do not build these (they belong to other tasks): onboarding (entity
creation), the entity switcher page, a session-guard middleware and the
`/home` dispatch into an entity, a browser-language (`Accept-Language`) locale
middleware, the navbar redesign, card-layout changes. Also out: e-mail
invitations, queues/tickets, billing, restoring deleted entities.

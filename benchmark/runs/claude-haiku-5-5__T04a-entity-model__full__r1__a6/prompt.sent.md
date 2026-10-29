You are working autonomously in a non-interactive session: nobody will answer questions, review a plan or confirm anything. Do not ask for clarification or permission. When something is ambiguous, make a reasonable decision consistent with the task and the existing code, and keep going until the task is fully implemented.

The task:

# Entity data model: tenants, memberships, roles and policies

## Context

PegaFila is multi-tenant: a business (an **entity**) owns queues, totems and
staff. Users already authenticate; they will work inside one entity at a time.
A user relates to entities through **memberships** with a role: `owner`
(exactly one per entity, the only one who manages settings/billing), `admin`
(manager) and `employee`. This task adds only the persistence, the Eloquent
model and the authorization policies; no routes, pages or session handling.
Read `docs/database-schema.md` and update it to reflect what you implement
(it still describes an `owner_membership_id` FK that this design replaces).

## Requirements

- `entities`: `id`, `name`, `slug` (unique index named `entities_slug_unique`),
  timestamps, soft deletes. Entities are bound in routes by `slug`.
- `entity_memberships`: `id`, `entity_id`, `user_id` (FKs, cascade on delete),
  `role` string defaulting to `employee`, timestamps, unique
  `(entity_id, user_id)` named `entity_memberships_entity_user_unique`.
- The database itself must reject a second owner per entity, portably on
  SQLite and MariaDB: add a stored generated column `owner_seq` (1 when
  `role = 'owner'`, otherwise NULL) and a unique index on
  `(entity_id, owner_seq)` named `entity_memberships_one_owner`. Different
  entities may each have their own owner; any number of non-owners is fine.
- Authorization rules:
  - Entity: anyone authenticated may create one; any member may view; owner and
    admin may update/delete; only the owner may manage settings. Non-members
    get nothing.
  - Membership: any member of the same entity may view a membership; owner and
    admin may assign roles; deleting a membership is never allowed for the
    owner's membership, is allowed for self-removal, and otherwise only for
    owner/admin of that entity.

## Contract

- `App\Models\Entity` (`HasFactory`, `SoftDeletes`, `getRouteKeyName()` =
  `slug`, `memberships()`, `users()` (many-to-many through memberships),
  `owner()` relation returning the owner membership query, so
  `$entity->owner()->first()` is the owner `EntityMembership` or null).
- `App\Models\EntityMembership` (`HasFactory`; `role` cast to `UserRole`;
  local scopes `owner()`, `admin()`, `employee()`; relations `entity()`,
  `user()`).
- Enum `App\Models\UserRole`: `Owner = 'owner'`, `Admin = 'admin'`,
  `Employee = 'employee'`; static `manageable()` returns `[Admin, Employee]`.
- `App\Models\User::memberships()`, `User::entities()`,
  `User::membershipFor(int $entityId): ?EntityMembership`.
- Factories: `Entity::factory()` (non-empty name, unique slug);
  `EntityMembership::factory()` (creates its entity and user, role employee)
  with states `owner()`, `admin()`, `employee()`.
- `App\Policies\EntityPolicy` (constructed without arguments):
  `create(User)`, `view(User, Entity)`, `update(User, Entity)`,
  `delete(User, Entity)`, `manageSettings(User, Entity)`, all returning bool.
- `App\Policies\EntityMembershipPolicy` (constructed without arguments):
  `view(User, EntityMembership)`, `assignRole(User, EntityMembership)`,
  `delete(User, EntityMembership)`, all returning bool.

## Out of scope

Do not build these (they belong to other tasks): the tenant session
(`current_entity_id`, middleware, entity switcher), onboarding, dashboard,
members and settings pages, routes, navbar, browser-language locale
middleware, translations. Also out: invitations, queues/tickets, billing.

You are working autonomously in a non-interactive session: nobody will answer questions, review a plan or confirm anything. Do not ask for clarification or permission. When something is ambiguous, make a reasonable decision consistent with the task and the existing code, and keep going until the task is fully implemented.

The task:

# Entities: data model, onboarding and the tenant session

## Context

PegaFila is multi-tenant: a business (an **entity**) owns queues, totems and
staff. Users already authenticate (login, register, e-mail verification and a
`/home` route exist); they must now work inside one entity at a time. A user
relates to entities through **memberships** with a role: `owner` (exactly one
per entity), `admin` (manager) and `employee`. This task builds the data model
and policies, the onboarding page that creates a user's first entity, the
tenant session (which entity the user is working in), the entity switcher and
a minimal entity dashboard. All screen text comes from `lang/*/ui.php`
(pt_BR and en). Read `docs/database-schema.md` and update it.

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

## Part 2: tenant session, onboarding, switcher, dashboard

- `session('current_entity_id')` holds the current entity. Only the HTTP layer
  reads it: a `current_entity` route middleware resolves it into an in-request
  tenant context; when the user is not a member of the session entity it
  aborts 403. When the session is empty: 0 memberships -> `onboarding`;
  exactly 1 -> set the session and continue; more than 1 -> `entity.switcher`.
- `GET /home` (keeps its name `home`, `auth` + `verified`) now dispatches the
  same way: 0 -> onboarding, 1 -> set the session and redirect to that
  entity's dashboard (any role), >1 -> switcher.
- `POST entity.pick` sets the session for an entity the user belongs to (403
  otherwise, session untouched), writes an audit log line on the `audit` log
  channel, and redirects to that entity's dashboard.
- **Onboarding** (Livewire full-page `CreateEntity`): field `name` (required).
  Creates the entity with a unique slug derived from the name (`acme-corp`,
  then `acme-corp-2`, ...) and makes the creator its `owner` in one
  transaction; the creator is always owner (no client input can change that).
  It must retry when the slug collides at insert time (a concurrent request
  inserted the same slug after the uniqueness check). Then it logs
  `Log::channel('audit')->info('Entity created', ['entity_id' => ..,
  'actor_id' => ..])`, sets the session and redirects to the dashboard.
  Title "Crie sua entidade" / heading "Crie sua empresa" (en "Create your
  entity" / "Create your company").
- **Dashboard** (Livewire full-page `Dashboard`, `auth` + `verified` +
  `current_entity`): shows the entity name. A user who is not a member of the
  requested entity gets 403, even with a valid session for another entity.
- **Switcher** (plain Blade page using the existing `default-page` layout):
  lists only the user's entities, each as a POST form to `entity.pick`; the
  current one is a `button is-fullwidth is-link` with `data-current="1"`,
  others `button is-fullwidth is-light` (no tags). Title "Trocar de entidade"
  (en "Switch entity").
- **Navbar entry** (in the `default-page` layout): for an authenticated user
  show the user's name (already there) and a link to `entity.switcher` only
  when the user has more than one membership.
- All new pages require `auth` + `verified`; guests are redirected to `login`.

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
- Livewire `App\Livewire\Entity\CreateEntity` (public `string $name`,
  `submit()`, and an overridable
  `protected function uniqueSlug(string $name): string` that `submit()` calls
  on every attempt); `App\Livewire\Entity\Dashboard` (mount parameter
  `entity`).
- Routes: `onboarding` (GET `/onboarding`), `entity.switcher` (GET
  `/e/switcher`), `entity.pick` (POST `/e/{entity:slug}/pick`),
  `entity.dashboard` (GET `/e/{entity:slug}`); middleware alias
  `current_entity`.
- Lang key `ui.switch_entity` and the onboarding texts above, both locales.

## Out of scope

Do not build these (they belong to other tasks): the members page and the
settings page (edit/delete/ownership transfer) and their routes, links from the
dashboard to them, a browser-language (`Accept-Language`) locale middleware,
the Alpine dropdown navbar redesign, card-layout centering changes. Also out:
invitations, queues/tickets, billing, restoring deleted entities.

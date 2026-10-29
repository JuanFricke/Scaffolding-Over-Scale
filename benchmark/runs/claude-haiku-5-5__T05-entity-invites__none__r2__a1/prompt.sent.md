You are working autonomously in a non-interactive session: nobody will answer questions, review a plan or confirm anything. Do not ask for clarification or permission. When something is ambiguous, make a reasonable decision consistent with the task and the existing code, and keep going until the task is fully implemented.

The task:

# Invite-only membership for entities

## Context

Today a manager adds an existing user to an entity instantly by e-mail
(`Members::addMember()`), and roles are changed with one click. That leaks
which e-mails have accounts and lets anyone be added without consent. Replace
it with **invites**: a manager (owner or admin) invites an e-mail address with
a role; the invitee receives an e-mail, signs in (or registers) with that
address and accepts or declines the invite. Membership exists only after
acceptance. While at it, the members page becomes manager-only and gets a
member detail modal with an explicit "save role" and a confirmation modal for
removal.

## Requirements

### Invites
1. New table `entity_invites`: `entity_id` (FK, cascade), `invited_by`
   (nullable FK to users), `email`, `role` (default `employee`),
   `expires_at`, `accepted_at` (nullable), timestamps; unique
   `(entity_id, email)`. E-mails are always stored lowercase and trimmed
   (normalize in the model so every write path agrees).
2. Invites expire after 7 days. An invite is pending when not accepted and not
   expired.
3. `sendInvite()` on the members page: authorize as manager; validate
   `inviteEmail` (`required|email:strict|max:255`) and `inviteRole`
   (`required|in:admin,employee`; `owner` is never invitable); then reject with
   an error on `inviteEmail` when the address already belongs to a member, or
   when a pending invite for it already exists in this entity (an expired one
   may be replaced). A unique-constraint violation at insert time (race) must
   also become an error on `inviteEmail`, never a 500. Then create the invite,
   queue the invite e-mail to that address, write an audit log, reset the form.
   Rate limit successful invites per manager and entity (10 per hour); invalid
   input must not consume the quota.
4. `cancelInvite($inviteId)`: managers delete an invite of their entity.
5. A `PendingInvites` Livewire component lists the signed-in user's pending
   invites (matching e-mail case-insensitively) with Accept / Decline:
   - `accept($inviteId)`: only the invitee (e-mail match) may accept, else 403;
     expired -> error on key `invite`; already accepted -> no-op without
     errors (idempotent); otherwise create the membership with the invite role
     (never a duplicate), set `accepted_at`, set the tenant session and redirect
     to the entity dashboard.
   - `decline($inviteId)`: only the invitee; deletes the invite.
6. The pending invites list is shown on the **entity switcher** page and on
   **onboarding**. On onboarding it appears inside the same box, after the
   create form, separated by an `<hr>`, titled `ui.invites_title`
   ("Pending invites" / "Convites pendentes"), buttons "Accept"/"Aceitar" and
   "Decline"/"Recusar". When there are no invites, render no `<hr>` at all.

### Invite e-mail
A queued markdown mailable using the existing PegaFila mail theme, markdown
view `emails.entity-invite`, rendering: a greeting, "You are invited to join
:entity as :role." (role translated via `ui.role_*`: en "Admin", pt_BR
"Administrador"), the instruction
"Access the link below to sign in and accept your invite:", a button
"Sign in to PegaFila" pointing to `route('login')`, the expiry date, and the
signature "Team PegaFila". All strings are translation keys; pt_BR
translations in `lang/pt_BR.json` must produce "Você foi convidado...",
"Acesse o link abaixo para entrar e aceitar seu convite:", "Entrar no PegaFila"
and "Time PegaFila". Subject: "You are invited to :entity".

### Members page (manager-only)
1. Mounting the members page requires owner/admin; employees get 403 (both
   the Livewire component and the `entity.members` route).
2. Remove `addMember()`/`assignRole()`; the page shows the invite form (field
   `inviteEmail`, role select), the pending invites list, and the members list.
   Title "Membros de :entity" / "Members of :entity"; invite section
   "Convidar membro" / "Invite member"; submit "Enviar convite" / "Send invite".
   A validation error on the invite e-mail renders exactly once
   (one `help is-danger` element).
3. `openMember($membershipId)` opens a Bulma modal for a membership of this
   entity (a foreign membership must fail with a not-found exception and
   select nothing); sets `selectedMembershipId` and prefills the draft
   `memberRole` with the current role. The modal header is
   `<p class="modal-card-title">{{ __('ui.members_details') }}</p>` (not the
   member's name); the body shows the member's name first, then e-mail and
   role. The role `<select>` has no empty option.
4. Changing `memberRole` persists nothing until `saveRole()`: validates
   `memberRole` in `admin,employee` (owner -> error on `memberRole`), the
   owner's membership is immutable (403), and the last manager cannot be
   demoted (403).
5. `confirmRemoval()` sets `confirmingRemoval = true` and shows a confirmation
   modal titled `ui.members_remove_title` (no `wire:confirm` browser dialog);
   `cancelRemoval()` closes it; `removeMember($membershipId)` keeps the
   existing rules (never the owner, never the last manager) and on success
   resets `selectedMembershipId` to `null` and `confirmingRemoval` to `false`.

## Contract
- `App\Models\EntityInvite` (`HasFactory`; casts `role` to
  `App\Models\UserRole`, `expires_at`/`accepted_at` datetime; `entity()`).
- `Entity::invites()` relation.
- Factory `EntityInvite::factory()` (defaults: an entity, a unique e-mail,
  role employee, expires in 7 days) with state `expired()`.
- `App\Mail\EntityInviteMail` (constructor `(EntityInvite $invite)`,
  `ShouldQueue`, `content()->markdown === 'emails.entity-invite'`).
- `App\Livewire\Entity\Members`: public `inviteEmail`, `inviteRole`,
  `selectedMembershipId` (`?int`), `memberRole`, `confirmingRemoval` (`bool`);
  methods `sendInvite()`, `cancelInvite($id)`, `openMember($id)`, `saveRole()`,
  `confirmRemoval()`, `cancelRemoval()`, `removeMember($id)`.
- `App\Livewire\Entity\PendingInvites`: `accept($id)`, `decline($id)`.
- Lang keys: `ui.invites_title`, `ui.members_details`,
  `ui.members_remove_title`, `ui.role_owner|admin|employee`, plus the texts
  quoted above in both locales.

## Out of scope
Signed invite links/tokens, inviting users into multiple entities at once,
resending invites.

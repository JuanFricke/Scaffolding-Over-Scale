# Rubric

Score each dimension from 1 to 5. The anchors define 1, 3 and 5; use 2 and 4 for changes in
between. Every score needs evidence (`path:line` or a quoted fragment).

| id | dimension | 5 | 3 | 1 |
|---|---|---|---|---|
| `requirements` | **Meets the task**: every requirement and contract in `task.md` is implemented, edge cases included | all requirements and the contract met; edge cases handled | main path done; some requirement, edge case or contract detail missing or wrong | most requirements missing, wrong contract, or the code cannot work (syntax error, wrong API) |
| `conventions` | **Project conventions** (`conventions.md`): Actions for domain writes, `#[Validate]` in Livewire, policies for authorization, generated migrations, `$fillable`/`$guarded`, Blade components, Bulma, docs kept in sync, sibling style | follows every convention that applies | follows most; one or two clear deviations | ignores the conventions (service layers, logic in views, hand-rolled patterns the project already has) |
| `security` | **Security**: server-side authorization of every action, validation of all input, escaping (`{{ }}`), mass-assignment safety, Livewire policy (locked/validated properties, no trust in client parameters), no secrets or unsafe output | no weakness found; authorization and validation everywhere they are needed | a gap with limited impact (one action not authorized but guarded elsewhere, a field not validated) | exploitable flaw (unauthorized write, unescaped user input, trusting client-side IDs) |
| `tests` | **Tests**: the change ships with Pest/PHPUnit tests that cover its requirements, including unauthorized-call and tamper tests for Livewire actions; tests are meaningful, not weakened | tests cover all requirements and the failure/authorization paths | some tests, happy path only, or important cases missing | no tests for new behavior, or existing tests weakened/deleted |
| `simplicity` | **Simplicity** ("write less, correctly"): reuses what exists, no speculative abstractions, no duplication, minimum code that fully works | lean and direct; reuses existing code | some duplication or unnecessary indirection | heavy over-engineering or copy-paste |
| `readability` | **Readability and maintainability**: clear names, small focused methods, consistent with sibling files, no dead code or leftover debugging | easy to read and change | understandable with effort; some long methods or unclear names | hard to follow; dead code, debug output, inconsistent style |
| `scope` | **Scope discipline**: only what the task asks; no unrelated refactors, files or features | everything in the diff serves the task | a few unrelated edits | large unrelated changes or features not asked for |

`overall`: 1–5, would you approve this pull request?
- 5: approve as is.
- 4: approve with nits.
- 3: needs changes before merging.
- 2: needs substantial rework.
- 1: reject.

`confidence`: `high`, `medium` or `low`, about your own review. Use `low` when the diff was
summarized or you could not verify something important.

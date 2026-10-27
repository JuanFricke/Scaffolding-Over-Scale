# Harness snapshot v1 — provenance

- Source repository: `PegaFila/PegaFilaWeb` (**private**)
- Tag: `tcc-baseline-v1` (annotated tag)
- Commit: `25491d8ec9a37a4d7277fe242c8f40b5f1c84ca9` (committed 2026-10-26)
- Vendored on: 2026-10-27
- Command used:

  ```bash
  git -C ../PegaFilaWeb archive tcc-baseline-v1 AGENTS.md CLAUDE.md opencode.json .claude/settings.json ai \
    | tar -x -C benchmark/harness/v1
  ```

Contents: `AGENTS.md`, `CLAUDE.md`, `opencode.json`, `.claude/settings.json`, `ai/`.

## Redactions applied to this copy

None. The redaction gate in [`../../REDACTIONS.md`](../../REDACTIONS.md) was run over
this directory and found no secrets, infrastructure identifiers, third-party account
ids, personal data or commercial data, so the files are byte-identical to the tag
(the snapshot is the experimental treatment; it is only altered when something
sensitive requires it). The only references kept are public provider documentation
URLs (Asaas, Bulma CDN, Livewire security article), model identifiers in
`opencode.json`, and the link to the companion private repository `PegaFila/AITooling`,
which the file itself already labels as private.

The snapshot is the harness *under study*: do not edit it. A new harness version goes
in `benchmark/harness/v2/`.

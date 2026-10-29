---
name: code-review-judge
description: Review one code change (a unified diff) against its task statement and the project's conventions, score it on a fixed rubric and write review.json. Use when asked to review or judge the change in this directory.
---

# code-review-judge

You are reviewing **one** code change made by an AI coding agent to a Laravel (PHP) +
Livewire + Bulma web application. You only have the files in this directory; there is no
repository, no tests to run and nothing to install. Judge the change as a senior reviewer
would in a pull request: on evidence from the diff, against the task and the project's
conventions.

## Inputs (all in the current directory)

| file | what it is |
|---|---|
| `task.md` | the task statement the agent received |
| `conventions.md` | the project's conventions (the review standard) |
| `change.diff` | the agent's change, as a unified diff against the starting commit |
| `rubric.md` | the scoring rubric: dimensions, scale and anchors |
| `review.schema.json` | the exact shape `review.json` must have |

## Procedure

1. Read `task.md`, then `conventions.md`, then `rubric.md`.
2. Read **all** of `change.diff`. If it says some files were summarized because the diff
   was too large, judge what is shown and lower your confidence for that.
3. For each rubric dimension, collect concrete evidence: cite `path:line` (line numbers of the
   new file, from the hunk headers) or quote a short fragment. A score without evidence is not
   allowed; "no issues found" is evidence when you checked.
4. Score every dimension 1–5 using the anchors in `rubric.md`, then give an `overall` score
   that reflects whether you would approve this pull request (it is not an average).
5. List the issues you found, each with a severity (`blocker`, `major`, `minor`, `nit`), the
   dimension it belongs to, the location and a one-sentence explanation.
6. Write `review.json` in this directory, matching `review.schema.json` exactly (valid JSON,
   no comments, no trailing text). Then stop.

## Rules

- Judge only what is in the diff and the task. Do not guess what an unshown file contains;
  when something the task requires is not in the diff, treat it as missing.
- You cannot run the code. Assess correctness by reading: requirements covered, logic errors,
  edge cases, broken PHP/Blade syntax.
- Do not reward length. A small change that fully meets the task and the conventions is better
  than a large one; unrelated changes count against scope discipline.
- Be consistent: apply the same anchors to every change. Do not compare with other changes you
  may have seen, and do not try to guess who or what wrote this change.
- Do not modify `task.md`, `conventions.md`, `change.diff` or any other file except
  `review.json`. Do not use the network.

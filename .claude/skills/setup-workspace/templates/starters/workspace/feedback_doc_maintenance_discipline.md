---
name: feedback_doc_maintenance_discipline
description: For any project with a docs stack — README + CLAUDE.md + project-context.md + .claude/docs/* update in the same change as the code, not deferred.
metadata:
  type: feedback
---

For any project repo with a documentation stack (README.md, CLAUDE.md, `.claude/memory/project-context.md`, `.claude/docs/architecture.md`, `.claude/docs/conventions.md`), the docs move in lockstep with the code: changes to code that affect any of those docs land in the same commit, not in a follow-up.

The per-project mapping of "what code change updates which doc" belongs in that project's CLAUDE.md under a section like "Keeping docs in sync" — the table is project-specific because doc surfaces differ (a CLI has a Usage section; a library has an API reference; a web app has routes and components). Workspace memory holds the rule; the project's CLAUDE.md holds the table.

**Why:** Stale docs are worse than no docs — they lie. A README documenting a constant the code never reads is a silent failure mode that compounds across sessions: future engineers act on the doc, the code does something else, and the discrepancy isn't caught until someone debugs from first principles. The cost of a brief doc edit in the same commit is always lower than the cost of accumulated drift.

**How to apply:** Before closing any change in a project repo, scan against that project's CLAUDE.md "Keeping docs in sync" table. If a row matches, update the corresponding doc(s) in the same commit. If a project has no such table yet, add one as part of the first non-trivial change and seed this rule into that project's `.claude/memory/` so future sessions see it. `MEMORY.md` is not a substitute for the docs themselves — it carries non-derivable context (decisions, gotchas, past incidents), not how-it-works.

# When to Save (and When Not To)

The auto-memory system is small on purpose. Every entry has a context cost — it shows up in MEMORY.md and gets considered on every turn. Save sparingly. Prune regularly.

## Save when

- The user **corrects** you on approach, tone, scope, tools, or output format.
- The user **confirms** a non-obvious choice you made ("yes, that's exactly what I wanted").
- You learn a fact about the user (role, expertise, preferences) you'll need next time.
- You learn project context (deadlines, constraints, stakeholders) that isn't in the code.
- You learn where to find something in an external system.
- The user **explicitly says** "remember this" or "save this."

## Do NOT save

- **Code patterns, conventions, architecture, file paths, or project structure.** These are derivable by reading the current project state. CLAUDE.md is the right place for conventions; the code itself is the right place for architecture.
- **Git history, recent changes, or who-changed-what.** `git log` and `git blame` are authoritative.
- **Debugging solutions or fix recipes.** The fix is in the code; the commit message has the context.
- **Anything already in CLAUDE.md.** Don't keep two copies of the same rule.
- **Ephemeral state.** In-progress task tracking, current conversation context, todo items — those belong in `TodoWrite` or a plan file, not memory.

These exclusions apply **even when the user asks you to save them**. If asked to save an activity summary or a PR list, ask back what was *surprising* or *non-obvious* — that is the part worth keeping.

## File format

Each memory is its own file in `~/.claude/projects/<slug>/memory/`. Filename convention: `<type>_<topic>.md` (e.g. `feedback_testing.md`, `user_role.md`, `reference_logging.md`).

Frontmatter is required:

```markdown
---
name: <human-readable title>
description: <one-line — used to decide relevance in future conversations>
type: <user|feedback|project|reference>
---

<memory content>
```

For `feedback` and `project` types, structure the body as:

```
<rule or fact>

**Why:** <reason>
**How to apply:** <when and where this kicks in>
```

The *why* is what lets you judge edge cases instead of blindly applying the rule.

## Then update MEMORY.md

After writing the file, add **one line** to `MEMORY.md`:

```
- [Title](file.md) — one-line hook
```

Keep each entry under ~150 chars. `MEMORY.md` is an index, never the memory itself.

## Update over duplicate

Before writing a new memory, check if an existing one covers the same topic. Update the existing file rather than creating a parallel one. Two memories saying nearly the same thing is worse than one memory said well.

## When memories go stale

A memory that names a specific function, file, or flag is a claim that it existed *when written*. Things get renamed, removed, or never merged. Before recommending from memory:

- Memory names a file path → check the file exists
- Memory names a function or flag → grep for it
- User is about to act on the recommendation → verify first

If recalled memory conflicts with current observation, trust the observation and update the stale memory.

For activity-log-style memories ("I shipped X this week", "we have N open PRs"), prefer `git log` or live queries over recalling the snapshot.

## Cadence and pruning

- Aim to keep `MEMORY.md` under ~40 entries / 200 lines.
- Run `memory-hygiene` monthly (or when MEMORY.md exceeds 30 entries).
- Archive stale entries — don't delete. Archives are reversible; deletes aren't.

## Memory vs other persistence

Auto-memory is for things you'll want **next session**. Don't use it for:

- **Plans** — use the plan file tied to the current task.
- **TodoWrite** — for in-session task tracking.
- **Project memory** (`repo/.claude/memory/`) — for repo-scope conventions and domain context shared with collaborators.
- **CLAUDE.md** — for rules that must fire at every turn (the highest-cost layer; promote here only if a memory has been violated despite being saved).

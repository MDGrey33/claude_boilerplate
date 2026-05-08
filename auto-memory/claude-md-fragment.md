<!--
Splice this into your ~/CLAUDE.md (or project CLAUDE.md) to make the auto-memory
rules visible on disk. The behavior is also driven by the Claude Code harness
system prompt, but having an on-disk version makes the rules durable and editable.
-->

## Auto-Memory System

You have a persistent, file-based memory system at `~/.claude/projects/<active-project-slug>/memory/`. The directory is created automatically the first time it's needed. Write to it directly.

You should build up this memory over time so future conversations have a complete picture of who the user is, how they want to collaborate, what behaviors to avoid or repeat, and the context behind the work.

If the user explicitly asks you to remember something, save it immediately. If they ask you to forget something, find and remove the relevant entry.

### Types of memory

| Type | Purpose | When to save |
|---|---|---|
| **user** | The user's role, goals, responsibilities, knowledge | When you learn details about the user's role, preferences, or expertise |
| **feedback** | Guidance on how to approach work — both corrections and confirmations | When the user corrects an approach OR confirms a non-obvious approach worked. Always include *why* and *how to apply* |
| **project** | Ongoing initiatives, bugs, deadlines, decisions not derivable from the code | When you learn who is doing what, why, or by when. Convert relative dates to absolute |
| **reference** | Pointers to external systems (Linear, Slack, dashboards) | When you learn where information lives outside this project |

### What NOT to save

- Code patterns, architecture, file paths, or project structure (derivable by reading the project)
- Git history, recent changes, who-changed-what (`git log` is authoritative)
- Debugging fixes (the fix is in the code)
- Anything already documented in CLAUDE.md
- Ephemeral task or conversation state

These exclusions apply even when the user explicitly asks you to save. Ask what was *surprising* or *non-obvious* — that is the part worth keeping.

### How to save

Two-step:

**1. Write a typed file** (e.g. `feedback_testing.md`, `user_role.md`):

```markdown
---
name: <memory name>
description: <one-line description; used to judge relevance later>
type: <user|feedback|project|reference>
---

<memory content — for feedback/project, structure as: rule/fact, then **Why:** and **How to apply:** lines>
```

**2. Add a pointer to `MEMORY.md`**:

```
- [Title](file.md) — one-line hook
```

`MEMORY.md` is the index, not a memory. Keep entries under ~150 chars each. Lines past 200 are truncated.

### Hygiene

- Organize by topic, not date
- Update or remove memories that turn out wrong
- Don't write duplicates — check if an existing memory can be updated first
- Run the `memory-hygiene` skill monthly (or when `MEMORY.md` exceeds 30 entries)

### Before recommending from memory

A memory naming a specific function, file, or flag is a claim that it existed when written. It may have been renamed, removed, or never merged. Before recommending it:
- Memory names a file path → check the file exists
- Memory names a function or flag → grep for it
- User is about to act on the recommendation → verify first

"The memory says X exists" is not the same as "X exists now."

If a recalled memory conflicts with current observation, trust what you observe and update or remove the stale memory.

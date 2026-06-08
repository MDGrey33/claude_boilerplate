---
name: project-registry
description: Manage the workspace's project registry at `<workspace>/.claude/projects-index.json`. Single mutation point for the registry — other skills read the file directly, all writes funnel through here. Actions: `add`, `remove`, `update`, `list`.
user_invocable: true
args: |
  Pick a mode based on user intent:
  - `add <slug> [description]` — register a new project. Auto-creates the registry on first call. Refuses on slug clash. The project must already exist at `<workspace>/projects/<slug>/` (real dir or symlink).
  - `remove <slug>` — unregister a project. Confirm with the user before removing. Does NOT delete files on disk.
  - `update <slug> <field> <value>` — update a single field on an existing project. Allowed fields: `description`.
  - `list` — show registered projects with their derived paths. Default action when no args.
---

# /project-registry

This skill owns `<workspace>/.claude/projects-index.json`. Other skills read the file directly (cheap, safe — reads don't mutate). All writes funnel through this skill so mutation is single-pointed and validated.

## Schema

```json
{
  "schemaVersion": "1.0",
  "projects": {
    "<slug>": {
      "description": "<optional>",
      "created": "<ISO-8601 with TZ offset>"
    }
  }
}
```

The project's path is **derived** by convention: `<workspace>/projects/<slug>/`. It's not stored in the registry. If a user wants the project's real dir to live elsewhere, they create a symlink at `<workspace>/projects/<slug>/` pointing at the real location — Memnyx sees the symlink path.

Memnyx doesn't model "topic vs repo" distinctions in the registry. That's a conceptual framing for users (personal cross-cutting work vs team-shared codebase), but Memnyx treats every registered project identically. If you want the project committed to a remote, that's a normal git workflow — it has nothing to do with the registry.

## Workspace resolution

The workspace is the user's current working directory (`cwd`). Per v2 design, the user always starts Claude from the workspace root, so `cwd/.claude/projects-index.json` is the registry path.

If the registry doesn't exist, `add` creates it on first call with an empty `projects` map.

## Actions

### `add <slug> [description]`

Register a new project.

**Validation:**
- `slug` matches `^[a-z][a-z0-9-]*$` (lowercase, hyphens; starts with a letter).
- `<workspace>/projects/<slug>/` exists on the filesystem (real dir or symlink). The path is convention-derived, not user-supplied.
- `description` is optional; defaults to empty string.

**Behavior:**
1. Read the registry. If missing, treat as empty.
2. If `<slug>` is already registered, refuse with a message suggesting `update` or `remove` first.
3. Add entry with a fresh `created` timestamp (ISO-8601, local TZ).
4. Atomic write.

**Hint on missing project dir:** if `<workspace>/projects/<slug>/` doesn't exist, refuse and tell the user to either run `/setup-workspace add-project` (which scaffolds it), `mkdir <workspace>/projects/<slug>` (for a fresh project), or `ln -s /path/to/real/repo <workspace>/projects/<slug>` (to point at an existing repo elsewhere).

### `remove <slug>`

Unregister a project. **Does not delete files** — only removes the registry entry.

**Behavior:**
1. Read the registry.
2. If `<slug>` doesn't exist, refuse.
3. Show the entry being removed and confirm with the user.
4. Remove entry. Atomic write.

### `update <slug> <field> <value>`

Update a single field on an existing project. Allowed field: `description`.

**Behavior:** read, update, atomic write.

### `list`

Show registered projects as a table: `slug | path | description`. The path column is computed from the slug at display time. Default action when no args.

## Implementation

Action work is delegated to `scripts/registry.py`. Invoke as:

```
python3 .claude/skills/project-registry/scripts/registry.py <action> [args...]
```

The script handles argument parsing, validation, JSON read/write, and atomic mutation. Output goes to stdout in human-readable form.

## Important rules

- **Reads bypass this skill.** Other skills should read `<workspace>/.claude/projects-index.json` directly. This skill is for writes (and the convenience `list`).
- **No filesystem side effects beyond the registry file.** Project scaffolding (creating dirs, gitignore patterns, generating CLAUDE.md from templates) is `/setup-workspace`'s job, not this skill's. This skill does NOT create symlinks or directories.
- **No deletion of project files.** `remove` only unregisters; the project's content on disk is untouched.
- **Confirm before destructive actions.** `remove` requires user confirmation. `update` does not.

## Concurrency

Per v2 design, single mutation point eliminates concurrent-write races between skills. Two simultaneous user invocations of this skill could still collide; v1 ignores this. Future: mtime-check pattern.

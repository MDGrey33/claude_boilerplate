---
name: setup-workspace
description: Initialise a workspace, register projects under it, or sync upstream changes. Single entry point for workspace lifecycle.
user_invocable: true
args: |
  Pick a mode based on user intent:
  - `init --workspace <path> [--source <path>] [--dry-run]` — first-time workspace setup. Run from inside the cloned boilerplate folder; pass `--workspace` to point at the target. `--source` defaults to cwd when cwd is a v2 boilerplate; pass it explicitly only when running from elsewhere. `--dry-run` previews what would be created/skipped without writing anything.
  - `add-project <slug> [description]` — scaffold a project under `<workspace>/projects/<slug>/` and register it via `/project-registry add`. Run from the workspace root.
  - `sync` — pull upstream skill/agent updates from source. Diff-detects local changes and asks before overwriting.
---

# /setup-workspace

Owns workspace lifecycle: `init` (first-time setup), `add-project` (register a project), and `sync` (update from source).

## Workspace conventions

- **Sibling layout.** The boilerplate source clone and the workspace live at sibling paths — for example, `~/src/claude_boilerplate/` and `~/workspace/`. Source must NOT live inside the workspace, and the workspace must NOT live inside the source. `init` refuses if the layout is wrong.
- **Init runs once from the source clone.** After init, the user works from the workspace; the source clone stays around for `/setup-workspace sync` (upstream updates).
- **Workspace = `cwd` for `add-project`, `sync`, and ongoing work.**
- Per v2 design principles: skills, agents, identity, brag log, MCP server configs, and the project registry all live in the workspace.

## `init --workspace <path> [--source <path>]`

First-time workspace setup.

### Why init runs from the source clone

Before init, the workspace's `.claude/skills/` is empty — `/setup-workspace` doesn't exist there yet. So init is invoked from a Claude session started inside the cloned boilerplate, where the skill is already present. Init then deploys the skill (and everything else) into the target workspace. After init, the user starts fresh sessions from the workspace.

### Invocation

```
cd ~/src/claude_boilerplate          # or wherever you cloned it
claude
/setup-workspace init --workspace ~/workspace
```

`--source` defaults to cwd. Pass `--source <path>` only when running from somewhere other than the source clone.

A v2 boilerplate is identified by the marker file `.claude/skills/setup-workspace/templates/workspace-CLAUDE.md.tmpl`. `init` refuses if cwd is not a v2 boilerplate and `--source` is not provided.

### Prerequisites

- The boilerplate cloned to a folder OUTSIDE the intended workspace (e.g., `~/src/claude_boilerplate/`).
- The target workspace folder exists (`mkdir -p ~/workspace` if needed).
- Confirm workspace and source paths with the user before invoking the script (the agent reads the values from script output and asks).

### Dry run

Pass `--dry-run` to preview what init would do without writing anything. The script prints the same created/skipped summary, prefixed with `[DRY RUN]`. Useful when the user wants to verify the plan before committing. The agent should default to running `--dry-run` first when paths haven't been confirmed, then re-run without it.

### Behavior

The init action is **idempotent**. Re-running is safe:
- Skills, agents, and `agent-guardrails.md` are **overwritten** from source (always fresh — these are upstream-owned).
- Other docs (`architecture.md`, `conventions.md`, `cognee-usage.md`, etc.) are deployed only if missing in the workspace (templates, evolved by the user after init).
- `CLAUDE.md`, `MEMORY.md`, `lessons-learned.md`, `project-context.md`, `me/*.md`, `.gitignore`, `settings.json` are deployed only if missing — never overwritten.

### Steps

1. **Resolve workspace and source.** `--workspace` is required; `--source` defaults to cwd when cwd is a v2 boilerplate. The script validates the sibling layout (refuses if source and workspace overlap) and prints both paths — confirm with the user before proceeding.
2. **Create scaffolding** (idempotent):
   - At workspace root: `workstreams/`, `sessions/active/`, `artifacts/`, `me/`.
   - Under `.claude/`: `memory/`, `skills/`, `agents/`, `docs/`.
3. **Deploy from source:**
   - `<source>/.claude/skills/*` → `<workspace>/.claude/skills/` (overwrite).
   - `<source>/.claude/agents/*` → `<workspace>/.claude/agents/` (overwrite, if source has agents).
   - `<source>/.claude/docs/agent-guardrails.md` → `<workspace>/.claude/docs/agent-guardrails.md` (overwrite).
   - Other `<source>/.claude/docs/*` → `<workspace>/.claude/docs/` (deploy only if missing — these are templates).
4. **Generate `<workspace>/CLAUDE.md`** from `templates/workspace-CLAUDE.md.tmpl` (skip if exists).
5. **Deploy starter files** (skip if exists):
   - `<workspace>/.claude/memory/MEMORY.md` — empty header.
   - `<workspace>/.claude/memory/lessons-learned.md` — empty header.
   - `<workspace>/.claude/memory/project-context.md` — workspace-level domain context template (user fills in).
   - `<workspace>/me/identity.md` — placeholder profile (user fills in).
   - `<workspace>/me/brag-log.md` — empty header.
   - `<workspace>/me/growth.md` — empty header.
   - `<workspace>/.gitignore` — gitignores per-engineer working state.
6. **Settings.json:** copy from source only if `<workspace>/.claude/settings.json` is missing. If exists, skip with a note suggesting `/setup-workspace sync` for future updates.
7. **Print summary:** what was created, what was skipped, and suggested next steps (`/setup-workspace add-project`, `/setup-cognee`).

### Implementation

The init action is delegated to `scripts/init.py`:

```
python3 .claude/skills/setup-workspace/scripts/init.py --workspace <path> [--source <path>] [--dry-run]
```

When run from cwd = source clone (the recommended flow), the relative path above works. From elsewhere, use the absolute path to the script in the source.

## `add-project <slug> [description]`

Scaffold a project under `<workspace>/projects/<slug>/` and register it via `/project-registry add`.

### Inputs

- `<slug>` — required. Lowercase + hyphens; must start with a letter. Same shape as `/project-registry add`.
- `<description>` — optional one-line. Stored on the registry entry and substituted into the project's `CLAUDE.md`.

### Prerequisites

- `cwd = workspace`. The user is at the workspace root.
- `<workspace>/projects/<slug>/` already exists. `add-project` does NOT create the project root — the user creates it first, either as a fresh dir or as a symlink to an existing repo:
  ```
  mkdir <workspace>/projects/<slug>                       # fresh project
  ln -s /path/to/repo <workspace>/projects/<slug>         # symlink existing
  ```
  Keeps the boilerplate out of physical placement decisions.

### Dry run

Pass `--dry-run` to preview what would be created/skipped without writing anything. Particularly useful when the project dir is a symlink to an existing repo: confirms whether an existing `CLAUDE.md` or `.gitignore` would be preserved, and which gitignore patterns would be appended.

### Behavior

The action is **idempotent**. Re-running is safe:
- Existing files (`CLAUDE.md`, `MEMORY.md`, `lessons-learned.md`, `project-context.md`, `settings.json`) are preserved — never overwritten.
- `.gitignore` is created fresh if missing, or appended in-place with only the patterns it lacks (line-by-line check).
- `/project-registry add` is skipped when the slug is already registered.

### Steps

1. **Pre-flight checks:**
   - cwd looks like a v2 workspace (has `.claude/skills/setup-workspace/`).
   - slug matches `^[a-z][a-z0-9-]*$`.
   - `<workspace>/projects/<slug>/` exists (real dir or symlink).
2. **Create directories at the project root:** `workstreams/`, `sessions/active/`, `artifacts/`, `.claude/memory/`. Skip if exists.
3. **Write starter files** (skip if exists):
   - `.claude/memory/MEMORY.md` — empty header.
   - `.claude/memory/lessons-learned.md` — empty header.
   - `.claude/memory/project-context.md` — project-level domain context template (user fills in: business domain, users, constraints, what "done" looks like).
   - `.claude/settings.json` — empty `{}`. Project-level allowlists evolve here as the project's needs surface; user-specific layers go into `settings.local.json` (gitignored).
4. **Generate `CLAUDE.md`** from `templates/project-CLAUDE.md.tmpl` with `{{project_name}}` and `{{description}}` substituted. Skip if exists (typical when symlinking to a real repo that already has its own CLAUDE.md).
5. **Update `.gitignore`** at the project root: append `workstreams/`, `sessions/`, `collected/`, `artifacts/`, `contributions/`. Idempotent — line-by-line check; only missing patterns are added.
6. **Register via `/project-registry add`** — the registry receives `<slug> [description]`. Skipped when the slug is already registered.
7. **Print summary:** what was created, what was skipped.

### Why `collected/` and `contributions/` aren't scaffolded

These dirs are created by their owning skills on first use (mirrors the `init` pattern at the workspace level). Pre-creating empty dirs pollutes `git status` until something actually lands in them; deferring keeps the project clean until the dir is actually needed.

### Implementation

The add-project action is delegated to `scripts/add_project.py`:

```
python3 .claude/skills/setup-workspace/scripts/add_project.py <slug> [description] [--dry-run]
```

The script handles validation, idempotent scaffolding, template substitution, and the registry call. Output goes to stdout in human-readable form.

## `sync`

*(To be built in build-plan step 8. Not yet implemented.)*

## Important rules

- **Idempotent.** Re-running any action is safe.
- **Never overwrite user content.** CLAUDE.md, MEMORY.md, lessons-learned.md, identity, brag log, growth, gitignore, settings.json — once present, stay as the user has them.
- **Always overwrite upstream-owned content.** Skills, agents, agent-guardrails.md — these are the boilerplate's contract; staleness is worse than slight churn.
- **Refuse, don't guess.** If the source can't be uniquely identified, fail with a clear hint rather than picking arbitrarily.
- **No project scaffolding here.** That's `/setup-workspace add-project`'s job, not `init`'s.

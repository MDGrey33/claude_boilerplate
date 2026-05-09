---
name: setup-workspace
description: Initialise a workspace, register projects under it, or sync upstream changes. Single entry point for workspace lifecycle. Run from the workspace root (`cwd` = workspace).
user_invocable: true
args: |
  Pick a mode based on user intent:
  - `init [--workspace <path>] [--source <path>] [--dry-run]` — first-time workspace setup. Auto-detects workspace and source from cwd when invoked from inside the boilerplate clone (`<workspace>/source/<repo>/`) or from the workspace root (with `source/<v2-boilerplate>/` underneath). Pass flags explicitly to override. `--dry-run` previews what would be created/skipped without writing anything.
  - `add-project <slug> [description]` — scaffold a project under `<workspace>/projects/<slug>/` and register it via `/project-registry add`.
  - `sync` — pull upstream skill/agent updates from source. Diff-detects local changes and asks before overwriting.
---

# /setup-workspace

Owns workspace lifecycle: `init` (first-time setup), `add-project` (register a project), and `sync` (update from source). Run from the workspace root.

## Workspace conventions

- Workspace = `cwd`. The user always starts Claude from the workspace root.
- Boilerplate source lives at `<workspace>/source/<repo>/`. Cloned manually before `init` (v1).
- Per v2 design principles: skills, agents, identity, brag log, MCP server configs, and the project registry all live in the workspace.

## `init [--workspace <path>] [--source <path>]`

First-time workspace setup.

### The chicken-and-egg

Before init, the user's intended workspace folder is empty — `/setup-workspace` doesn't yet live at `<workspace>/.claude/skills/`. So init is invoked from the boilerplate clone itself, where the skill is present. Init then deploys the skill (and everything else) into the workspace. After init, the user `cd`s to the workspace and works from there.

### Two invocation styles (both auto-detected)

**Style A — from inside the source clone (recommended for first-time bootstrap):**
```
cd <workspace>/source/<v2-boilerplate>/
claude
/setup-workspace init
```
Workspace inferred as cwd's grandparent (per the `<workspace>/source/<repo>/` convention). Source = cwd.

**Style B — from the workspace root (works after init has deployed the skill):**
```
cd <workspace>/
claude
/setup-workspace init
```
Workspace = cwd. Source auto-detected by scanning `<workspace>/source/` for a v2 boilerplate.

**Style C — explicit flags (works from anywhere):**
```
/setup-workspace init --workspace ~/my-space --source ~/Downloads/claude_boilerplate
```

A v2 boilerplate is identified by the marker file `.claude/skills/setup-workspace/templates/workspace-CLAUDE.md.tmpl`. Auto-detection refuses if it's ambiguous (multiple boilerplates under `source/`) or impossible (cwd doesn't match any pattern); the user passes flags explicitly to disambiguate.

### Prerequisites

- A v2 boilerplate cloned somewhere reachable (e.g., `<workspace>/source/<repo>/`). If `source/` doesn't exist or is empty, init refuses with a hint to clone first.
- Confirm the detected workspace and source with the user before invoking the script (the agent reads the detected paths from script output and asks).

### Dry run

Pass `--dry-run` to preview what init would do without writing anything. The script prints the same created/skipped summary, prefixed with `[DRY RUN]`. Useful when the user is uncertain and wants to verify the detection and plan first. The agent should default to running `--dry-run` first when the user hasn't confirmed paths, then re-run without it after confirmation.

### Behavior

The init action is **idempotent**. Re-running is safe:
- Skills, agents, and `agent-guardrails.md` are **overwritten** from source (always fresh — these are upstream-owned).
- Other docs (`architecture.md`, `conventions.md`, `cognee-usage.md`, etc.) are deployed only if missing in the workspace (templates, evolved by the user after init).
- `CLAUDE.md`, `MEMORY.md`, `lessons-learned.md`, `me/*.md`, `.gitignore`, `settings.json` are deployed only if missing — never overwritten.

### Steps

1. **Resolve workspace and source.** Auto-detect per the styles above, or use explicit `--workspace` / `--source` flags. The script's first output lines print what it detected — confirm with the user before proceeding.
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
   - `<workspace>/me/identity.md` — placeholder profile (user fills in).
   - `<workspace>/me/brag-log.md` — empty header.
   - `<workspace>/me/growth.md` — empty header.
   - `<workspace>/.gitignore` — gitignores per-engineer working state.
6. **Settings.json:** copy from source only if `<workspace>/.claude/settings.json` is missing. If exists, skip with a note suggesting `/setup-workspace sync` for future updates.
7. **Print summary:** what was created, what was skipped, and suggested next steps (`/setup-workspace add-project`, `/setup-cognee`).

### Implementation

The init action is delegated to `scripts/init.py`:

```
python3 <source>/.claude/skills/setup-workspace/scripts/init.py [--workspace <path>] [--source <path>]
```

When invoked from Style A (cwd is source clone), the relative path `python3 .claude/skills/setup-workspace/scripts/init.py` works. From Style B/C, use the full path to the script in the source.

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
- Existing files (`CLAUDE.md`, `MEMORY.md`, `lessons-learned.md`, `settings.json`) are preserved — never overwritten.
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

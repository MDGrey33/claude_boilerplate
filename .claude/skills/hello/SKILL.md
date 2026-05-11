---
name: hello
description: Start a session — locate workspace, classify cwd, resolve project + workstream + open item, load memory, write session marker, recap context
user_invocable: true
---

# Session Start

You are starting a new working session. Resolve the active context, load memory, and orient the user.

## Steps

### 1. Self-locate the workspace

The skill's base directory is `<workspace>/.claude/skills/hello/`. Resolve `<workspace>` by walking up three directory levels. Validate that `<workspace>/.claude/.workspace` exists. If validation fails, abort with a setup-broken error — this is not recoverable from inside /hello.

### 2. Classify cwd

Compute one of four cases. The result is a *hint* for phrasing in step 7; it does not by itself decide the active project.

- **Outside workspace** — cwd is not a descendant of `<workspace>/`. Refuse with: "cd into `<workspace>` (or a subdirectory) and rerun /hello." Stop here.
- **Workspace-level** — cwd equals `<workspace>/`, or is under `<workspace>/` but not under `<workspace>/projects/<slug>/`. Hint = workspace-level work.
- **Registered project** — cwd is under `<workspace>/projects/<slug>/` and `<slug>` is in the registry. Hint = that project.
- **Unregistered project** — cwd is under `<workspace>/projects/<slug>/` but `<slug>` is NOT in the registry. Hint = offer inline registration via `/setup-workspace add-project`.

### 3. Load workspace-scope context

Read all in parallel; skip silently if a file is missing:

- `<workspace>/me/identity.md`
- `<workspace>/.claude/memory/MEMORY.md`
- `<workspace>/.claude/memory/lessons-learned.md`
- `<workspace>/.claude/memory/project-context.md`
- `<workspace>/sessions/latest-session.md`

Read the project registry directly from `<workspace>/.claude/projects-index.json` (registry mutations go via `/project-registry`; reads bypass it). Treat missing as empty.

### 4. Scan active session markers

List markers from:

- `<workspace>/sessions/active/*.md` (workspace-level sessions)
- `<workspace>/projects/*/sessions/active/*.md` (project-level sessions)

For each, parse frontmatter (`project_slug`, `workstream_slug`, `open_item_slug`, `started_at`) and compute age. Held for the overlap check at step 13.

### 5. Run /mcp-doctor

Inline call in session mode. Surfaces server health to fold into the recap.

### 6. Recap (workspace-scope)

```
Session Start
=============
Workspace:  <path>
Cwd hint:   <workspace-level | project=<slug> | unregistered=<slug> | outside>
Last session: <one-line summary, or "No previous sessions">
Active sessions elsewhere: <list with ages, or "none">
MCP status: <from /mcp-doctor>
Lessons:    <N> conventions, <M> patterns
Identity:   loaded / placeholder
```

### 7. Resolve project (open-ended)

Phrasing branches on the cwd hint. In every variant, be honest about inference and invite explicit override — never imply the model deterministically knows whether work "is a project":

- **Workspace-level hint** → "What are you working on today? I'll infer whether to treat it as project work or workspace-level work and confirm before proceeding. You can also explicitly say 'register a new project' or 'this is a one-off task' to skip the inference."
- **Registered-project hint** → "Looks like you're in `<slug>`. Continuing on that, or working on something else today? (If something else, I'll infer the scope and confirm — or you can ask me to register a new project.)"
- **Unregistered-project hint** → "`<slug>` isn't registered yet. Want me to register and scaffold it now (calls `/setup-workspace add-project`), or are you treating this as a one-off?"

Resolution rules — match the registry first:

1. **Semantic match against registered slugs and descriptions.** If a plausible match exists, confirm with the user ("That sounds like `<slug>` — continue there?"). The registry is the source of truth for whether work belongs to a project; topic shape (personal, cross-cutting, leadership update, team activity, 1:1 prep, etc.) is not a signal to skip the registry — users may register a project (e.g., `my-work`) precisely for that work.
2. **Ambiguity** between two or more registered projects → ask one clarifying question.
3. **Explicit user override.** If the user explicitly says "register a new project" / "create a project" / "one-off task" / similar, honour that immediately without further inference. Explicit override always beats inference.
4. **No match, user describes a new project** → fall through to step 8 (new-project handling).
5. **No match, user confirms it's not project-bound** → set scope = workspace-level. Workspace-level is the fallback when no project fits — never the default for a topic shape.

**Empty registry caveat.** When no projects are registered, paths 1–2 are unreachable; the resolver collapses to inference (paths 3–5) with no anchored confirmation. State this honestly in the question rather than pretending registry-backed matching is happening.

### 8. New-project handling

When the user names a project that isn't registered (and it's not the unregistered-cwd branch):

1. Confirm the slug with the user (lowercase, hyphens, starts with a letter).
2. If `<workspace>/projects/<slug>/` doesn't exist, instruct the user to create it first:
   - Fresh project: `mkdir <workspace>/projects/<slug>`
   - Existing repo elsewhere: `ln -s /path/to/real/repo <workspace>/projects/<slug>`
3. Run `/setup-workspace add-project <slug> [description]`. Scaffolds the project AND registers it in one step. Do NOT call `/project-registry add` directly — it doesn't scaffold memory or session-marker dirs.

The project is now selected.

### 9. Layer project-scope context (when scope = project)

Read in parallel; skip silently if missing:

- `<workspace>/projects/<slug>/.claude/memory/MEMORY.md`
- `<workspace>/projects/<slug>/.claude/memory/lessons-learned.md`
- `<workspace>/projects/<slug>/.claude/memory/project-context.md`
- `<workspace>/projects/<slug>/sessions/latest-session.md`

List `<workspace>/projects/<slug>/workstreams/*.md` (read on demand at step 11).

For workspace-level scope, the equivalents at `<workspace>/.claude/memory/` are already loaded in step 3; just list `<workspace>/workstreams/*.md`.

### 10. Cognee semantic search (conditional no-op)

If cognee is loaded (per /mcp-doctor's report), call `cognee_search "project context recent work"` and fold useful findings into the recap. If cognee is not loaded, skip silently.

### 11. Resolve workstream

Phrasing branches on the active scope's `latest-session.md`:

- **Names an active workstream** → "Last time you were on `<workstream>`. Continue, or working on something else?"
- **Otherwise** → "Which workstream are you on, or is this a new one?"

Resolution:

- **Continue** → load the named workstream file from the active scope's `workstreams/`.
- **Match an existing workstream** (semantic, not regex) → confirm and load.
- **New** → derive a slug from the user's description (sanitisation below); offer for confirmation; create `<scope>/workstreams/<slug>.md` with a one-line header (`# Workstream: <slug>` plus start date). No open-items section pre-populated — that's content `/bye` accumulates.

**Slug sanitisation** (workstream and open-item slugs):

- Lowercase the input.
- Replace any non-alphanumeric character (except hyphens) with hyphens.
- Collapse repeated hyphens into single hyphens.
- Trim to 50 characters.
- Force `.md` extension on workstream filenames.
- Reject input containing `..`, `/`, or other path separators — re-prompt.
- Always join the sanitised slug to `<scope>/workstreams/` (never concatenate raw user input into a path).
- Fail with a validation prompt if the input cannot be safely normalised.

### 12. Resolve open item (conflict unit)

Read the workstream file. Find checkbox lines (`- [ ] ...`).

Either:

- **Slug from checkbox text** — if the user's answer or a follow-up identifies one of the existing checkboxes, derive a slug from the first ~50 chars of that line (same sanitisation as workstream slugs). Capture the verbatim checkbox text as `open_item_summary`.
- **User-named fallback** — if no checkbox matches, ask the user to name the work in a few words; sanitise the same way; capture the user phrase as `open_item_summary`.

Ask explicitly: "Which open item are you tackling? (Or is this a new one not yet on the list?)" Do NOT add new items to the workstream file — `/bye` writes that on session close.

**Ad-hoc workspace work.** If the user explicitly skips workstream/open-item resolution (purely exploratory session, no binding intended), set `workstream_slug: ad-hoc` and `open_item_slug: ad-hoc`. The marker still writes; `/bye` treats these as transient and removes the marker without writing to a workstream file.

### 13. Overlap check

Against the active markers from step 4:

- **Same `project_slug` + same `workstream_slug` + same `open_item_slug`** → conflict. Show: "Another session (started `<age>` ago) is already on this open item. Stand down, or proceed?" The user owns the decision; no auto-resolve.
- **Same workstream, different open item** → not a conflict. Note in the final recap that another session is on a sibling item.
- **Different workstream / different project / one is workspace-level and the other isn't** → not a conflict.

Skip the overlap check entirely when `open_item_slug = ad-hoc`.

### 14. Write the session marker

Path:

- Project context → `<workspace>/projects/<slug>/sessions/active/<id>.md`.
- Workspace-level → `<workspace>/sessions/active/<id>.md`.

`<id>` format: `YYYY-MM-DD-HHMMSS-<6 hex>` (human-readable for grep, collision-safe at second resolution).

Marker content:

```yaml
---
project_slug: <slug or "workspace">
workstream_slug: <slug>
open_item_slug: <slug>
open_item_summary: <verbatim checkbox text or user-named phrase>
started_at: <ISO-8601 with TZ offset>
session_id: <id>
---

Active session marker. Removed by /bye on session close.
```

Atomic write. No mtime-check — the id is unique by construction, no race.

### 15. Final recap

```
Active context
──────────────
Project:    <slug or "workspace">
Workstream: <slug>
Open item:  <summary>

Open items in this scope:
  <workstream-1>:
    - <item>
    - <item>
  <workstream-2>:
    - <item>

Marker: <relative path>
```

Open items are listed grouped by workstream — never flat, never all attributed to the active workstream. Cross-reference each `workstreams/*.md` file in the active scope to build the list. If a sibling session was flagged in step 13, note it under the active item.


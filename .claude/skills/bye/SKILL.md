---
name: bye
description: End the session — summarize work, persist context, capture lessons, close the active marker
user_invocable: true
---

# Session End

You are wrapping up the current working session. Summarize, persist, and hand off. v2 paths assumed throughout; scope comes from the active session marker, never from cwd.

## Steps

1. **Resolve scope.** The skill's base directory is `<workspace>/.claude/skills/bye/`; resolve `<workspace>` by walking up three directory levels and validate that `<workspace>/.claude/.workspace` exists. Then scan `<workspace>/sessions/active/*.md` and `<workspace>/projects/*/sessions/active/*.md`. For each marker, parse frontmatter: `project_slug`, `workstream_slug`, `open_item_slug`, `open_item_summary`, `started_at`, `session_id`.

   - One match → select it. Scope is `<workspace>` if `project_slug = workspace`, else `<workspace>/projects/<project_slug>`.
   - >1 matches → apply workstream-slug disambiguation before asking:
     1. If the current workstream slug is known from conversation context (i.e., `/hello` ran this session), filter markers by that slug. If exactly one matches, select it silently.
     2. If multiple markers share the same workstream slug, select the most recently created — use the timestamp embedded in the filename (`<YYYY-MM-DD>-<workstream-slug>-<HHMMSS>-<6hex>.md`).
     3. Only ask when the workstream slug is unknown, or when step 1 yields zero matches. Show each candidate's project + workstream + open item + age.
   - 0 matches → ask the user which scope to write to (workspace, or which project from the registry). Proceed without a marker to remove at step 13.


2. **Summarize the session**: Review the conversation and identify:
   - What was accomplished (tasks completed, files changed)
   - Key decisions made
   - Open items and next steps
   - Problems encountered and how they were resolved
   - The open item bound to this session — is it complete? Ask the user if unclear; do not mark complete silently.

3. **Write session narrative into the active marker**: Read the marker file at `<scope>/sessions/active/<filename>` (frontmatter already there from `/hello`). Append the session narrative body below the frontmatter closing `---`. No mtime-check — this is the session's own unique file; no other process writes to it.

   ```markdown
   # Session

   **Date**: YYYY-MM-DD
   **Duration**: ~Xh (estimate based on conversation length)
   **Workstream**: <workstream_slug>

   ## Accomplished
   - [list of completed items]

   ## Key Decisions
   - [list of decisions and rationale]

   ## Open Items
   - [ ] [next steps and pending work — grouped by workstream when listing across multiple]

   ## Problems & Resolutions
   - [issues encountered and how they were fixed]
   ```

4. **Update active workstream**: Edit `<scope>/workstreams/<workstream_slug>.md` in place — surgical edits, not full rewrite. Use mtime-check. Status line → today's date + one-line current state. Open Items → mark closed `[x]` (with user confirmation), append new `[ ]`. Decisions → append today's with `[YYYY-MM-DD]` prefix. Long-form artifacts (drafts, comparison docs, design specs over ~15 lines) go to `<scope>/artifacts/<workstream_slug>/<filename>.md`; the workstream gets a one-line pointer.

5. **Identify lessons**: Review the session for:
   - Mistakes made and corrections applied
   - New patterns or conventions discovered
   - User preferences expressed
   - Tool tips or workarounds found
   - Architectural insights

6. **Capture lessons**: If any lessons were identified, invoke the `/lessons` skill with the identified lessons. Do not pass scope — `/lessons` reads the marker itself.

7. **Curate MEMORY.md**: If any patterns were confirmed during this session (proven across multiple sessions, not just one-offs), update `<scope>/.claude/memory/MEMORY.md` with mtime-check. This is a curation step — edit to reflect current truth, don't just append. Remove stale entries. When promoting a lesson into MEMORY.md, also remove the source entry from `<scope>/.claude/memory/lessons-learned.md` — that file is an inbox, not an archive.

8. **Update personal workspace** (`<workspace>/me/` — never per-project, regardless of marker scope):
   - **identity.md**: Fill missing fields by name across the whole file. Never modify Preferences, Writing Style, Growth, or organic content.
   - **brag-log.md**: Append "led / oversight / flagged" accomplishments only; BAU is not brag-worthy.
   - **growth.md**: Note focus-area gaps surfaced during the session. Don't over-record.
   - **team.md**: Propose additions; do not write silently. Starter is scaffolded by `/setup-workspace init`.

9. **Check project docs for staleness**: If this session made structural changes (new dependency, changed data flow, new service interaction):
   - Read `<scope>/.claude/memory/project-context.md` — does it still reflect reality?
   - Read `<scope>/.claude/docs/architecture.md` — does it need updating?
   - If stale, **propose** specific updates. Do NOT write them silently — the user approves or skips.

10. **Store in cognee** (if available): If the cognee MCP is loaded, call `cognee_add` with the session summary text, then `cognee_cognify` to integrate it into the knowledge graph for future semantic retrieval.

11. **Suggest contributions**: If any lessons from this session seem broadly useful beyond this scope, mention that the user can run `/contribute` to generalize and stage them for the boilerplate.

12. **Output farewell**:

   ```
   Session Complete
   ================
   Scope: [workspace | projects/<slug>]
   Tasks completed: [count]
   Lessons captured: [count]
   Open items: [count]
   Workstream: [name] — updated / none
   Memory: updated / unchanged
   Personal: brag-log updated / identity updated / unchanged
   Cognee: synced / skipped
   Marker: [path] — promoted to sessions/ / kept (session paused)

   See you next time! Run /hello to pick up where we left off.
   ```

13. **Promote the session marker**: Move `<scope>/sessions/active/<filename>` → `<scope>/sessions/<filename>` (directory move only — filename unchanged). Then prune: keep the last 10 files matching `*-<workstream-slug>-*.md` in `<scope>/sessions/` (sorted by filename descending), delete older ones. Skip in two cases: (a) no marker was selected at step 1 (0-match case — write the narrative to a fresh file at `<scope>/sessions/<YYYY-MM-DD>-<workstream-slug>-<6hex>.md` instead, then prune); (b) the user signaled mid-`/bye` that the session isn't actually closing — leave the marker in `active/` untouched (reflect "kept (session paused)" in the farewell). Promotion is the last action — if any earlier step fails, the marker stays in `active/`.

## mtime-check protocol

For every shared-file write at steps 4, 7, 8 (not step 3 — the session file is the session's own unique file; no mtime-check needed):

1. Read the file; capture mtime.
2. Compute the edit.
3. Re-stat. If mtime changed since the read, re-read and re-apply the targeted change. Retry up to 3 times.
4. Write.

On retry exhaustion (>3 conflicts), prompt the user.

## Auto-memory branch (deferred)

When auto-memory is adopted (per `v2-design-principles.md` §Session lifecycle), step 6 routes through `/memory-hygiene graduate` instead of `/lessons`. Unused until adoption.

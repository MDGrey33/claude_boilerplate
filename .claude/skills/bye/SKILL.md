---
name: bye
description: End the session — summarize work, capture lessons, persist memory
user_invocable: true
---

# Session End

You are wrapping up the current working session. Summarize, persist, and hand off.

## Steps

1. **Summarize the session**: Review the conversation and identify:
   - What was accomplished (tasks completed, files changed)
   - Key decisions made
   - Open items and next steps
   - Problems encountered and how they were resolved

2. **Write session summary**: Write the summary to `.claude/memory/sessions/latest-session.md` (overwrite the file):

   ```markdown
   # Last Session

   **Date**: YYYY-MM-DD
   **Duration**: ~Xh (estimate based on conversation length)
   **Workstream**: [name of active workstream file, e.g., boilerplate-redesign.md]

   ## Accomplished
   - [list of completed items]

   ## Key Decisions
   - [list of decisions and rationale]

   ## Open Items
   - [ ] [next steps and pending work]

   ## Problems & Resolutions
   - [issues encountered and how they were fixed]
   ```

3. **Update active workstream**: If a workstream was active during this session, update its file in `.claude/memory/workstreams/` with new context, decisions, and open items from this session.

4. **Identify lessons**: Review the session for:
   - Mistakes made and corrections applied
   - New patterns or conventions discovered
   - User preferences expressed
   - Tool tips or workarounds found
   - Architectural insights

5. **Capture lessons**: If any lessons were identified, invoke the `/lessons` skill with the identified lessons.

6. **Curate MEMORY.md**: If any patterns were confirmed during this session (proven across multiple sessions, not just one-offs), update `.claude/memory/MEMORY.md`. This is a curation step — edit to reflect current truth, don't just append. Remove stale entries.

7. **Update personal workspace** (`~/.claude/me/`):
   - **brag-log.md**: If accomplishments worth noting for the engineer's career record, append them with date and repo context.
   - **identity.md**: If new role info, domain expertise, or preferences were revealed, update. Only on first session if file doesn't exist — create a minimal placeholder from what was observed.
   - **team.md**: If new team members or collaborators were mentioned, propose additions. Create the file on first encounter if it doesn't exist.
   - **growth.md**: If areas for improvement surfaced (e.g., engineer asked for help in an unfamiliar area), note it. Only if clearly relevant, don't over-record.

8. **Check project docs for staleness**: If this session made structural changes (new dependency, changed data flow, new service interaction):
   - Read `.claude/memory/project-context.md` — does it still reflect reality?
   - Read `.claude/docs/architecture.md` — does it need updating?
   - If stale, **propose** specific updates. Do NOT write them silently — the engineer approves or skips.

9. **Store in cognee** (if available): If the cognee MCP is healthy, call `cognee_add` with the session summary text, then call `cognee_cognify` to integrate it into the knowledge graph for future semantic retrieval.

10. **Suggest contributions**: If any lessons from this session seem broadly useful beyond this project, mention that the user can run `/contribute` to generalize and stage them for the boilerplate.

11. **Output farewell**:

   ```
   Session Complete
   ================
   Tasks completed: [count]
   Lessons captured: [count]
   Open items: [count]
   Workstream: [name] — updated / created / none
   Memory: updated / unchanged
   Personal: brag-log updated / identity updated / unchanged
   Cognee: synced / skipped

   See you next time! Run /hello to pick up where we left off.
   ```

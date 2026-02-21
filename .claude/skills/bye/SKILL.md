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

   ## Accomplished
   - [list of completed items]

   ## Key Decisions
   - [list of decisions and rationale]

   ## Open Items
   - [ ] [next steps and pending work]

   ## Problems & Resolutions
   - [issues encountered and how they were fixed]
   ```

3. **Identify lessons**: Review the session for:
   - Mistakes made and corrections applied
   - New patterns or conventions discovered
   - User preferences expressed
   - Tool tips or workarounds found
   - Architectural insights

4. **Capture lessons**: If any lessons were identified, invoke the `/lessons` skill with the identified lessons.

5. **Store in cognee** (if available): If the cognee MCP is healthy, call `cognee_add` with the session summary text, then call `cognee_cognify` to integrate it into the knowledge graph for future semantic retrieval.

6. **Update MEMORY.md**: If any stable patterns were confirmed during this session (patterns seen across multiple sessions, not just one-offs), update `.claude/memory/MEMORY.md` accordingly.

7. **Suggest contributions**: If any lessons from this session seem broadly useful beyond this project, mention that the user can run `/contribute` to generalize and stage them for the boilerplate.

8. **Output farewell**:

   ```
   Session Complete
   ================
   Tasks completed: [count]
   Lessons captured: [count]
   Open items: [count]
   Memory: updated / unchanged
   Cognee: synced / skipped

   See you next time! Run /hello to pick up where we left off.
   ```

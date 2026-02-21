---
name: hello
description: Start a new session — loads context, checks MCP health, recaps last session
user_invocable: true
---

# Session Start

You are starting a new working session. Load context and orient the user.

## Steps

1. **Load last session**: Read `.claude/memory/sessions/latest-session.md`. Note what was done, key decisions, and open items.

2. **Load accumulated knowledge**: Read `.claude/memory/MEMORY.md` for stable patterns and key decisions.

3. **Load lessons**: Read `.claude/memory/lessons-learned.md` for conventions and patterns to keep in mind.

4. **Check MCP health**: Run the `/mcp-doctor` skill to verify MCP servers are available.

5. **Query cognee** (if healthy): If the cognee MCP is healthy, call `cognee_search` with a query like "project context recent work" to retrieve relevant semantic context from the knowledge graph. Incorporate any useful findings.

6. **Present summary** to the user:

   ```
   Session Start
   =============
   Last session: [brief recap or "No previous sessions"]
   Open items: [list or "None"]
   MCP status: [cognee: healthy/unhealthy]
   Lessons active: [count] conventions, [count] patterns
   ```

7. **Ask the user**: "Continue previous work, or start something new?"

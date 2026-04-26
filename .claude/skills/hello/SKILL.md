---
name: hello
description: Start a new session — loads context, checks MCP health, recaps last session
user_invocable: true
---

# Session Start

You are starting a new working session. Load context and orient the user.

## Steps

1. **Check personal workspace**: Check if `~/.claude/me/identity.md` exists.
   - If missing, note it. Do not interrogate the user — identity will be built up organically by `/bye` as you work together.
   - If present, read it for user profile, role, and preferences.

2. **Load project context** (read all in parallel):
   - `.claude/memory/MEMORY.md` — distilled knowledge, stable patterns
   - `.claude/memory/lessons-learned.md` — conventions and lessons
   - `.claude/memory/project-context.md` — essential domain context
   - `.claude/memory/sessions/latest-session.md` — last session recap and active workstream

3. **Check MCP health**: Run the `/mcp-doctor` skill to verify MCP servers are available.

4. **Query cognee** (if healthy): If the cognee MCP is healthy, call `cognee_search` with a query like "project context recent work" to retrieve relevant semantic context from the knowledge graph. Incorporate any useful findings.

5. **Present summary** to the user:

   ```
   Session Start
   =============
   Last session: [brief recap or "No previous sessions"]
   Open items: [grouped by workstream — cross-reference `.claude/memory/workstreams/`
                files if latest-session.md has a flat list; never present all items
                as belonging to the last active workstream]
   MCP status: [cognee: healthy/unhealthy, other servers]
   Lessons active: [count] conventions, [count] patterns
   Identity: [loaded / not set up yet — will build over time]
   ```

6. **Ask what the user is working on**: After the summary, ask:
   - If a previous workstream exists in `latest-session.md`: "Last time you were working on [workstream name]. Want to continue that, or working on something else today?"
   - If no previous workstream: "What are you working on today?"

7. **Resolve workstream**: Based on the user's answer:
   - If they want to continue the last workstream, load it from `.claude/memory/workstreams/`
   - If they describe something new, list files in `.claude/memory/workstreams/` and check if any match the topic
     - If a match exists, confirm: "Looks like this relates to [workstream name] — shall I load that, or create a new one?"
     - If no match, create a new workstream file. If the scope is ambiguous, ask one clarifying question to name it well.
   - When creating a new workstream file, sanitize the filename:
     - Lowercase the workstream name
     - Replace any non-alphanumeric characters (except hyphens) with hyphens (allow only a-z, 0-9, and -)
     - Collapse repeated hyphens into single hyphens
     - Trim to a reasonable length (e.g., 50 characters)
     - Force the `.md` extension
     - Reject any input containing `..`, `/`, or other path separators — prompt for clarification if detected
     - Always join the sanitized slug to `.claude/memory/workstreams/` (never concatenate raw user input)
     - Fail with a validation prompt if the name cannot be safely normalized
   - The active workstream is now set for this session. `/bye` will use it without guessing.

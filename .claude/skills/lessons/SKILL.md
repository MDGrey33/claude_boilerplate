---
name: lessons
description: Capture and integrate lessons learned
user_invocable: true
args: Optional lesson description as free text
---

# Lessons Learned Handler

You are capturing lessons learned from the current session or from explicit user input.

## Input

Lessons can come from:
- The `/bye` skill passing identified lessons
- The user invoking `/lessons "description of what was learned"`
- Manual invocation with `/lessons` (you'll ask what was learned)

## Steps

1. **Gather lessons**: If lessons were passed as input, use those. If invoked manually without input, ask the user what they learned.

2. **Categorize** each lesson into one of:
   - `convention` — code style, naming, project patterns
   - `bug-pattern` — common mistakes, gotchas, debugging insights
   - `preference` — user preferences for tools, workflow, communication
   - `architecture` — structural decisions, design patterns
   - `tool-usage` — tips for tools, CLIs, MCP servers, frameworks

3. **Append to lessons file**: Read `.claude/memory/lessons-learned.md`, then append each lesson under the appropriate category section with this format:

   ```markdown
   - **[YYYY-MM-DD]** Description of the lesson
   ```

4. **Store in cognee** (if available): If the cognee MCP is healthy, call `cognee_add` with the lesson text (prefixed with its category), then call `cognee_cognify` to integrate it into the knowledge graph.

5. **Trigger skills-manager**: Invoke the `/skills-manager` skill to assess whether the lessons warrant updates to any skill files. Pass the lessons as context.

6. **Report**: Tell the user what was captured:

   ```
   Lessons captured: [count]
   Categories: [list]
   Cognee: stored / skipped (MCP unavailable)
   Skills review: [triggered / no changes needed]
   ```

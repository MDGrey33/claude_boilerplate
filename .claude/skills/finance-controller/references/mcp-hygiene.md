# MCP Hygiene Decision Rules

Loaded on demand when the audit flags MCP issues.

## Principle

MCP manifests load on every session. Every enabled server costs context before any work begins. The right answer is almost never "add another MCP" — it's usually "move this one to project scope" or "defer to ToolSearch."

## Decision tree per server

For each connected MCP, answer in order:

1. **Used in the last 30 days?** No → propose disable.
2. **Project-specific (touches only 1-2 codebases)?** Yes → propose moving to project-local `.mcp.json`.
3. **Heavy (≥ 20 tools) and rarely invoked?** Yes → propose migrating to deferred loading (ToolSearch pattern).
4. **Core to daily work?** Yes → keep always-on.

## Common patterns

| Pattern | Recommendation | Reason |
|---|---|---|
| Productivity MCPs used daily (Gmail, Calendar, Drive) | Keep always-on | Justified by daily use |
| Project-management MCPs (Jira, Asana, Linear) with ≥ 20 tools | Evaluate | Move to project scope unless used daily across multiple projects |
| Authentication-failing MCPs | Disable or re-auth | Dead MCPs still load their manifest; fix or remove |
| Design tools (Figma, etc.) | Disable when not in use | Re-enable via `claude mcp add` when starting a design session |
| Knowledge-graph / ingestion MCPs (cognee, etc.) | Project scope | Move to the specific project's `.mcp.json` |
| Browser / OS automation (Playwright, computer-use) | Keep always-on | Broad utility across projects |

## Re-enable patterns

For disabled MCPs, document how to re-enable in one line so future-you isn't stuck:

```bash
# Figma — re-enable when doing design work
claude mcp add figma https://mcp.figma.com/mcp

# Cognee — re-enable per project
cd ~/code/<project> && cp ~/.mcp-templates/cognee.json .mcp.json
```

(Store these patterns in `.claude/memory/mcp-reenable-recipes.md` if you accumulate more than ~5.)

## What finance-controller does NOT touch

- Does **not** run `claude mcp remove` — only recommends the command.
- Does **not** move `.mcp.json` files — only recommends the move and target path.
- Does **not** decide the user's tool preferences. If they want a specific MCP always-on, that's their call.

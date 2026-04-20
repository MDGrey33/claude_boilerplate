# patterns.md — community patterns and heuristics

Sources:
- https://github.com/wshobson/agents (184 agents, statistical analysis)
- https://github.com/VoltAgent/awesome-claude-code-subagents (130+ agents)
- https://github.com/davila7/claude-code-templates
- https://github.com/wshobson/commands
- https://glama.ai/mcp/servers

This file captures community-validated patterns that are not in official docs.
For surface-level reference, see the [surfaces/](surfaces/) files.
For failure modes, see [pitfalls.md](pitfalls.md).

## Four-tier model routing

The community consensus for subagent model selection:

| Model | Task type | Signal to use it |
|:--|:--|:--|
| `opus` | Complex reasoning, architecture, security | Security audits, system design, financial modeling |
| `sonnet` | General development | Coding, debugging, testing, deployment |
| `haiku` | Quick utility tasks | Documentation, search, simple checks |
| `inherit` | Cost control | High-volume tasks; let user set cost policy at session level |

`inherit` means the subagent uses whichever model the user selected for the
session. Opus tasks often complete in fewer iterations despite higher per-token
cost — measured 65% net token reduction for complex architectural work in the
wshobson collection.

Set via `model:` in the subagent frontmatter. Default is `inherit`.

## Progressive disclosure sizing

Skills follow a three-layer progressive disclosure architecture:

- **SKILL.md description** — always in context; `description + when_to_use`
  capped at 1,536 chars. Front-load trigger phrases.
- **SKILL.md body** — loaded on invoke; target 1,500–8,000 tokens for
  the body. If it balloons, move bulk to sibling files.
- **Sibling files** (`reference.md`, `examples.md`, scripts) — loaded on
  demand. SKILL.md must reference them so Claude knows where to look.

Community sizing from official skills repository:

| Skill type | Target body size |
|:--|:--|
| Simple utility | 500–1,500 tokens |
| Medium (API integration, doc generation) | 1,500–4,000 tokens |
| Complex multi-step | 4,000–8,000 tokens |
| Over 10,000 tokens | Split or decompose |

## Trigger phrase engineering

The `description` field is the semantic discovery hook. Claude matches
description text to the user's words. Rules:

1. **Action verb first:** "Generate", "Analyze", "Debug", "Deploy"
2. **Domain terms:** "Kubernetes manifests", "React components", "SQL queries"
3. **Input/output types:** "from JSON schema", "to PDF document"
4. **Edge cases:** "with error recovery", "supporting TypeScript"

Anti-patterns:
- "Helps with coding tasks" — too vague, no semantic hooks
- "Makes things better" — zero domain signal
- "Uses AST parsing" — describes how, not when

If a skill never triggers automatically, add `when_to_use:` with natural
language phrasings the user actually says.

## When to split a skill

| Condition | Action |
|:--|:--|
| Body under ~8,000 tokens, all instructions needed together | Keep in one SKILL.md |
| Body over ~10,000 tokens | Move bulk to sibling files, reference from SKILL.md |
| Distinct phases (plan / execute / validate) | Separate skills |
| Optional advanced features rarely used | Separate skill with `disable-model-invocation: true` |
| Clear domain boundary (Python vs JS, read vs write) | Separate skills |
| Skills share dependencies and compose naturally | Bundle as plugin |

"2–8 components per plugin" is the community-validated guideline (average
3.6 from wshobson/agents collection).

## Hook recipe pointers

Common hook patterns — see [surfaces/hooks.md](surfaces/hooks.md) for full
examples:

| Pattern | Hook event | Notes |
|:--|:--|:--|
| Block destructive Bash | `PreToolUse` on Bash with exit 2 | Simpler: use `permissions.deny` for static blocks |
| Auto-format after edit | `PostToolUse` on `Edit\|Write` | Deterministic linting |
| Load env at session start | `SessionStart` with `$CLAUDE_ENV_FILE` | Persists for session |
| Log every subagent finish | `SubagentStop` | Audit trail |
| Gate compaction | `PreCompact` | Save notes, or exit 2 to block |
| Alert on idle/permission | `Notification` | Desktop notification or Slack |
| Validate Claude's answer | `Stop` | Block until tests pass |

Hooks are the **only** deterministic surface. Memory and skills are
instructions Claude tries to follow; hooks are code the harness runs.
Anything that must happen on every X belongs in a hook, not CLAUDE.md.

## Curated agent collections

When building a new subagent, check these before writing from scratch:

- [wshobson/agents](https://github.com/wshobson/agents) — 184 production-ready
  agents across 25 categories, organized as plugins, with model routing and
  tool scoping patterns documented.
- [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents)
  — 130+ curated agents across 10 categories.

## MCP catalog pointers

When an integration already exists as an MCP server, use it rather than
building a subagent:

- [glama.ai/mcp/servers](https://glama.ai/mcp/servers) — 21,811 open-source
  servers indexed (2026-04-20). Filter by remote/local, language, category.
- [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)
  — curated community list (85.1k stars).
- [registry.modelcontextprotocol.io](https://registry.modelcontextprotocol.io)
  — official MCP registry.

Top categories available: Developer Tools (7,702), App Automation (4,042),
Search (4,013), Databases (2,073), Autonomous Agents (1,995).

## SDK vs Claude Code CLI — when to use which

| Situation | Pick |
|:--|:--|
| Interactive development at desk | Claude Code CLI |
| One-off task | CLI |
| CI/CD pipeline | Agent SDK |
| Production automation running unattended | Agent SDK |
| Custom app with programmatic control | Agent SDK |
| Need in-process MCP tools (no subprocess) | Agent SDK + `create_sdk_mcp_server` |

They share the same engine and config. CLI sessions and SDK agents can both
read `.claude/` for skills, memory, and plugins.

## ScheduleWakeup vs CronCreate vs /loop

| Tool | Use when |
|:--|:--|
| `/loop` (no interval) | Self-pacing poll; ScheduleWakeup picks delays to stay in cache window |
| `/loop 4m <prompt>` | Fixed short interval, stays in 5-min cache TTL |
| `CronCreate` | You want an explicit cron expression or one-shot reminder |
| `/schedule` (Routines) | Must survive machine off; minimum 1-hour interval |
| Desktop scheduled tasks | Local files, survive session close, minimum 1 minute |

Avoid shell `sleep 300` in loops — it busts the 5-minute prompt cache.

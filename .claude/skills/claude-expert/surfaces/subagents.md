# Subagents — deep reference

Source: https://code.claude.com/docs/en/sub-agents

## What a subagent is

> "Subagents are specialized AI assistants that handle specific types of
> tasks. Use one when a side task would flood your main conversation with
> search results, logs, or file contents you won't reference again: the
> subagent does that work in its own context and returns only the summary."

Each subagent runs in its **own context window** with its own system prompt,
tools, permissions, and (optionally) model, memory, MCP servers, and hooks.

Subagents work within a single session. For cross-session parallel teammates,
see agent teams (different feature).

## Why / when

- Isolate verbose output (test runs, log dumps, large search results).
- Enforce tool restrictions (read-only reviewer, DB-read-only agent).
- Route to cheaper model (Haiku) for routine work.
- Reuse configurations across projects (user-level subagents).

Use the main conversation when the task needs back-and-forth or when latency
matters — subagents start fresh.

## Where they live

| Source | Path / flag | Priority |
|:--|:--|:--|
| Managed | managed settings `.claude/agents/` | 1 (highest) |
| CLI | `--agents '{"name": {...}}'` JSON | 2 |
| Project | `.claude/agents/*.md` | 3 |
| User | `~/.claude/agents/*.md` | 4 |
| Plugin | plugin `agents/*.md` | 5 (lowest) |

`--add-dir` does NOT load subagents from added directories. For cross-project
sharing, use `~/.claude/agents/` or a plugin.

Plugin subagents **ignore** `hooks`, `mcpServers`, and `permissionMode` for
security. Copy into `.claude/agents/` if you need those fields.

## Frontmatter schema

Required: `name`, `description`.

| Field | Description |
|:--|:--|
| `name` | Lowercase, hyphens. |
| `description` | When Claude should delegate. Use "proactively" for auto-delegation. |
| `tools` | Allowlist. Omit to inherit all. Space-separated or YAML list. `Agent(worker, researcher)` to restrict which subagents this agent can spawn. |
| `disallowedTools` | Denylist. Applied first, then `tools` resolves. |
| `model` | `sonnet`/`opus`/`haiku`/full ID/`inherit`. Default `inherit`. |
| `permissionMode` | `default`/`acceptEdits`/`auto`/`dontAsk`/`bypassPermissions`/`plan`. |
| `maxTurns` | Max agentic turns. |
| `skills` | Array of skills preloaded into context at startup. |
| `mcpServers` | Array of inline server configs or string refs. |
| `hooks` | Lifecycle hooks scoped to this subagent. |
| `memory` | `user`/`project`/`local`. Enables cross-session learning. |
| `background` | `true` = always run in background. |
| `effort` | `low`/`medium`/`high`/`xhigh`/`max`. |
| `isolation` | `worktree` = run in a temp git worktree. |
| `color` | `red`/`blue`/`green`/`yellow`/`purple`/`orange`/`pink`/`cyan`. |
| `initialPrompt` | Auto-submitted as first user turn when agent is main session. |

Subagents start in the parent's cwd; `cd` doesn't persist between tool calls.
For an isolated repo copy, set `isolation: worktree`.

## Body

Markdown after the frontmatter is the **system prompt** for the subagent.
Subagents receive only this, not the default Claude Code system prompt.

## Built-in subagents

| Agent | Model | Tools | Purpose |
|:--|:--|:--|:--|
| Explore | Haiku | Read-only | File discovery, code search |
| Plan | Inherit | Read-only | Plan-mode research |
| general-purpose | Inherit | All | Complex multi-step |
| statusline-setup | Sonnet | — | `/statusline` configuration |
| Claude Code Guide | Haiku | — | Questions about Claude Code features |

## Invocation

### Natural language
Mention the subagent by name; Claude typically delegates.

### @-mention
`@"code-reviewer (agent)"` guarantees that subagent runs. Plugin subagents
appear as `@<plugin-name>:<agent-name>`.

### Session-wide
```bash
claude --agent code-reviewer
```
Or in settings:
```json
{ "agent": "code-reviewer" }
```

### Nesting rule
**Subagents CANNOT spawn other subagents.** For nested delegation, use skills
(which can spawn subagents via `context: fork`) or chain from the main
conversation.

### Restricting spawnable subagents
When an agent runs as the main thread with `claude --agent`, it can spawn
subagents via the Agent tool. Restrict with `tools: Agent(worker,
researcher)`. Exclusive allowlist. `Agent` alone allows any. Omitting Agent
entirely blocks all spawning.

## Tool control

- `tools: Read, Grep, Glob, Bash` — allowlist only.
- `disallowedTools: Write, Edit` — inherit everything except these.
- If both set, `disallowedTools` applied first, then `tools` resolves.

## MCP server scoping

```yaml
mcpServers:
  - playwright:
      type: stdio
      command: npx
      args: ["-y", "@playwright/mcp@latest"]
  - github   # string ref to already-configured server
```

Inline servers start when subagent spawns, stop when it ends. Keeps tools
out of the main conversation context (saving description budget).

## Permission modes

| Mode | Behavior |
|:--|:--|
| `default` | Standard prompts |
| `acceptEdits` | Auto-accept edits and fs cmds in cwd/additionalDirectories |
| `auto` | Background classifier reviews |
| `dontAsk` | Auto-deny unless pre-approved |
| `bypassPermissions` | Skip prompts (still prompts for `.git`, `.claude`, `.vscode`, `.idea`, `.husky`) |
| `plan` | Read-only exploration |

Parent mode can override: `bypassPermissions` and `acceptEdits` from parent
take precedence. `auto` parent forces `auto` on subagent regardless of frontmatter.

## Preloading skills

```yaml
skills:
  - api-conventions
  - error-handling-patterns
```

Full skill content is **injected at startup**, not just made available. Does
NOT inherit skills from parent.

## Persistent memory

`memory: user|project|local`.

| Scope | Location |
|:--|:--|
| `user` | `~/.claude/agent-memory/<agent-name>/` |
| `project` | `.claude/agent-memory/<agent-name>/` |
| `local` | `.claude/agent-memory-local/<agent-name>/` |

When enabled: system prompt gets read/write instructions, first 200 lines or
25 KB of `MEMORY.md` injected, Read/Write/Edit tools auto-enabled.

## Hooks

Defined in frontmatter or `settings.json`. Frontmatter hooks fire only when
agent is spawned as a subagent, NOT when run as the main session via
`--agent`. Stop hooks in frontmatter auto-convert to `SubagentStop`.

`settings.json` can also watch `SubagentStart` / `SubagentStop` events for
main-session lifecycle.

## Disabling specific subagents

```json
{ "permissions": { "deny": ["Agent(Explore)", "Agent(my-custom-agent)"] } }
```

Or CLI: `claude --disallowedTools "Agent(Explore)"`.

## Running foreground vs background

- Foreground — blocks main conversation until complete. Permission prompts
  pass through.
- Background — runs concurrently. Claude Code pre-approves all needed
  permissions before launching. Auto-denies unapproved tools after.

User presses `Ctrl+B` to background a running task. Disable background tasks
entirely with `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`.

## Resume and transcripts

- Each invocation creates a fresh instance unless resumed via `SendMessage`
  (requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`).
- Transcripts in `~/.claude/projects/{project}/{sessionId}/subagents/agent-{id}.jsonl`.
- Survive main-conversation compaction.
- Auto-cleanup via `cleanupPeriodDays` (default 30).
- Auto-compaction inside subagent at ~95% by default; override with
  `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50`.

## Gotchas

- No nesting: subagent cannot spawn another subagent.
- Plugin subagents: `hooks`, `mcpServers`, `permissionMode` ignored.
- `--add-dir` doesn't load subagents from added directories.
- `cd` in Bash doesn't persist between tool calls and doesn't affect parent.
- Session-wide `claude --agent` replaces the default system prompt entirely
  (CLAUDE.md and memory still load).
- Adding a subagent file manually requires session restart or `/agents` to reload.

## Four-tier model routing (community consensus)

Source: https://github.com/wshobson/agents (statistical analysis of 184 agents)

Community analysis of production agent repositories reveals a consensus pattern:

| Model | Use case | When to pick |
|:--|:--|:--|
| `opus` | Complex reasoning, architecture, security | Security audits, system design, financial modeling |
| `sonnet` | General development, refactoring | Coding, debugging, testing, deployment |
| `haiku` | Quick utility tasks | Documentation, searches, simple checks |
| `inherit` | User-controlled cost optimization | High-volume tasks where cost matters more than capability ceiling |

`inherit` (42 of 184 sampled agents) matches the parent conversation model —
useful when users want to set cost policy at the session level. Opus tasks
often complete in fewer iterations despite higher per-token cost, yielding
a net 65% token reduction for complex architectural work.

Curated agent collections: [github.com/wshobson/agents](https://github.com/wshobson/agents) (184 agents, 25 categories),
[github.com/VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) (130+ agents).

## Canonical tool scopes

Community has converged on four canonical least-privilege tool sets:

| Role | Tools | Example agents |
|:--|:--|:--|
| Read-only reviewer/auditor | `Read, Grep, Glob` | security auditor, compliance checker |
| Research/analyst | `Read, Grep, Glob, WebFetch, WebSearch` | market research, trend monitoring |
| Code writer/developer | `Read, Write, Edit, Bash, Glob, Grep` | feature dev, bug fixer |
| Documentation writer | `Read, Write, Edit, Glob, Grep, WebFetch, WebSearch` | technical writer, API docs |

## Disambiguation

- **Subagent vs skill:** subagent = isolated context + own system prompt;
  skill = instructions loaded into existing context. Subagent when verbose
  output would flood main; skill when the work needs conversational context.
- **Subagent with preloaded skills vs skill with `context: fork`:**
  - Subagent + `skills:` — the subagent's markdown body is the system prompt;
    skill content is reference material.
  - Skill `context: fork` — the skill body IS the task prompt; agent type
    provides the environment.
- **Subagent vs agent team:** subagents are single-session workers; agent
  teams coordinate across separate sessions and support parallel teammates
  communicating with each other.
- **Subagent vs MCP tool:** subagent = behavior pattern; MCP = external
  capability. Pair them.

## Minimal worked example — read-only code reviewer

```
~/.claude/agents/code-reviewer.md
```

```markdown
---
name: code-reviewer
description: Expert code review specialist. Proactively reviews code for quality, security, and maintainability. Use immediately after writing or modifying code.
tools: Read, Grep, Glob, Bash
model: inherit
---

You are a senior code reviewer ensuring high standards of code quality and security.

When invoked:
1. Run `git diff` to see recent changes
2. Focus on modified files
3. Begin review immediately

Review checklist:
- Code is clear and readable
- Functions and variables are well-named
- No duplicated code
- Proper error handling
- No exposed secrets or API keys
- Input validation implemented
- Good test coverage
- Performance considerations addressed

Provide feedback organized by priority:
- Critical issues (must fix)
- Warnings (should fix)
- Suggestions (consider improving)

Include specific examples of how to fix issues.
```

Invoke: "Use the code-reviewer subagent to review my recent changes" or
`@"code-reviewer (agent)" review this`.

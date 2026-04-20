---
name: claude-expert
description: Definitive reference for how Claude Code works — disambiguates skills vs hooks vs subagents vs MCPs vs slash commands vs memory vs settings. Use when asked "how does Claude Code X work", "what's the difference between X and Y", "where should this live", "build me a [skill|hook|agent|mcp|slash command]", "configure Claude Code", or when picking the right surface for a new capability.
---

# claude-expert — the router, not the doer

This skill is the **reference** for Claude Code's extension surfaces. It tells
you which surface to pick and where to read for depth. It does not itself edit
settings, write skills, or modify keybindings — for those, delegate to the
existing doer skills listed at the bottom.

All content is distilled from the official docs at
[code.claude.com/docs](https://code.claude.com/docs/en/overview). When details
here conflict with the live docs, the live docs win.

## Decision tree — which surface?

**Fastest answer for "skill vs subagent vs hook vs md-file":** see the
[four-way table at the top of decision-tree.md](decision-tree.md#the-four-way-skill-vs-subagent-vs-hook-vs-md-file).
The full per-goal lookup is below it. The short form of the primary table:

| I want to... | Surface | Deep dive |
|:--|:--|:--|
| Automate behavior on every tool call, prompt, or session event | **Hook** | [surfaces/hooks.md](surfaces/hooks.md) |
| Give Claude a reusable playbook it loads when relevant | **Skill** | [surfaces/skills.md](surfaces/skills.md) |
| Let the user type `/foo` to run a workflow | **Skill** (custom commands merged into skills) | [surfaces/slash-commands.md](surfaces/slash-commands.md) |
| Run specialist work in an isolated context window | **Subagent** | [surfaces/subagents.md](surfaces/subagents.md) |
| Connect to an external service, DB, or API | **MCP server** | [surfaces/mcp.md](surfaces/mcp.md) |
| Persist a fact/preference across sessions | **Memory** (`CLAUDE.md` or auto-memory) | [surfaces/memory.md](surfaces/memory.md) |
| Configure permissions, env vars, hooks at a project or user level | **Settings.json** | [surfaces/settings.md](surfaces/settings.md) |
| Ship a bundle (skills + agents + hooks + MCP) to a team | **Plugin** | [surfaces/plugins.md](surfaces/plugins.md) |
| Block or auto-approve a tool call | **Permission rule** or **PreToolUse hook** | [surfaces/permissions.md](surfaces/permissions.md) |
| Build a standalone agent outside the CLI (Python/TS) | **Agent SDK** | [surfaces/agent-sdk.md](surfaces/agent-sdk.md) |
| Run recurring or scheduled work | **`/loop`**, **CronCreate**, Routines, Desktop scheduled tasks | [surfaces/background-tasks.md](surfaces/background-tasks.md) |
| Rebind a keyboard shortcut | **Keybindings** (`~/.claude/keybindings.json`) | [surfaces/keybindings.md](surfaces/keybindings.md) |
| Understand what loads into context and when | **Context management** | [surfaces/context-management.md](surfaces/context-management.md) |
| Use Claude Code in VS Code / JetBrains / Desktop / web | **IDE integration** | [surfaces/ide-integrations.md](surfaces/ide-integrations.md) |

## Short summaries of each surface

### Skills
A `SKILL.md` file (markdown + YAML frontmatter) at
`~/.claude/skills/<name>/SKILL.md` or `.claude/skills/<name>/SKILL.md`. Claude
loads the description eagerly into context and the body on-demand when invoked
(by `/skill-name` or automatically when the description matches). Custom
commands have been merged into skills: `.claude/commands/deploy.md` and
`.claude/skills/deploy/SKILL.md` both produce `/deploy` — skills add a
directory for supporting files and more frontmatter. Keep SKILL.md under 500
lines; offload references. See [surfaces/skills.md](surfaces/skills.md).

### Hooks
User-defined shell commands, HTTP endpoints, prompts, or LLM agents that run
automatically at lifecycle events (`PreToolUse`, `PostToolUse`,
`SessionStart`, `UserPromptSubmit`, `Stop`, `SubagentStop`, `FileChanged`,
etc.). Configured in `settings.json`, plugin `hooks/hooks.json`, or
skill/agent frontmatter. Hooks can block tool calls (exit 2 or `deny`),
inject context, or enforce policy — this is the **only** way to deterministically
force the harness to do something. Memory/preferences CANNOT fulfill
"from now on, every time X". See [surfaces/hooks.md](surfaces/hooks.md).

### Subagents
Markdown files with YAML frontmatter at `.claude/agents/<name>.md` or
`~/.claude/agents/<name>.md`. Each runs in its own context window with its
own tool restrictions, model, permission mode, optional MCP servers, and
optional memory. Claude delegates automatically (by `description` match) or
on request (`@agent-name` or `--agent <name>`). Use when you need context
isolation; skip when the task needs quick back-and-forth. Built-ins:
`Explore`, `Plan`, `general-purpose`. See
[surfaces/subagents.md](surfaces/subagents.md).

### MCP (Model Context Protocol)
External tools/data/APIs connected over stdio, HTTP, or SSE. Add via
`claude mcp add --transport <http|sse|stdio> <name> ...`. Tools are exposed
as `mcp__<server>__<tool>`. Scopes: local (default), project (shared via
`.mcp.json`), user. Build an MCP server when an integration is reusable
across agents/sessions; build a subagent or skill when it's Claude-specific
behavior. See [surfaces/mcp.md](surfaces/mcp.md).

### Slash commands
Built-in commands (like `/help`, `/compact`, `/config`, `/doctor`) plus
bundled skills (like `/simplify`, `/batch`, `/debug`, `/loop`, `/claude-api`).
Custom slash commands = skills. Plugin-provided commands are namespaced
`/plugin-name:command-name`. See
[surfaces/slash-commands.md](surfaces/slash-commands.md).

### Settings
JSON files at four scopes: managed (enterprise policy, not overridable),
project-local (`.claude/settings.local.json`, gitignored), project
(`.claude/settings.json`, in VCS), user (`~/.claude/settings.json`). Hold
permissions rules, env vars, hooks, model, statusLine, autoMode classifier,
plugins, attribution, sandbox, etc. Arrays merge across scopes. See
[surfaces/settings.md](surfaces/settings.md).

### Plugins
Distributable bundles with a `.claude-plugin/plugin.json` manifest plus any
of `skills/`, `agents/`, `hooks/`, `.mcp.json`, `.lsp.json`, `monitors/`,
`bin/`, `settings.json`. Installed via marketplaces (`/plugin`) or loaded
ad-hoc with `--plugin-dir`. Plugin skills are namespaced
`/plugin-name:skill-name`. See [surfaces/plugins.md](surfaces/plugins.md).

### Memory
`CLAUDE.md` files (written by you) + auto-memory (written by Claude). Project
root CLAUDE.md loads in full at session start; subdirectory ones load on
demand; `.claude/rules/*.md` can be scoped by `paths:` globs. Auto-memory
lives at `~/.claude/projects/<project>/memory/MEMORY.md` by default and
injects its first 200 lines / 25 KB. Use `@path` imports. Memory is context,
NOT enforcement. See [surfaces/memory.md](surfaces/memory.md).

### Agent SDK
TypeScript (`@anthropic-ai/claude-agent-sdk`) or Python
(`claude-agent-sdk`). Same tools, agent loop, and context management as the
CLI, programmable. Use for CI/CD, production automation, custom apps. Not
for interactive development — use the CLI for that. See
[surfaces/agent-sdk.md](surfaces/agent-sdk.md).

### Permissions
Allow/ask/deny rules in `settings.json`. Precedence: deny > ask > allow,
first match wins. Tool rules like `Bash(git commit *)`, `Read(./.env)`,
`WebFetch(domain:example.com)`, `Agent(Explore)`, `mcp__server__*`,
`Skill(name)`. Permission modes: `default`, `acceptEdits`, `plan`, `auto`,
`dontAsk`, `bypassPermissions`. See
[surfaces/permissions.md](surfaces/permissions.md).

### Background / scheduled tasks
`/loop [interval] [prompt]` — session-scoped recurring prompt (7-day
expiry). `CronCreate`/`CronList`/`CronDelete` — session-scoped Claude-callable
tools using 5-field cron expressions. `/schedule` or Routines — cloud-run,
survive machine off. Desktop scheduled tasks — local, survive session close.
See [surfaces/background-tasks.md](surfaces/background-tasks.md).

### Context management
Skill descriptions = 1% of context window / 8,000 char fallback budget
(override with `SLASH_COMMAND_TOOL_CHAR_BUDGET`). Per-skill description +
`when_to_use` capped at 1,536 chars. Invoked skills re-attached after
compaction at 5,000 tokens each, combined 25,000-token budget. See
[surfaces/context-management.md](surfaces/context-management.md).

### IDE integrations
VS Code and JetBrains plugins. Share CLAUDE.md, settings, MCP servers,
conversation history with the CLI. Extension has an internal `ide` MCP
server exposing `mcp__ide__getDiagnostics` and `mcp__ide__executeCode`
(Jupyter, user-confirmed). See
[surfaces/ide-integrations.md](surfaces/ide-integrations.md).

### Keybindings
`~/.claude/keybindings.json`. Contexts (`Global`, `Chat`, `Autocomplete`,
`Confirmation`, `Scroll`, `MessageSelector`, and many others). Action
namespaces (`chat:submit`, `app:interrupt`, etc.). Chord syntax:
`ctrl+x ctrl+s`. Reserved: `Ctrl+C`, `Ctrl+D`, `Ctrl+M`. Hot-reloaded. See
[surfaces/keybindings.md](surfaces/keybindings.md).

## Delegation — claude-expert is the reference, not the editor

This skill answers "what is X" and "where should Y live". To actually change
the system, delegate:

| Task | Delegate to |
|:--|:--|
| Write/update a skill, archive an old one, reorganize skills | `skills-manager` |
| Edit `~/.claude/settings.json`, `.claude/settings.json`, add permission rules (allow/ask/deny), add/edit hooks, configure env vars | `update-config` |
| Edit `~/.claude/keybindings.json` | `keybindings-help` |
| Check MCP server health | `mcp-doctor` |
| Build a prioritized permission allowlist from transcripts | `fewer-permission-prompts` (bundled) |

Say it plain: claude-expert teaches the map; the doer skills drive the car.

## How to use this skill

- **Free-form question:** "How do hooks differ from memory?" → claude-expert
  points you to [surfaces/hooks.md](surfaces/hooks.md) and
  [surfaces/memory.md](surfaces/memory.md), or answers from the summary if the
  answer is short.
- **Which-surface question:** "Where should I put a rule that blocks `rm -rf`?"
  → claude-expert points you to PreToolUse deny or a `deny` permission rule,
  then delegates writing it to `update-config`.
- **Scoped arg:** Pass a surface name: `/claude-expert hooks` opens the hooks
  reference; `/claude-expert settings` opens settings; etc. (claude-expert
  reads the file and brings it into context.)
- **For doing:** don't let claude-expert edit. Ask it which surface, then
  delegate to the doer.

## Answer protocol — docs first

When answering "how does Claude Code actually do X":

1. **Read the relevant `surfaces/<topic>.md`** for the distilled doc answer.
2. **If that's sufficient, answer and stop.** Cite `code.claude.com/docs`.
3. **If the surface file is silent, ambiguous, or flagged `(docs unclear —
   verify before relying on this)`**, follow the live docs at
   [code.claude.com/docs](https://code.claude.com/docs/en/overview) and the
   SDK repos (`anthropics/claude-agent-sdk-*`).
4. **Delegate deep doc reads to the `Explore` subagent** to keep main context clean.

## Pointer

Full disambiguation table: [decision-tree.md](decision-tree.md).
Community patterns, routing rules, catalog pointers: [patterns.md](patterns.md).
Common failure modes with fixes: [pitfalls.md](pitfalls.md).

## Version / freshness

Based on docs read 2026-04. `docs.claude.com/en/docs/claude-code/*`
301-redirects to `code.claude.com/docs/en/*`. Agent SDK docs live on
`code.claude.com/docs/en/agent-sdk/*` (formerly `platform.claude.com`).

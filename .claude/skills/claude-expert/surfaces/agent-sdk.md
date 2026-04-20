# Agent SDK — deep reference

Source: https://code.claude.com/docs/en/agent-sdk/overview (formerly hosted
at platform.claude.com; now redirects to code.claude.com). Note: the SDK
was renamed from "Claude Code SDK" to "Claude Agent SDK".

## What the SDK is

> "Build AI agents that autonomously read files, run commands, search the
> web, edit code, and more. The Agent SDK gives you the same tools, agent
> loop, and context management that power Claude Code, programmable in
> Python and TypeScript."

Same engine as the CLI; different interface. Use the SDK when you're
building production automation, CI/CD pipelines, or custom apps. Use the
CLI for interactive development.

## Packages

| Language | Package | Install |
|:--|:--|:--|
| TypeScript | `@anthropic-ai/claude-agent-sdk` | `npm install @anthropic-ai/claude-agent-sdk` |
| Python | `claude-agent-sdk` | `pip install claude-agent-sdk` |

TypeScript SDK bundles a native Claude Code binary as optional dep — no
separate CLI install required.

## Authentication

```bash
export ANTHROPIC_API_KEY=your-api-key
```

Or third-party providers:
- `CLAUDE_CODE_USE_BEDROCK=1` + AWS creds.
- `CLAUDE_CODE_USE_VERTEX=1` + GCP creds.
- `CLAUDE_CODE_USE_FOUNDRY=1` + Azure creds.

**Critical restriction:** Anthropic does NOT allow third-party developers
to offer claude.ai login or rate limits in their own products (agents
built on the SDK included) without prior approval. Use API key auth.

## Opus 4.7 requirement

`claude-opus-4-7` requires Agent SDK v0.2.111+. A `thinking.type.enabled`
error typically means the SDK is too old. Older versions use `thinking.type`
as a string; v0.2.111+ uses `thinking.type.adaptive` and `output_config.effort`.

## Primary primitives

### `query` generator (stateless)

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    async for message in query(
        prompt="Find and fix the bug in auth.py",
        options=ClaudeAgentOptions(allowed_tools=["Read", "Edit", "Bash"]),
    ):
        print(message)

asyncio.run(main())
```

TypeScript:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Find and fix the bug in auth.ts",
  options: { allowedTools: ["Read", "Edit", "Bash"] }
})) {
  console.log(message);
}
```

### `ClaudeSDKClient` (streaming / sessions)

For resumable sessions and multi-turn conversations. See `/en/agent-sdk/sessions`.

## Capabilities (what the SDK exposes)

### Built-in tools

Read, Write, Edit, Bash, Monitor, Glob, Grep, WebSearch, WebFetch,
AskUserQuestion — same as the CLI. Plus standard Claude Code internals.

### Hooks

Callback functions instead of shell commands:

```python
from claude_agent_sdk import HookMatcher

async def log_file_change(input_data, tool_use_id, context):
    file_path = input_data.get("tool_input", {}).get("file_path", "unknown")
    # ... write to audit log
    return {}

options = ClaudeAgentOptions(
    hooks={
        "PostToolUse": [
            HookMatcher(matcher="Edit|Write", hooks=[log_file_change])
        ]
    },
)
```

Available events: `PreToolUse`, `PostToolUse`, `Stop`, `SessionStart`,
`SessionEnd`, `UserPromptSubmit`, and more.

### Subagents

```python
from claude_agent_sdk import AgentDefinition

options = ClaudeAgentOptions(
    allowed_tools=["Read", "Glob", "Grep", "Agent"],  # Agent tool required
    agents={
        "code-reviewer": AgentDefinition(
            description="Expert code reviewer for quality and security.",
            prompt="Analyze code quality and suggest improvements.",
            tools=["Read", "Glob", "Grep"],
        )
    },
)
```

Messages from a subagent's context include `parent_tool_use_id` so you can
track which subagent produced what.

### MCP servers

```python
options = ClaudeAgentOptions(
    mcp_servers={
        "playwright": {"command": "npx", "args": ["@playwright/mcp@latest"]}
    }
)
```

Same stdio/HTTP/SSE schemas as the CLI. Inline MCPs can be defined
programmatically.

### Permissions

`allowed_tools` / `allowedTools` pre-approves. `permission_mode` sets
mode. For interactive approvals, use the `AskUserQuestion` tool.

### Sessions

```python
# First query — capture session ID
session_id = None
async for message in query(prompt="Read the auth module",
                           options=ClaudeAgentOptions(allowed_tools=["Read"])):
    if isinstance(message, SystemMessage) and message.subtype == "init":
        session_id = message.data["session_id"]

# Resume with full context
async for message in query(prompt="Now find callers",
                           options=ClaudeAgentOptions(resume=session_id)):
    if isinstance(message, ResultMessage):
        print(message.result)
```

## Filesystem-based config

By default, the SDK loads `.claude/` from cwd and `~/.claude/` for skills,
slash commands, memory, and plugins. Restrict with `setting_sources`
(Python) or `settingSources` (TypeScript) in `ClaudeAgentOptions`.

Loaded config:

| Feature | Location |
|:--|:--|
| Skills | `.claude/skills/*/SKILL.md` |
| Slash commands | `.claude/commands/*.md` |
| Memory | `CLAUDE.md` or `.claude/CLAUDE.md` |
| Plugins | Programmatic via `plugins` option |

## Agent SDK vs alternatives

### Agent SDK vs Anthropic Client SDK

Client SDK gives direct API access — you implement the tool loop. Agent
SDK handles the loop, provides tools, manages context.

```python
# Client SDK: you implement
response = client.messages.create(...)
while response.stop_reason == "tool_use":
    result = your_tool_executor(response.tool_use)
    response = client.messages.create(tool_result=result, **params)

# Agent SDK: handled
async for message in query(prompt="Fix the bug in auth.py"):
    print(message)
```

### Agent SDK vs Claude Code CLI

| Use case | Best choice |
|:--|:--|
| Interactive development | CLI |
| CI/CD pipelines | SDK |
| Custom applications | SDK |
| One-off tasks | CLI |
| Production automation | SDK |

Teams often use both. Workflows translate between them directly.

## Changelog / issue tracking

- TypeScript: https://github.com/anthropics/claude-agent-sdk-typescript
- Python: https://github.com/anthropics/claude-agent-sdk-python

## Branding (for third-party integrations)

Allowed: "Claude Agent", "Claude", "{YourAgentName} Powered by Claude".
NOT permitted: "Claude Code", "Claude Code Agent", Claude Code ASCII art
or visuals.

## Prompt caching in the SDK

Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

Two TTL options:
- **5-minute TTL (default):** ephemeral cache. Reuse within 5 minutes at no extra
  cost. Cache hits cost 10% of base input token price.
- **1-hour TTL:** 2x base price to write; 10% to read.

Cache writes cost 25% more than base (5-min) or 2x base (1-hour). For a
100,000-token cached document reused 10 times, total cost ~$1.075 vs. $5
without caching — **78% savings**.

Best practice: place stable content first (tools, system instructions),
variable content (messages) last. Cache invalidates when tool definitions
change, images are added/removed, or web search toggles. Monitor via
`response.usage.cache_read_input_tokens`.

**Sleep >300s busts the 5-min cache.** In agentic loops avoid `sleep 300`
or longer; use ScheduleWakeup (dynamic `/loop`) or the `Monitor` tool to
stay within the cache window.

## Gotchas

- Subagent invocation via Agent tool requires `"Agent"` in `allowed_tools`.
- Opus 4.7 requires SDK v0.2.111+.
- No claude.ai login in third-party products without prior Anthropic approval.
- Default filesystem config loading can be surprising in CI — set
  `setting_sources` explicitly when you want isolation.
- HookMatcher in SDK accepts callbacks; in CLI hooks are shell commands,
  HTTP, prompt, or LLM.

## Disambiguation

- **Agent SDK vs CLI:** same engine, different interface. SDK for
  automation, CLI for interactive.
- **Agent SDK vs Anthropic Client SDK:** Client SDK is raw API access;
  Agent SDK wraps tools, loop, context.
- **Agent SDK subagent vs CLI subagent:** same concept. SDK defines via
  `AgentDefinition`; CLI via `.claude/agents/*.md`.
- **Agent SDK MCP vs CLI MCP:** identical config schema. SDK passes inline
  via `mcp_servers`; CLI reads `.mcp.json`.

## Minimal example

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    async for message in query(
        prompt="Find all TODO comments and create a summary",
        options=ClaudeAgentOptions(allowed_tools=["Read", "Glob", "Grep"]),
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

More: https://github.com/anthropics/claude-agent-sdk-demos (email
assistant, research agent, etc.).

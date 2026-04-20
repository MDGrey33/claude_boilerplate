# Hooks — deep reference

Source: https://code.claude.com/docs/en/hooks

## What hooks are

> "Hooks are user-defined shell commands, HTTP endpoints, or LLM prompts that
> execute automatically at specific points in Claude Code's lifecycle."

Hooks are the **only deterministic** extension surface. The harness runs them
regardless of what Claude decides. Memory and skills are instructions Claude
tries to follow; hooks are code the harness executes. If a requirement is
"from now on, every time X happens, do Y", the correct surface is always a
hook.

## Where hooks live

- `~/.claude/settings.json` — user scope, all projects.
- `.claude/settings.json` — project scope, shared in VCS.
- `.claude/settings.local.json` — project local, gitignored.
- Plugin `hooks/hooks.json` — plugin-scoped.
- Skill or agent frontmatter → `hooks:` block — component-scoped lifecycle.

Managed settings can enforce `allowManagedHooksOnly: true` to block user
and project hooks.

## All hook events (authoritative)

### Session events

| Event | Matchers | When it fires |
|:--|:--|:--|
| `SessionStart` | `startup`, `resume`, `clear`, `compact` | Session begins or resumes |
| `SessionEnd` | — | Session ends |
| `InstructionsLoaded` | `session_start`, `nested_traversal`, `path_glob_match`, `include`, `compact` | CLAUDE.md / rules load |

### Prompt / turn events

| Event | When it fires |
|:--|:--|
| `UserPromptSubmit` | Before Claude processes a user prompt |
| `Stop` | Claude finishes responding |
| `StopFailure` | Turn ends due to API error. Matchers: `rate_limit`, `authentication_failed`, `billing_error`, `invalid_request`, `server_error`, `max_output_tokens`, `unknown` |

### Tool events

| Event | When it fires |
|:--|:--|
| `PreToolUse` | Before a tool call. Can block, modify input, or grant approval. |
| `PostToolUse` | After a tool succeeds. |
| `PostToolUseFailure` | After a tool fails. |
| `PermissionRequest` | User permission dialog shown. Can auto-approve/deny. |
| `PermissionDenied` | Auto mode classifier denies a call. Can allow retry. |

Matcher for tool events: tool name. Supports `Bash`, `Edit`, `Write`,
`Read`, `Glob`, `Grep`, `Agent`, `WebFetch`, `WebSearch`, `AskUserQuestion`,
`mcp__<server>__.*` regex, pipe-separated lists like `Edit|Write`, `*` for
all.

### Agent / task events

| Event | Matcher | When it fires |
|:--|:--|:--|
| `SubagentStart` | Agent type name | Subagent spawned |
| `SubagentStop` | Agent type name | Subagent completes |
| `TaskCreated` | — | `TaskCreate` tool used |
| `TaskCompleted` | — | Task marked complete |
| `TeammateIdle` | — | Agent-team teammate about to idle |

### File / config events

| Event | Matcher | When it fires |
|:--|:--|:--|
| `FileChanged` | literal filenames | Watched file changes on disk |
| `ConfigChange` | `user_settings`, `project_settings`, `local_settings`, `policy_settings`, `skills` | Config file changes |
| `CwdChanged` | — | cwd changes (e.g. after `cd`) |

### Compaction / utility events

| Event | Matcher | When it fires |
|:--|:--|:--|
| `PreCompact` | — | Before context compaction |
| `PostCompact` | — | After compaction |
| `Notification` | `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog` | Claude Code notifies user |
| `Elicitation` | MCP server name | MCP requests user input |
| `ElicitationResult` | — | After user responds |

### Worktree events

- `WorktreeCreate` — exit 0 with path on stdout; non-zero fails creation.
- `WorktreeRemove` — no decision control.

## Hook types (handlers)

| Type | Config keys |
|:--|:--|
| `command` | `command`, `timeout` (default 600s), `statusMessage`, `async`, `asyncRewake`, `shell` |
| `http` | `url`, `timeout` (default 30s), `headers`, `allowedEnvVars` |
| `prompt` | `prompt`, `model`, `timeout` (default 30s) |
| `agent` | `prompt`, `timeout` (default 60s) |

Env vars available to commands: `CLAUDE_PROJECT_DIR`, `CLAUDE_PLUGIN_ROOT`,
`CLAUDE_PLUGIN_DATA`, `CLAUDE_ENV_FILE` (write export statements here for
SessionStart/CwdChanged/FileChanged), `CLAUDE_CODE_REMOTE="true"` in web env.

## Matchers

- `"*"`, `""`, or omitted → match all.
- Letters/digits/`_`/`|` → exact or pipe-separated list (`Edit|Write`).
- Other characters → JavaScript regex (`^Notebook`, `mcp__memory__.*`).

## `if` conditional filtering

Works on `PreToolUse`, `PostToolUse`, `PostToolUseFailure`,
`PermissionRequest`, `PermissionDenied`. Uses permission-rule syntax:

```json
{ "type": "command", "if": "Bash(rm *)", "command": "script.sh" }
```

## JSON input contract (stdin)

Common fields: `session_id`, `transcript_path`, `cwd`, `permission_mode`,
`hook_event_name`, plus event-specific data (`tool_input`, `tool_response`,
`prompt`, `error`, `message`, etc.).

## JSON output contract (stdout)

Top-level:

```json
{
  "continue": true,
  "stopReason": "message when continue=false",
  "suppressOutput": false,
  "systemMessage": "warning to user",
  "hookSpecificOutput": { "hookEventName": "...", "...": "..." }
}
```

Output is capped at 10,000 characters injected into context; longer output
saves to a file.

## Exit codes

| Code | Meaning | Effect |
|:--|:--|:--|
| 0 | Success | stdout JSON is processed |
| 2 | Blocking error | Action blocked; stderr shown; no JSON processed |
| other | Non-blocking error | First line of stderr in transcript |

Exit 2 blocks for: `PreToolUse`, `PermissionRequest`, `UserPromptSubmit`,
`Stop`, `SubagentStop`, `TeammateIdle`, `TaskCreated`, `TaskCompleted`,
`ConfigChange`, `PreCompact`, `WorktreeCreate`, `Elicitation`,
`ElicitationResult`.

Exit 2 does NOT block for: `PostToolUse`, `PostToolUseFailure`,
`PermissionDenied`, `Notification`, `SubagentStart`, `SessionStart`,
`SessionEnd`, `CwdChanged`, `FileChanged`, `PostCompact`,
`InstructionsLoaded`, `StopFailure`.

## Decision control specifics

### PreToolUse

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow|deny|ask|defer",
    "permissionDecisionReason": "reason",
    "updatedInput": { "field": "new value" },
    "additionalContext": "context for Claude"
  }
}
```

Multiple hooks precedence: **deny > defer > ask > allow**. Rule precedence:
`permissions.deny` ALWAYS blocks, even if a hook returned `allow`. Similarly,
`permissions.ask` always prompts. But a hook exit 2 preempts even allow rules.

### UserPromptSubmit

Can block with `{"decision": "block", "reason": "..."}` and erase the
prompt, or add context via `additionalContext`. Can set `sessionTitle`.

### PostToolUse

Cannot block (tool already ran). Can inject context via
`additionalContext`. For MCP tools, can replace output via
`updatedMCPToolOutput`.

### Stop / SubagentStop

Can prevent stopping with `{"decision": "block"}` or exit code 2.

## Component-scoped hooks

Inside a skill or subagent, hooks apply only while the component runs:

```yaml
---
name: secure-ops
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/security-check.sh"
---
```

For subagents, Stop hooks are auto-converted to `SubagentStop`. Frontmatter
hooks fire when the agent is spawned as a subagent (via Agent tool or
@-mention), NOT when the agent runs as the main session via `--agent`.

Plugin-loaded subagents do NOT support `hooks`, `mcpServers`, or
`permissionMode` — these fields are silently ignored for security reasons.

## `disableAllHooks` and URL/env allowlists

- `disableAllHooks: true` — disables all hooks and custom status line. Can't
  disable individual hooks while keeping them configured.
- `allowedHttpHookUrls: ["https://hooks.example.com/*"]` — restrict HTTP hook
  destinations. Arrays merge across scopes.
- `httpHookAllowedEnvVars` — intersection with each hook's `allowedEnvVars`.
- Managed-only `allowManagedHooksOnly: true` — only managed hooks and hooks
  from managed-force-enabled plugins load.

## View configured hooks

Type `/hooks` inside Claude Code. Read-only browser shows events, matchers,
handlers, and source (User/Project/Local/Plugin/Session/Built-in).

## Gotchas

- **Exit 1 is NOT blocking.** Use exit 2 to enforce policy.
- **Hook output > 10 KB gets truncated** into a preview + path.
- **HTTP hooks** that return 2xx with JSON get parsed; text becomes context;
  non-2xx is non-blocking error.
- **Deny rules beat hooks.** A `permissions.deny` match blocks even when a
  PreToolUse hook returned `allow`.
- **SSE MCP transport** is deprecated; prefer HTTP for MCP-server callers.
- **Plugin hooks that fail to load** are silently skipped; check `/hooks`.

## Disambiguation

- **Hook vs memory (CLAUDE.md):** memory is context Claude *tries to follow*;
  hooks are code the harness executes. "From now on, every X" → hook.
- **Hook vs skill:** skills are prompts; hooks are harness-level. Use hooks
  when deterministic behavior matters.
- **Hook vs permission rule:** deny rule for static blocks (simpler);
  PreToolUse hook for dynamic validation or input rewriting.
- **PreToolUse hook vs permissions.ask:** `ask` rule prompts the user;
  PreToolUse hook can block outright or inject context without prompting.

## Hook input JSON schema (key fields)

Common fields on stdin for every hook event:

| Field | Description |
|:--|:--|
| `session_id` | Current session UUID |
| `transcript_path` | Path to JSONL transcript file |
| `cwd` | Current working directory |
| `permission_mode` | Active permission mode (`default`, `acceptEdits`, etc.) |
| `hook_event_name` | Event name string (e.g. `"PreToolUse"`) |

Event-specific fields (PreToolUse): `tool_name`, `tool_input` (full input object).
Event-specific fields (PostToolUse): `tool_name`, `tool_input`, `tool_response`.
Event-specific fields (UserPromptSubmit): `prompt`.
Event-specific fields (Stop): `message` (Claude's final response).
Event-specific fields (StopFailure): `error`, `error_type`.

## SessionStart hook — env persistence recipe

Source: https://code.claude.com/docs/en/hooks

Write export statements to `$CLAUDE_ENV_FILE` from a SessionStart hook to
persist env vars for the entire session:

```bash
#!/bin/bash
# ~/.claude/hooks/load-env.sh
if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo "export NODE_ENV=production" >> "$CLAUDE_ENV_FILE"
  echo "export APP_ENV=$(cat ~/.app-env)" >> "$CLAUDE_ENV_FILE"
fi
```

Matchers: `startup` (fresh start), `resume` (resumed session),
`clear` (after /clear), `compact` (after /compact).

## PreCompact hook recipe

Monitor or gate context compaction:

```json
{
  "hooks": {
    "PreCompact": [
      {
        "matcher": "auto",
        "hooks": [{"type": "command", "command": "~/.claude/hooks/log-compaction.sh"}]
      }
    ]
  }
}
```

Use `PreCompact` to log that a compaction occurred, save notes before
context is summarized, or block automatic compaction (exit 2). Note:
exit 2 blocks for `PreCompact` but NOT for `PostCompact`.

## SubagentStop hook recipe

Fires when a subagent finishes (success or failure). Add to `settings.json`
to audit every subagent completion:

```json
{
  "hooks": {
    "SubagentStop": [
      {
        "hooks": [{"type": "command", "command": "~/.claude/hooks/log-subagent.sh"}]
      }
    ]
  }
}
```

Can block (exit 2) to prevent the subagent from being marked done until
conditions are met (e.g., tests pass).

## Notification hook

Fires on `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog`.
Cannot block. Use to integrate external notification systems (Slack, desktop
notifications) when Claude needs attention.

## Minimal worked example — block destructive rm

```bash
# ~/.claude/hooks/block-rm.sh
#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')
if echo "$COMMAND" | grep -q 'rm -rf'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "Destructive rm -rf blocked by hook"
    }
  }'
else
  exit 0
fi
```

```json
// ~/.claude/settings.json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "if": "Bash(rm *)",
            "command": "\"$HOME\"/.claude/hooks/block-rm.sh"
          }
        ]
      }
    ]
  }
}
```

Delegate authoring to the `update-config` skill — it knows the settings
layout, backup dates, and which hook goes in which scope.

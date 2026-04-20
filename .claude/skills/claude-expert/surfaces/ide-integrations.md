# IDE integrations

Sources:
- https://code.claude.com/docs/en/vs-code
- https://code.claude.com/docs/en/jetbrains
- https://code.claude.com/docs/en/desktop-quickstart
- https://code.claude.com/docs/en/claude-code-on-the-web

All integrations share the same engine. CLAUDE.md, settings, MCP servers,
session history work across every surface.

## VS Code extension

### Requirements

- VS Code 1.98.0+.
- Anthropic account (or third-party provider).

### Install

- Marketplace link: `vscode:extension/anthropic.claude-code` or Cursor
  link `cursor:extension/anthropic.claude-code`.
- Extensions view search "Claude Code".

### Open

- **Editor toolbar Spark icon** (top-right) — fastest when a file's open.
- **Activity Bar** — sessions list, always visible.
- **Command Palette** — "Claude Code" → "Open in New Tab/Sidebar/Window".
- **Status Bar** — "✱ Claude Code" bottom-right.

### What it provides

- Graphical chat panel (default) or terminal mode (set
  `claudeCode.useTerminal: true`).
- Inline diffs for proposed edits — accept/reject per change. Editing the
  diff before accepting tells Claude you modified it.
- `@file.ts#5-10` mentions with fuzzy matching.
- Editor selection auto-visible to Claude (toggle via eye-slash icon).
- `Option+K` / `Alt+K` inserts an @-mention for the current selection.
- Permission modes selectable from prompt box (default / plan / auto-accept).
- `/` command menu: attach files, switch models, toggle thinking,
  `/usage`, `/remote-control`, MCP/hooks/memory/permissions/plugins submenus.
- Context indicator on prompt box.
- Multi-line input: `Shift+Enter`.
- `Ctrl+G` or external editor integration.
- Conversation history with AI-generated titles.
- Remote session resumption (Claude.ai web sessions) via session history.

### Drag to reposition

Claude panel docks anywhere: secondary sidebar (right, default),
primary sidebar (left), editor area (as tab). Claude remembers
preference.

### Multiple conversations

`Open in New Tab` / `Open in New Window` from command palette. Small
colored dot on spark icon: blue = permission pending, orange = Claude
finished while hidden.

### Checkpoints (VS Code only)

Hover any message → rewind. Three options:
- Fork conversation from here (keeps code).
- Rewind code to here (keeps conversation).
- Fork conversation AND rewind code.

### Plugin management GUI

Type `/plugins` in prompt box → manage plugins interface. Two tabs:
Plugins and Marketplaces. Install scope: for you / for project / locally.

### Browser automation

`@browser` in the prompt box (requires Claude in Chrome extension 1.0.36+).

### VS Code extension settings

| Setting | Default | Purpose |
|:--|:--|:--|
| `claudeCode.useTerminal` | `false` | Use terminal mode instead of panel |
| `claudeCode.initialPermissionMode` | `default` | New-conversation mode |
| `claudeCode.preferredLocation` | `panel` | `sidebar` or `panel` |
| `claudeCode.autosave` | `true` | Auto-save before read/write |
| `claudeCode.useCtrlEnterToSend` | `false` | Send via Ctrl/Cmd+Enter |
| `claudeCode.enableNewConversationShortcut` | `false` | Cmd/Ctrl+N |
| `claudeCode.respectGitIgnore` | `true` | Exclude gitignored from file search |
| `claudeCode.usePythonEnvironment` | `true` | Activate workspace Python env |
| `claudeCode.allowDangerouslySkipPermissions` | `false` | Adds Auto and Bypass modes to selector |
| `claudeCode.claudeProcessWrapper` | — | Executable used to launch Claude |

Settings at `~/.claude/settings.json` are shared with CLI.

## Built-in `ide` MCP server (VS Code specifics)

When the extension is active, it runs a local MCP server named `ide`
that the CLI connects to automatically. Bound to `127.0.0.1` on a random
high port. Per-activation random auth token in lock file under
`~/.claude/ide/` with `0600` perms.

Hidden from `/mcp`. Visible to `PreToolUse` hooks allowlisting MCP tools.

Two tools exposed to the model:

| Tool | Writes? | Notes |
|:--|:--|:--|
| `mcp__ide__getDiagnostics` | No | Returns language-server diagnostics (Problems panel). Optional file scope. |
| `mcp__ide__executeCode` | Yes | Runs Python in active Jupyter notebook. **Always prompts** via Quick Pick — can't run silently. |

The rest of the server's RPC (open diffs, read selection, save files) is
filtered out before the tool list reaches Claude — used internally by the
CLI.

## VS Code command palette commands

| Command | Shortcut | Purpose |
|:--|:--|:--|
| Focus Input | `Cmd/Ctrl+Esc` | Toggle focus between editor and Claude |
| Open in Side Bar | — | Left sidebar |
| Open in Terminal | — | Terminal mode |
| Open in New Tab | `Cmd/Ctrl+Shift+Esc` | New tab |
| Open in New Window | — | Separate window |
| New Conversation | `Cmd/Ctrl+N` (if enabled + focused) | Start new |
| Insert @-Mention Reference | `Option+K` / `Alt+K` | Reference current file + selection |
| Show Logs | — | Debug logs |
| Logout | — | Sign out |

## Deep-link handler

`vscode://anthropic.claude-code/open?prompt=<URL-encoded>[&session=<id>]`
opens a new Claude Code tab, optionally pre-filled.

## JetBrains plugin

IntelliJ IDEA, PyCharm, WebStorm, and other JetBrains IDEs. Interactive
diff viewer, selection context sharing, marketplace install.

See https://code.claude.com/docs/en/jetbrains for specifics.

## Desktop app (macOS/Windows)

Standalone app. Visual diffs, multiple side-by-side sessions, scheduled
tasks, cloud session kickoff. Paid subscription required.

`claude-cli://open?q=...` URL scheme.

## Web

https://claude.ai/code. Start long-running tasks, work on repos you don't
have locally, run multiple tasks in parallel. iOS app also supports web
sessions.

Pull a web session into the terminal: `claude --teleport` or `/teleport`.

## Share features across CLI and IDE

Shared:
- `~/.claude/settings.json` and `.claude/settings.json`.
- CLAUDE.md files.
- MCP servers.
- Skills, subagents, commands.
- Conversation history (extension and CLI).

Not shared / CLI-only:
- `!` bash shortcut (input-box shell cmds).
- Tab completion.
- Some built-in commands (type `/` in extension to see what's available).

## VS Code extension vs CLI feature matrix

| Feature | CLI | VS Code |
|:--|:--|:--|
| Commands and skills | All | Subset (type `/`) |
| MCP server config | Yes | Partial (CLI add; GUI manage via `/mcp`) |
| Checkpoints | Yes | Yes |
| `!` bash shortcut | Yes | No |
| Tab completion | Yes | No |

## Disambiguation

- **Native Claude Code CLI vs IDE extension:** same engine. IDE adds
  visual diffs, @-mentions, panel UX. Some CLI commands missing from IDE.
- **IDE extension vs Desktop app:** IDE integrates into your editor;
  Desktop is standalone with multi-session support.
- **Built-in `ide` MCP server vs user MCPs:** `ide` is automatic, hidden,
  bound to localhost with per-session auth token. Not in `/mcp`. User
  MCPs are configured and visible.

## Gotchas

- `/pr-comments` removed in 2.1.91; ask Claude directly.
- `/vim` removed in 2.1.92; use `/config` → Editor mode.
- If `ANTHROPIC_API_KEY` is in shell but extension shows sign-in, VS Code
  didn't inherit env. Launch via `code .` from a shell, or sign in with
  Claude account instead.
- `mcp__ide__executeCode` ALWAYS prompts via Quick Pick — PreToolUse
  allowlist lets Claude propose cell execution, but the Quick Pick is what
  lets it actually run.
- Restricted Mode (VS Code workspace trust) blocks the extension — not a
  bug, a security design.

## Minimal workflow

```
$ code my-project
> Open Claude Code panel
> Select code → Option+K to @-mention
> Ask: "Refactor this for readability"
> Review inline diff, accept or edit
```

For CLI features inside VS Code: open integrated terminal (` Ctrl+` ` /
` Cmd+` `) and run `claude`.

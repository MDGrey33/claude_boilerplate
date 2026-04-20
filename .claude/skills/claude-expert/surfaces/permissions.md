# Permissions — deep reference

Source: https://code.claude.com/docs/en/permissions

## Tiered permission model

| Tool type | Example | Approval required | "Yes, don't ask again" behavior |
|:--|:--|:--|:--|
| Read-only | File reads, Grep | No | N/A |
| Bash commands | Shell execution | Yes | Permanently per project directory + command |
| File modification | Edit/write files | Yes | Until session end |

## Three buckets

- **Allow** — no prompt.
- **Ask** — prompt on use.
- **Deny** — blocked.

Evaluation order: **deny > ask > allow**. First match wins. Deny ALWAYS
blocks.

Manage via `/permissions`. UI shows rules by source (managed/user/project/local).

## Permission modes

Set via `permissions.defaultMode` in settings, `--permission-mode` flag, or
`/permissions` dialog.

| Mode | Behavior |
|:--|:--|
| `default` | Prompt on first use of each tool |
| `acceptEdits` | Auto-accept file edits + common fs cmds (`mkdir`, `touch`, `mv`, `cp`) for paths in cwd or `additionalDirectories` |
| `plan` | Read-only exploration (Plan Mode) |
| `auto` | Classifier reviews commands and protected-dir writes (research preview) |
| `dontAsk` | Auto-deny unless pre-approved |
| `bypassPermissions` | Skip prompts (still prompts for `.git`, `.claude`, `.vscode`, `.idea`, `.husky` except `.claude/commands`, `.claude/agents`, `.claude/skills`) |

Block modes:
- `permissions.disableBypassPermissionsMode: "disable"` — block bypass.
- `permissions.disableAutoMode: "disable"` — block auto.

### Mode details

**`default`** — prompts on first use of each tool. "Yes, don't ask again" saves
a rule permanently per project directory + command (Bash) or until session end
(file edits).

**`acceptEdits`** — auto-approves file edits (Write, Edit) and common filesystem
Bash commands (`mkdir`, `touch`, `rm`, `rmdir`, `mv`, `cp`, `sed`) for paths
inside cwd or `additionalDirectories`. Paths outside that scope still prompt.

**`plan`** — read-only exploration. Claude researches and proposes changes without
making them. When done, you choose: approve into `auto`, approve into `acceptEdits`,
or review each edit. Exit by pressing `Shift+Tab` again. Useful for understanding
scope before committing.

**`auto`** — background classifier reviews each action. Requires Sonnet 4.6,
Opus 4.6, or Opus 4.7 on Team/Enterprise/API; Opus 4.7 on Max. Anthropic
API only (not Bedrock/Vertex/Foundry). After 3 consecutive denials or 20 total
denials, auto mode pauses and prompts. Configure trusted infra via
`autoMode.environment`. Blocks `curl | bash`, production deploys, mass deletions.

**`dontAsk`** — auto-denies everything except `permissions.allow` rules and
read-only Bash. Use for CI pipelines.

**`bypassPermissions`** — skips all prompts except writes to protected paths
(`.git`, `.claude`, `.vscode`, `.idea`, `.husky`). Only use in isolated
containers/VMs without network access.

Switch: `Shift+Tab` to cycle, `--permission-mode <mode>` at CLI startup, or
`/permissions` dialog, VS Code mode indicator, Desktop mode selector.

## Permission rule syntax

Format: `Tool` or `Tool(specifier)`.

### Match all

`Bash`, `WebFetch`, `Read`, `Edit`, `Write`. Equivalent to `Bash(*)`.

### Bash with specifiers

- `Bash(npm run build)` — exact.
- `Bash(npm run *)` — prefix with word-boundary.
- `Bash(* install)` — suffix.
- `Bash(git * main)` — middle wildcard, `*` spans multiple args.
- `Bash(ls *)` — word boundary; matches `ls -la` not `lsof`.
- `Bash(ls*)` — no boundary; matches both `ls -la` and `lsof`.
- `Bash(ls:*)` — equivalent to `Bash(ls *)` (only recognized at end).

### Read / Edit — gitignore semantics

Four path types:

| Pattern | Meaning | Example |
|:--|:--|:--|
| `//path` | Absolute from filesystem root | `Read(//Users/alice/secrets/**)` |
| `~/path` | From home dir | `Read(~/Documents/*.pdf)` |
| `/path` | Project-root-relative (**NOT absolute**) | `Edit(/src/**/*.ts)` |
| `path` or `./path` | Cwd-relative | `Read(*.env)` |

Windows: paths normalized to POSIX before matching. `C:\Users\alice` becomes
`/c/Users/alice`. Use `//c/**/.env` or `//**/.env`.

### WebFetch

`WebFetch(domain:example.com)` — restrict by domain.

### MCP

- `mcp__puppeteer` — all tools from `puppeteer`.
- `mcp__puppeteer__*` — explicit wildcard.
- `mcp__puppeteer__puppeteer_navigate` — single tool.
- Regex like `mcp__.*__write.*` across servers.

### Agent (subagents)

- `Agent(Explore)` — built-in.
- `Agent(my-custom)` — custom.
- `Agent(worker, researcher)` — in `tools:` field, allowlist.

### Skill

- `Skill(commit)` — exact.
- `Skill(review-pr *)` — prefix with args.
- `Skill` — the Skill tool itself (e.g. deny all skills).

## Compound commands

Recognized separators: `&&`, `||`, `;`, `|`, `|&`, `&`, newlines. Each
subcommand must match a rule.

Approving compound via "yes, don't ask again" saves separate rules for each
subcommand needing approval (up to 5 per compound).

## Process wrappers (auto-stripped)

`timeout`, `time`, `nice`, `nohup`, `stdbuf`, bare `xargs`. So
`Bash(npm test *)` matches `timeout 30 npm test`.

`xargs` with flags NOT stripped — matched as `xargs` command itself.

**Exec wrappers (NOT auto-approvable via prefix):** `watch`, `setsid`,
`ionice`, `flock`, `find -exec`, `find -delete`. Need exact-match rules.

## Read-only commands (always no prompt)

`ls`, `cat`, `head`, `tail`, `grep`, `find`, `wc`, `diff`, `stat`, `du`,
`cd`, read-only forms of `git`. Not configurable. To require a prompt,
add `ask` or `deny` rule.

Unquoted globs allowed for read-only commands (`ls *.ts`, `wc -l src/*.py`).
Commands with write-capable flags (`find`, `sort`, `sed`, `git`) still
prompt if unquoted glob present.

`cd` into a path inside cwd or `additionalDirectories` is read-only. Compound
like `cd packages/api && ls` is fine; `cd ... && git ...` always prompts.

## Symlinks

- **Allow rules:** apply when both symlink path AND target match. Symlink
  pointing outside an allowed dir still prompts.
- **Deny rules:** apply if EITHER symlink or target matches.

## WebFetch limitations

Bash network tools (`curl`, `wget`) still run if `Bash` is allowed, even
if `WebFetch(domain:...)` is the only allowed WebFetch.

For reliable URL filtering:
1. Deny `Bash(curl *)`, `Bash(wget *)`.
2. Use `WebFetch(domain:...)` for allowed domains.
3. Or use a PreToolUse hook for dynamic validation.

## Managed settings

Admin-only settings:

| Setting | Effect |
|:--|:--|
| `allowedChannelPlugins` | Channel plugin allowlist |
| `allowManagedHooksOnly` | Only managed hooks load |
| `allowManagedMcpServersOnly` | Only managed MCP allowlist applies |
| `allowManagedPermissionRulesOnly` | Only managed rules; user/project rules ignored |
| `blockedMarketplaces` | Plugin marketplace blocklist |
| `channelsEnabled` | Allow channels feature |
| `forceRemoteSettingsRefresh` | Fail startup if remote fetch fails |
| `strictKnownMarketplaces` | Allowlist of marketplaces users can add |
| `sandbox.filesystem.allowManagedReadPathsOnly` | Strict read-path enforcement |
| `sandbox.network.allowManagedDomainsOnly` | Strict domain enforcement |

## Settings precedence

1. Managed settings (non-overridable).
2. Command line args.
3. `.claude/settings.local.json`.
4. `.claude/settings.json`.
5. `~/.claude/settings.json`.

Deny at any level blocks all levels. User allow + project deny → blocked.

## Hooks + permissions interplay

- Hook return values do NOT bypass `deny` or `ask` rules.
- Hook exit code 2 DOES preempt allow rules (blocks before permission check).
- `PreToolUse` hooks can allow/deny/ask/defer, but deny rule still wins.
- Run all bash commands without prompts except some: allow `Bash` and use a
  PreToolUse hook to reject specific commands.

## Sandboxing

Separate OS-level layer on macOS, Linux, WSL2. Complements permissions:
permissions are at Claude's decision layer; sandbox is enforced at OS.

- Sandbox filesystem restrictions use Read/Edit deny rules (merged).
- Sandbox network combines WebFetch allow/deny with `sandbox.network`
  allowed/deniedDomains.
- `autoAllowBashIfSandboxed: true` (default) — sandboxed Bash skips prompts.

## Auto mode

Research preview. Classifier reviews each tool call. Denials logged to
`/permissions` → "Recently denied" tab. Press `r` to mark for retry.

Configure classifier via `autoMode.environment`, `autoMode.allow`,
`autoMode.soft_deny` in settings (NOT project `settings.json`):

- `environment` — prose describing trusted infra.
- `allow` / `soft_deny` — REPLACE defaults; always copy defaults first via
  `claude auto-mode defaults`.

Inspect: `claude auto-mode config`, `claude auto-mode critique`.

## Permission utility: `fewer-permission-prompts` skill

Bundled skill that scans transcripts for common Bash/MCP tool calls and
writes a prioritized allowlist to `.claude/settings.json`. Useful for
reducing prompt fatigue after trust is established.

## Gotchas

- **URL patterns in Bash rules are fragile** — variables, redirects,
  protocol changes all bypass them. Prefer denying `curl`/`wget` and using
  WebFetch.
- **`/path` is NOT absolute in Read/Edit rules.** Use `//path`.
- **Read/Edit deny only applies to Claude's file tools**, not Bash
  subprocesses. `Read(./.env)` deny doesn't block `cat .env`. Use sandbox
  for OS-level enforcement.
- **Process wrappers only strip listed names** — not `direnv exec`,
  `devbox run`, `npx`, `docker exec`. Rules must include the runner.
- **`xargs` with flags** NOT stripped.
- **Auto mode classifier** defaults get replaced wholesale if you set
  `allow` or `soft_deny`. Always copy first.

## Disambiguation

- **Permission rule vs hook:** rule for static allow/deny; hook for dynamic
  validation or input rewriting.
- **Permission deny vs sandbox deny:** permission deny stops Claude from
  using the tool; sandbox deny stops any subprocess from accessing the
  resource.
- **`/permissions` vs `settings.json`:** `/permissions` is the UI; all rules
  are stored in `settings.json` at the scope you chose.

## Minimal worked example

```json
{
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      "Bash(npm run *)",
      "Bash(git status *)",
      "Bash(git diff *)",
      "Read",
      "Glob",
      "Grep"
    ],
    "deny": [
      "WebFetch",
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(rm -rf *)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Edit(//**/.ssh/**)"
    ],
    "ask": ["Bash(git push *)"]
  }
}
```

Delegate edits to the `update-config` skill; to auto-generate an allowlist
from your own usage, use `/fewer-permission-prompts`.

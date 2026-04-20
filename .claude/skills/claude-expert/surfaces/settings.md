# Settings — deep reference

Source: https://code.claude.com/docs/en/settings

## What settings do

`settings.json` configures the harness: permissions, env vars, hooks, model,
sandbox, statusLine, auto-mode classifier, plugins, attribution, and more.
Unlike CLAUDE.md, settings are **enforced** by the harness, not just read by
Claude.

## Scopes (precedence high → low)

1. **Managed** — enterprise policy. Can't be overridden.
   - Server-managed (Anthropic admin console).
   - MDM / OS-level: macOS `com.anthropic.claudecode` plist; Windows
     `HKLM\SOFTWARE\Policies\ClaudeCode` (REG_SZ / REG_EXPAND_SZ with `Settings`
     JSON). User-level registry `HKCU\SOFTWARE\Policies\ClaudeCode` is lowest
     managed priority.
   - File-based: macOS `/Library/Application Support/ClaudeCode/`;
     Linux/WSL `/etc/claude-code/`; Windows `C:\Program Files\ClaudeCode\`.
     `managed-settings.json` plus a drop-in dir `managed-settings.d/*.json`
     (numeric prefixes for order).
2. **Command line arguments** — `--permission-mode`, `--agents`, `--add-dir`,
   `--plugin-dir`, etc. Session-only.
3. **Local project** — `.claude/settings.local.json` (gitignored).
4. **Project** — `.claude/settings.json` (in VCS).
5. **User** — `~/.claude/settings.json`.

Arrays like `permissions.allow`, `sandbox.filesystem.allowWrite` **merge**
(concat + dedupe). Scalars like `model` take the highest-precedence value.

## Schema hint

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": { ... },
  "hooks": { ... },
  "env": { ... }
}
```

The schema line enables autocomplete and validation in editors.

## Key setting fields (abridged)

### Permissions

| Key | Description |
|:--|:--|
| `permissions.allow` | Allowlist rules |
| `permissions.ask` | Rules that prompt |
| `permissions.deny` | Denylist rules (takes precedence) |
| `permissions.additionalDirectories` | Extra dirs Claude can access |
| `permissions.defaultMode` | `default`/`acceptEdits`/`plan`/`auto`/`dontAsk`/`bypassPermissions` |
| `permissions.disableBypassPermissionsMode` | `"disable"` to block bypass mode |
| `permissions.skipDangerousModePermissionPrompt` | Skip bypass-mode confirmation (ignored in project settings for security) |

### Hooks

`hooks` — object keyed by event name. See surfaces/hooks.md.

Hook-related:
- `disableAllHooks` — kill-switch.
- `allowedHttpHookUrls` — URL pattern allowlist.
- `httpHookAllowedEnvVars` — env var allowlist for HTTP hook headers.
- `allowManagedHooksOnly` (managed-only) — block non-managed hooks.

### Env and execution

| Key | Description |
|:--|:--|
| `env` | Env vars applied every session |
| `apiKeyHelper` | `/bin/sh` script generating API auth (sent as `X-Api-Key` / `Authorization: Bearer`) |
| `awsAuthRefresh`, `awsCredentialExport` | Bedrock auth helpers |
| `otelHeadersHelper` | OTel header generator |
| `defaultShell` | `"bash"` or `"powershell"` (requires `CLAUDE_CODE_USE_POWERSHELL_TOOL=1`) |
| `includeGitInstructions` | Include built-in git workflow instructions (default `true`) |
| `disableSkillShellExecution` | Disable `!` shell injection in skills/commands |
| `disableDeepLinkRegistration` | Don't register `claude-cli://` handler |

### Model and effort

| Key | Description |
|:--|:--|
| `model` | Default model ID |
| `availableModels` | Allowlist restricting `/model`/`ANTHROPIC_MODEL` |
| `modelOverrides` | Map model IDs to provider-specific (e.g. Bedrock ARN) |
| `effortLevel` | Persist session effort (`low`/`medium`/`high`/`xhigh`) |
| `alwaysThinkingEnabled` | Enable extended thinking by default |
| `showThinkingSummaries` | Show thinking summaries interactively |

### Attribution

- `attribution.commit` — commit message trailers. Empty string hides.
- `attribution.pr` — PR description text. Empty string hides.
- `includeCoAuthoredBy` — **deprecated**; use `attribution`.

### Session and UI

| Key | Description |
|:--|:--|
| `cleanupPeriodDays` | Session file retention. Default 30. Min 1. |
| `statusLine` | `{"type": "command", "command": "~/.claude/statusline.sh"}` |
| `outputStyle` | Named output style |
| `viewMode` | `"default"`/`"verbose"`/`"focus"` |
| `tui` | `"default"` or `"fullscreen"` |
| `language` | Preferred response language |
| `spinnerTipsEnabled`, `spinnerTipsOverride`, `spinnerVerbs` | Spinner customization |
| `companyAnnouncements` | Start-of-session announcements |
| `prefersReducedMotion` | Accessibility |

### Auto-memory

| Key | Description |
|:--|:--|
| `autoMemoryEnabled` | Default `true`. `false` to disable. |
| `autoMemoryDirectory` | Custom dir. NOT accepted in project settings. |

### Auto-mode classifier

| Key | Description |
|:--|:--|
| `autoMode.environment` | Array of prose rules describing trusted infra |
| `autoMode.allow` | Prose exceptions to soft_deny (replaces defaults) |
| `autoMode.soft_deny` | Prose block rules (replaces defaults) |
| `disableAutoMode` | `"disable"` to block auto mode |

Inspect: `claude auto-mode defaults`, `claude auto-mode config`,
`claude auto-mode critique`.

### Plugins

| Key | Description |
|:--|:--|
| `enabledPlugins` | `{"plugin@marketplace": true/false}` |
| `extraKnownMarketplaces` | Add marketplaces. Repository-level prompts team to install. |
| `strictKnownMarketplaces` | Managed-only allowlist |
| `blockedMarketplaces` | Managed-only blocklist |
| `pluginTrustMessage` | Managed-only custom warning message |

### Sandbox

| Key | Description |
|:--|:--|
| `sandbox.enabled` | macOS, Linux, WSL2 |
| `sandbox.failIfUnavailable` | Exit at startup if sandbox can't start |
| `sandbox.autoAllowBashIfSandboxed` | Default `true` |
| `sandbox.excludedCommands` | Commands exempt from sandbox |
| `sandbox.allowUnsandboxedCommands` | Disable the `dangerouslyDisableSandbox` escape hatch |
| `sandbox.filesystem.allowWrite`/`denyWrite`/`allowRead`/`denyRead` | Paths; merge from all scopes |
| `sandbox.network.allowedDomains`/`deniedDomains` | Wildcards supported |
| `sandbox.network.allowUnixSockets`/`allowAllUnixSockets` | |
| `sandbox.enableWeakerNestedSandbox`/`enableWeakerNetworkIsolation` | Reduces security; use sparingly |
| `sandbox.filesystem.allowManagedReadPathsOnly` | Managed-only strict mode |
| `sandbox.network.allowManagedDomainsOnly` | Managed-only strict mode |

Sandbox path prefixes: `/` absolute; `~/` home; `./` or no prefix = project
root (for project settings) or `~/.claude` (for user settings). Legacy
`//path` also absolute.

### MCP

| Key | Description |
|:--|:--|
| `enableAllProjectMcpServers` | Auto-approve `.mcp.json` servers |
| `enabledMcpjsonServers` / `disabledMcpjsonServers` | Per-server approval |
| `allowedMcpServers` / `deniedMcpServers` | Managed-only lists |
| `allowManagedMcpServersOnly` | Managed-only strict mode |

### Main-thread as subagent

`agent: "code-reviewer"` — run the main session with that subagent's system
prompt and tool restrictions. CLI `--agent` overrides.

### File suggestion

```json
{ "fileSuggestion": { "type": "command", "command": "~/.claude/file-suggestion.sh" } }
```
The script gets `{"query": "..."}` on stdin, prints up to 15 paths to stdout.

### Memory-related

| Key | Description |
|:--|:--|
| `claudeMdExcludes` | Skip specific CLAUDE.md files by path/glob |

### Worktree

- `worktree.symlinkDirectories` — e.g. `["node_modules", ".cache"]`.
- `worktree.sparsePaths` — sparse checkout.

### Global config (lives in `~/.claude.json`, NOT settings.json)

Putting these in settings.json triggers schema errors:
`autoConnectIde`, `autoInstallIdeExtension`, `autoScrollEnabled`,
`editorMode` (`"normal"`/`"vim"`), `externalEditorContext`,
`showTurnDuration`, `terminalProgressBarEnabled`, `teammateMode`.

## Verify active settings

`/status` shows active layers, origins (e.g. "Enterprise managed settings
(remote)"), and parse errors.

## Gotchas

- **`claudeMdExcludes` doesn't exclude managed CLAUDE.md.** Policy always applies.
- **`autoMemoryDirectory` ignored** if set in project settings.
- **Managed-only settings fail silently** when placed in user/project.
- **Arrays merge, scalars overwrite.** When same scalar key appears in
  multiple scopes, higher precedence wins. When same array key appears,
  entries from all scopes are combined (dedup).
- **`permissions.allow` in user settings but `permissions.deny` in
  project** → project wins, blocked.
- **Sandbox path syntax differs from Read/Edit rules.** Sandbox uses `/tmp`
  as absolute; Read/Edit rules interpret `/tmp` as project-root-relative
  and require `//tmp` for absolute.
- **`$schema` with version mismatch** may show false positives on recent
  settings. Schema lags behind CLI.

## Disambiguation

- **Settings vs CLAUDE.md:** settings are enforced, CLAUDE.md is
  interpreted. Use settings for permissions, env vars, hooks; use CLAUDE.md
  for behavioral guidance.
- **Local vs user settings:** local = this project, private to you.
  User = everywhere, private. Project = this project, shared.
- **Managed CLAUDE.md vs managed settings:** managed CLAUDE.md shapes
  behavior (may drift); managed settings enforce policy (no drift).

## Minimal example

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": ["Bash(npm run lint)", "Bash(npm run test *)"],
    "deny": ["Bash(curl *)", "Read(./.env)", "Read(./secrets/**)"]
  },
  "env": { "CLAUDE_CODE_ENABLE_TELEMETRY": "1" },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [{
          "type": "command",
          "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/format.sh"
        }]
      }
    ]
  }
}
```

Delegate edits to the `update-config` skill. It handles backups, schema
validation, and picking the right scope file.

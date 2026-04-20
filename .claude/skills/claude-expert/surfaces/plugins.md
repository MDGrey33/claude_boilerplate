# Plugins — deep reference

Source: https://code.claude.com/docs/en/plugins

## What a plugin is

A distributable bundle of Claude Code extensions. A plugin is a directory
with `.claude-plugin/plugin.json` plus any of:

- `skills/<name>/SKILL.md`
- `commands/*.md` (legacy; use `skills/` for new plugins)
- `agents/*.md`
- `hooks/hooks.json`
- `.mcp.json` at plugin root
- `.lsp.json` at plugin root
- `monitors/monitors.json`
- `bin/` (executables added to PATH while enabled)
- `settings.json` (default settings when enabled; only `agent` and
  `subagentStatusLine` keys currently honored)

## Manifest: `.claude-plugin/plugin.json`

```json
{
  "name": "my-plugin",
  "description": "What this plugin does",
  "version": "1.0.0",
  "author": { "name": "Your Name" },
  "homepage": "...",
  "repository": "...",
  "license": "..."
}
```

`name` becomes the skill namespace. Plugin skills are always namespaced as
`/<plugin-name>:<skill-name>`. Version uses semver.

## Plugin vs standalone

| | Standalone (`.claude/`) | Plugin |
|:--|:--|:--|
| Skill names | `/hello` | `/my-plugin:hello` |
| Best for | Personal, project-specific, quick experiments | Sharing, versioned, multi-project |

The docs recommend: start standalone, convert when ready to share.

## Loading

- Installed via `/plugin` (browse a marketplace, install, toggle).
- Local development: `claude --plugin-dir ./my-plugin` (repeatable for multi).
- `--plugin-dir` overrides an installed marketplace plugin of the same
  name for that session (except managed-force-enabled plugins).
- `/reload-plugins` picks up changes mid-session.

## Env vars inside plugin code

- `${CLAUDE_PLUGIN_ROOT}` — install directory. Use for bundled files.
- `${CLAUDE_PLUGIN_DATA}` — persistent per-plugin data dir that survives
  updates.

## Security restrictions on plugin-provided content

Plugin-provided **subagents** do NOT support `hooks`, `mcpServers`, or
`permissionMode`. These fields are silently ignored. Copy the agent file
into `.claude/agents/` if you need those fields, or use permission rules
or `enabledPlugins` in managed settings.

Plugin-provided **hooks** are subject to `allowManagedHooksOnly` if that
managed-only setting is on.

## Known public marketplaces

Source: https://github.com/davila7/claude-code-templates, https://github.com/wshobson/commands

| Marketplace | Contents | Notable |
|:--|:--|:--|
| Anthropic official skills | https://github.com/anthropics/skills | 21 official skills |
| wshobson/commands | https://github.com/wshobson/commands | 57 commands/workflows |
| davila7/claude-code-templates | https://github.com/davila7/claude-code-templates | 169+ scientific skills, agent templates, MCP configs, settings, hooks |

Install flow: `/plugin` opens the browser, type the marketplace URL or plugin name,
toggle to enable. Local development: `claude --plugin-dir ./my-plugin`.

## Marketplaces

A marketplace is a JSON manifest (`.claude-plugin/marketplace.json`) that
lists available plugins. Marketplace source types:

| Type | Fields |
|:--|:--|
| `github` | `repo`, optional `ref`, `path` |
| `git` | `url`, optional `ref`, `path` |
| `url` | `url`, optional `headers` (download marketplace.json only; plugins must use external sources) |
| `npm` | `package` (scoped ok) |
| `file` | `path` (absolute to marketplace.json) |
| `directory` | `path` (absolute dir with `.claude-plugin/marketplace.json`) |
| `hostPattern` | `hostPattern` (regex against marketplace host) |
| `settings` | Inline plugin list; plugins must reference external sources |

## Settings for plugins

In `~/.claude/settings.json`, `.claude/settings.json`, or
`.claude/settings.local.json`:

```json
{
  "enabledPlugins": {
    "formatter@acme-tools": true,
    "experimental@personal": false
  },
  "extraKnownMarketplaces": {
    "acme-tools": {
      "source": { "source": "github", "repo": "acme-corp/claude-plugins" }
    }
  }
}
```

`enabledPlugins` format: `"<plugin-name>@<marketplace-name>": true|false`.
When a project ships `extraKnownMarketplaces`, team members trust-dialog
that marketplace, then see prompts per-plugin.

## Managed controls

Managed-only settings for plugins:

| Setting | Effect |
|:--|:--|
| `enabledPlugins` (managed) | Force-enable or block plugins org-wide |
| `strictKnownMarketplaces` | Allowlist of marketplace sources |
| `blockedMarketplaces` | Blocklist checked before download |
| `pluginTrustMessage` | Custom warning text |

Exact matching on `repo`, `ref`, `path` for git-type sources. `hostPattern`
uses regex on extracted host.

## Converting standalone to plugin

1. `mkdir -p my-plugin/.claude-plugin`.
2. Write `my-plugin/.claude-plugin/plugin.json`.
3. Copy `.claude/commands/`, `.claude/agents/`, `.claude/skills/` into
   `my-plugin/` at same names.
4. If migrating hooks from `settings.json`, create
   `my-plugin/hooks/hooks.json` with the `hooks` object from settings.
   Hook command format is identical.
5. `claude --plugin-dir ./my-plugin` to test.

After migration, remove originals from `.claude/` to avoid duplicates (the
plugin version takes precedence when loaded).

## `.lsp.json` — language servers

```json
{
  "go": {
    "command": "gopls",
    "args": ["serve"],
    "extensionToLanguage": { ".go": "go" }
  }
}
```

Users installing the plugin must have the LSP binary installed.

## `monitors/monitors.json` — background watchers

```json
[
  {
    "name": "error-log",
    "command": "tail -F ./logs/error.log",
    "description": "Application error log"
  }
]
```

Each stdout line becomes a notification in the session. Auto-start when
plugin enabled.

## Viewing / debugging

- `/plugin` — manage plugins in the CLI.
- `/mcp` — list MCP servers including plugin-provided.
- `/agents` — see subagents including plugin-provided.
- `/hooks` — see hooks including plugin-provided (flagged as source).

## Gotchas

- Don't nest `commands/`, `agents/`, `skills/`, or `hooks/` **inside**
  `.claude-plugin/`. Only `plugin.json` goes there.
- Plugin skills are always namespaced; can't use bare `/name`.
- Plugin `settings.json` only honors `agent` and `subagentStatusLine` as of
  docs-read (docs may expand this — verify current list).
- Plugin-provided subagent `hooks`, `mcpServers`, `permissionMode` silently
  ignored.
- URL-based marketplaces only fetch `marketplace.json` — plugins must
  reference external sources. For relative paths, use git-based marketplace.

## Disambiguation

- **Plugin vs standalone `.claude/`:** standalone for personal; plugin for
  sharing.
- **Plugin vs MCP:** plugin is a bundle of Claude-config; MCP is a single
  external-tool integration. A plugin can CONTAIN MCP servers.
- **Marketplace vs plugin:** marketplace is the index; plugin is the unit
  installed.

## Minimal example

```
my-first-plugin/
├── .claude-plugin/
│   └── plugin.json     {"name":"my-first-plugin","version":"1.0.0"}
└── skills/
    └── hello/
        └── SKILL.md
```

```yaml
# skills/hello/SKILL.md
---
description: Greet the user warmly and ask how you can help them today.
---

Greet the user named "$ARGUMENTS" warmly. Make the greeting personal.
```

`claude --plugin-dir ./my-first-plugin` then `/my-first-plugin:hello Alex`.

## Submit to the Anthropic marketplace

- Claude.ai: https://claude.ai/settings/plugins/submit
- Console: https://platform.claude.com/plugins/submit

After listing, use `/en/plugin-hints` to prompt users from your own CLI.

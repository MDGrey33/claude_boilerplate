# MCP — Model Context Protocol

Source: https://code.claude.com/docs/en/mcp

## What MCP is

MCP (Model Context Protocol) is an open standard for connecting AI tools to
external data sources. MCP servers give Claude Code access to tools,
databases, APIs, and more — exposed as tools named `mcp__<server>__<tool>`.

Connect an MCP server when you're copying data into chat from another tool
(issue tracker, dashboard, CRM, etc.) — the server lets Claude read/act
directly.

## Transports

| Transport | Use case | Notes |
|:--|:--|:--|
| HTTP | Remote cloud services | Recommended. Supports OAuth, headers, auto-reconnect with exponential backoff (5 attempts). |
| SSE | Legacy remote | **Deprecated** — use HTTP. |
| stdio | Local processes | Direct system access, custom scripts. No auto-reconnect. |

## Adding servers

```bash
# HTTP
claude mcp add --transport http <name> <url>
claude mcp add --transport http notion https://mcp.notion.com/mcp

# With auth header
claude mcp add --transport http secure https://api.example.com/mcp \
  --header "Authorization: Bearer YOUR_TOKEN"

# stdio
claude mcp add --transport stdio <name> [--env KEY=VAL] -- <command> [args...]
claude mcp add --transport stdio --env AIRTABLE_API_KEY=YOUR_KEY airtable \
  -- npx -y airtable-mcp-server
```

Option ordering: all flags (`--transport`, `--env`, `--scope`, `--header`,
`--client-id`, `--callback-port`) come **before** the server name. `--`
separates from the command and its args.

## Management

```bash
claude mcp list                    # all configured servers
claude mcp get github              # details for one
claude mcp remove github
claude mcp reset-project-choices   # reset .mcp.json approval dialog
```

Inside Claude Code: `/mcp` — manage servers, inspect OAuth state,
authenticate, reconnect.

## Scopes

| Scope | Loads in | Shared | Stored |
|:--|:--|:--|:--|
| Local (default) | Current project only | No | `~/.claude.json` (per project) |
| Project | Current project only | Yes (via VCS) | `.mcp.json` in project root |
| User | All your projects | No | `~/.claude.json` |

Precedence (same name across scopes): local > project > user > plugin >
claude.ai connectors. Plugins and connectors match by endpoint rather than
name.

## `.mcp.json` format

```json
{
  "mcpServers": {
    "shared-server": {
      "type": "http",
      "url": "https://mcp.example.com/mcp",
      "headers": { "Authorization": "Bearer ${API_TOKEN}" }
    }
  }
}
```

Env var expansion: `${VAR}` or `${VAR:-default}` in `command`, `args`, `env`,
`url`, `headers`. Failing to set a required var breaks parsing.

Project-scoped `.mcp.json` prompts for approval on first use (security).

## Tool naming

Each MCP tool is exposed as `mcp__<server>__<tool>`. Permission rules:

- `mcp__puppeteer` — any tool from `puppeteer` server.
- `mcp__puppeteer__*` — explicit wildcard.
- `mcp__puppeteer__puppeteer_navigate` — single tool.
- `mcp__.*__write.*` — regex across servers.

## Authentication

### OAuth

- Dynamic client registration — default; discovered via RFC 9728 then RFC
  8414.
- CIMD (Client ID Metadata Document) — auto-discovered.
- Pre-configured: `--client-id YOURID --client-secret --callback-port 8080`.
- `--callback-port` fixes port (match your registered redirect URI).
- Use `/mcp` → select server → "Authenticate" in the browser.
- Tokens stored in system keychain (macOS) or credentials file.
- `authServerMetadataUrl` in `.mcp.json` overrides discovery (v2.1.64+).
- `oauth.scopes: "channels:read chat:write"` pins requested scopes
  (RFC 6749 §3.3 format). Takes precedence over advertised scopes.
  `offline_access` auto-appended when supported for token refresh.

### Non-OAuth (Kerberos, SSO, short-lived tokens)

`headersHelper` command/script runs on each connection, stdout JSON merges
into headers. 10-second shell timeout. Env vars passed:
`CLAUDE_CODE_MCP_SERVER_NAME`, `CLAUDE_CODE_MCP_SERVER_URL`.

```json
{
  "mcpServers": {
    "internal-api": {
      "type": "http",
      "url": "https://mcp.internal.example.com",
      "headersHelper": "/opt/bin/get-auth-headers.sh"
    }
  }
}
```

`headersHelper` executes arbitrary shell; when in project/local scope it
only runs after workspace trust is accepted.

## Env vars and limits

- `MCP_TIMEOUT=10000 claude` — 10-second server startup timeout.
- `MAX_MCP_OUTPUT_TOKENS=50000` — raise the warning threshold (default warn
  at 10,000 tokens). Docs imply this is the warn threshold, not a hard cap.
- `MCP_CLIENT_SECRET=...` — CI-friendly secret input.

## Subagent-scoped servers

Subagents can declare inline servers that exist only for the subagent:

```yaml
mcpServers:
  - playwright:
      type: stdio
      command: npx
      args: ["-y", "@playwright/mcp@latest"]
```

Keeping a server out of `.mcp.json` and into a subagent definition saves
tool-description context in the main conversation. Use for single-purpose
tools.

## Dynamic tool updates

MCP servers can send `list_changed` notifications; Claude Code refreshes
available tools/prompts/resources without requiring reconnect.

## Push messages via channels

MCP servers can also push messages into the session ("channels"). Requires
`claude/channel` capability on the server and `--channels` at CLI startup.
See https://code.claude.com/docs/en/channels.

## Plugin-provided MCP servers

Plugins can bundle MCP servers in `.mcp.json` at the plugin root or inline
in `plugin.json`. Auto-start when the plugin is enabled. Env vars
`${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}` available.

## MCP prompts as slash commands

MCP servers can expose prompts. These appear as
`/mcp__<server>__<prompt>`, dynamically discovered.

## Windows note

On native Windows (not WSL), stdio servers with `npx` need `cmd /c`:

```bash
claude mcp add --transport stdio my-server -- cmd /c npx -y @some/package
```

## MCP catalogs

Source: https://glama.ai/mcp/servers

When looking for an existing MCP server before building one:

- **glama.ai/mcp/servers** — 21,811 open-source servers indexed (2026-04-20).
  Breakdown: 9,705 remote-capable, 5,352 hybrid, 4,853 local-only.
  Top categories: Developer Tools (7,702), App Automation (4,042), Search (4,013),
  Databases (2,073).
- **github.com/punkpeye/awesome-mcp-servers** — curated community list (85.1k stars).
- **registry.modelcontextprotocol.io** — official MCP registry.

## In-process SDK MCP servers

Source: https://code.claude.com/docs/en/agent-sdk/mcp

When using the Agent SDK, you can define MCP tools **in-process** (no
subprocess, no IPC latency, simpler deployment):

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("query_db", "Query the database", {"sql": str})
async def query_db(args):
    result = run_query(args["sql"])
    return {"content": [{"type": "text", "text": result}]}

server = create_sdk_mcp_server(name="my-tools", version="1.0.0", tools=[query_db])
options = ClaudeAgentOptions(mcp_servers={"db": server})
```

Benefits over subprocess stdio: no startup delay, easier debugging, type
safety, single-process deployment. Mix freely with external stdio/HTTP servers
in the same `mcp_servers` dict.

## Disambiguation

- **MCP vs subagent:** MCP is external tool access; subagent is Claude
  behavior. Often pair: MCP for the tool, subagent that uses it.
- **MCP vs skill:** skill is instructions; MCP is capability. An MCP that
  exposes `query_database` lets Claude query; a skill tells Claude
  when/how to query.
- **Built-in `ide` MCP server vs user MCPs:** when running in VS Code, the
  extension runs a hidden `ide` MCP server exposing
  `mcp__ide__getDiagnostics` and `mcp__ide__executeCode`. Visible to hooks
  but not to `/mcp`. Nothing to configure.

## Managed / enterprise restrictions

| Setting | Effect |
|:--|:--|
| `allowedMcpServers` | Allowlist (managed-only). Empty array = lockdown. |
| `deniedMcpServers` | Denylist (managed-only). Merges from all sources. |
| `allowManagedMcpServersOnly` | Only managed allowlist respected; users can still define servers but they're ignored. |
| `enableAllProjectMcpServers` | Auto-approve all `.mcp.json` servers. |
| `enabledMcpjsonServers` / `disabledMcpjsonServers` | Per-server approval lists. |

## Gotchas

- **SSE is deprecated.** Migrate to HTTP.
- **Option order matters**: flags before the name, `--` before command.
- **Project-scope servers prompt for approval** on first use; reset with
  `claude mcp reset-project-choices`.
- **Env var expansion** breaks when required var is unset with no default.
- **Auto-reconnect** only works for HTTP/SSE, not stdio.
- **10-second timeout** on `headersHelper`. No caching — script reruns on
  every connect.
- **Warning threshold** for output is 10,000 tokens; larger outputs still
  work but may bloat context.

## Minimal worked example

```bash
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp
```
Then `/mcp` → Authenticate. Now Claude can answer:

> "What are the most common errors in the last 24 hours?"

Delegate health checks to the `mcp-doctor` skill.

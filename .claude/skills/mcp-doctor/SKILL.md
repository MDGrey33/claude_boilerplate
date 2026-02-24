---
name: mcp-doctor
description: Check health of configured MCP servers
user_invocable: true
---

# MCP Doctor

You are performing a health check on all configured MCP servers using direct process-level testing (not MCP tool calls, which require a loaded session).

## Steps

1. **Read MCP configuration**: Read `.mcp.json` from the project root to discover all configured MCP servers, their transport type, and their setup details.

2. **Classify each server**: For each entry in `.mcp.json`, determine the transport:
   - **stdio** — has `command` and `args` fields (e.g., cognee with a Python binary, playwright with `npx`)
   - **HTTP/SSE** — has a `url` field

3. **Health-check each server via its native transport**: Do NOT call MCP tools (they require the server to already be loaded in the Claude Code session). Instead, test connectivity directly:

   **For stdio servers using Python** (command points to a Python binary):
   - Write and run a short Python script using the **same Python binary** from the server's `command` field
   - The script should import `mcp.ClientSession`, `StdioServerParameters`, and `stdio_client` from the MCP Python SDK
   - It should connect to the server using the `command`, `args`, and `env` from `.mcp.json`
   - On successful connection: call `initialize()`, then `list_tools()`, print the tool count and tool names
   - On failure: print the error message
   - Use a reasonable timeout (15 seconds) so it doesn't hang

   **For stdio servers using npx/node** (e.g., playwright):
   - Write and run a similar connection test, but use the Node.js MCP SDK or simply attempt to start the process and read its initial stdio output
   - Alternatively, run the configured command with a short timeout and check that it starts without error

   **For HTTP/SSE servers** (url is set):
   - Use the MCP Python SDK's SSE or streamable HTTP client to connect, or fall back to a simple HTTP reachability check against the configured URL
   - Report whether the endpoint responds

   **Key principle**: This skill describes *what to do*. You generate the actual test scripts on the fly based on what you find in `.mcp.json`. Do not use pre-baked scripts.

4. **Report results**: Present a status table covering ALL configured servers:

   ```
   MCP Health Report
   ─────────────────
   Server        Status     Transport  Tools
   cognee        healthy    stdio      23 tools
   playwright    healthy    stdio      12 tools
   other-server  unhealthy  http       (connection refused)
   ```

   If a server is healthy, show the tool count. If unhealthy, show the error summary.

5. **If any server is unhealthy**, troubleshoot based on the actual config found in `.mcp.json`:

   **For local clone setups** (command points to a Python path):
   - Verify the configured Python binary exists at the path shown in `command`
   - Verify the configured `server.py` exists at the path shown in `args`
   - Check that `LLM_API_KEY` in the `env` block has an actual value (not a shell variable reference like `${LLM_API_KEY}`)
   - If paths don't exist, suggest running `/setup-cognee` to reinstall

   **For Docker setups** (command is `docker`):
   - Check that Docker is running (`docker info`)
   - Check that the cognee-mcp image is available (`docker images` for the image name from `args`)
   - If a `--network` flag is in `args`, verify that Docker network exists (`docker network ls`)
   - Check that any backing services (Postgres containers) are running based on the `DB_HOST` in the env/args
   - If Docker host address issues suspected, note that macOS uses `host.docker.internal` while Linux may need the bridge network IP

   **For HTTP/SSE setups** (url is set):
   - Check that the URL is reachable
   - Check that the service is running at the configured host/port

   **For npx-based servers** (e.g., playwright):
   - Verify `npx` is available and the package can be resolved
   - Check Node.js version if relevant

   **General checks** (all setups):
   - Verify `LLM_API_KEY` is present and looks like a real key (not empty, not a placeholder) — for servers that need it
   - If all else fails, suggest running the relevant setup skill (e.g., `/setup-cognee`, `/setup-playwright-mcp`)

   **Do not hardcode any paths** — derive everything from what's actually in `.mcp.json`.

6. **Return** the health status so calling skills can use it.

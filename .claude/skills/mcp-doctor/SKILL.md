---
name: mcp-doctor
description: Check health of configured MCP servers
user_invocable: true
---

# MCP Doctor

You are performing a health check on configured MCP servers.

## Steps

1. **Read MCP configuration**: Read `.mcp.json` from the project root to discover configured MCP servers and their setup details.

2. **Determine setup type from config**: Inspect the cognee entry in `.mcp.json` to understand what kind of setup is configured:
   - If `command` is `docker` → Docker-based setup
   - If `command` points to a Python binary path → local clone setup
   - If `url` is set → HTTP/SSE transport setup
   - Note the actual paths, images, network names, and env vars configured

3. **Check each server**: For each configured MCP server, run a lightweight health check:
   - **cognee**: Call the `cognee_list_datasets` MCP tool. If it returns a response (even an empty list), the server is healthy. If it errors or times out, it's unhealthy.
   - For any other MCP servers: attempt to list their available tools. If tools are returned, the server is healthy.

4. **Report results**: Present a status table:

   ```
   MCP Health Report
   -----------------
   cognee:  healthy / unhealthy / not configured
   Setup:   local clone / docker / http
   ```

5. **If unhealthy**, troubleshoot based on the actual config found in `.mcp.json`:

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

   **General checks** (all setups):
   - Verify `LLM_API_KEY` is present and looks like a real key (not empty, not a placeholder)
   - If all else fails, suggest running `/setup-cognee` for a fresh configuration

   **Do not hardcode any paths** — derive everything from what's actually in `.mcp.json`.

6. **Return** the health status so calling skills can use it.

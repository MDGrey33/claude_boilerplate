---
name: mcp-doctor
description: Check health of configured MCP servers
user_invocable: true
---

# MCP Doctor

You are performing a health check on configured MCP servers.

## Steps

1. **Read MCP configuration**: Read `.mcp.json` from the project root to discover configured MCP servers.

2. **Check each server**: For each configured MCP server, run a lightweight health check:
   - **cognee**: Call the `cognee_list_datasets` MCP tool. If it returns a response (even an empty list), the server is healthy. If it errors or times out, it's unhealthy.
   - For any other MCP servers: attempt to list their available tools. If tools are returned, the server is healthy.

3. **Report results**: Present a status table:

   ```
   MCP Health Report
   -----------------
   cognee:  healthy / unhealthy / not configured
   ```

4. **If unhealthy**, suggest remediation:
   - Check that `LLM_API_KEY` environment variable is set
   - Check that the MCP server command is installed (e.g., `uvx`, `npx`)
   - Check that Docker is running (if using Docker setup)
   - Suggest running `uvx --from cognee-mcp cognee-mcp` manually to see errors

5. **Return** the health status so calling skills can use it.

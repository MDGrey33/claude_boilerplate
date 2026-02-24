---
name: setup-playwright-mcp
description: Install and configure Playwright MCP for browser automation
user_invocable: true
---

# Setup Playwright MCP — Browser Automation for Claude Code

You are helping the user add the Playwright MCP server, which gives Claude Code the ability to interact with web browsers (navigate, click, fill forms, take screenshots, etc.).

## Step 1: Check Prerequisites

Verify the following are available:
- **Node.js** (v18+) — run `node --version`
- **npx** — run `npx --version`

If either is missing, search the web for current installation instructions for the user's detected OS/platform and help them install it.

## Step 2: Test Playwright MCP Starts

Run a quick smoke test to confirm the package can be fetched and started:
- Run `npx @playwright/mcp --help` (or start it briefly with a timeout)
- If it fails due to missing dependencies or network issues, troubleshoot with the user

## Step 3: Write `.mcp.json` Entry

Merge the following entry into `.mcp.json` in the project root:

```json
{
  "playwright": {
    "command": "npx",
    "args": ["@playwright/mcp"]
  }
}
```

**Rules**:
- If `.mcp.json` already exists with other servers (e.g., cognee), **merge** — do not overwrite existing entries
- If `.mcp.json` doesn't exist, create it with just this entry

## Step 4: Ensure `.mcp.json` in `.gitignore`

Check `.gitignore` for `.mcp.json`. If not already listed, add it. The file may contain secrets from other server configs and is machine-specific.

## Step 5: Verify

Run `/mcp-doctor` to confirm the playwright server is reachable and reports its tools.

## Step 6: Report

Summarize what was configured:

```
Playwright MCP Setup Complete
==============================
Node.js:      (detected version)
npx:          available
.mcp.json:    playwright entry added
.gitignore:   .mcp.json entry present
Health check: passed / failed

⚠ Restart Claude Code for the new MCP server to load.

Available capabilities:
- Browser navigation and interaction
- Form filling and clicking
- Screenshot capture
- JavaScript execution in browser context

Next steps:
- Restart Claude Code to activate the server
- Ask Claude Code to open a URL or interact with a web page
```

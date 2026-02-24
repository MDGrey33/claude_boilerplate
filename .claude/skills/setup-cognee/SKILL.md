---
name: setup-cognee
description: Install and configure cognee-mcp on this machine
user_invocable: true
args: Optional preferred preset (recommended, minimal, docker)
---

# Setup Cognee — Install & Configure cognee-mcp

You are helping the user get cognee-mcp running on their machine. Walk through setup interactively, detecting what's already installed and what needs to be done.

**Important**: The cognee MCP server is run from a local clone of the cognee repo (the `cognee-mcp/` subdirectory) or via the Docker image `cognee/cognee-mcp:main`. There is no PyPI package — do not attempt `uvx`, `pip install`, or any package-manager-based installation.

## Step 0: Check Latest Documentation

Before executing any installation steps, look up current documentation:
- Search the web for "cognee MCP server setup" to find current instructions
- Check https://github.com/topoteretes/cognee for the `cognee-mcp/` subdirectory README
- Use findings to inform installation commands — if docs show different flags, dependencies, or steps than what this skill describes, **adapt accordingly** and tell the user what changed

## Step 1: Detect Environment

Detect what's available on this machine:
- **OS and platform** (macOS, Linux, WSL — affects Docker host address, shell profile path, package managers)
- **Available tools**: `git`, `python3` (version — need 3.10+), `uv`, `docker`, `docker compose` vs `docker-compose`
- **Current shell** (from `$SHELL` — determines which profile file to suggest for env vars)
- **Whether `LLM_API_KEY` is set** in the current environment
- **Whether port 5432 is in use** (existing Postgres instance)
- **Whether cognee is already cloned** (check common locations: `~/cognee`, project-relative)
- **Whether `.mcp.json` already exists** in the project root (and what's in it)
- **Whether `.env` already exists** in the project root

Report findings to the user before proceeding.

## Determining DB_HOST

After detecting the environment, apply this principle whenever writing database host addresses to `.env` or `.mcp.json`. Both files should use the address appropriate for the process that reads them.

| Connecting process runs… | DB runs in… | DB_HOST value |
|---|---|---|
| Locally (Python on host) | Docker container on host | `127.0.0.1` |
| In Docker container | Same docker compose stack | Service name (e.g., `postgres`) |
| In Docker container | Host machine directly | OS-dependent: `host.docker.internal` on macOS, bridge IP on Linux |

**Key rule**: Both `.env` and `.mcp.json` are read by the cognee-mcp process. Use the address that matches where that process runs relative to the database. Do not mix — e.g., don't put `host.docker.internal` in `.env` if the process reading it runs on the host.

## Default Database Credentials

When a preset requires PostgreSQL, use these dev-only defaults unless the user specifies otherwise. Reference this section from any goal that writes DB config to `.env` or `.mcp.json`.

| Variable | Default | Notes |
|---|---|---|
| `DB_PROVIDER` | `postgres` | |
| `DB_HOST` | Per **Determining DB_HOST** | Never hardcode — always derive |
| `DB_PORT` | `5432` | Check if already in use first |
| `DB_NAME` | `cognee_db` | Dev default |
| `DB_USER` | `cognee` | Dev default |
| `DB_PASSWORD` | `cognee` | Dev default — communicate to user these are insecure |

These are for local development only. For production or shared environments, use unique credentials.

## Step 2: Choose Preset

Present three presets, recommending the first. If the user passed a preset argument, use that.

| Preset | Description | Requires |
|--------|-------------|----------|
| **recommended** | Local clone + PostgreSQL/PGVector via Docker | git, Python 3.10+, uv, Docker |
| **minimal** | Local clone + file-based defaults (SQLite/LanceDB/Kuzu) | git, Python 3.10+, uv |
| **docker** | Everything via Docker containers | Docker |

If required tools are missing for the chosen preset, tell the user what's needed and offer to help install them by searching the web for current installation instructions for their detected OS/platform.

## Step 3a: Choose LLM Provider

Ask the user which LLM provider they want to use:
- **OpenAI** (recommended) — most compatible with cognee's structured output extraction
- **Anthropic** — set `LLM_PROVIDER=anthropic`, `LLM_MODEL` to current best Sonnet model
- **Ollama** (local, free) — requires configuring BOTH LLM and embeddings (see Ollama section below)

**Critical gotcha to communicate**: If using Ollama, both LLM and embedding config must be set. If only one is configured, the other defaults to OpenAI and fails without an OpenAI key.

## Step 3b: Configure API Key

This is a dedicated step — do not combine it with provider selection.

1. **Check existing environment**: Look for the key in common environment variables:
   - `$LLM_API_KEY`, `$OPENAI_API_KEY`, `$ANTHROPIC_API_KEY` (depending on chosen provider)
2. **If found**: Show a masked version for confirmation (first 4 + last 4 characters, e.g., `sk-p...Xk9f`). Ask the user to confirm this is the key they want to use.
3. **If not found**: Explicitly ask the user to provide their API key. Use a dedicated prompt — do not combine this with other questions.
4. **Persistence**: Detect the shell profile path from `$SHELL` and OS:
   - zsh → `~/.zshrc`
   - bash on Linux → `~/.bashrc`
   - bash on macOS → `~/.bash_profile` (macOS login shells don't source `~/.bashrc` by default)
   - fish → `~/.config/fish/config.fish`

   Instruct the user to add their API key export to the detected profile so it persists across terminal sessions.
5. **Store the literal value**: Save the actual key value for use in `.env` and `.mcp.json` in later steps. Never use shell variable references like `${LLM_API_KEY}` in config files — Claude Code does not expand them.

## Step 4: Install & Configure

Each preset defines **goals** — achieve each goal using the tools and paths detected in Step 1, and the latest docs from Step 0. Do not use hardcoded commands from this skill file blindly; verify against current documentation.

### Recommended Preset

**Goal 1: Ensure uv is installed**
If `uv` is not found, look up current installation instructions from https://docs.astral.sh/uv/getting-started/installation/ for the detected platform and install it.

**Goal 2: Clone cognee repo**
If not already cloned, ask the user where they want it. Suggest `~/cognee` as default. Clone from https://github.com/topoteretes/cognee.git

**Goal 3: Install cognee-mcp dependencies**
Run `uv sync` in the `cognee-mcp` subdirectory of the clone. Check the cognee docs (Step 0) for the current recommended flags. Verify the venv Python and `server.py` exist afterward.

**Goal 4: Start PostgreSQL + PGVector**
Use Docker to run a PGVector container. Before starting:
- Check if port 5432 is already in use
- Refer to the **Determining DB_HOST** section to choose the correct address
- Use the **Default Database Credentials** defined below (communicate these are dev-only defaults)

**Goal 5: Write `.env`**
Write a `.env` file with actual literal values based on what was detected and chosen. If `.env` already exists, merge — don't overwrite unrelated config. Include:
- LLM config (provider, model, API key — the literal value from Step 3b)
- Database config (provider, host per **Determining DB_HOST**, port, credentials)
- Vector DB provider
- `ENABLE_BACKEND_ACCESS_CONTROL=false` (see Access Control Note below)

**Goal 6: Write `.mcp.json`**
Write the cognee entry to `.mcp.json` following these **mandatory rules**:
- Use **actual literal values** — Claude Code does not expand shell variables like `${LLM_API_KEY}` or `$HOME`
- Use **resolved absolute paths** — no `~`, `$HOME`, or relative paths (e.g., `/Users/username/cognee/...`)
- Use the **actual API key value** from Step 3b in the `env` block
- Use the correct `DB_HOST` per **Determining DB_HOST** — consistent with what's in `.env`
- Include `ENABLE_BACKEND_ACCESS_CONTROL=false` in the `env` block
- If `.mcp.json` already exists with other servers, **merge** the cognee entry — don't overwrite

**Goal 7: Add `.mcp.json` to `.gitignore`**
If not already listed, add it. The file contains secrets and is machine-specific.

### Minimal Preset

Same as Recommended Goals 1-3, then:
- **Skip** Goal 4 (no Postgres — uses file-based SQLite/LanceDB defaults)
- **Skip** Goal 5 (no `.env` needed — defaults are fine)
- **Goal 6**: Write `.mcp.json` with `LLM_API_KEY` and `ENABLE_BACKEND_ACCESS_CONTROL=false` in env (same literal-value and absolute-path rules)
- **Goal 7**: Same gitignore step

**Note to communicate**: Minimal setup can hit file locking issues under heavy use. Suggest upgrading to recommended later if this happens.

### Docker Preset

**Goal 1: Clone cognee repo** (for docker-compose files)

**Goal 2: Write `.env` in the cognee repo directory**
With LLM config, **Default Database Credentials**, and `ENABLE_BACKEND_ACCESS_CONTROL=false`. Refer to **Determining DB_HOST** — for containers in the same compose stack, `DB_HOST` should be the service name (e.g., `postgres`).

**Goal 3: Start the stack via docker compose**
Detect whether `docker compose` (V2) or `docker-compose` (V1) is available. Check cognee docs for current compose profiles and flags.

**Goal 4: Detect the Docker network name**
The compose stack creates a network (typically `cognee_default`). Detect the actual name.

**Goal 5: Write `.mcp.json`**
Use `docker` as the command, with the detected network name. Same literal-value rules. Pass env vars via `-e` flags in args, with the API key in the `env` block. Include `ENABLE_BACKEND_ACCESS_CONTROL=false`. Refer to **Determining DB_HOST** for the correct `DB_HOST` value — the MCP container needs to reach the database, so use the address appropriate for a Docker container reaching the DB.

**Goal 6**: Same gitignore step

## Access Control Note

Cognee v0.5.0+ defaults to multi-user access control mode (`ENABLE_BACKEND_ACCESS_CONTROL=true`), which requires authentication tokens and user management. This causes confusing errors in single-user local development setups.

This skill sets `ENABLE_BACKEND_ACCESS_CONTROL=false` by default in both `.env` and `.mcp.json` to disable access control for local development.

**When to enable it**: If you're sharing a cognee instance across multiple users or deploying to a shared environment, set `ENABLE_BACKEND_ACCESS_CONTROL=true` and configure authentication. See the Expansion Path table below.

## Step 5: Verify

Run `/mcp-doctor` to confirm cognee is healthy.

If it fails, troubleshoot based on the error. Common issues vary by setup type — `/mcp-doctor` will provide setup-specific diagnostics.

## Step 6: Report

Summarize what was configured:

```
Cognee Setup Complete
=====================
Preset:       recommended / minimal / docker
Database:     PostgreSQL+PGVector / SQLite+LanceDB (file-based)
Graph:        Kuzu (embedded)
LLM:          OpenAI / Anthropic / Ollama
API key:      configured / missing
Clone:        /path/to/cognee
.mcp.json:    updated
.env:         created / updated / not needed
.gitignore:   .mcp.json entry present
Access ctrl:  disabled (single-user default)
Health check: passed / failed

Next steps:
- Run /hello to start your first session
- Run /mcp-doctor anytime to check connectivity
```

## Ollama Configuration

If the user chose Ollama as their LLM provider, these environment variables must ALL be set (in both `.env` and `.mcp.json` env block):

| Variable | Purpose | Example value |
|----------|---------|---------------|
| `LLM_PROVIDER` | LLM backend | `ollama` |
| `LLM_MODEL` | Chat model | `llama3.1:8b` |
| `LLM_ENDPOINT` | Ollama API | `http://localhost:11434/v1` |
| `LLM_API_KEY` | Placeholder | `ollama` |
| `EMBEDDING_PROVIDER` | Embedding backend | `ollama` |
| `EMBEDDING_MODEL` | Embedding model | `nomic-embed-text:latest` |
| `EMBEDDING_ENDPOINT` | Embedding API | `http://localhost:11434/api/embed` |
**Critical**: All embedding variables must be set. If only LLM is configured for Ollama, embeddings default to OpenAI and fail without an OpenAI key.

**Tokenizer**: If the chosen embedding model requires a HuggingFace tokenizer (e.g., nomic-embed-text needs `HUGGINGFACE_TOKENIZER`), look up the correct tokenizer name for the specific model version the user selected. Do not assume a fixed value — check the model's documentation.

The user also needs Ollama installed and the models pulled. Search the web for current Ollama installation instructions for their platform if needed.

## Expansion Path

After initial setup, these upgrades are config-only changes:

| Need | Change |
|------|--------|
| More LLM throughput | Add `LLM_RATE_LIMIT_ENABLED=true`, `LLM_RATE_LIMIT_REQUESTS=60` |
| Multiple agents sharing memory | Switch cognee-mcp to HTTP transport, point all agents at one instance |
| Remote/shared graph DB | Add Neo4j via docker compose, set `GRAPH_DATABASE_PROVIDER=neo4j` |
| Team usage with permissions | Set `ENABLE_BACKEND_ACCESS_CONTROL=true` (disabled by default for local dev — see Access Control Note) |
| Cloud storage | Set `STORAGE_BACKEND=s3` + AWS credentials |
| Caching layer | Add Redis via docker compose |
| Better model | Change `LLM_MODEL` to a higher-tier model |

## Advanced: HTTP/SSE Transport (Shared Instance)

For multi-agent setups or remote access, cognee-mcp can run as an HTTP server instead of stdio. This allows multiple Claude Code instances to share one knowledge graph.

When configured this way, `.mcp.json` uses a `url` field instead of `command`/`args`:
```
"cognee": { "url": "http://<host>:<port>/mcp" }
```

Use the actual host and port the cognee-mcp HTTP server binds to — check the cognee-mcp docs for current flags to start the server in HTTP mode and which port it defaults to.

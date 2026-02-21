---
name: setup-cognee
description: Install and configure cognee-mcp on this machine
user_invocable: true
args: Optional preferred method (recommended, minimal, docker-full, local)
---

# Setup Cognee — Install & Configure cognee-mcp

You are helping the user get cognee-mcp running on their machine. Walk through setup interactively, detecting what's already installed and what needs to be done.

## Steps

### 1. Detect Environment

Check what's available on this machine (run these in parallel):
- `which uv` and `which uvx` — is uv installed?
- `which docker` and `docker info 2>/dev/null | head -5` — is Docker installed and running?
- `python3 --version` — Python version (need 3.10+)
- `echo $LLM_API_KEY` — is an API key set?
- `docker ps --filter name=postgres --format '{{.Names}}' 2>/dev/null` — is Postgres already running?
- Check if `.mcp.json` exists in the project root
- Check if `.env` exists in the project root

### 2. Choose Setup Level

Present these options, **recommending the first** if Docker is available:

**Option A: Recommended — uvx + PostgreSQL/PGVector (most robust)**
- cognee-mcp via uvx (simple, managed by Claude Code)
- PostgreSQL + PGVector via Docker (one container, handles relational + vector)
- Kuzu embedded for graph (zero config, in-process, fast)
- Eliminates file-based DB locking (SQLite, LanceDB)
- Best expansion path for future needs
- Requires: Docker + uv + LLM API key

**Option B: Minimal — uvx + file-based defaults**
- cognee-mcp via uvx
- SQLite + LanceDB + Kuzu (all file-based, zero infrastructure)
- Good for trying things out, but file locking can cause issues under load
- Requires: uv + LLM API key

**Option C: Docker full-stack**
- Everything in Docker (cognee-mcp + Postgres + optional Neo4j/Redis)
- Most isolated, reproducible
- Requires: Docker + LLM API key

**Option D: Local clone (for development)**
- Clone cognee repo, run from source
- Full access to modify cognee itself
- Requires: git + Python 3.10+ + uv + LLM API key

Ask the user which they prefer if not specified. Default to Option A.

### 3. Configure API Key

If `LLM_API_KEY` is not set, ask the user for their API key and explain the options:

- **OpenAI** (recommended): Most compatible with instructor/structured output extraction. Least troubleshooting. Set `LLM_API_KEY` to your OpenAI key.
- **Anthropic**: Set `LLM_PROVIDER=anthropic`, `LLM_MODEL=claude-3-5-sonnet-20241022`, `LLM_API_KEY=your-anthropic-key`
- **Ollama** (local, free): Requires configuring BOTH LLM and embeddings to avoid OpenAI fallback. See Ollama section below.

Tell the user to add the key to their shell profile (`~/.zshrc` or `~/.bashrc`):
```bash
export LLM_API_KEY="sk-..."
```

**Critical gotcha**: If you configure only LLM or only embeddings, the other defaults to OpenAI. Either configure both or have a valid OpenAI key.

### 4. Install & Configure (based on chosen option)

---

#### Option A: Recommended (uvx + PostgreSQL/PGVector)

**Step 4a-1: Install uv if missing**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Step 4a-2: Start PostgreSQL + PGVector**

Check if a cognee Postgres container is already running:
```bash
docker ps --filter name=postgres --format '{{.Names}}'
```

If not running, start it. Use the cognee docker-compose if available, otherwise run directly:

```bash
# Option 1: If user has the cognee repo cloned
cd /path/to/cognee && docker compose --profile postgres up -d

# Option 2: Standalone container (no repo needed)
docker run -d \
  --name cognee-postgres \
  -e POSTGRES_USER=cognee \
  -e POSTGRES_PASSWORD=cognee \
  -e POSTGRES_DB=cognee_db \
  -p 5432:5432 \
  --restart unless-stopped \
  pgvector/pgvector:pg17
```

Verify it's running:
```bash
docker ps --filter name=postgres
```

**Step 4a-3: Create `.env`**

Write a `.env` file in the project root (or update the existing one):

```env
# LLM — OpenAI recommended
LLM_API_KEY="${LLM_API_KEY}"
LLM_MODEL="openai/gpt-4o-mini"

# Database — PostgreSQL handles both relational + vector storage
DB_PROVIDER=postgres
DB_HOST=127.0.0.1
DB_PORT=5432
DB_USERNAME=cognee
DB_PASSWORD=cognee
DB_NAME=cognee_db
VECTOR_DB_PROVIDER=pgvector

# Graph — Kuzu embedded (default, no config needed)
# GRAPH_DATABASE_PROVIDER=kuzu
```

**Important**: If a `.env` already exists, merge these values — don't overwrite unrelated config.

**Step 4a-4: Configure `.mcp.json`**

Write or merge into `.mcp.json`:

```json
{
  "mcpServers": {
    "cognee": {
      "command": "uvx",
      "args": ["--from", "cognee-mcp", "cognee-mcp"],
      "env": {
        "LLM_API_KEY": "${LLM_API_KEY}",
        "DB_PROVIDER": "postgres",
        "DB_HOST": "127.0.0.1",
        "DB_PORT": "5432",
        "DB_USERNAME": "cognee",
        "DB_PASSWORD": "cognee",
        "DB_NAME": "cognee_db",
        "VECTOR_DB_PROVIDER": "pgvector"
      }
    }
  }
}
```

If `.mcp.json` already exists with other servers, merge the cognee entry — don't overwrite.

---

#### Option B: Minimal (uvx + file-based defaults)

**Step 4b-1: Install uv if missing**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Step 4b-2: Configure `.mcp.json`**

```json
{
  "mcpServers": {
    "cognee": {
      "command": "uvx",
      "args": ["--from", "cognee-mcp", "cognee-mcp"],
      "env": {
        "LLM_API_KEY": "${LLM_API_KEY}"
      }
    }
  }
}
```

No `.env` needed — defaults to SQLite + LanceDB + Kuzu (all file-based).

**Note**: This setup can hit file locking issues if cognee is writing while you search. Fine for light usage. Run `/setup-cognee recommended` later to upgrade.

---

#### Option C: Docker full-stack

**Step 4c-1: Clone cognee repo** (for docker-compose)
```bash
git clone https://github.com/topoteretes/cognee.git ~/cognee
```

**Step 4c-2: Create `.env` in the cognee repo**
```env
LLM_API_KEY="${LLM_API_KEY}"
LLM_MODEL="openai/gpt-4o-mini"
DB_PROVIDER=postgres
DB_HOST=postgres
DB_PORT=5432
DB_USERNAME=cognee
DB_PASSWORD=cognee
DB_NAME=cognee_db
VECTOR_DB_PROVIDER=pgvector
```

**Step 4c-3: Start the stack**
```bash
cd ~/cognee
docker compose --profile postgres --profile mcp up -d
```

This starts PostgreSQL + PGVector and cognee-mcp together. The `docker compose` command automatically creates a `cognee_default` Docker network so the containers can communicate by service name (e.g., `postgres` resolves to the Postgres container). The `cognee/cognee-mcp:main` image is published on Docker Hub by the cognee team.

**Step 4c-4: Configure `.mcp.json`**

First, find the Docker network name created by compose:
```bash
docker network ls | grep cognee
```

Then configure `.mcp.json` using that network name (typically `cognee_default`):

```json
{
  "mcpServers": {
    "cognee": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--network", "cognee_default",
        "-e", "LLM_API_KEY",
        "-e", "DB_PROVIDER=postgres",
        "-e", "DB_HOST=postgres",
        "-e", "DB_PORT=5432",
        "-e", "DB_USERNAME=cognee",
        "-e", "DB_PASSWORD=cognee",
        "-e", "DB_NAME=cognee_db",
        "-e", "VECTOR_DB_PROVIDER=pgvector",
        "cognee/cognee-mcp:main"
      ],
      "env": {
        "LLM_API_KEY": "${LLM_API_KEY}"
      }
    }
  }
}
```

---

#### Option D: Local clone

**Step 4d-1: Clone and install**
```bash
git clone https://github.com/topoteretes/cognee.git ~/cognee
cd ~/cognee/cognee-mcp
uv sync --dev --all-extras --reinstall
```

**Step 4d-2: Start Postgres** (same as Option A, step 4a-2)

**Step 4d-3: Create `.env`** (same as Option A, step 4a-3)

**Step 4d-4: Configure `.mcp.json`**
```json
{
  "mcpServers": {
    "cognee": {
      "command": "$HOME/cognee/cognee-mcp/.venv/bin/python",
      "args": ["$HOME/cognee/cognee-mcp/src/server.py"],
      "env": {
        "LLM_API_KEY": "${LLM_API_KEY}",
        "DB_PROVIDER": "postgres",
        "DB_HOST": "127.0.0.1",
        "DB_PORT": "5432",
        "DB_USERNAME": "cognee",
        "DB_PASSWORD": "cognee",
        "DB_NAME": "cognee_db",
        "VECTOR_DB_PROVIDER": "pgvector"
      }
    }
  }
}
```

### 5. Verify

Run `/mcp-doctor` to confirm cognee is healthy.

If it fails, troubleshoot based on the error:

**Common issues:**
- **"uvx: command not found"**: Run `curl -LsSf https://astral.sh/uv/install.sh | sh`, restart terminal
- **"docker: command not found"**: Install Docker Desktop from https://docker.com
- **Postgres connection refused**: Check `docker ps` — is the container running? Check port 5432 isn't taken by another Postgres.
- **API key errors**: Verify with `echo $LLM_API_KEY` — should not be empty
- **"relation does not exist"**: First run — cognee auto-runs migrations. Wait a moment and retry.
- **Mixed provider errors** (Ollama): You must configure BOTH LLM and embeddings. See Ollama section below.
- **Python version errors**: cognee-mcp requires Python 3.10+
- **File locking errors** (minimal setup): Upgrade to recommended setup with Postgres

### 6. Report

```
Cognee Setup Complete
=====================
Setup level: recommended / minimal / docker-full / local
Database: PostgreSQL+PGVector / SQLite+LanceDB
Graph: Kuzu (embedded)
LLM: OpenAI / Anthropic / Ollama
API key: configured / missing
.mcp.json: updated
.env: created / updated / not needed
Health check: passed / failed

Next steps:
- Run /hello to start your first session
- Run /mcp-doctor anytime to check connectivity
```

## Ollama Setup (Local LLM — No API Key Needed)

If the user wants fully local operation with Ollama:

1. Install Ollama: https://ollama.com
2. Pull models:
   ```bash
   ollama pull llama3.1:8b
   ollama pull nomic-embed-text:latest
   ```
3. Add to `.env`:
   ```env
   LLM_PROVIDER=ollama
   LLM_MODEL=llama3.1:8b
   LLM_ENDPOINT=http://localhost:11434/v1
   LLM_API_KEY=ollama
   EMBEDDING_PROVIDER=ollama
   EMBEDDING_MODEL=nomic-embed-text:latest
   EMBEDDING_ENDPOINT=http://localhost:11434/api/embed
   HUGGINGFACE_TOKENIZER=nomic-ai/nomic-embed-text-v1.5
   ```

**Critical**: You MUST set all embedding variables. If you only set LLM to Ollama, embeddings default to OpenAI and fail without an OpenAI key.

## Expansion Path

After the initial setup, these upgrades are config-only changes:

| Need | Change |
|------|--------|
| More LLM throughput | Add `LLM_RATE_LIMIT_ENABLED=true`, `LLM_RATE_LIMIT_REQUESTS=60` |
| Multiple agents sharing memory | Switch cognee-mcp to HTTP transport, point all agents at one instance |
| Remote/shared graph DB | Add Neo4j: `docker compose --profile neo4j up -d`, set `GRAPH_DATABASE_PROVIDER=neo4j` |
| Team usage with permissions | Set `REQUIRE_AUTHENTICATION=True`, `ENABLE_BACKEND_ACCESS_CONTROL=True` |
| Cloud storage | Set `STORAGE_BACKEND=s3` + AWS credentials |
| Caching layer | Add Redis: `docker compose --profile redis up -d` |
| Better model | Change `LLM_MODEL=openai/gpt-4o` or `openai/o3-mini` |

## Advanced: HTTP/SSE Transport (Shared Instance)

For multi-agent setups or remote access, run cognee-mcp as an HTTP server:

```bash
# Start as HTTP server
uvx --from cognee-mcp cognee-mcp --transport http --host 127.0.0.1 --port 8000 --path /mcp

# Or with Docker
docker run -d \
  --name cognee-mcp-server \
  -e TRANSPORT_MODE=http \
  --env-file ./.env \
  -p 8000:8000 \
  --restart unless-stopped \
  cognee/cognee-mcp:main
```

Then configure `.mcp.json` with a URL instead of a command:
```json
{
  "mcpServers": {
    "cognee": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

---
name: setup-cognee
description: Install and configure cognee-mcp on this machine
user_invocable: true
args: Optional storage backend (file-based, postgres) or --refresh-setup
---

# Setup Cognee — Install & Configure cognee-mcp

You are helping the user get cognee-mcp running on this machine. Walk through setup interactively, detecting what is already installed and what needs to be done.

**Important**: The cognee MCP server runs from a local clone of the cognee repo (the `cognee-mcp/` subdirectory) or via the Docker image `cognee/cognee-mcp:main`. There is no PyPI package — do not attempt `uvx`, `pip install`, or any package-manager-based installation.

## Configuration model

Two config files are involved:

- **`.mcp.json`** (workspace root) — **canonical source of truth**. Claude Code reads this to launch the cognee MCP server. The `env` block is what the skill writes and edits.
- **`cognee-mcp/.env`** — **generated artifact**, derived verbatim from `.mcp.json`'s `env` block. Cognee's `__init__.py` calls `dotenv.load_dotenv(override=True)`, so any `.env` in cognee's dotenv search path overrides the env Claude Code provides. Keeping it aligned prevents drift; keeping it present at all shields the setup from any higher `.env` (cognee's walk-up search terminates at the first `.env` it finds).

`.env` carries a header marking it as generated. Users edit `.mcp.json` and re-run `/setup-cognee --refresh-setup` to propagate.

**Probe isolation**: when the graph DB is the default file-based Ladybug, the in-session cognee MCP holds an exclusive lock on `<SYSTEM_ROOT>/databases/cognee_graph_ladybug` from Claude Code session boot. Verification probes must override `SYSTEM_ROOT_DIRECTORY` to a temp dir to avoid contention; `DATA_ROOT_DIRECTORY` gets overridden alongside for cleanliness — not lock-avoidance — so probe markers don't pollute the user's data. With a remote graph DB (Neo4j), no lock contention; isolation is still cleaner.

## Verification modes

Three layers, each covers different ground:

1. **`/setup-cognee --refresh-setup`** — re-syncs deps, provider extras, `.env`, then runs an end-to-end stdio probe against isolated data dirs. Covers everything post-install: dependency drift, provider extras after a `git pull`, `.env` drift, runtime config correctness.
2. **`/mcp-doctor`** (session mode) — confirms cognee tools surface in-session after a Claude Code restart. Covers MCP-server-load only.
3. **Fresh tear-down + reinstall** (manual) — `rm -rf <cognee-mcp>/.venv <DATA_ROOT> <SYSTEM_ROOT>`, then `/setup-cognee`. Covers the install path itself (clone, initial `.mcp.json` write, interactive prompts). Run after major cognee version bumps or whenever this skill is edited. Not automated — the install is interactive.

## --refresh-setup mode

Run after a cognee-mcp `git pull` or `.mcp.json` edit. Three things drift independently, each with its own corrective action:

- **Lockfile vs installed deps — and cognee itself.** `uv sync` restores whatever the repo's lockfile pins. Upstream cognee fixes ship to PyPI ahead of the committed lockfile (the AnthropicAdapter `max_tokens` bug in cognee <1.1.0 was the canonical case). Record the currently installed cognee version first so the rollback gate (below) has something to pin back to. Advance cognee with `uv sync --upgrade-package cognee`; fall back to the lockfile version on resolution or network failure.
- **Provider extras.** `uv add` writes to `pyproject.toml`, which a `git pull` may overwrite. Re-apply the extras declared in `.mcp.json` (`LLM_PROVIDER`, `EMBEDDING_PROVIDER`). After each change, run an import-check rollback gate: if the configured provider's adapter no longer imports, pin cognee back to the pre-upgrade version. Read installed cognee source for the import path — cognee reorganises these between versions.
- **`.env` vs `.mcp.json`.** Cognee's `__init__.py` calls `dotenv.load_dotenv(override=True)`, so a stale `.env` silently wins over the env Claude Code provides. Compare, and strict-regenerate from `.mcp.json` on any drift — values OR a missing generated-artifact header.

Then exercise the install end-to-end via the stdio probe (see Step 5 Phase 1) — with `SYSTEM_ROOT_DIRECTORY` (and `DATA_ROOT_DIRECTORY` for cleanliness) overridden to a temp dir so it doesn't contend with the in-session cognee's Ladybug lock. Validate the real `DATA_ROOT_DIRECTORY` / `SYSTEM_ROOT_DIRECTORY` from `.mcp.json` separately with a writability check — no subprocess needed.

After the probe passes, tell the user to restart Claude Code; the in-session cognee still has the previous config cached in memory.

Common failure modes:
- `[Errno 61] Connect call failed ('127.0.0.1', 5432)` — `.env` still declares Postgres; regenerate from `.mcp.json`.
- `Embedding connection test timed out` — `EMBEDDING_PROVIDER` not set or unreachable.
- `ModuleNotFoundError: <provider>` — provider extra not installed; re-apply it.
- `Field required ... data` — schema mismatch; the probe is hardcoding param names instead of reading the input schema.
- `IO exception: Could not set lock on file ... cognee_graph_ladybug` — `SYSTEM_ROOT_DIRECTORY` override didn't apply for the probe.

## Step 0: Check latest documentation

Look up current cognee MCP setup docs before executing install steps — flags, deps, or steps may have changed since this skill was written. Tell the user what changed if anything differs.

## Step 1: Detect environment

Detect what's available:
- OS and platform (affects Docker host address, shell profile path)
- Available tools: `git`, `python3` (3.10–3.13 — cognee deps have no wheels for 3.14 yet), `uv`, `docker`, `docker compose`
- Current shell (from `$SHELL`)
- Whether `LLM_API_KEY` is already set
- Whether port 5432 is in use (Postgres backend only)
- Whether cognee is already cloned (`~/cognee`, project-relative)
- Whether `.mcp.json` and `cognee-mcp/.env` already exist, and what's in them

Report findings before proceeding.

## Determining DB_HOST

Only relevant for the Postgres backend. The address depends on where the cognee process runs relative to the database:

| Connecting process | DB runs in | DB_HOST |
|---|---|---|
| Locally (Python on host) | Docker container on host | `127.0.0.1` |
| In Docker container | Same docker compose stack | Service name (e.g., `postgres`) |
| In Docker container | Host machine directly | macOS: `host.docker.internal`. Linux: bridge IP. |

The address in `.mcp.json`'s env is the one the cognee process will use.

## Default database credentials

Dev-only defaults for the Postgres backend (communicate "dev-only" to the user):

| Variable | Default | Notes |
|---|---|---|
| `DB_PROVIDER` | `postgres` | |
| `DB_HOST` | per Determining DB_HOST | derive, don't hardcode |
| `DB_PORT` | `5432` | check if already in use |
| `DB_NAME` | `cognee_db` | |
| `DB_USERNAME` | `cognee` | cognee uses `db_username` (pydantic-settings); `DB_USER` is silently ignored |
| `DB_PASSWORD` | `cognee` | dev-only, insecure |

## Step 2: Choose storage backend

Two backends. Recommend the first.

| Backend | Description | Requires | When to pick |
|---|---|---|---|
| **file-based** *(default)* | SQLite (relational) + LanceDB (vector) + Ladybug (graph). All file-based under `~/cognee-data/`. | git, Python 3.10–3.13, uv | Single-user local dev. Tarball one directory for backup. No Docker overhead. SQLite WAL handles 2-3 parallel Claude Code sessions with bursty writes. |
| **postgres+docker** | PostgreSQL+pgvector via Docker (relational + vector). Ladybug for graph. | git, Python 3.10–3.13, uv, Docker | Sustained heavy parallel writes. Production-shaped local setups. |

If the user passes a preset (`file-based` or `postgres`), use it. The choice is reversible — same data model, different connection strings.

**Embedding choice is orthogonal to storage choice** (see Step 3c). Don't bundle them.

## Step 3a: Choose LLM provider

LLM and embedding providers are independent — the LLM choice does NOT configure embeddings.

- **OpenAI** — most compatible with cognee's structured-output extraction.
- **Anthropic** — set `LLM_PROVIDER=anthropic`, `LLM_MODEL` to the current best Sonnet model. The `anthropic` package is a cognee optional extra — not pulled in by `uv sync` alone; add it explicitly in Step 4.
- **Ollama** (local, free) — requires configuring BOTH LLM and embeddings via Ollama (see Ollama Configuration).

## Step 3b: API key

If `$LLM_API_KEY`, `$OPENAI_API_KEY`, or `$ANTHROPIC_API_KEY` is already set in the user's environment, show a masked version (first 4 + last 4 chars) and confirm. Otherwise ask for the key in a dedicated prompt.

**Use the literal key value in `.mcp.json` and `.env`** — Claude Code does not expand shell variables like `${LLM_API_KEY}`. Also instruct the user to persist the key in their shell profile (`~/.zshrc`, `~/.bashrc`, `~/.bash_profile`, or fish config depending on `$SHELL`) so it's available to terminal sessions.

## Step 3c: Choose embedding provider

Three options. Recommend the first. **Always set `EMBEDDING_DIMENSIONS` explicitly** — cognee falls back to 3072 (an OpenAI assumption) on registry-lookup miss, which silently corrupts ingest for non-default models.

| Provider | Model | Dim | MTEB | Cost | Notes |
|---|---|---|---|---|---|
| **fastembed** *(default)* | `BAAI/bge-large-en-v1.5` | 1024 | ~64.2 | free, local | No API key, no egress. First-use downloads ~1.2GB to `~/.cache/fastembed/`. Cognee optional extra — add explicitly in Step 4. |
| **OpenAI** | `text-embedding-3-large` | 3072 | ~64.6 | ~$0.13/1M tokens | Requires `OPENAI_API_KEY` and egress to api.openai.com. |
| **Voyage** | `voyage-3` | 1024 | ~65.6 | free tier exists | Requires `VOYAGE_API_KEY`. Anthropic-recommended embeddings. Cognee optional extra. |

For the chosen provider, set in `.mcp.json`'s env:
- `EMBEDDING_PROVIDER`
- `EMBEDDING_MODEL`
- `EMBEDDING_DIMENSIONS` (model's real dim — verify; cognee's fallback is wrong for non-OpenAI)
- `EMBEDDING_MAX_TOKENS` (`512` for bge-large; check provider docs otherwise)

For Ollama, see Ollama Configuration.

## Step 3d: Data directory

Cognee defaults to writing databases inside the venv (`.venv/lib/python<ver>/site-packages/cognee/.cognee_system/databases/`) — won't survive `uv sync --reinstall`, hidden from backup tooling. Always set both:

- `DATA_ROOT_DIRECTORY=<absolute path>/data` — ingested data files
- `SYSTEM_ROOT_DIRECTORY=<absolute path>/system` — SQLite / LanceDB / graph DBs

Default suggestion: `~/cognee-data/` (with `~` expanded). Ask if the user wants this or somewhere else.

## Step 4: Install & configure

Each backend defines goals. Achieve each using the tools and paths from Step 1 and the docs from Step 0.

### File-based backend (SQLite + LanceDB + Ladybug)

**Goal 1: Ensure `uv` is installed.** If not present, follow current install instructions from astral.sh.

**Goal 2: Clone cognee repo.** Suggest `~/cognee` if not already cloned. Repo: `https://github.com/topoteretes/cognee.git`.

**Goal 3a: Run `uv sync` in `cognee-mcp/`.** Cognee-mcp's `pyproject.toml` declares only a Python floor; the real upper bound is set transitively by deps with narrow ABI wheels. On a "no wheel for cpXY" failure, retry with `--python <version>` picking the highest installed Python whose minor sits inside the supported ABI set.

**Goal 3b: Provider extras.** Run `uv add <package>` for each declared provider that's an optional cognee extra:
- `anthropic` for `LLM_PROVIDER=anthropic`
- `fastembed` for `EMBEDDING_PROVIDER=fastembed`
- `voyageai` for `EMBEDDING_PROVIDER=voyage`

Note: `uv add` writes to `pyproject.toml`; a future `git pull` may overwrite it. Use `/setup-cognee --refresh-setup` after any update.

**Goal 4: Write `.mcp.json`.** Create the `mcpServers.cognee` entry (or merge if `.mcp.json` already has other servers). Create the data dirs from Step 3d if they don't exist.

- Literal values everywhere — Claude Code does not expand `${VAR}` or `$HOME`.
- Resolved absolute paths — no `~` or relative paths.
- The actual API key from Step 3b in the env block.
- Env block:
  - LLM: `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`
  - Embedding: `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `EMBEDDING_DIMENSIONS`, `EMBEDDING_MAX_TOKENS`
  - Storage: `DB_PROVIDER=sqlite`, `VECTOR_DB_PROVIDER=lancedb`, `GRAPH_DATABASE_PROVIDER=ladybug`
  - Data dirs: `DATA_ROOT_DIRECTORY`, `SYSTEM_ROOT_DIRECTORY`
  - Access control: `ENABLE_BACKEND_ACCESS_CONTROL=false` (see Access Control Note)

**Goal 5: Generate `cognee-mcp/.env` from `.mcp.json`.** Every `KEY=VALUE` line verbatim, with this header:

```
# GENERATED by /setup-cognee — DO NOT EDIT.
# This file is derived from .mcp.json's `env` block to align cognee's
# dotenv-override (cognee/__init__.py:11) with Claude Code's MCP config.
# To change config: edit .mcp.json, then run `/setup-cognee --refresh-setup`.
```

If `cognee-mcp/.env` already exists, replace it entirely. Custom env belongs in `.mcp.json`.

**Goal 6: Add `.mcp.json` to `.gitignore`.** Contains secrets, machine-specific.

### Postgres+Docker backend

Same as file-based, with these additions:

- Before Goal 4: start PostgreSQL+pgvector via Docker. Check port 5432 isn't already in use. Address per Determining DB_HOST. Credentials per Default Database Credentials (dev-only).
- Goal 4: env block additionally carries `DB_PROVIDER=postgres`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD`, and `VECTOR_DB_PROVIDER=pgvector` (replacing `lancedb`). Graph DB remains `ladybug` by default.
- Goals 5, 6: identical to file-based.

## Access Control Note

Cognee v0.5.0+ defaults to multi-user access control (`ENABLE_BACKEND_ACCESS_CONTROL=true`), which requires auth tokens and user management. Causes confusing errors in single-user local dev. This skill sets it to `false` by default. For shared instances, see the Expansion Path.

## Step 5: Verify

### Phase 1: Pre-flight stdio probe

Exercise the install through cognee's stdio interface end-to-end: connect, list tools (confirm `remember` / `recall` present), call `remember` with a unique probe-id, call `recall` querying for that id. **The probe-id must appear verbatim in the recall response** — that's the assertion; anything less is a partial pass.

Pass through Claude Code's env explicitly (`env -i HOME=$HOME PATH=$PATH <vars from .mcp.json>`) so the child sees the same env it would see at session boot.

**Schema-driven, not hardcoded.** Cognee renames tool input parameters across versions (`data` vs `information` for `remember`). Read the input schema and build the args from it.

**Probe isolation only when needed.** A fresh install assumes no in-session cognee — the probe can use the user's real `DATA_ROOT_DIRECTORY` / `SYSTEM_ROOT_DIRECTORY` because they're empty and nothing holds a lock. If running `/setup-cognee` to reconfigure an already-loaded cognee, use `/setup-cognee --refresh-setup` instead — that path runs the probe against temp dirs to avoid Ladybug lock contention.

**Tell the user the wait.** ~30s normally. ~100s on a fresh fastembed install (downloads ~1.2GB of embedding weights and runs an LLM extraction call). Without the heads-up the probe will feel hung.

Common failure modes:
- `[Errno 61] Connect call failed ('127.0.0.1', 5432)` — `.env` still declares Postgres; regenerate from `.mcp.json`.
- `Embedding connection test timed out` — `EMBEDDING_PROVIDER` not set or unreachable.
- `ModuleNotFoundError: <provider>` — provider extra not installed; re-apply from Goal 3b.
- `Field required ... data` — schema mismatch; probe is hardcoding param names.

### Phase 2: Post-restart check

After the user restarts Claude Code, run `/mcp-doctor` to confirm cognee tools surface in-session. If absent after a clean restart, run `/mcp-doctor --deep` for the startup error.

## Step 6: Report

```
Cognee Setup Complete
=====================
Backend:           file-based / postgres+docker
LLM:               <provider>/<model>
Embedding:         <provider>/<model> (<dim>-dim)
Data dir:          <DATA_ROOT_DIRECTORY>
Clone:             <path>
.mcp.json:         updated
.env:              generated from .mcp.json
.gitignore:        .mcp.json entry present
Access control:    disabled (single-user default)
Pre-flight probe:  passed (remember+recall round-trip with probe-id <id>)

Next steps:
- Restart Claude Code so the cognee MCP server loads in-session
- Run /mcp-doctor to confirm cognee tools surface
- Run /hello to start a session

Notes:
- First `remember` call takes ~10-30s (cognee extracts a knowledge graph via the LLM).
  Subsequent calls amortise.
- If fastembed: first call also downloads ~1.2GB to ~/.cache/fastembed/.
- To change config: edit .mcp.json, then /setup-cognee --refresh-setup.
```

## Ollama Configuration

If the user chose Ollama, set BOTH LLM and embedding env vars to Ollama. If only one is set, the other defaults to OpenAI and fails without an OpenAI key.

| Variable | Example value |
|---|---|
| `LLM_PROVIDER` | `ollama` |
| `LLM_MODEL` | `llama3.1:8b` |
| `LLM_ENDPOINT` | `http://localhost:11434/v1` |
| `LLM_API_KEY` | `ollama` (placeholder) |
| `EMBEDDING_PROVIDER` | `ollama` |
| `EMBEDDING_MODEL` | `nomic-embed-text:latest` |
| `EMBEDDING_ENDPOINT` | `http://localhost:11434/api/embed` |
| `EMBEDDING_DIMENSIONS` | check the model's docs — `nomic-embed-text` is 768 |

If the embedding model requires a HuggingFace tokenizer (e.g., `nomic-embed-text` needs `HUGGINGFACE_TOKENIZER`), look up the right one for the chosen model version.

User also needs Ollama installed and models pulled.

## Expansion Path

Config-only changes (edit `.mcp.json`, then `/setup-cognee --refresh-setup`):

| Need | Change |
|---|---|
| More LLM throughput | Add `LLM_RATE_LIMIT_ENABLED=true`, `LLM_RATE_LIMIT_REQUESTS=60` |
| Multiple agents sharing memory | Switch cognee-mcp to HTTP transport, point all agents at one instance |
| Remote/shared graph DB | Add Neo4j via docker compose, set `GRAPH_DATABASE_PROVIDER=neo4j` |
| Team usage with permissions | Set `ENABLE_BACKEND_ACCESS_CONTROL=true` |
| Cloud storage | Set `STORAGE_BACKEND=s3` + AWS credentials |
| Caching layer | Add Redis via docker compose |
| Better model | Change `LLM_MODEL` |
| File-based → Postgres | Change `DB_PROVIDER`, `VECTOR_DB_PROVIDER`, add `DB_*` vars; start the Postgres container |

## Advanced: HTTP/SSE Transport (Shared Instance)

For multi-agent setups or remote access, cognee-mcp can run as an HTTP server instead of stdio. Multiple Claude Code instances can then share one knowledge graph.

`.mcp.json` uses `url` instead of `command`/`args`:
```
"cognee": { "url": "http://<host>:<port>/mcp" }
```

The `.env`-as-derived-artifact pattern doesn't apply in HTTP mode — the cognee process is shared and runs separately. The cognee process's env is managed wherever it's hosted.

Check current cognee-mcp docs for the flags to start the server in HTTP mode.

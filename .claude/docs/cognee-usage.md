# Cognee MCP Usage Guide

This project uses [cognee](https://github.com/topoteretes/cognee) via MCP for persistent semantic memory.

## Available MCP Tools

### `cognee_add`
Add text or data to cognee for processing.

```
cognee_add(text="Session summary: implemented auth flow using JWT tokens...")
```

Use this to store session summaries, lessons learned, and project context.

### `cognee_cognify`
Process added data into the knowledge graph. Call this after `cognee_add` to extract entities and relationships.

```
cognee_cognify()
```

### `cognee_search`
Search the knowledge graph semantically.

```
cognee_search(query="authentication patterns used in this project")
```

Returns relevant context from all previously stored knowledge.

### `cognee_list_datasets`
List all datasets in cognee. Useful as a health check.

```
cognee_list_datasets()
```

## Typical Workflows

### Storing a lesson
```
1. cognee_add(text="[convention] Always use type hints for function signatures")
2. cognee_cognify()
```

### Retrieving context at session start
```
1. cognee_search(query="recent work and open items")
2. cognee_search(query="project conventions and patterns")
```

### Storing a session summary
```
1. cognee_add(text="Session summary: Added pagination to the /users endpoint, fixed N+1 query in orders list")
2. cognee_cognify()
```

## Timing: cognee_cognify is async

After calling `cognee_cognify`, the knowledge graph processing runs asynchronously. If you search immediately after, you may get incomplete results. In practice this is only an issue in `/bye` where we add + cognify + potentially search in quick succession. The skills are designed to add/cognify as a fire-and-forget step — the results will be available next session via `/hello`.

## When Cognee is Unavailable

All skills gracefully degrade when cognee MCP is down. Markdown memory files (`.claude/memory/`) serve as the primary persistent store. Cognee adds semantic search over accumulated knowledge but is not required for basic operation.

## Infrastructure

The recommended setup uses:
- **cognee-mcp via uvx** — managed by Claude Code, no manual server management
- **PostgreSQL + PGVector** — single Docker container for relational + vector storage (no file locking)
- **Kuzu** — embedded graph DB, in-process, zero config

Start Postgres if not running:
```bash
docker run -d --name cognee-postgres \
  -e POSTGRES_USER=cognee -e POSTGRES_PASSWORD=cognee -e POSTGRES_DB=cognee_db \
  -p 5432:5432 --restart unless-stopped pgvector/pgvector:pg17
```

Run `/setup-cognee` for full guided setup on a new machine.

## Troubleshooting

- **MCP not connecting**: Run `/mcp-doctor` for diagnostics, then `/setup-cognee` if needed
- **No results from search**: Ensure you've run `cognee_cognify` after adding data
- **Slow responses**: Cognee processes data asynchronously; wait a moment after cognify
- **Connection refused on port 5432**: Check `docker ps` — is cognee-postgres running?
- **File locking errors**: You're likely on the minimal (SQLite/LanceDB) setup. Run `/setup-cognee recommended` to upgrade to Postgres.

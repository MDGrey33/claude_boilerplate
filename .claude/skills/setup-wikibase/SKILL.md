---
name: setup-wikibase
description: Install and configure a local Wikibase Suite for projects that need a Wikidata-style knowledge graph with claim-level provenance
user_invocable: true
args: Optional preferred preset (minimal, full)
---

## Model Selection

See `.claude/skills/_shared/MODEL_SELECTION.md` (in your workspace) for full policy.

- **Default model:** Sonnet — Wikibase setup involves environment detection, Docker compose authoring, schema design judgment, and migration script generation
- **Demote to Haiku when:** running pre-built migration scripts on a chunk of data (mechanical batch processing)
- **Promote to Opus when:** never — generation involves judgment but is not novel reasoning

# Setup Wikibase — Local Knowledge Graph with Provenance

You are helping the user stand up a local Wikibase instance — the same software that powers Wikidata. This is the right choice when the project needs:

- Structured statements with **claim-level references** (every fact carries its source URL + retrieval date + archive snapshot)
- A **standard, queryable** knowledge graph (SPARQL endpoint, not a custom format)
- **Off-the-shelf visualization tools** (Reasonator, SQID, Wikidata Graph Builder)
- **Federation** with Wikidata if/when the project goes public

For projects that just need semantic search over markdown notes, **cognee** (see `setup-cognee`) is lighter weight. See `.claude/docs/memory-systems.md` for the full decision tree.

---

## Step 0: Check Latest Documentation

Before executing installation steps, look up current documentation:
- WMDE's release pipeline: https://github.com/wmde/wikibase-release-pipeline
- Wikibase Docker images: https://hub.docker.com/u/wikibase
- The image tags rotate (e.g. `wdqs:0.3.143` → `wdqs:wdqs0.3.156`); check Docker Hub for currently-published tags before pinning

If the current docs show different image tags or compose patterns than what this skill describes, **adapt accordingly** and tell the user what changed.

## Step 1: Detect Environment

Detect what's available:
- **OS / platform** (macOS Apple Silicon needs `platform: linux/amd64` overrides for Wikibase images that lack arm64 manifests)
- **Docker** (`docker --version`, `docker compose version` — need v2.10+)
- **Available RAM** — full stack uses ~2-4 GiB idle, more under load. Recommend 8+ GiB system minimum.
- **Available ports** — needs 8080, 8834, 8889, 9191 free. Check via `lsof -nP -iTCP:8080 -sTCP:LISTEN`.
- **iCloud sync directory** — Wikibase data volumes (MariaDB, Blazegraph indexes) must NOT live inside an iCloud-synced path; they get heavy and should sit outside.

Report findings before proceeding.

## Step 2: Decide Hosting Path

The user has two real options. Help them pick:

| | Self-hosted Docker | Hosted (wikibase.cloud) |
|---|---|---|
| **Effort** | ~30 min initial + ongoing ops | Sign-up only |
| **Data location** | Local | WMDE-hosted |
| **Cost** | Free | Free for non-commercial |
| **Customization** | Full (custom properties, hooks, etc.) | Limited |
| **Federation w/ Wikidata** | Yes (when published online) | Yes (built-in) |
| **Best for** | Personal / private data, full control | Public data, no ops appetite |

If the user picks hosted, direct them to https://www.wikibase.cloud/ and stop here.

If self-hosted, continue.

## Step 3: Compose Setup

The official `wikibase-release-pipeline` repo's `deploy/` compose is **production-oriented** (Traefik + Let's Encrypt + real DNS). For local development, write a **minimal compose** that exposes services on plain HTTP localhost ports.

Key services in a minimal stack:
- `wikibase` (MediaWiki + Wikibase extension) → `:8080`
- `wikibase-jobrunner` (background queue)
- `mysql` (MariaDB — internal only)
- `wdqs` (Blazegraph SPARQL endpoint)
- `wdqs-proxy` (nginx → exposes WDQS at `:8834` with CORS headers)
- `wdqs-updater` (syncs Wikibase → triplestore)
- `wdqs-frontend` (query UI) → `:8889`
- `quickstatements` (bulk-import UI) → `:9191`

**Critical environment vars to get right:**

```yaml
wikibase:
  environment:
    MW_WG_SERVER: http://localhost:8080            # public-facing URL — used in entity URIs
    DB_SERVER: mysql:3306
    QUICKSTATEMENTS_PUBLIC_URL: http://localhost:9191
    WDQS_PUBLIC_ENDPOINT_URL: http://localhost:8834/sparql
    WDQS_PUBLIC_FRONTEND_URL: http://localhost:8889
    METADATA_CALLBACK: "false"

wdqs-updater:
  environment:
    WIKIBASE_HOST: wikibase                          # Docker-internal DNS for fetching entity data
    WIKIBASE_CONCEPT_URI: http://localhost:8080      # MUST match the public URL prefix in entity URIs
    MEDIAWIKI_API_URL: http://wikibase/w/api.php

quickstatements:
  environment:
    QUICKSTATEMENTS_PUBLIC_URL: http://localhost:9191
    WIKIBASE_PUBLIC_URL: http://localhost:8080
```

**Apple Silicon caveat:** add `platform: linux/amd64` to all `wikibase/*` images (no arm64 manifests as of writing). Docker Desktop on M-series runs them via Rosetta — slower but works.

**`--bare` flag breaks keychain auth.** Don't use it for the wrapper script that runs `claude -p` against this stack — `--bare` blocks OAuth lookup; the user gets `Not logged in · Please run /login`.

## Step 4: Smoke-Test the Stack

After `docker compose up -d`, verify:

```bash
docker compose ps                                          # all services should be healthy
curl -sf http://localhost:8080/wiki/Main_Page              # MediaWiki up
curl -sf "http://localhost:8834/namespace/wdq/sparql" \
  --data-urlencode 'query=SELECT (COUNT(*) AS ?n) WHERE {?s ?p ?o}'  # SPARQL up
# Open in a browser:
#   http://localhost:8080  (Wikibase)
#   http://localhost:8889  (Query Service UI)
#   http://localhost:9191  (QuickStatements)
```

## Step 5: Define Foundation Schema

Before bulk-importing any data, the user needs:

1. **A property catalog** — every relation in their data needs a Wikibase property (`Pnnn`). Don't skip the references properties — `stated-in`, `reference-URL`, `retrieved`, `archive-URL` are non-negotiable.

2. **A foundation item set** — types like `human`, `political party`, `source organization`; per-source items (CVK, Wikipedia LV, etc.) so references can point at them.

3. **A `property-map.yaml` and `item-map.yaml`** committed to the repo — every script reads these by key name (`P["stated_in"]`, `Q["src_wikipedia_lv"]`) and never hardcodes Pnnn/Qnnn.

See `.claude/docs/wikibase-migration-patterns.md` for the full schema-design checklist + property catalog template.

## Step 6: Bulk Import Strategy

For >1000 entities, the user needs the migration patterns documented separately. Key non-obvious points:

- **Use `wikibaseintegrator` (Python lib)**, not raw HTTP. Handles login token refresh, JSON encoding of statements with qualifiers and references.
- **Default `claims.add()` is `APPEND_OR_REPLACE`** — same-property statements get deduped silently. For multi-valued statements (e.g. one person ran in multiple elections) use `ActionIfExists.FORCE_APPEND` or you'll lose data.
- **Concurrent writes to the same item lose data** — fetch+modify+write is racy. Partition workers by **entity ID**, never by claim index.
- **MediaWiki sessions expire under long batch runs.** Wrap writes in a re-login retry. MediaWiki's login throttle gives a 5-minute lockout if simultaneous workers all try to re-login at once — stagger.
- **Smoke-test with realistic duration before fanning out.** A 5-record test in 10 seconds is too short to trip session expiry. Run one worker for 5+ minutes before launching N parallel workers.

Full pattern reference: `.claude/docs/wikibase-migration-patterns.md`.

## Step 7: Install Helper Scripts

The skill should leave the user with these scripts in their project:

- `01_create_foundation.py` — creates the Pnnn/Qnnn foundation, writes property-map.yaml + item-map.yaml
- `02_bulk_create_entities.py` — partitioned, idempotent worker (entity-ID-keyed shard files)
- `make_index_page.py` — generates a wikitext index page that lists all entities of a class
- `lib_wbi.py` — shared helpers (login, references, session refresh)

A reference implementation lives at: see the project that contributed this skill (kept private; the patterns are documented in `wikibase-migration-patterns.md`).

## Step 8: Update Project Memory

Add to `.claude/memory/MEMORY.md`:
- Wikibase URL + SPARQL endpoint
- Location of `property-map.yaml` and `item-map.yaml`
- The `make_index_page.py` invocation to refresh the index after data changes

---

## When NOT to Use Wikibase

- Project just needs semantic search over markdown → **use cognee** (`setup-cognee`)
- Project's data fits in a relational schema with foreign keys → **use Postgres + a thin app layer**
- Data has no claims-of-fact (e.g. pure code) → wiki is the wrong shape

If the user describes a project that doesn't fit the Wikibase niche, suggest the alternative and stop.

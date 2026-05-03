# Wikibase Migration Patterns

Generalized lessons from migrating a structured-domain dataset (~12K entities, ~14K relations, ~1K secondary claims) from a custom claim-store into a self-hosted Wikibase instance. Read alongside `setup-wikibase` skill.

## The migration roadmap

For a dataset of N structured entities + M relations, the phases are:

1. **Spike (1 day)** — stand up Wikibase, define the minimum schema (10-20 properties, 5-10 base items), write 5 test entities by hand, verify SPARQL works. **Decision gate**: if anything blocks, stop or pivot to hosted (wikibase.cloud).
2. **Schema design (1-2 days)** — full property catalog + item taxonomy. Output: `property-map.yaml`, `item-map.yaml`, written `data-model.md`.
3. **Foundation creation** — run `01_create_foundation.py`. Creates the Pnnn / Qnnn entries that all subsequent scripts reference by key, never by ID.
4. **Bulk entity creation** — partitioned, parallel workers. ~100-1000 entities/min depending on stack.
5. **Relation linking** — partitioned BY ENTITY (not by relation index — see below). Adds statements to existing entities.
6. **Secondary-claim extraction** — Haiku-driven, reference-attached. Optional but high-value for qualitative facts.
7. **Index pages** — wikitext content pages that aggregate items via SPARQL or hand-curation.

## Schema design

### Property catalog — non-negotiables

Every Wikibase deployment needs these reference properties before any data:

| Key | Datatype | Purpose |
|---|---|---|
| `instance_of` | wikibase-item | classifies an item (mirrors Wikidata P31) |
| `stated_in` | wikibase-item | reference: source organization or work |
| `reference_url` | url | reference: web URL |
| `retrieved` | time | reference: when the source was accessed |
| `archive_url` | url | reference: web.archive.org snapshot |
| `archive_date` | time | reference: snapshot date |

Without these, statements cannot have provenance and the wiki is no better than a spreadsheet.

### Item taxonomy — minimum classes

| Class item | Used for |
|---|---|
| `human` (mirror Q5) | every person item gets `instance of: human` |
| `source_org` | publishers / databases / wiki orgs (one item per source: Wikipedia, your data registry, news outlets) |
| Per-domain class items | one item per entity type in the domain (e.g. `political party`, `legislative bill`, `election event`) |

### Property-map convention

Commit `property-map.yaml` and `item-map.yaml` to the repo. Every script reads them via key name:

```python
# DO:
P = load_property_map()
it.claims.add(ItemValue(value=Q["src_wikipedia"], prop_nr=P["stated_in"]))

# DON'T:
it.claims.add(ItemValue(value="Q42", prop_nr="P19"))
```

When the foundation is recreated (e.g. on a fresh machine) the IDs change. Key-name indirection makes scripts portable.

## Bulk-import patterns

### 1. Partition by entity, not by relation

**The bug**: launching N workers each handling a chunk of relations (e.g. candidacies 0-2000, 2000-4000, …). When two workers both process relations for the same entity, they each fetch the entity, modify it locally, and write — the second write **overwrites** the first. You'll lose ~50% of data with 6 parallel workers.

**The fix**: partition workers by **entity ID** (e.g. person_id 0-2000, 2000-4000, …). Each worker fetches each of its entities ONCE, accumulates all statements for that entity locally, writes ONCE.

```python
# Group relations by parent entity first
by_person = defaultdict(list)
for relation in relations:
    by_person[relation.person_id].append(relation)

# Now partition by person_id (not relation index)
my_persons = sorted(by_person.keys())[offset:offset+count]
for pid in my_persons:
    item = wbi.item.get(entity_id=person_qid_for(pid))
    for relation in by_person[pid]:
        item.claims.add(...)   # accumulate locally
    item.write()                # one write per person
```

### 2. Use FORCE_APPEND for multi-valued properties

`wikibaseintegrator`'s default for `claims.add()` is `ActionIfExists.APPEND_OR_REPLACE`. If the same property already exists with the same value, the new statement replaces the old. For multi-valued statements (one person ran in multiple elections, served in multiple roles), this silently dedupes:

```python
from wikibaseintegrator.wbi_enums import ActionIfExists

# WRONG: only the LAST candidacy survives
for c in person_candidacies:
    item.claims.add(ItemValue(value=election_qid_for(c), prop_nr=P["ran_in_election"]))

# RIGHT: all candidacies preserved; first call clears any old data, subsequent calls append
first = True
for c in person_candidacies:
    action = ActionIfExists.REPLACE_ALL if first else ActionIfExists.FORCE_APPEND
    item.claims.add(
        ItemValue(value=election_qid_for(c), prop_nr=P["ran_in_election"]),
        action_if_exists=action,
    )
    first = False
```

### 3. Wrap writes in session-refresh retry

MediaWiki sessions expire under long batch runs. The error looks like:

```
MWApiError: 'You are no longer logged in, so the action could not be completed.'
```

Wrap each write in a 3-attempt retry that re-logs in on session-expiry errors:

```python
class SessionRefresher:
    SESSION_ERR_FRAGMENTS = ("no longer logged in", "Login required",
                             "assertbotfailed", "session timeout")
    def __init__(self):
        self.wbi = get_wbi()
    def is_session_error(self, e):
        return any(f.lower() in str(e).lower() for f in self.SESSION_ERR_FRAGMENTS)
    def refresh(self):
        self.wbi = get_wbi()
        return self.wbi

# In the worker loop:
for attempt in range(3):
    try:
        item.write()
        break
    except Exception as e:
        if sr.is_session_error(e) and attempt < 2:
            wbi = sr.refresh()
            time.sleep(1)
            continue
        raise
```

### 4. Beware MediaWiki's login throttle

MediaWiki imposes a 5-minute lockout if a single user makes too many login attempts in a short window. With 6 parallel workers all hitting session expiry simultaneously, all 6 try to re-login at once, **one of them trips the throttle** and is locked out for 5 minutes.

Mitigations:
- Stagger worker start times by a few seconds
- After session-expiry detection, sleep a randomized delay (1-3 sec) before re-login attempt
- For very long-running migrations, use a Bot Password (separate `Special:BotPasswords` flow) which has higher rate limits

### 5. Per-worker shard files for idempotency

Each worker writes its progress to `shards/<phase>-<worker>.json`. On crash/restart, the worker resumes from where it left off. After all workers finish, merge shards into the master `id-map.json`.

```python
# Each worker:
shard_file = SHARDS_DIR / f"persons-{worker_id}.json"
shard = json.loads(shard_file.read_text()) if shard_file.exists() else {}

for entity in my_chunk:
    if entity.id in shard:        # already processed
        continue
    qid = create_in_wikibase(entity)
    shard[entity.id] = qid
    if (i + 1) % 25 == 0:
        shard_file.write_text(json.dumps(shard))   # persist every 25
```

## URL & datatype gotchas

### `file://` URLs are rejected

Wikibase rejects any reference URL not on http/https. Local-only files (your project's source markdown) cannot be referenced via `file://` — they fail with `An URL scheme "file" is not supported`.

Workaround: create a "source organization" item for the local registry, attach a string-typed property holding the file path, and reference the item (not a URL).

### Property datatypes are immutable

Once a property is created with datatype `string`, you cannot change it to `wikibase-item`. If you discover the wrong type later, you must:
1. Create a new property with the right type
2. Migrate all statements to the new property
3. Deprecate the old one (Wikibase has no delete-property API)

Check datatypes carefully when authoring `01_create_foundation.py`.

### Label uniqueness

Wikibase enforces uniqueness of (label + description + language). If two entities have the same name (e.g. two people called "John Smith") AND identical descriptions, the second create fails with:

```
Item Q123 already has label "John Smith" associated with language code en, using the same description text.
```

Mitigations:
- Make descriptions distinctive at create time (include date of birth, city, role, ID)
- For genuine duplicates, look up the existing Q-ID and add the slug as an alias instead of creating a new item

This will hit ~10-30% of any large person dataset depending on naming variance.

## LLM-assisted secondary claims

For qualitative claims (positions, education, career history) that don't fit the structured schema, a Haiku-then-Sonnet escalation works well:

1. **Haiku per profile** — read the source markdown + a `[Ref]→URL` map, emit structured statements with reference IDs. Haiku handles ~95% of profiles correctly when given a fixed allow-list of properties + a "skip if no fit" escape.
2. **Audit pass** — verify every emitted statement has a reference ID that exists in the URLs map; spot-check a random sample of source-excerpts against the original profile.
3. **Sonnet escalation** — for the small percentage Haiku gets wrong (typically 1-3 profiles out of 100), re-run with Sonnet. Common Haiku failure: hallucinated reference IDs when the profile uses a non-default ID format (numeric instead of alphanumeric).

Pattern for invoking via `claude -p`:

```bash
# Process one entity:
claude --model haiku --dangerously-skip-permissions --add-dir <project> -p "<prompt>"

# Fan out 8 in parallel:
cat slugs.txt | xargs -P 8 -I {} ./process_one.sh {}
```

`--bare` flag breaks keychain auth — don't use it.

## Index pages

After bulk import, build human-readable wikitext content pages that aggregate items. Two patterns:

### SPARQL-driven listings

Run a SPARQL query at build time, embed results as wikilinks:

```python
results = run_sparql("SELECT ?p ?label WHERE { ?p wdt:P-instance-of wd:Q-class ... }")
wikitext = "\n".join(f"* [[Item:{r['p']}|{r['label']}]]" for r in results)
edit_page("Index Of Class", wikitext)
```

### Per-entity-type pages

For "show me all members of party X", you can either:
- Write the SPARQL query directly into the wiki and link to the WDQS frontend with `?query=...`
- Build the listing offline and edit a static wikitext page (faster page-load, requires regeneration on data change)

## Lessons that surface late

Two patterns that don't show up until you're deep in:

### Smoke-test long enough to exercise runtime failure modes

A 5-record smoke test in 10 seconds proves writes work, but doesn't trip session expiry, login throttle, or rate limits. Before fanning out 6 parallel workers, run **one** worker for 5+ minutes. Many production failures only surface under realistic duration.

### Don't fabricate relationship terms

When the source data is loose ("X and Y are members of the same household"), don't promote that to a stronger label ("X is Y's spouse") in your structured statements. Mirror the source's wording, even if it's less specific. Use neutral terms (`partner`, `household-member`) when the source doesn't say more.

## See also

- `setup-wikibase` skill — installation walkthrough
- `memory-systems.md` — when Wikibase is/isn't the right choice
- `wikibaseintegrator` Python lib: https://github.com/LeMyst/WikibaseIntegrator

---
*Authored 2026-05. Patterns generalized from a real migration project; specific scripts kept private but the patterns reproduce on any structured-domain dataset.*

# Memory Systems for Claude Code Projects

When a project needs persistent knowledge that survives across sessions, you have several real options. This doc lays out the choice space and when each is right.

## Decision tree

```
Does the data carry CLAIMS that need primary-source provenance?
├─ NO  → use cognee (setup-cognee) for semantic search over markdown
│        OR plain markdown + grep if scope is small
│
└─ YES → does the data have STRUCTURED entities + relations?
         │
         ├─ NO  → use a claim-store pattern (atomic facts as files,
         │        with frontmatter for source/confidence). Best for
         │        "things I read or believe" — Zettelkasten-style.
         │
         └─ YES → use Wikibase (setup-wikibase) for a Wikidata-grade
                  knowledge graph with claim-level references.
                  Use Semantic MediaWiki only if you need rich
                  free-text wiki pages alongside the structured data.
```

## The four options compared

| | cognee | claim-store (custom) | Semantic MediaWiki | Wikibase |
|---|---|---|---|---|
| **Storage** | Postgres + vector DB | Markdown files w/ YAML frontmatter | MediaWiki + SMW extension | MediaWiki + Wikibase + Blazegraph |
| **Query** | Semantic search via embeddings | grep / file walk | SMW Special:Ask | SPARQL endpoint |
| **Entities** | Implicit (graph emerges from text) | Implicit (slug = entity) | Pages with semantic annotations | First-class items (Q-IDs) |
| **Relations** | Inferred (embeddings) | None native; inferred via text | Properties, queryable | Properties + qualifiers, queryable |
| **References** | Whatever the markdown says | Frontmatter `source_file` (free-form) | `<ref>` tags (footnote-style) | First-class: `stated-in`, `reference-URL`, `retrieved`, `archive-URL` |
| **Confidence model** | None | Custom (e.g. Subjective Logic) | None | Statement rank: preferred / normal / deprecated |
| **Visualization** | Custom UI required | None | Semantic Result Formats (D3, timelines) | Free: Reasonator, SQID, Wikidata Graph Builder |
| **Standard format** | No | No | Yes (MediaWiki) | Yes (RDF, federates with Wikidata) |
| **Setup effort** | Medium (Docker, Postgres) | Trivial (write files) | Medium (MediaWiki + extension) | High (multi-container Docker stack) |
| **Idle RAM** | ~500 MB | 0 | ~1 GB | ~2-4 GB |
| **Right for** | Semantic search over notes | Personal knowledge with provenance | Wiki PAGES with structured data | Knowledge GRAPH with structured statements |

## When you've picked wrong

These are the symptoms of mismatched abstractions, observed in practice:

### Custom claim-store, want a database
- "I have 12,000 entities and need to find all the ones with property X" → very slow with file-walk
- "Entity types and relations keep growing" → no schema enforcement, drift accelerates
- → migrate to Wikibase

### Wikibase, want a wiki
- "I want a page that aggregates everything about X with a narrative" → Wikibase items are statement-tables, not prose
- → either (a) author wikitext content pages alongside the items, or (b) pick Semantic MediaWiki instead

### cognee, want strict provenance
- "I need to know exactly which sentence in which article said this" → cognee gives you semantic similarity, not citation-grade traceability
- → use claim-store or Wikibase

### Custom claim-store, want standard tooling
- "I want to share this data with a collaborator" → no off-the-shelf viewer reads your custom format
- → migrate to Wikibase (RDF export, Reasonator, SPARQL all work)

## Compounding patterns

You can combine systems where they make sense:

- **cognee + Wikibase**: cognee for fuzzy "find me articles about X" queries, Wikibase for "give me the structured fact about X with citation"
- **Wikibase + content pages**: Wikibase for entities; MediaWiki content pages (live in the same instance) for hand-authored narratives that link back to items
- **Claim-store as staging → Wikibase as production**: capture raw observations as claim files, migrate the cleaned-up structured ones to Wikibase, keep the rest as archive

## Anti-patterns

- **Atomic claim files for relational data**: storing 11,000 person entities as 11,000 separate markdown files because "every fact is a claim" — the structure is in the data, use a database
- **Wikibase for plain documents**: storing a free-text essay as Wikibase statements — wrong shape, use a wiki page
- **Confidence scores on certain facts**: a person's date of birth from an official registry doesn't need a Subjective Logic belief score; it's a fact. Confidence belongs on contested claims (positions, controversies, hearsay).
- **References pointing to internal notes**: a claim that cites "my synthesized profile" is unsourced; the synthesis is your interpretation, not a primary source. Always trace refs to the original document/URL.

## See also

- `setup-cognee` skill — install + configure cognee for this project
- `setup-wikibase` skill — install + configure Wikibase for this project
- `wikibase-migration-patterns.md` — generalized patterns for bulk-importing into Wikibase

---
*Authored: 2026-05. Generalized from a real migration of a structured-domain dataset (≈12K entities, ≈14K relations) from a custom claim-store to Wikibase.*

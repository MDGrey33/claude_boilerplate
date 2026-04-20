# Skill → Model Tier Routing

## Pricing (per million tokens, 2026)

| Tier | Input | Output | Cache read |
|---|---|---|---|
| Haiku 4.5 | $1 | $5 | ~$0.10 |
| Sonnet 4.6 | $3 | $15 | ~$0.30 |
| Opus 4.7 | $5 | $25 | ~$0.50 |

Opus is **5× Haiku** and **1.67× Sonnet**. Cache hits cut reads by ~90%.

## Routing table by skill archetype

| Archetype | Default | Promote to Sonnet | Promote to Opus |
|---|---|---|---|
| **Scan / audit / health-check** | Haiku | Diagnosing non-obvious failure | Never |
| **Lookup / validator / formatter** | Haiku | Ambiguous input | Never |
| **Dedup / classification / extraction** | Haiku | Semantic equivalence needed | Never |
| **Research synthesis (3-10 sources)** | Sonnet | — | ≥ 15 sources with contradictions |
| **Code edit to a single file** | Sonnet | — | Architectural refactor |
| **Outreach / email / drafting** | Sonnet | — | C-suite, legal, or compliance copy |
| **Orchestration / planning** | Sonnet | — | Cross-skill, cross-system redesigns |
| **Fact-check (uncontested)** | Sonnet | — | Disputed / court-settled claims |
| **Holistic skill review** | Sonnet | — | ≥ 15 skills + cascading changes |
| **Architecture proposals** | Opus | — | (already top) |
| **Quality-gate / orchestrator / critic** | Opus | — | (already top) |
| **Security / credentials / compliance** | Opus | — | (already top) |

## Expected distribution

From research: ~20% Haiku / ~60% Sonnet / ~20% Opus. If finance-controller's audit shows skills declaring Opus > 25%, flag for review.

## How to apply

Every SKILL.md should either declare `Default model:` directly in its frontmatter or reference a shared policy file. Skills with no declaration are unobservable by cost-auditing tools and should be flagged by finance-controller as 🟠 Orange priority.

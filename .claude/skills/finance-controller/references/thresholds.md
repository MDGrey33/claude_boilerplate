# Finance Controller Thresholds

Loaded on demand. Each threshold has a source and rationale so downstream judgment calls aren't arbitrary.

## Global principle

Tokens are cheap individually, expensive at session scale. Anything in the always-loaded path (CLAUDE.md, skill descriptions, MCP manifests) pays its cost on **every** session start and **every** context compaction. Anything deferred (supporting files, scripts) pays only when used.

Optimize for cache-friendliness too: stable prefixes hit the 5-minute Anthropic cache and read at ~10% of list price.

## CLAUDE.md

| Severity | Tokens | Rationale |
|---|---|---|
| 🟢 Green | ≤ 3,000 | Anthropic cookbook target for system prompts |
| 🟡 Yellow | ≤ 5,000 | Still workable; audit on next cycle |
| 🟠 Orange | ≤ 8,000 | Modern models over-trigger with this much steering |
| 🔴 Red | > 8,000 | Degrades instruction adherence; move content to `.claude/memory/*.md` |

Tuning: recent Claude models are more proactive than older ones. Instructions that say "ALWAYS / CRITICAL / MUST" now cause over-triggering. Prefer "Use X when Y."

## SKILL.md (per skill)

| Severity | Tokens | Rationale |
|---|---|---|
| 🟢 Green | ≤ 400 | Anthropic cookbook pattern (frontmatter-only skills) |
| 🟡 Yellow | ≤ 1,500 | Acceptable for complex skills with inline decision tables |
| 🟠 Orange | ≤ 3,000 | Defer examples and procedures to `references/` or `scripts/` |
| 🔴 Red | > 3,000 | Split now — body content belongs in supporting files |

## Skill model-tier declaration

| Severity | Coverage | Rationale |
|---|---|---|
| 🟢 Green | 100% of skills declare `Default model:` | Full finops visibility |
| 🟡 Yellow | ≥ 95% | Close; finish the long tail |
| 🟠 Orange | ≥ 85% | Enough uncertainty that cost auditing is unreliable |
| 🔴 Red | < 85% | Fix this first — you cannot optimize what you don't measure |

## MCP servers (connected)

Based on the progressive disclosure research and community reports:

| Severity | Connected MCPs | Rationale |
|---|---|---|
| 🟢 Green | ≤ 5 | Light manifest, fast startup |
| 🟡 Yellow | 6 – 8 | Consider moving project-scoped MCPs to `.mcp.json` at the project root |
| 🟠 Orange | 9 – 12 | Audit and disable candidates |
| 🔴 Red | > 12 | Manifest bloat likely exceeds several thousand tokens per session |

**Tool-count overlay:** even at ≤ 5 servers, a single MCP with 50+ tools (e.g., Atlassian) can dominate context. See `mcp-hygiene.md` for per-server decisions.

## Cost ceilings (per session)

| Lever | Budget | Rationale |
|---|---|---|
| Opus spend per session | < $5 unless explicitly requested for quality | Budget discipline |
| Sonnet share of LLM calls | ≥ 60% | Default tier for reasoning |
| Haiku share of LLM calls | ≥ 20% | Shows you're downgrading when you can |

## What NOT to threshold

- Absolute session length (Claude auto-compacts; let it).
- Raw tool-call count (modern models are more proactive, which is a feature).
- Individual Bash command length.

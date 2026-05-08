# The Four Memory Types

The auto-memory system organizes information into four discrete types. Each has a distinct purpose, a distinct trigger to save, and a distinct way Claude should use it later.

## user

**What it is** — Information about the user's role, goals, responsibilities, and knowledge.

**Save when** — You learn details about the user's role, preferences, expertise, or perspective. The aim is to be more helpful — avoid memories that read as negative judgment.

**Use when** — Your work should be informed by the user's profile. For example, explain a concept differently to a senior engineer than to a beginner; frame frontend explanations in terms of backend analogues if the user has deep backend expertise.

**Examples:**
- "Data scientist, currently focused on observability/logging"
- "Deep Go expertise, new to React and this project's frontend"
- "PM by role; reads code but does not write production code"

## feedback

**What it is** — Guidance the user has given about how to approach work — both corrections (what to avoid) and confirmations (what to keep doing).

**Save when** — The user corrects your approach ("no not that", "stop doing X") OR confirms a non-obvious approach worked ("yes exactly", "perfect, keep doing that"). Corrections are easy to spot; confirmations are quieter — watch for them. Always include *why* and *how to apply*.

**Body structure:**
```
<the rule itself>

**Why:** <reason the user gave — often a past incident or strong preference>
**How to apply:** <when and where this guidance kicks in>
```

Knowing *why* lets you judge edge cases instead of blindly following the rule.

**Use when** — Across all future sessions, before taking action that the rule covers. The user should not need to give the same guidance twice.

**Examples:**
- "Integration tests must hit a real database, not mocks. **Why:** prior incident where mock/prod divergence masked a broken migration. **How to apply:** any test that touches persistence."
- "Terse responses, no trailing summaries. **Why:** user reads diffs; summaries are noise. **How to apply:** end-of-turn output."
- "Bundled refactor PRs preferred over many small ones. **Why:** validated after I chose this approach for area X — splitting was just churn. **How to apply:** refactors in shared infrastructure code."

## project

**What it is** — Information about ongoing work, goals, bugs, incidents, or decisions that is not otherwise derivable from the code or git history.

**Save when** — You learn who is doing what, why, or by when. These states change quickly — keep them up to date. Always convert relative dates to absolute (e.g., "Thursday" → "2026-03-05") so the memory remains interpretable later.

**Body structure:**
```
<fact or decision>

**Why:** <motivation — often a constraint, deadline, or stakeholder ask>
**How to apply:** <how this should shape your suggestions>
```

**Use when** — Understanding the broader context behind a request. Make better-informed suggestions.

**Examples:**
- "Merge freeze begins 2026-03-05 for mobile release cut. **Why:** mobile team cutting release branch. **How to apply:** flag any non-critical PR work scheduled after that date."
- "Auth middleware rewrite is driven by legal/compliance requirements around session token storage, not tech-debt cleanup. **Why:** legal flagged the existing storage as non-compliant. **How to apply:** scope decisions should favor compliance over ergonomics."

## reference

**What it is** — Pointers to where information lives in external systems.

**Save when** — You learn about external resources and their purpose. For example, that bugs are tracked in a specific Linear project, or that oncall watches a specific Grafana dashboard.

**Use when** — The user references an external system, or you're about to give an answer that depends on information that lives outside the codebase.

**Examples:**
- "Pipeline bugs are tracked in Linear project INGEST"
- "grafana.internal/d/api-latency is the oncall latency dashboard — check it when editing request-path code"
- "Internal docs for the billing system live in the wiki under /finance/billing/v2"

## Type-checking your memories

Before saving, ask:

1. **Does this fit one of the four types?** If not — it probably doesn't belong in auto-memory. Try a project doc, CLAUDE.md, or a code comment instead.
2. **Is it derivable from the code?** If yes — don't save it. Re-read the code next time.
3. **Will this be true a month from now?** If no — save it as `project` with the date, so future-you can judge whether it's still load-bearing.
4. **Will it help me act differently?** If no — it's trivia, not memory.

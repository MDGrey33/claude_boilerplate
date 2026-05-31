# Model Selection & Script-First Policy

**Applies to:** every skill. Read this before invoking subagents, LLM calls, or deciding whether to run a script.

This is the shared policy that each skill's `## Model Selection` section refers to. It lives at `.claude/skills/_shared/MODEL_SELECTION.md` and is deployed to your workspace alongside the skills.

---

## The Core Rule

**Match the model (and the mechanism) to the job.** Using the largest model for everything wastes money and time; using the smallest for everything loses quality. Using an LLM for something a 10-line script can do deterministically is the worst of both worlds.

Decision order:

1. **Can a deterministic script do this?** → use a script. No LLM at all.
2. **Can the small/fast tier do this reliably?** → use it. Cheap and fast for bounded, structured tasks.
3. **Does this need judgment, synthesis, or nuance?** → use the balanced default tier (most reasoning work).
4. **Is this high-stakes, architectural, or contradictory?** → use the premium tier. Sparingly.

Model IDs change over time — see the [models overview](https://docs.claude.com/en/docs/about-claude/models/overview) for current Haiku / Sonnet / Opus tiers and pick the current member of each tier.

---

## Model Tiers

### Small / fast tier (Haiku-class) — cheap, fast, narrow

Use for:
- Structured extraction (regex-heavy parsing, JSON reshaping, CSV cleanup)
- Classification with a finite label set (sentiment, topic tags, yes/no questions)
- Dedup & fuzzy matching against known sets
- Short summaries of a single document
- Simple assertions ("does this selector exist?")
- Catalog lookups, dictionary-style QA
- Routing decisions ("which skill handles this?")
- Basic validation (schema check, format check)

Avoid for:
- Anything requiring multi-step reasoning
- Anything where a wrong answer cascades
- Anything that touches code other people will read

### Balanced tier (Sonnet-class) — default for reasoning work

Use for:
- Research synthesis (combining several sources into a finding)
- Profile / summary writing
- Code edits to skills, templates, configs
- Reasoning about failures and root causes
- Drafting outreach, emails, summaries
- Most day-to-day orchestration
- Writing tests for code

**This is the default.** Promote to the premium tier only when the task clearly needs it.

### Premium tier (Opus-class) — premium reasoning, sparingly

Use for:
- Architectural proposals (new skill design, schema migrations, system redesigns)
- Resolving contradictions between multiple trusted sources
- Holistic skill-system review when considering a major change
- Synthesis across many (15+) research reports
- Security / privacy / credentials reasoning
- Legal and compliance drafting
- When the user explicitly asks for "the highest quality possible"

**Budget check:** before invoking the premium tier, ask — could the balanced tier do this 90% as well for a fraction of the cost? If yes, use the balanced tier.

---

## The Script-First Rule

**Before invoking ANY LLM, ask: can a script do this?**

A script is the right answer when:
- The task is deterministic (same input → same output every time)
- The rules can be written down exhaustively
- The data shape is known and stable
- The work can be verified by assertions, not human review

Examples where scripts beat LLM calls:

| Task | Script | LLM? |
|------|--------|------|
| Moving files to canonical locations | `mv` + ledger append | No |
| Computing file checksums | `sha256sum` | No |
| Counting/grouping records by a field | `jq` / `collections.Counter` | No |
| Validating JSON against a schema | `jsonschema` lib | No |
| Deduping by ID | Python `dict` / `set` | No |
| Rotating old files into archive | `pathlib.rename` | No |
| Building a dropdown from categories | `set` + sort | No |

Examples where an LLM earns its cost:

| Task | Why LLM |
|------|---------|
| Extracting structured facts from free-form prose | Needs NLU |
| Deciding if two differently-worded statements are equivalent | Semantic comparison |
| Rating source credibility when context matters | Judgment |
| Writing a profile from several raw research files | Synthesis + style |
| Deciding whether a new skill proposal duplicates existing ones | Holistic reasoning |

**If a task has a deterministic core and an LLM-flavored wrapper, split it:** script for the core, LLM only for the wrapper. Don't feed 10,000 records through an LLM to add slugs when `re.sub` does it in milliseconds.

**Rule of thumb:** the first time you handle a shape of input, use the LLM to figure out how. The second time, write the script. The third time, the script should already exist.

---

## How a Skill Declares Its Model Preference

Every skill's `SKILL.md` should have a `## Model Selection` section near the top:

```markdown
## Model Selection

- **Default model:** {small | balanced | premium tier}
- **Deterministic parts:** {list — these run as scripts, not LLM calls}
- **Promote to premium when:** {list of triggers}
- **Demote to small when:** {list of triggers}
```

The default model handles a typical invocation. Promotions and demotions are runtime decisions based on the specific input.

---

## Guardrails

- **Never default to the premium tier.** If a skill's default is premium, it needs explicit justification.
- **Never route a deterministic task to any LLM.** Run the script.
- **Never use the small tier for something that fails silently.** Reserve it for tasks where output can be verified with an assertion.
- **Always log which model was used** when a skill invokes an LLM subagent.
- **Always measure.** If a task runs often, track its time, cost, and quality, and promote or demote based on evidence.

---

## Changing This Policy

This file is the single source of truth for model selection. Route changes through `/skills-manager`.

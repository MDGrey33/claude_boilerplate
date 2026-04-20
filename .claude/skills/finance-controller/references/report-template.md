# Finance Controller Report Template

The audit run produces a report in this shape. Keep it scannable — the user should see the headline in 5 seconds.

## Template

```markdown
# Finance Controller Audit — {{date}}

## Headline
{{ one sentence: overall state, biggest lever }}

## Surface snapshot
| Surface | State | Current | Target |
|---|---|---|---|
| CLAUDE.md | 🟢/🟡/🟠/🔴 | {{tokens}} tok | ≤ 3k tok |
| Skills (total) | — | {{n}} | — |
| Skills with tier declared | 🟢/🟡/🟠/🔴 | {{pct}}% | 100% |
| Bloated skills (>1.5k tok) | 🟢/🟡/🟠/🔴 | {{n}} | 0 |
| MCPs connected | 🟢/🟡/🟠/🔴 | {{n}} | ≤ 5 |

## Recommendations (prioritized by impact/risk)

### 🔴 R-XYZ-1 — {{title}}
- **Target:** {{file or server}}
- **Impact:** {{estimated tokens saved per session / estimated $ saved per month}}
- **Risk:** low / medium / high
- **Action:** {{exact diff or command}}
- **Route:** {{skills-manager UPDATE / direct Edit with approval / claude mcp remove}}

### 🟠 R-XYZ-2 — {{title}}
…

### 🟡 Deferred (next cycle)
- R-XYZ-3 — {{title}} — {{one-line}}

## Quality safeguards applied
- Did not recommend Opus downgrade for: {{list of quality-critical skills kept at Opus}}
- Did not touch CLAUDE.md content marked as load-bearing: {{list}}

## Next audit
{{scheduled date or trigger}}
```

## Recommendation ID format

- `R-CMD-n` — CLAUDE.md change
- `R-SKL-n` — skill file change
- `R-MCP-n` — MCP change
- `R-POL-n` — policy change

IDs persist in `.claude/memory/finance-controller-log.md` so future audits can reference prior decisions.

## Headline sentence patterns

- Good state: "Setup is within budget; {{lever}} is the only yellow flag."
- Moderate: "One orange flag on {{surface}}. Estimated {{impact}} saved per session if applied."
- Poor: "Three red flags. Biggest single lever: {{title}} — {{impact}}."

Never use generic "everything looks fine" when flags exist. Always name the next most useful move.

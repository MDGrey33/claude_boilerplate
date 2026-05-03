# Incident Lessons — Knowledge Graph Migration (2026-05)

Two cross-cutting lessons surfaced during a Wikibase migration. Generalized for the boilerplate's `lessons-learned.md`.

---

## Lesson: Smoke-test must exercise the failure mode you're guarding against

**Context**: After patching a script run by N parallel workers, the natural reflex is to immediately re-fan-out. A 5-item smoke test ("does it not crash?") proves correctness but is too short to trip session expiry, rate limits, login throttles, or memory growth.

**Failure mode observed**:
1. Patched a candidacy-import script with `SessionRefresher` to handle MediaWiki session expiry.
2. Smoke-tested 5 records (10 seconds runtime). 0 errors.
3. Fanned out to 6 parallel workers.
4. After ~3 minutes, a worker hit MediaWiki's 5-minute login-throttle when 6 workers all simultaneously tried to re-login at session expiry.
5. Smoke test never had a chance to exercise the failure I'd just patched.

**Rule**: After ANY edit to a script that has multiple parallel invocations queued, run a 1-worker smoke test that is **long enough to exercise the runtime failure mode being guarded against**, not just write-correctness. For data-migration scripts with auth: include at least one expected session-expiry interval (~10 min on MediaWiki) in the smoke test before fan-out.

**Pattern**: patch → smoke test that exercises the actual concern (runtime, scale, race) → verify → fan out. NEVER patch → fan out → wait.

---

## Lesson: Don't fabricate relationship terms (or any qualitative label)

**Context**: When ingesting personal-life data into a structured graph, the temptation is to promote vague source language ("household member", "lives with") to a more specific structured label ("spouse", "married") because Wikibase has a clean property for it.

**Failure mode observed**:
1. Source file listed two people as members of the same household.
2. I created a `spouse` property and linked them.
3. User flagged it: "partner not spouse, that you improvised and fabricated."
4. The source never said "spouse" or "married."

**Rule**: Use the **exact** word the source uses. If the source says "partner", create a `partner` property — not `spouse`. If the source says "lives with", don't promote to "co-resident". Same rule for occupation titles, education degrees, location specifics — mirror the source's wording, not a polished or more-specific version.

**Pattern**: When a structured property doesn't perfectly match the source's vagueness, **add a more general property** rather than forcing the data into a stronger label. When in doubt, ask the user before writing.

This applies far beyond family data — it's the same anti-pattern as a research summary calling someone a "co-founder" when the source said "early employee", or labeling a quote "endorsement" when the source said "comment". Quiet promotion of vague to specific is fabrication.

---

## When these lessons compound

Both surface during the **last mile** of a migration — when you're moving fast and the framework feels familiar. The first one is a velocity problem (skipping rigor on the smoke test); the second is a precision problem (auto-completing the source's wording in your head). Both are most likely to bite when:

- The user is watching and you feel pressure to produce visible progress
- The remaining work feels mechanical
- You've successfully done the same operation 10x before in this session

Counter-pressure: **slow down on the last mile**. The same care that got you to 95% complete is the care needed for the last 5%, and the cost of getting it wrong now is highest because you're closest to "done" in the user's mental model.

---
name: Auth middleware rewrite — driven by compliance
description: The auth middleware rewrite is a legal/compliance requirement, not a tech-debt cleanup
type: project
---

The auth middleware rewrite that started 2026-04-15 is being driven by legal/compliance requirements around session token storage, not by engineering tech-debt preferences. Target completion: 2026-06-30.

**Why:** Legal flagged the existing token storage as non-compliant with the new data-residency rules. The deadline is regulatory, not aspirational.

**How to apply:** When making scope decisions on this rewrite, favor compliance correctness over developer ergonomics or performance. Don't suggest "while we're in here, let's also refactor X" — extra scope risks the deadline. Defer ergonomics improvements to a follow-up issue.

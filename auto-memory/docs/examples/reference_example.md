---
name: Pipeline bug tracking
description: Where pipeline bugs are tracked and where the oncall latency dashboard lives
type: reference
---

- **Pipeline bugs** → Linear project `INGEST`. Search there before opening a new issue; the team triages weekly.
- **Oncall latency dashboard** → `grafana.internal/d/api-latency`. This is the dashboard oncall watches; if you're touching request-handling code, regressions here will page someone.
- **Internal billing docs** → wiki `/finance/billing/v2`.

**How to apply:** When the user references "INGEST", "the latency dashboard", or "the billing wiki" without giving a URL, point them at the resource above. When suggesting changes to request-path code, mention the latency dashboard as the verification surface.

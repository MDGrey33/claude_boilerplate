---
name: Integration tests must use a real database
description: Don't mock the DB in integration tests; run against a real instance to catch migration drift
type: feedback
---

Integration tests must hit a real database, not mocks.

**Why:** A prior incident — mocked tests passed locally but a production migration failed because the mock didn't model the real schema constraint. Mock/prod divergence masked the bug for a full release cycle.

**How to apply:** Any test that touches persistence (read or write). Unit tests of pure logic are fine to mock. If a test imports the ORM or hits a repository class, it's an integration test — wire it through Testcontainers or a local Postgres, never a mock.

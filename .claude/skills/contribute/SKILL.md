---
name: contribute
description: Generalize a lesson and stage it for boilerplate contribution
user_invocable: true
args: Optional description of the lesson or improvement to generalize
---

# Contribute — Generalize Lessons for Boilerplate

You are preparing a generalized contribution that can be pulled into the shared boilerplate repo. The contribution must be **project-agnostic** — no project names, file paths, domain terms, API keys, or internal details.

## Steps

1. **Gather input**: If a lesson or improvement was passed as argument, use it. Otherwise, read `.claude/memory/lessons-learned.md` and ask the user which lessons they'd like to contribute back.

2. **Classify the contribution** into one of these types:
   - `skill-update` — improvement to an existing skill's instructions
   - `new-skill` — a new skill that would benefit all projects
   - `convention` — a general coding or workflow convention
   - `memory-template` — improvement to memory file structure or initial content
   - `docs` — improvement to documentation in `.claude/docs/`
   - `config` — improvement to `.mcp.json`, `settings.json`, or `CLAUDE.md`

3. **Generalize**: Rewrite the lesson to remove all project-specific details:
   - Replace project names with `[project]` or generic terms
   - Replace specific file paths with generic patterns (e.g., `src/auth/login.ts` → "authentication modules")
   - Replace domain-specific terms with generic equivalents
   - Replace specific tool/framework names only if the lesson applies broadly; keep them if the lesson is framework-specific
   - Keep the actionable insight intact — the generalized version must be just as useful

4. **Write the contribution**: Create a new file in `.claude/contributions/` with this format:

   **Filename**: `YYYY-MM-DD-<short-slug>.md` (e.g., `2025-06-15-improve-hello-mcp-retry.md`)

   **Content**:
   ```markdown
   # Contribution: <title>

   **Type**: skill-update | new-skill | convention | memory-template | docs | config
   **Target**: <which file(s) in the boilerplate this would affect>
   **Date**: YYYY-MM-DD

   ## Problem

   <What problem or gap was discovered>

   ## Recommendation

   <The generalized improvement, with specific text/changes to apply>

   ## Rationale

   <Why this improves the boilerplate, based on real project experience>
   ```

5. **Review with user**: Show the contribution and ask:
   - "Does this look project-agnostic? Any details I should strip?"
   - "Ready to save, or want to adjust?"

6. **Save**: Write the file to `.claude/contributions/`.

7. **Report**:
   ```
   Contribution staged
   ===================
   File: .claude/contributions/<filename>.md
   Type: <type>
   Target: <target files>

   To integrate into boilerplate, run /pull-contributions from the boilerplate repo
   and point it at this project's .claude/contributions/ folder.
   ```

## Important Rules

- **Never include**: project names, internal URLs, API endpoints, team names, proprietary domain terms, specific file paths from the project
- **Always include**: the actionable recommendation, the category, which boilerplate files would change
- **Ask before saving**: Always show the user the generalized version before writing it

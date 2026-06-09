---
name: contribute
description: Generalize a lesson and stage it for Memnyx contribution. Delegates sanitization to `sanitizer` before staging.
user_invocable: true
args: Optional description of the lesson or improvement to generalize
---

## Model Selection

See `.claude/skills/_shared/MODEL_SELECTION.md` (in your workspace) for full policy.

- **Default model:** Sonnet 4.6 — generalizing a project-specific fix into a reusable pattern needs judgment about what's portable
- **Promote to Sonnet when:** never — generalization is the core task
- **Promote to Opus when:** never

# Contribute — Generalize Lessons for Memnyx

You are preparing a generalized contribution that can be pulled into Memnyx. The contribution must be **project-agnostic** — no project names, file paths, domain terms, API keys, or internal details.

**Setup — Resolve `<workspace>` and scope**: The skill's base directory is `<workspace>/.claude/skills/contribute/`; walk up three directory levels and validate that `<workspace>/.claude/.workspace` exists. Abort with a setup-broken error if validation fails. Then read the active session marker from `<workspace>/sessions/active/*.md` and `<workspace>/projects/*/sessions/active/*.md` to determine scope: if `project_slug` is `workspace`, scope is `<workspace>`; otherwise scope is `<workspace>/projects/<project_slug>`. If no marker exists, ask the user whether to read from workspace or a specific project before proceeding.

## Steps

1. **Gather input**: If a lesson or improvement was passed as argument, use it. Otherwise, read `<scope>/.claude/memory/lessons-learned.md` and ask the user which lessons they'd like to contribute back.

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

4. **Sanitize (MANDATORY)**: Write the draft to a temp path and invoke `sanitizer` on it:
   ```
   /sanitizer <temp-draft-path> --mode=boilerplate
   ```
   If sanitizer returns any findings (SECRET, PII, PRIVATE_CONTEXT, or TONE), **do not proceed**. Surface the full report to the user and apply recommended fixes before continuing. The sanitizer is the dedicated scrubber — do not duplicate its logic here.

5. **Write the contribution**: Create a new file in `<workspace>/contributions/` with this format:

   **Filename**: `YYYY-MM-DD-<short-slug>.md` (e.g., `2025-06-15-improve-hello-mcp-retry.md`)

   **Content**:
   ```markdown
   # Contribution: <title>

   **Type**: skill-update | new-skill | convention | memory-template | docs | config
   **Target**: <which file(s) in Memnyx this would affect>
   **Date**: YYYY-MM-DD

   ## Problem

   <What problem or gap was discovered>

   ## Recommendation

   <The generalized improvement, with specific text/changes to apply>

   ## Rationale

   <Why this improves Memnyx, based on real project experience>
   ```

6. **Review with user**: Show the contribution along with the sanitizer report and ask:
   - "Sanitizer pass — findings above. Any other adjustments needed?"
   - "Ready to save, or want to adjust?"

7. **Save**: Write the file to `<workspace>/contributions/`.

8. **Report**:
   ```
   Contribution staged
   ===================
   File: <workspace>/contributions/<filename>.md
   Type: <type>
   Target: <target files>

   To integrate into Memnyx, run /pull-contributions from the Memnyx repo
   and point it at <workspace>/contributions/.
   ```

## Important Rules

- **Never include**: project names, internal URLs, API endpoints, team names, proprietary domain terms, specific file paths from the project
- **Always include**: the actionable recommendation, the category, which Memnyx files would change
- **Ask before saving**: Always show the user the generalized version before writing it

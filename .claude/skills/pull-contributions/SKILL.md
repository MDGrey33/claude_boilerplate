---
name: pull-contributions
description: Pull generalized contributions from a project into the boilerplate. Runs `sanitizer --check` as a mandatory gate before integration.
user_invocable: true
args: Path to a project's .claude/contributions/ folder
---

## Model Selection

See `~/.claude/skills/_shared/MODEL_SELECTION.md` for full policy.

- **Default model:** Haiku 4.5 — mechanical file copy + path rewrite from project to boilerplate
- **Promote to Sonnet when:** a contribution needs de-identification or rewording before merging
- **Promote to Opus when:** never

# Pull Contributions — Integrate Project Learnings into Boilerplate

You are integrating generalized contributions from a project into this boilerplate repo. This skill is meant to be run **from the boilerplate repo**, not from a project.

## Steps

1. **Locate contributions**: The user provides a path to a project's `.claude/contributions/` folder (e.g., `~/code/my-project/.claude/contributions/`). Read all `.md` files in that folder.

   If no path is provided, ask the user for it.

2. **Sanitize gate (MANDATORY)**: Run `sanitizer` in check mode on the contributions folder:
   ```
   /sanitizer <contributions-folder-path> --check --mode=boilerplate
   ```
   - Exit code `0` → proceed.
   - Exit code `1` → **halt**. Surface the sanitizer report. Do NOT pull any contribution with findings. Ask the user to run `/sanitizer <path> --apply` in the source project to fix, then re-run this skill.
   - Do not duplicate sanitization logic here — the sanitizer is the single source of truth for what leaks.

3. **Review each contribution** (content check only, not PII/secret — that's sanitizer's job):
   - **Actionable**: The recommendation is concrete enough to apply.
   - **Categorized correctly**: The type and target file make sense.

3. **Present a summary** of all contributions found:

   ```
   Contributions found: [count]
   ─────────────────────────────
   1. [title] (type: skill-update, target: .claude/skills/hello/SKILL.md)
   2. [title] (type: convention, target: CLAUDE.md)
   ...
   ```

   Ask: "Which contributions should I integrate? (all / specific numbers / none)"

4. **For each approved contribution**, apply the changes:

   - **skill-update**: Read the target skill file, apply the recommended changes, show the diff to the user for approval before writing.
   - **new-skill**: Create the new skill directory and SKILL.md. Show the content for approval.
   - **convention**: Add to the relevant section of CLAUDE.md or `.claude/docs/conventions.md`.
   - **memory-template**: Update the memory file templates (MEMORY.md, lessons-learned.md, etc.).
   - **docs**: Update the target doc file.
   - **config**: Update the target config file. Be extra careful with `.mcp.json` and `settings.json`.

5. **Always ask for approval** before writing any changes. Show exact diffs or new content.

6. **After integration**, ask: "Should I mark the processed contributions as integrated?"
   - If yes, rename the contribution files to add an `integrated-` prefix (e.g., `integrated-2025-06-15-improve-hello-mcp-retry.md`). This prevents re-processing.

7. **Update CLAUDE.md** if new skills were added (add to the skills table).

8. **Report**:

   ```
   Pull Complete
   =============
   Reviewed: [count] contributions
   Integrated: [count]
   Skipped: [count] (with reasons)
   Files modified: [list]

   Remember to commit the changes to the boilerplate repo.
   ```

## Important Rules

- **Never auto-apply**: Always show changes and get user approval before modifying any file
- **Flag leaks**: If a contribution contains project-specific details, flag it and suggest how to generalize
- **Preserve structure**: When editing existing files, maintain their format and style
- **One at a time**: Apply contributions individually so the user can approve/reject each one

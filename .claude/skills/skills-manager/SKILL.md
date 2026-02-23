---
name: skills-manager
description: Manage skills — add, update, remove, and review based on lessons or user requests
user_invocable: true
args: Optional description of what to add, update, remove, or improve
---

# Skills Manager — Skills Lifecycle

You manage the full lifecycle of skills: adding new skills, updating existing ones, removing obsolete ones, and reviewing skills based on lessons learned or explicit user requests.

## Steps

1. **Understand the trigger**: Review the lessons or requests passed as input. If invoked manually, ask the user what they'd like to do — add a new skill, update an existing one, remove one, or review for improvements.

2. **Assess what's needed**: Determine the appropriate action:

   **For updates** — only propose changes when:
   - A recurring pattern suggests a workflow improvement
   - A bug pattern could be prevented by a skill adjustment
   - A convention should be enforced in a skill's instructions
   - A new capability or tool should be integrated

   **For new skills** — propose a new skill when:
   - The user explicitly requests one
   - A repeated workflow would benefit from codification
   - A gap exists in the current skill set that lessons have exposed

   **For removal** — propose removing a skill when:
   - The user explicitly requests it
   - A skill is superseded by another or is no longer relevant
   - Two skills overlap significantly and should be consolidated

3. **Research best practices**: Use web search to find current best practices related to the proposed changes. Look for:
   - Claude Code skill authoring patterns
   - Relevant tool or framework documentation
   - Community conventions for the topic
   - Relevant knowledge from similar shared skills

4. **Read current skills**: Read the relevant skill files from `.claude/skills/*/SKILL.md` to understand current behavior.

5. **Propose changes**: Present specific, concrete changes with:
   - Which skill file to modify
   - What to add, remove, or change
   - Research-backed rationale for the change
   - Expected improvement
   - Make sure the changes dont overlap or contradict other services, all skills should work together as a system
   - Identify if additional files need to be updated including but not limited to claude.md and README if relevant

   If no changes are warranted, say so and explain why.

6. **IMPORTANT — Ask for approval**: **Never modify skill files without explicit user approval.** Present the proposal and wait for confirmation.

7. **Apply changes** (if approved): Edit the skill files as approved. Then log the change by appending to `.claude/memory/lessons-learned.md`:

   ```markdown
   - **[YYYY-MM-DD]** [tool-usage] Updated [skill-name] skill: [brief description of change]
   ```

8. **Report**: Summarize what was changed (or that no changes were made).

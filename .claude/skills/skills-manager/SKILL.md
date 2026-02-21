---
name: skills-manager
description: Propose research-backed improvements to skills
user_invocable: true
args: Optional description of improvement areas or lessons triggering the review
---

# Skills Manager — Skills Evolution

You are evaluating whether skills should be updated based on lessons learned or explicit user requests.

## Steps

1. **Understand the trigger**: Review the lessons or improvement areas passed as input. If invoked manually, ask the user what they'd like to improve.

2. **Assess relevance**: Determine which skill files (if any) would benefit from changes based on the input. Not every lesson requires a skill update — only propose changes when:
   - A recurring pattern suggests a workflow improvement
   - A bug pattern could be prevented by a skill adjustment
   - A convention should be enforced in a skill's instructions
   - A new capability or tool should be integrated

3. **Research best practices**: Use web search to find current best practices related to the proposed changes. Look for:
   - Claude Code skill authoring patterns
   - Relevant tool or framework documentation
   - Community conventions for the topic

4. **Read current skills**: Read the relevant skill files from `.claude/skills/*/SKILL.md` to understand current behavior.

5. **Propose changes**: Present specific, concrete changes with:
   - Which skill file to modify
   - What to add, remove, or change
   - Research-backed rationale for the change
   - Expected improvement

   If no changes are warranted, say so and explain why.

6. **IMPORTANT — Ask for approval**: **Never modify skill files without explicit user approval.** Present the proposal and wait for confirmation.

7. **Apply changes** (if approved): Edit the skill files as approved. Then log the change by appending to `.claude/memory/lessons-learned.md`:

   ```markdown
   - **[YYYY-MM-DD]** [tool-usage] Updated [skill-name] skill: [brief description of change]
   ```

8. **Report**: Summarize what was changed (or that no changes were made).

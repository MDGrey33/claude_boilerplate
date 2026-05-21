"""Shared starter-file mappings for setup-workspace scripts.

Single source of truth for which files under `templates/starters/{workspace,project}/`
get deployed where. Imported by init.py, add_project.py, and sync.py — keeping all
three scripts aligned so a new starter only needs to be added in one place.

Each entry is (source_filename_under_starters_dir, destination_relpath_from_root).
- WORKSPACE_STARTERS: copied at `init` time, rooted at the workspace.
- PROJECT_STARTERS: copied at `add-project` time, rooted at the project dir.
"""

WORKSPACE_STARTERS = [
    ("MEMORY.md", ".claude/memory/MEMORY.md"),
    ("lessons-learned.md", ".claude/memory/lessons-learned.md"),
    ("project-context.md", ".claude/memory/project-context.md"),
    ("feedback_doc_maintenance_discipline.md", ".claude/memory/feedback_doc_maintenance_discipline.md"),
    ("identity.md", "me/identity.md"),
    ("brag-log.md", "me/brag-log.md"),
    ("growth.md", "me/growth.md"),
    ("team.md", "me/team.md"),
    ("gitignore", ".gitignore"),
]

PROJECT_STARTERS = [
    ("MEMORY.md", ".claude/memory/MEMORY.md"),
    ("lessons-learned.md", ".claude/memory/lessons-learned.md"),
    ("project-context.md", ".claude/memory/project-context.md"),
    ("settings.json", ".claude/settings.json"),
    ("architecture.md", ".claude/docs/architecture.md"),
    ("conventions.md", ".claude/docs/conventions.md"),
]

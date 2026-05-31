#!/usr/bin/env python3
"""Skill-table parity check.

Guards against the drift that the post-merge adversarial review caught: the
on-disk skill set and the skill tables in the user-facing docs getting out of
sync (a dead row pointing at a deleted skill, or a real skill missing from a
table). Three doc surfaces must list EXACTLY the skills that exist on disk:

  - README.md                                              (Skills Reference table)
  - CLAUDE.md                                              (Available Skills table)
  - .claude/skills/setup-workspace/templates/
        workspace-CLAUDE.md.tmpl                           (generated-workspace table)

The third is the one the original reconciliation missed — init.py emits it
verbatim as every fresh workspace's CLAUDE.md, so a stale table there ships
straight to users.

Run: python3 scripts/check_skill_tables.py
Exit 0 if all three tables match the on-disk skill set; exit 1 (with a diff)
otherwise. Wired into CI via .github/workflows/skill-table-parity.yml.

Convention: directories under .claude/skills/ whose name starts with "_"
(e.g. _shared/) are shared assets, not skills, and are excluded.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / ".claude" / "skills"

# Doc surfaces that must each carry a skill table matching the on-disk set.
DOC_SURFACES = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "CLAUDE.md",
    SKILLS_DIR / "setup-workspace" / "templates" / "workspace-CLAUDE.md.tmpl",
]

# Matches a markdown table row whose first cell is a slash command, e.g.
#   | `/setup-voice` | Manual | ... |
TABLE_ROW = re.compile(r"^\|\s*`/([a-z0-9][a-z0-9-]*)`\s*\|")


def disk_skills() -> set[str]:
    return {
        p.name
        for p in SKILLS_DIR.iterdir()
        if p.is_dir() and not p.name.startswith("_") and (p / "SKILL.md").is_file()
    }


def table_slugs(doc: Path) -> set[str]:
    if not doc.is_file():
        return set()
    return {
        m.group(1)
        for line in doc.read_text().splitlines()
        if (m := TABLE_ROW.match(line))
    }


def main() -> int:
    disk = disk_skills()
    if not disk:
        print(f"error: no skills found under {SKILLS_DIR}", file=sys.stderr)
        return 1

    ok = True
    print(f"On-disk skills ({len(disk)}): {', '.join(sorted(disk))}\n")
    for doc in DOC_SURFACES:
        rel = doc.relative_to(REPO_ROOT)
        listed = table_slugs(doc)
        missing = disk - listed          # on disk but not documented
        extra = listed - disk            # documented but not on disk (dead rows)
        if missing or extra:
            ok = False
            print(f"✗ {rel}")
            if missing:
                print(f"    MISSING from table : {', '.join(sorted(missing))}")
            if extra:
                print(f"    DEAD rows (no skill): {', '.join(sorted(extra))}")
        else:
            print(f"✓ {rel} ({len(listed)} skills, matches disk)")

    if not ok:
        print("\nSkill tables are out of sync with the on-disk skill set.", file=sys.stderr)
        return 1
    print("\nAll skill tables match the on-disk skill set.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

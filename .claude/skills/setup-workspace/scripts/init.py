#!/usr/bin/env python3
"""Initialise a workspace from a v2 boilerplate source.

Usage:
    init.py [--workspace <path>] [--source <path>] [--dry-run]

Auto-detects workspace and source from cwd:
- If cwd is a v2 boilerplate at `<workspace>/source/<repo>/`, infers
  workspace = cwd's grandparent, source = cwd.
- If cwd has `source/<v2-boilerplate>/` underneath, infers workspace = cwd
  and source = the v2 boilerplate found there.
- Otherwise refuses; user passes --workspace and/or --source explicitly.

A v2 boilerplate is identified by the marker file:
  .claude/skills/setup-workspace/templates/workspace-CLAUDE.md.tmpl

Idempotent. Skills/agents/agent-guardrails.md are overwritten on re-run; user
content (CLAUDE.md, memory files, identity, gitignore, settings.json, doc
templates) is preserved if already present.

Use --dry-run to preview without writing anything.
"""

import argparse
import shutil
import sys
from pathlib import Path

WORKSPACE_TEMPLATE_REL = ".claude/skills/setup-workspace/templates/workspace-CLAUDE.md.tmpl"

# Dirs to create at workspace root
ROOT_DIRS = ["workstreams", "sessions/active", "artifacts", "me"]
# Dirs to create under .claude/
CLAUDE_DIRS = ["memory", "skills", "agents", "docs"]

# Starter file content (only written if missing)
MEMORY_STARTER = "# MEMORY\n\nDistilled patterns and decisions for this workspace.\n"
LESSONS_STARTER = "# Lessons Learned\n\nRaw lessons inbox. Promoted to MEMORY.md once stable; pruned when promoted.\n"
BRAG_STARTER = "# Brag Log\n\nAccomplishments worth remembering, append-only.\n"
GROWTH_STARTER = "# Growth\n\nFocus areas, self-assessment notes, deliberate-practice goals.\n"
IDENTITY_STARTER = """# Identity

## Profile

<!-- Fill in your profile. Skills auto-populate fields when MCPs are connected. -->

- **Name**:
- **Title**:
- **Company**:
- **Timezone**:
- **GitHub username**:
- **Atlassian email**:
- **Slack user ID**:

## Preferences

<!-- How you want Claude to work with you -->

## Writing Style

<!-- Voice, tone, conventions you want preserved in drafts -->
"""
GITIGNORE_STARTER = """# Per-engineer working state — never commit
projects/
workstreams/
sessions/
collected/
artifacts/
contributions/

# Macos
.DS_Store
"""

# Module-level state set by main()
_WORKSPACE: Path | None = None
_DRY_RUN: bool = False


def workspace() -> Path:
    if _WORKSPACE is None:
        raise RuntimeError("workspace not initialised; call main() first")
    return _WORKSPACE


def is_dry_run() -> bool:
    return _DRY_RUN


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def is_v2_boilerplate(p: Path) -> bool:
    return (p / WORKSPACE_TEMPLATE_REL).is_file()


def find_workspace(workspace_arg: str | None) -> Path:
    if workspace_arg:
        p = Path(workspace_arg).expanduser().resolve()
        if not p.exists():
            die(f"workspace path does not exist: {p}")
        if not p.is_dir():
            die(f"workspace path is not a directory: {p}")
        return p

    cwd = Path.cwd()

    # Case 1 (preferred): cwd is a workspace — has source/<v2-boilerplate>/ underneath.
    # Check this BEFORE Case 2 because after init the workspace also has the v2
    # marker (via the deployed setup-workspace/templates), which would make Case 2
    # spuriously match.
    src_root = cwd / "source"
    if src_root.is_dir() and any(c.is_dir() and is_v2_boilerplate(c) for c in src_root.iterdir()):
        return cwd

    # Case 2: cwd is a v2 boilerplate clone at <workspace>/source/<repo>/
    if is_v2_boilerplate(cwd):
        if cwd.parent.name == "source":
            return cwd.parent.parent
        die(
            f"cwd ({cwd}) is a v2 boilerplate but not at the expected path "
            f"<workspace>/source/<repo>/.\n"
            f"hint: pass --workspace explicitly, e.g.:\n"
            f"  /setup-workspace init --workspace ~/my-space"
        )

    die(
        f"can't determine workspace from cwd ({cwd}).\n"
        f"hint: either run from inside the boilerplate clone (e.g., <workspace>/source/claude_boilerplate/),\n"
        f"or run from the workspace root (with source/<boilerplate>/ underneath),\n"
        f"or pass --workspace <path> explicitly."
    )


def find_source(source_arg: str | None) -> Path:
    if source_arg:
        p = Path(source_arg).expanduser().resolve()
        if not p.is_dir():
            die(f"source path is not a directory: {p}")
        if not is_v2_boilerplate(p):
            die(f"source at {p} is not a v2 boilerplate (missing {WORKSPACE_TEMPLATE_REL})")
        return p

    # Case 1 (preferred): look in <workspace>/source/. Always preferred over "cwd
    # is the boilerplate" because after init the workspace itself looks like a
    # v2 boilerplate (deployed setup-workspace/templates).
    src_root = workspace() / "source"
    if src_root.is_dir():
        candidates = [c for c in src_root.iterdir() if c.is_dir() and is_v2_boilerplate(c)]
        if len(candidates) == 1:
            return candidates[0]
        if len(candidates) > 1:
            names = ", ".join(c.name for c in candidates)
            die(
                f"multiple v2 boilerplates found under {src_root}: {names}\n"
                f"hint: pass --source explicitly, e.g.:\n"
                f"  /setup-workspace init --source {src_root}/{candidates[0].name}"
            )

    # Case 2: cwd is itself a v2 boilerplate (off-convention setup, no source/ dir).
    cwd = Path.cwd()
    if is_v2_boilerplate(cwd):
        return cwd

    # Neither.
    die(
        f"<workspace>/source/ does not exist or has no v2 boilerplate at {src_root}.\n"
        f"hint: clone one, e.g.:\n"
        f"  git clone https://github.com/MDGrey33/claude_boilerplate.git {src_root}/claude_boilerplate"
    )


def create_dirs(created: list, skipped: list) -> None:
    ws = workspace()
    for d in ROOT_DIRS:
        path = ws / d
        if path.exists():
            skipped.append(f"dir {d}/ (exists)")
        else:
            if not is_dry_run():
                path.mkdir(parents=True, exist_ok=True)
            created.append(f"dir {d}/")
    for d in CLAUDE_DIRS:
        path = ws / ".claude" / d
        if path.exists():
            skipped.append(f"dir .claude/{d}/ (exists)")
        else:
            if not is_dry_run():
                path.mkdir(parents=True, exist_ok=True)
            created.append(f"dir .claude/{d}/")


def deploy_dir(src: Path, dst: Path, overwrite: bool, created: list, skipped: list, label: str) -> None:
    """Copy contents of src into dst. If overwrite, dst entries are replaced."""
    if not src.is_dir():
        skipped.append(f"{label} (source missing)")
        return
    if not is_dry_run():
        dst.mkdir(parents=True, exist_ok=True)
    for entry in src.iterdir():
        target = dst / entry.name
        if target.exists() and not overwrite:
            skipped.append(f"{label}/{entry.name} (exists)")
            continue
        if not is_dry_run():
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            if entry.is_dir():
                shutil.copytree(entry, target)
            else:
                shutil.copy2(entry, target)
        created.append(f"{label}/{entry.name}")


def deploy_agent_guardrails(source: Path, created: list, skipped: list) -> None:
    src = source / ".claude/docs/agent-guardrails.md"
    dst = workspace() / ".claude/docs/agent-guardrails.md"
    if not src.is_file():
        skipped.append("docs/agent-guardrails.md (source missing)")
        return
    if not is_dry_run():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    created.append("docs/agent-guardrails.md (overwritten)")


def deploy_other_docs(source: Path, created: list, skipped: list) -> None:
    src_docs = source / ".claude/docs"
    dst_docs = workspace() / ".claude/docs"
    if not src_docs.is_dir():
        skipped.append("docs/ (source missing)")
        return
    if not is_dry_run():
        dst_docs.mkdir(parents=True, exist_ok=True)
    for entry in src_docs.iterdir():
        if entry.name == "agent-guardrails.md":
            continue
        target = dst_docs / entry.name
        if target.exists():
            skipped.append(f"docs/{entry.name} (exists; user-owned template)")
            continue
        if not is_dry_run():
            if entry.is_dir():
                shutil.copytree(entry, target)
            else:
                shutil.copy2(entry, target)
        created.append(f"docs/{entry.name}")


def deploy_settings(source: Path, created: list, skipped: list) -> None:
    src = source / ".claude/settings.json"
    dst = workspace() / ".claude/settings.json"
    if not src.is_file():
        skipped.append(".claude/settings.json (source missing)")
        return
    if dst.exists():
        skipped.append(".claude/settings.json (exists; run /setup-workspace sync to update later)")
        return
    if not is_dry_run():
        shutil.copy2(src, dst)
    created.append(".claude/settings.json")


def generate_claude_md(source: Path, created: list, skipped: list) -> None:
    template = source / WORKSPACE_TEMPLATE_REL
    dst = workspace() / "CLAUDE.md"
    if dst.exists():
        skipped.append("CLAUDE.md (exists)")
        return
    if not template.is_file():
        die(f"template missing at {template}")
    if not is_dry_run():
        content = template.read_text()
        content = content.replace("{{workspace_name}}", workspace().name)
        content = content.replace("{{workspace_path}}", str(workspace()))
        dst.write_text(content)
    created.append("CLAUDE.md")


def write_starter(path: Path, content: str, label: str, created: list, skipped: list) -> None:
    if path.exists():
        skipped.append(f"{label} (exists)")
        return
    if not is_dry_run():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    created.append(label)


def deploy_starters(created: list, skipped: list) -> None:
    ws = workspace()
    write_starter(ws / ".claude/memory/MEMORY.md", MEMORY_STARTER, ".claude/memory/MEMORY.md", created, skipped)
    write_starter(ws / ".claude/memory/lessons-learned.md", LESSONS_STARTER, ".claude/memory/lessons-learned.md", created, skipped)
    write_starter(ws / "me/identity.md", IDENTITY_STARTER, "me/identity.md", created, skipped)
    write_starter(ws / "me/brag-log.md", BRAG_STARTER, "me/brag-log.md", created, skipped)
    write_starter(ws / "me/growth.md", GROWTH_STARTER, "me/growth.md", created, skipped)
    write_starter(ws / ".gitignore", GITIGNORE_STARTER, ".gitignore", created, skipped)


def print_summary(source: Path, created: list, skipped: list) -> None:
    print()
    if is_dry_run():
        print("=== /setup-workspace init [DRY RUN] ===")
        print("(no files written; this is a preview)")
    else:
        print("=== /setup-workspace init complete ===")
    print(f"Workspace: {workspace()}")
    print(f"Source:    {source}")
    print()
    if created:
        verb = "Would create" if is_dry_run() else "Created"
        print(f"{verb} ({len(created)}):")
        for item in created:
            print(f"  + {item}")
    if skipped:
        verb = "Would skip" if is_dry_run() else "Skipped"
        print(f"\n{verb} ({len(skipped)}):")
        for item in skipped:
            print(f"  · {item}")
    print()
    if is_dry_run():
        print("Re-run without --dry-run to apply.")
    else:
        print("Next steps:")
        print(f"  - cd {workspace()} and start a new Claude session.")
        print("  - Customise CLAUDE.md and me/identity.md (placeholder values).")
        print("  - Register projects: /setup-workspace add-project <slug>")
        print("  - Optional: /setup-cognee for semantic search across memory.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Initialise a workspace from a v2 boilerplate source.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--workspace", help="Workspace path (auto-detected if omitted).")
    parser.add_argument("--source", help="Boilerplate source path (auto-detected if omitted).")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing anything.")
    return parser.parse_args()


def main() -> None:
    global _WORKSPACE, _DRY_RUN
    args = parse_args()
    _DRY_RUN = args.dry_run
    _WORKSPACE = find_workspace(args.workspace)
    source = find_source(args.source)

    if _DRY_RUN:
        print("=== DRY RUN — nothing will be written ===\n")
    print(f"Workspace: {_WORKSPACE}")
    print(f"Source:    {source}")
    print()

    created: list = []
    skipped: list = []

    create_dirs(created, skipped)
    deploy_dir(source / ".claude/skills", _WORKSPACE / ".claude/skills", overwrite=True, created=created, skipped=skipped, label="skills")
    deploy_dir(source / ".claude/agents", _WORKSPACE / ".claude/agents", overwrite=True, created=created, skipped=skipped, label="agents")
    deploy_agent_guardrails(source, created, skipped)
    deploy_other_docs(source, created, skipped)
    deploy_settings(source, created, skipped)
    generate_claude_md(source, created, skipped)
    deploy_starters(created, skipped)
    print_summary(source, created, skipped)


if __name__ == "__main__":
    main()

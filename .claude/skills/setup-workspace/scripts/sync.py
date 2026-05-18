#!/usr/bin/env python3
"""Sync upstream-owned content from a v2 boilerplate source to a workspace.

Usage:
    sync.py --workspace <path> [--source <path>]                  # report only
    sync.py --workspace <path> [--source <path>] --apply-all      # apply every update + new file
    sync.py --workspace <path> [--source <path>] --apply <relpath>...   # apply specific files

Compares the workspace's upstream-owned content against the source clone:
    - .claude/skills/**
    - .claude/agents/**
    - .claude/docs/agent-guardrails.md

Categorises each file as:
    unchanged    workspace matches source
    update       workspace differs from source (locally edited or upstream changed)
    new          source has the file, workspace doesn't
    local-only   workspace has the file, source doesn't (likely user-added)

Default mode prints the plan and exits. Apply modes write source-version files
to the workspace for the named (or all) update/new paths. local-only files are
never touched — sync doesn't remove user-added content.

Source path defaults to the absolute path stored in `<workspace>/.claude/.source`
(written by `init.py`). Pass `--source` explicitly to override.

Does NOT touch user-evolved content: CLAUDE.md, MEMORY.md, lessons-learned.md,
identity, workstreams, sessions, settings.json, project-context.md, or other
.claude/docs/* templates.
"""

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

WORKSPACE_MARKER_REL = ".claude/.workspace"
SOURCE_REF_REL = ".claude/.source"
SOURCE_BOILERPLATE_MARKER_REL = ".claude/skills/setup-workspace/templates/workspace-CLAUDE.md.tmpl"

SYNCED_DIRS = [".claude/skills", ".claude/agents"]
SYNCED_FILES = [".claude/docs/agent-guardrails.md"]

# Skipped during comparison (runtime artifacts, OS metadata).
SKIP_DIR_NAMES = {"__pycache__"}
SKIP_FILE_NAMES = {".DS_Store"}


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def is_v2_workspace(p: Path) -> bool:
    return (p / WORKSPACE_MARKER_REL).is_file()


def is_v2_boilerplate(p: Path) -> bool:
    return (p / SOURCE_BOILERPLATE_MARKER_REL).is_file()


def resolve_workspace(workspace_arg: str) -> Path:
    p = Path(workspace_arg).expanduser().resolve()
    if not p.is_dir():
        die(f"workspace path is not a directory: {p}")
    if not is_v2_workspace(p):
        die(f"{p} is not a v2 workspace (missing {WORKSPACE_MARKER_REL}). Run /setup-workspace init first.")
    return p


def resolve_source(source_arg: str | None, workspace: Path) -> Path:
    if source_arg:
        p = Path(source_arg).expanduser().resolve()
    else:
        ref = workspace / SOURCE_REF_REL
        if not ref.is_file():
            die(
                f"no source path provided and {SOURCE_REF_REL} not found in workspace.\n"
                f"hint: pass --source <path>, or re-run init to record the source."
            )
        recorded = ref.read_text().strip()
        if not recorded:
            die(f"{ref} is empty. Pass --source <path> explicitly.")
        p = Path(recorded).expanduser().resolve()

    if not p.is_dir():
        die(f"source path is not a directory: {p}")
    if not is_v2_boilerplate(p):
        die(f"source at {p} is not a v2 boilerplate (missing {SOURCE_BOILERPLATE_MARKER_REL})")
    return p


def walk_synced(root: Path, rel_root: str) -> list[str]:
    """Walk root/rel_root, return sorted list of relative paths (from root). Skips runtime artifacts."""
    base = root / rel_root
    if not base.is_dir():
        return []
    result = []
    for p in base.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in p.relative_to(root).parts):
            continue
        if p.name in SKIP_FILE_NAMES:
            continue
        result.append(str(p.relative_to(root)))
    return sorted(result)


def build_plan(workspace: Path, source: Path) -> dict:
    """Return {update, new, local_only, unchanged} lists of relative paths."""
    source_paths: set[str] = set()
    workspace_paths: set[str] = set()

    for d in SYNCED_DIRS:
        source_paths.update(walk_synced(source, d))
        workspace_paths.update(walk_synced(workspace, d))
    for f in SYNCED_FILES:
        if (source / f).is_file():
            source_paths.add(f)
        if (workspace / f).is_file():
            workspace_paths.add(f)

    update, new, local_only, unchanged = [], [], [], []

    for rel in sorted(source_paths | workspace_paths):
        src = source / rel
        dst = workspace / rel
        in_src = src.is_file()
        in_dst = dst.is_file()
        if in_src and not in_dst:
            new.append(rel)
        elif in_dst and not in_src:
            local_only.append(rel)
        elif in_src and in_dst:
            if filecmp.cmp(src, dst, shallow=False):
                unchanged.append(rel)
            else:
                update.append(rel)

    return {"update": update, "new": new, "local_only": local_only, "unchanged": unchanged}


def print_plan(workspace: Path, source: Path, plan: dict) -> None:
    print()
    print("=== sync plan ===")
    print(f"workspace: {workspace}")
    print(f"source:    {source}")
    print()
    print(f"== update ({len(plan['update'])}) ==")
    for rel in plan["update"]:
        print(f"M {rel}")
    print()
    print(f"== new ({len(plan['new'])}) ==")
    for rel in plan["new"]:
        print(f"+ {rel}")
    print()
    print(f"== local-only ({len(plan['local_only'])}) ==")
    for rel in plan["local_only"]:
        print(f"? {rel}")
    print()
    print(f"== unchanged ({len(plan['unchanged'])} files match source) ==")
    print()


def apply_paths(workspace: Path, source: Path, plan: dict, paths: list[str]) -> tuple[list[str], list[str]]:
    """Copy named paths from source to workspace. Returns (applied, skipped_with_reason)."""
    eligible = set(plan["update"]) | set(plan["new"])
    applied: list[str] = []
    skipped: list[str] = []

    for rel in paths:
        if rel not in eligible:
            skipped.append(f"{rel} (not in update/new plan)")
            continue
        src = source / rel
        dst = workspace / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        applied.append(rel)

    return applied, skipped


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Sync upstream-owned content from boilerplate source to workspace.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--workspace", required=True, help="Workspace path.")
    p.add_argument("--source", help="Boilerplate source path. Defaults to <workspace>/.claude/.source.")
    p.add_argument("--apply", nargs="+", metavar="RELPATH", help="Apply these update/new paths.")
    p.add_argument("--apply-all", action="store_true", help="Apply every update + new path.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.apply and args.apply_all:
        die("--apply and --apply-all are mutually exclusive.")

    workspace = resolve_workspace(args.workspace)
    source = resolve_source(args.source, workspace)
    plan = build_plan(workspace, source)

    if not args.apply and not args.apply_all:
        print_plan(workspace, source, plan)
        return

    targets = plan["update"] + plan["new"] if args.apply_all else args.apply
    applied, skipped = apply_paths(workspace, source, plan, targets)

    print()
    print("=== sync apply ===")
    print(f"workspace: {workspace}")
    print(f"source:    {source}")
    print()
    print(f"Applied ({len(applied)}):")
    for rel in applied:
        print(f"  + {rel}")
    if skipped:
        print()
        print(f"Skipped ({len(skipped)}):")
        for note in skipped:
            print(f"  · {note}")
    print()


if __name__ == "__main__":
    main()

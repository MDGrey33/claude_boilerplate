#!/usr/bin/env python3
"""Manage the workspace's project registry at <workspace>/.claude/projects-index.json.

Usage:
    registry.py add <slug> [<description>]
    registry.py remove <slug>
    registry.py update <slug> <field> <value>
    registry.py list

Workspace = cwd. Registry path = <cwd>/.claude/projects-index.json.
Project paths are convention-derived: <workspace>/projects/<slug>/ (must exist).
All writes are atomic (write to temp, replace).
"""

import json
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

SCHEMA_VERSION = "1.0"
ALLOWED_FIELDS = ("description",)
SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")


def workspace() -> Path:
    return Path.cwd()


def registry_path() -> Path:
    return workspace() / ".claude" / "projects-index.json"


def project_dir(slug: str) -> Path:
    return workspace() / "projects" / slug


def now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def load_registry() -> dict:
    p = registry_path()
    if not p.exists():
        return {"schemaVersion": SCHEMA_VERSION, "projects": {}}
    with p.open() as f:
        data = json.load(f)
    if data.get("schemaVersion") != SCHEMA_VERSION:
        die(f"schema version mismatch: expected {SCHEMA_VERSION}, found {data.get('schemaVersion')}")
    if "projects" not in data or not isinstance(data["projects"], dict):
        die(f"malformed registry at {p}: missing 'projects' map")
    return data


def save_registry(data: dict) -> None:
    p = registry_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=p.parent, delete=False) as tmp:
        json.dump(data, tmp, indent=2)
        tmp.write("\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(p)


def validate_slug(slug: str) -> None:
    if not SLUG_RE.match(slug):
        die(f"invalid slug '{slug}': lowercase + hyphens only, must start with a letter")


def validate_project_dir_exists(slug: str) -> None:
    pdir = project_dir(slug)
    if not pdir.exists():
        die(
            f"project directory does not exist: {pdir}\n"
            f"hint: run /setup-workspace add-project to scaffold it, "
            f"or `mkdir {pdir}` for a fresh project, "
            f"or `ln -s /path/to/real/repo {pdir}` to point at an existing one."
        )


def cmd_add(args: list) -> None:
    if len(args) < 1 or len(args) > 2:
        die("usage: add <slug> [description]")
    slug = args[0]
    desc = args[1] if len(args) == 2 else ""
    validate_slug(slug)
    validate_project_dir_exists(slug)
    data = load_registry()
    if slug in data["projects"]:
        die(f"slug '{slug}' already registered. use 'update' to modify or 'remove' first.")
    data["projects"][slug] = {
        "description": desc,
        "created": now_iso(),
    }
    save_registry(data)
    print(f"registered '{slug}' at {project_dir(slug)}")


def cmd_remove(args: list) -> None:
    if len(args) != 1:
        die("usage: remove <slug>")
    slug = args[0]
    data = load_registry()
    if slug not in data["projects"]:
        die(f"slug '{slug}' not registered.")
    print(f"removing '{slug}' at {project_dir(slug)}")
    del data["projects"][slug]
    save_registry(data)
    print(f"unregistered '{slug}'. files on disk are untouched.")


def cmd_update(args: list) -> None:
    if len(args) != 3:
        die("usage: update <slug> <field> <value>")
    slug, field, value = args
    if field not in ALLOWED_FIELDS:
        die(f"invalid field '{field}': must be one of {', '.join(ALLOWED_FIELDS)}")
    data = load_registry()
    if slug not in data["projects"]:
        die(f"slug '{slug}' not registered.")
    data["projects"][slug][field] = value
    save_registry(data)
    print(f"updated '{slug}': {field} -> {value}")


def cmd_list(_args: list) -> None:
    data = load_registry()
    projects = data["projects"]
    if not projects:
        print("no registered projects.")
        return
    rows = [
        (slug, str(project_dir(slug)), e.get("description", ""))
        for slug, e in sorted(projects.items())
    ]
    headers = ("slug", "path", "description")
    widths = [
        max(len(str(c)) for c in col) for col in zip(*([headers] + rows))
    ]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*("-" * w for w in widths)))
    for row in rows:
        print(fmt.format(*row))


COMMANDS = {
    "add": cmd_add,
    "remove": cmd_remove,
    "update": cmd_update,
    "list": cmd_list,
}


def main() -> None:
    if len(sys.argv) < 2:
        cmd_list([])
        return
    action = sys.argv[1]
    if action not in COMMANDS:
        die(f"unknown action '{action}'. use one of: {', '.join(COMMANDS)}")
    COMMANDS[action](sys.argv[2:])


if __name__ == "__main__":
    main()

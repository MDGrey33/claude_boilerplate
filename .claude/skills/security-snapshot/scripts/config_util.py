"""
Shared config + reports-dir helpers for the security-snapshot scripts.

config.json is the committed template (defaults + docs, no real values);
config.local.json (gitignored) overlays it with this deployment's real values,
local keys winning — so `/setup-workspace sync` can refresh config.json without
clobbering settings. All consumers (posture_snapshot / github_security_snapshot /
build_dashboard, plus run_analysis.sh's cfg_get) load config through here, so the
overlay, the empty/malformed-local handling, and value-stripping behave identically
everywhere instead of being reimplemented per script.
"""
import json
import os
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).parent


def load_config() -> dict:
    """
    config.json template overlaid by config.local.json (local keys win).

    Shallow merge (dict.update): a key in config.local.json replaces the template's
    value wholesale — correct for the flat keys here; no nested/deep merge intended.
    """
    template = _SCRIPT_DIR / "config.json"
    if not template.exists():
        sys.exit(f"error: {template} not found — see SKILL.md first-run configuration")
    cfg = json.loads(template.read_text())
    local = _SCRIPT_DIR / "config.local.json"
    if local.exists():
        text = local.read_text().strip()
        if text:  # an empty/whitespace local file just falls through to the template
            try:
                cfg.update(json.loads(text))
            except json.JSONDecodeError as e:
                sys.exit(f"error: {local} is not valid JSON ({e}) — fix it, "
                         "or delete it to fall back to the template")
    return cfg


def require(cfg: dict, key: str) -> str:
    val = (cfg.get(key) or "").strip()
    if not val:
        sys.exit(f"error: '{key}' is not set — run the skill's first-run setup (it prompts "
                 "for this and writes scripts/config.local.json), or edit config.local.json directly")
    return val


def resolve_reports_dir(args) -> Path:
    """Where to read/write snapshot artefacts. --reports-dir > $SECURITY_SNAPSHOT_REPORTS_DIR > error."""
    raw = args.reports_dir or os.environ.get("SECURITY_SNAPSHOT_REPORTS_DIR")
    if not raw:
        sys.exit("error: pass --reports-dir <path> or set SECURITY_SNAPSHOT_REPORTS_DIR")
    return Path(raw).expanduser().resolve()

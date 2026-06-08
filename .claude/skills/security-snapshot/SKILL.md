---
name: security-snapshot
description: Run the full security analysis pipeline — AWS Inspector V2 + GitHub security alerts → correlation → dashboard. Saves dated snapshots for trend tracking. Run monthly or on demand. Optional --deploy flag pushes the dashboard to Google Apps Script at the end.
user_invocable: true
args: |
  Optional flags:
  - --scope <name>  Where snapshots and dashboard land. Resolves to
                    <workspace>/projects/<name>/artifacts/security-snapshot/ for a project slug,
                    or <workspace>/artifacts/security-snapshot/ for "workspace".
                    Default is read from scripts/config.json (default_scope).
  - --deploy        After the pipeline completes, invoke /google-script-deploy to push the
                    dashboard to Apps Script. Without this flag the dashboard is saved
                    locally only (default). The dashboard is sensitive (account ID, repo
                    names, CVEs, secret-scanning counts) — deploy access MUST be DOMAIN or
                    stricter, never ANYONE_ANONYMOUS. See Step 8.
  If a step fails the skill stops and reports the failure — it does not continue with stale data.
---

# Security Snapshot

## Model Selection

See `.claude/skills/_shared/MODEL_SELECTION.md` (in your workspace) for full policy.

- **Default model:** Haiku — the pipeline is four scripts run in sequence with pass/fail gates; the scripts do the work
- **Promote to Sonnet when:** first-run configuration (prompting and validating org/profile/region), diagnosing a failed step, or interpreting an unusual delta
- **Promote to Opus when:** never

You are running the security analysis pipeline. This collects data from AWS Inspector V2
and GitHub, correlates findings, and regenerates the interactive dashboard.

Outputs land in per-date subfolders under `$REPORTS_DIR/<YYYYMMDD>/`. Running more than once on
the same day overwrites that folder's contents. Running on a new day creates a new dated folder
while preserving all previous ones. Always-current files (rendered dashboard, clasp deploy state)
sit at the top of `$REPORTS_DIR/`.

**Past dated folders are immutable history.** Correlation outputs co-locate with their inputs and
refuse to save when the latest inputs are from a previous day (run the collectors first — analysis
never refreshes a past folder, and never creates a dated folder with no collection behind it).
Rebuilding the dashboard against an older correlation reuses that day's existing snapshot untouched.

Do NOT run `build_dashboard.py` before the other three scripts complete — it depends on their output.

---

## Adapting this skill to a different workspace

All org-specific values live in `scripts/config.json`: `github_org`, `aws_profile`, `aws_region` (required — Step 0 prompts for them when missing), plus `owner_project` / `default_scope` (where snapshots and the dashboard land — point both at a project slug that exists in your workspace, check `ls projects/`; both normally hold the same value).

You'll know if a value is wrong on first run: every script errors with a clear message naming the missing or invalid setting. There is no silent misrouting — wrong values fail fast.

---

## Setup — resolve SCRIPT_DIR and REPORTS_DIR (do this first, reuse throughout)

The pipeline source lives in this skill folder; output goes under
`artifacts/security-snapshot/` in the scope resolved from `--scope` (default from `config.json`).
Resolve both once:

```bash
# Locate workspace from this skill's base directory (never from PWD — cwd
# drifts mid-session). Base dir is <workspace>/.claude/skills/security-snapshot/;
# the workspace is three levels up, validated by its marker file.
WS="$(cd "<skill-base-dir>/../../.." && pwd)"
[ ! -f "$WS/.claude/.workspace" ] && { echo "Workspace marker not found at $WS"; exit 1; }

SCRIPT_DIR="$WS/.claude/skills/security-snapshot/scripts"

# Resolve scope from config.json unless --scope was passed
SCOPE="$(python3 -c "import json; print(json.load(open('$SCRIPT_DIR/config.json'))['default_scope'])")"
# (apply user's --scope override here if invoked with one)

if [ "$SCOPE" = "workspace" ]; then
  REPORTS_DIR="$WS/artifacts/security-snapshot"
else
  REPORTS_DIR="$WS/projects/$SCOPE/artifacts/security-snapshot"
fi
mkdir -p "$REPORTS_DIR"
export SECURITY_SNAPSHOT_REPORTS_DIR="$REPORTS_DIR"
```

Use `"$SCRIPT_DIR"` for script invocations and `"$REPORTS_DIR"` for output paths (status
messages, the "Next step" line, the deploy invocation). Do NOT hardcode absolute paths.

Alternative for one-shot use: `bash "$SCRIPT_DIR/run_analysis.sh" [--scope <name>]` does
all of the above plus runs the pipeline end-to-end.

---

## Step 0 — First-run configuration

Read `$SCRIPT_DIR/config.json`. Three values are required: `github_org`, `aws_profile`,
`aws_region`. If any is empty or missing, this is a first run — prompt the user for them:

- **github_org** — the GitHub organization to scan (all repos are enumerated)
- **aws_profile** — an AWS profile with Inspector2 + STS read access (read-only recommended)
- **aws_region** — the region where Inspector V2 runs

Also offer the optional values while you're there: `dashboard_title` (defaults to
"Security Dashboard") and `annotations` (event markers on the Trend tab — fine to leave empty).

Validate before saving: `gh api orgs/<org> --jq .login` resolves, and
`aws sts get-caller-identity --profile <profile>` succeeds. Write the confirmed values back
to `config.json`. The Python scripts fail fast with a clear message if a required value is
missing, so a skipped Step 0 cannot silently misroute — but prompting here beats a mid-pipeline error.

If all three values are already set, skip silently.

---

## Step 1 — Prerequisite check

The skill installs what it can; only authentication is delegated to the user.

Read `aws_profile` from `$SCRIPT_DIR/config.json`, then run in parallel:

```bash
AWS_PROFILE="$(python3 -c "import json; print(json.load(open('$SCRIPT_DIR/config.json'))['aws_profile'])")"
python3 -c "import boto3; print('boto3 ok')"
gh auth status
aws sts get-caller-identity --profile "$AWS_PROFILE"
```

Evaluate results:
- **boto3 missing** → install it directly: `pip3 install boto3 --break-system-packages`. Re-check after install.
- **aws CLI missing** → install it directly (macOS: `brew install awscli`; Linux: the platform package manager). Re-check after install.
- **gh CLI missing** → install it directly (macOS: `brew install gh`). Re-check after install.
- **gh not authenticated or wrong account** → genuinely interactive. Tell the user to run
  `! gh auth login` (or `! gh auth switch --user <their-github-handle>` if they have multiple
  accounts) in the prompt, then re-check.
- **AWS profile fails** → credentials are the user's to fix: the profile may be missing from
  `~/.aws/config` or its credentials expired. Show the exact error and wait — do not create
  or modify AWS profiles yourself.

If any check still fails after these remedies, stop here. Do not proceed with stale or missing auth.

---

## Step 2 — Inspector V2 snapshot (~3 min)

```bash
python3 "$SCRIPT_DIR/posture_snapshot.py" --save --raw
```

Each python script reads `$SECURITY_SNAPSHOT_REPORTS_DIR` to know where to write. If the
env var isn't set in your shell, pass `--reports-dir "$REPORTS_DIR"` explicitly.

Watch for errors. If it exits non-zero, show the last 20 lines of output and stop.

---

## Step 3 — GitHub security snapshot (~2 min)

```bash
python3 "$SCRIPT_DIR/github_security_snapshot.py" --save --raw
```

Watch for errors. If it exits non-zero, show the last 20 lines of output and stop.

---

## Step 4 — Correlation analysis (~5 sec)

```bash
python3 "$SCRIPT_DIR/correlation.py" --save --raw
```

Reads the latest `raw-YYYYMMDD.json` and `github-raw-YYYYMMDD.json` from `$REPORTS_DIR`,
writes `correlation-YYYYMMDD.{md,json}` back to the same dir.

---

## Step 5 — Build dashboard (~1 sec)

```bash
python3 "$SCRIPT_DIR/build_dashboard.py"
```

Also writes `$REPORTS_DIR/<YYYYMMDD>/snapshot.json` — a slim per-day archive (~23KB) that
the dashboard embeds for its date picker, and that Step 6 reads to compute the delta vs the
previous run. The rendered `security-dashboard.html` always lands at the top of `$REPORTS_DIR/`.

---

## Step 6 — Delta comparison

Load the two most recent `<YYYYMMDD>/snapshot.json` files from `$REPORTS_DIR`
(globbing `$REPORTS_DIR/*/snapshot.json`, sorted by folder name descending).
Compare these metrics between previous and current:

| Metric | Direction | Meaning |
|---|---|---|
| `github.secrets_total` | ↓ good, ↑ bad | Open credential exposures |
| `github.vuln_critical` | ↓ good | Critical Dependabot alerts |
| `github.vuln_total` | ↓ good | Total Dependabot alerts |
| `github.code_total` | ↓ good | Code scanning errors |
| `inspector.critical` + `inspector.high` | ↓ good | Inspector C+H (fan-out inflated) |
| `correlation.zone_a_pkgs` | ↓ good | Packages confirmed in both sources |

If only one snapshot exists (first run): note "First run — no previous snapshot to compare."

Present as a compact delta table:

```text
Delta vs YYYY-MM-DD
───────────────────────────────
Secrets         148  →  148  (no change)
GH CRITICAL      191  →  185  ↓ 6
GH total       3,077  →  3,020  ↓ 57
Code scanning    470  →  470  (no change)
Inspector C+H  715K  →  715K  (no change)
Zone A pkgs      203  →  198  ↓ 5
```

---

## Step 7 — Report

Print a final summary using `"$REPORTS_DIR"` for any paths:

```text
Security Snapshot — YYYY-MM-DD
==============================
Scope:          <name>
Outputs at:     $REPORTS_DIR/YYYYMMDD/
Inspector V2:   ✓  posture.md + raw.json
GitHub:         ✓  github.md + github-raw.json
Correlation:    ✓  correlation.md + correlation.json
Dashboard:      ✓  security-dashboard.html  (N snapshots embedded, top-level)

[delta table]

Dashboard:  open $REPORTS_DIR/security-dashboard.html
Next step:  /google-script-deploy deploy "$REPORTS_DIR"
            (or pass --deploy to /security-snapshot next time to do it automatically)
```

Report the count of snapshots embedded in the dashboard (from build_dashboard.py output).
If any step was skipped due to an error, make that explicit in the summary. If the GitHub
step reported failed repo fetches (`vuln_fetch_failures` in github-raw.json) or a partial
scanning status (`rate_limited` / `auth_error`), list the affected repos and prompt the
user to rerun the snapshot later to refetch them.

---

## Step 8 — Optional: deploy to Apps Script (only if `--deploy` was passed)

> **⚠ The dashboard is sensitive — restrict the deployment.** The HTML embeds a full
> map of the org's security weaknesses: the AWS account ID + region, every repo name,
> open CVEs and vulnerable packages, and per-repo secret-scanning types and counts. The
> page renders a `CONFIDENTIAL — INTERNAL` badge on itself. When the deploy target is first
> set up, the access level **must be `DOMAIN`** (the org's Workspace domain only) or stricter
> — **never `ANYONE_ANONYMOUS`** (public, no sign-in). If a deployment already exists with a
> wider access level, stop and tell the user to restrict it before proceeding.

If the user invoked the skill with `--deploy`, invoke the deployment skill at the end:

```text
/google-script-deploy deploy "$REPORTS_DIR"
```

The deploy skill handles its own concerns (clasp checks, RAPT expiry, push, redeploy).
Access level is set when the GAS project is first created — for this dashboard it must be
`DOMAIN` or stricter, never `ANYONE_ANONYMOUS`.
The `clasp-projects.json` config travels with the snapshots under `$REPORTS_DIR`, so
the deploy skill picks up the right script ID + deployment ID automatically.

If deploy fails, security-snapshot's other outputs are already saved on disk — the user can
recover by re-running just `/google-script-deploy deploy "$REPORTS_DIR"` once the
underlying issue is fixed. Do not re-run the whole pipeline for a deployment failure.

Without `--deploy`, skip this step.

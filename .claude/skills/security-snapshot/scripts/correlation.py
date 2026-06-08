#!/usr/bin/env python3
"""
correlation.py — Cross-source vulnerability correlation

Joins AWS Inspector V2 (ECR/EC2) findings with GitHub Dependabot alerts
on (package_name, CVE_id) to identify three zones:

  Zone A — BOTH sources:   CVE confirmed in deployed image AND source code
  Zone B — Inspector only: In image, not in source lock file
  Zone C — GitHub only:    In source code, image may have been updated

Also surfaces: code scanning alerts by severity/repo, and secret scanning
summary (critical for triage separate from vulnerability correlation).

Usage:
    python3 correlation.py [--save] [--raw]
    python3 correlation.py --inspector raw-YYYYMMDD.json --github github-raw-YYYYMMDD.json

Auto-detects the most recent raw files if not specified.
Adds three analytical lenses beyond the CVE/package zone analysis:

  Lens 1 — Combined repo rankings:  Inspector + GitHub + code scanning + secrets
            per-repo score surfaces the true top offenders across all four signals.
  Lens 2 — Package quick-win table: impact/effort score for Zone A packages.
            (Inspector C+H + GitHub C+H) × repos_affected / effort.
  Lens 3 — Offender convergence:    repos that rank in the top tier across
            multiple categories simultaneously (the "fix this first" shortlist).
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def _resolve_reports_dir(args) -> Path:
    """Where to read/write snapshot artefacts. --reports-dir > $SECURITY_SNAPSHOT_REPORTS_DIR > error."""
    raw = args.reports_dir or os.environ.get("SECURITY_SNAPSHOT_REPORTS_DIR")
    if not raw:
        sys.exit("error: pass --reports-dir <path> or set SECURITY_SNAPSHOT_REPORTS_DIR")
    return Path(raw).expanduser().resolve()


# ── File discovery ────────────────────────────────────────────────────────────

def latest_file(filename: str, reports_dir: Path) -> Path | None:
    """Find the most recent dated-folder containing `filename` (e.g. 'raw.json').

    Layout: reports_dir/<YYYYMMDD>/<filename>. Returns the path whose parent
    folder name sorts highest (most recent date).
    """
    files = sorted(reports_dir.glob(f"*/{filename}"),
                   key=lambda p: p.parent.name, reverse=True)
    return files[0] if files else None


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


# ── CVE extraction helpers ────────────────────────────────────────────────────

CVE_RE = re.compile(r'CVE-\d{4}-\d+', re.IGNORECASE)
GHSA_RE = re.compile(r'GHSA-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}', re.IGNORECASE)


def cves_from_title(title: str) -> list[str]:
    return [m.upper() for m in CVE_RE.findall(title)]


def pkg_from_title(title: str) -> str:
    """Extract package name from 'CVE-XXXX - pkgname' or 'GHSA-... - pkgname'."""
    parts = title.split(" - ", 1)
    return parts[1].strip().lower() if len(parts) > 1 else title.lower()


# ── Build Inspector CVE index ─────────────────────────────────────────────────

def build_inspector_index(raw: dict) -> dict:
    """
    Returns {cve_id: {package, crit, high, med}} from title_stats.
    Also builds {package: {crit, high, med}} from package aggregation.
    """
    cve_index: dict[str, dict] = {}
    pkg_index: dict[str, dict] = {}

    # From title aggregation (top CVEs by severity)
    for t in raw.get("title_stats", {}).get("top_by_ch", []):
        title = t.get("title", "")
        pkg   = pkg_from_title(title)
        for cve in cves_from_title(title):
            if cve not in cve_index:
                cve_index[cve] = {
                    "package": pkg,
                    "crit": t.get("c", 0),
                    "high": t.get("h", 0),
                    "med":  t.get("m", 0),
                    "title": title,
                }

    # Package-level index (full set — 624 packages)
    for resp in raw.get("packages", []):
        p = resp.get("packageAggregation", {})
        name = p.get("packageName", "").lower()
        sc   = p.get("severityCounts", {})
        if name:
            pkg_index[name] = {
                "crit": sc.get("critical", 0),
                "high": sc.get("high", 0),
                "med":  sc.get("medium", 0),
            }

    return {"by_cve": cve_index, "by_pkg": pkg_index}


# ── Build GitHub CVE index ────────────────────────────────────────────────────

def build_github_index(raw: dict) -> dict:
    """
    Returns {cve_id: [{repo, package, severity, fix_available}]},
    {package: {repos, crit, high, mod, low, cves}}.
    """
    cve_index:  dict[str, list] = defaultdict(list)
    pkg_index:  dict[str, dict] = defaultdict(lambda: {
        "repos": set(), "crit": 0, "high": 0, "mod": 0, "low": 0, "cves": set()
    })

    for a in raw.get("vuln_alerts_detail", []):
        cve = (a.get("cve") or "").upper()
        pkg = (a.get("package") or "").lower()
        sev = (a.get("severity") or "").upper()

        if cve:
            cve_index[cve].append({
                "repo": a.get("repo"),
                "package": pkg,
                "severity": sev,
                "fix_available": a.get("fix_available", False),
                "patched": a.get("patched"),
            })

        if pkg:
            p = pkg_index[pkg]
            p["repos"].add(a.get("repo", ""))
            p["cves"].add(cve) if cve else None
            if sev == "CRITICAL": p["crit"] += 1
            elif sev == "HIGH":   p["high"] += 1
            elif sev in ("MODERATE", "MEDIUM"): p["mod"] += 1
            elif sev == "LOW":    p["low"] += 1

    # Serialise sets for JSON
    pkg_serialisable = {
        pkg: {
            "repos": len(v["repos"]),
            "crit": v["crit"], "high": v["high"], "mod": v["mod"], "low": v["low"],
            "cves": sorted(v["cves"]),
        }
        for pkg, v in pkg_index.items()
    }

    return {"by_cve": dict(cve_index), "by_pkg": pkg_serialisable}


# ── Three-zone correlation ────────────────────────────────────────────────────

def correlate(insp: dict, gh: dict) -> dict:
    """
    Produce three-zone analysis joining Inspector × GitHub on CVE or package.

    Zones join on bare CVE deliberately, not on (package, CVE): Inspector names
    OS/container packages (deb/apk) while Dependabot names manifest packages
    (npm/pip), so the same CVE rarely shares a package name across the two
    sources — a pair-wise join would collapse Zone A to near-empty and misreport
    genuine cross-source visibility of the same vulnerability. The package-level
    view is computed separately (zone_a_pkgs / pkg_overlap below).
    """

    insp_cves = set(insp["by_cve"].keys())
    gh_cves   = set(gh["by_cve"].keys())
    insp_pkgs = set(insp["by_pkg"].keys())
    gh_pkgs   = set(gh["by_pkg"].keys())

    # Zone A — CVE in both
    zone_a_cves = insp_cves & gh_cves
    zone_a = []
    for cve in sorted(zone_a_cves):
        i = insp["by_cve"][cve]
        g = gh["by_cve"][cve]
        gh_repos  = sorted(set(x["repo"] for x in g))
        gh_fixable = any(x["fix_available"] for x in g)
        zone_a.append({
            "cve":           cve,
            "package":       i["package"],
            "insp_crit":     i["crit"],
            "insp_high":     i["high"],
            "gh_alerts":     len(g),
            "gh_repos":      gh_repos,
            "gh_repos_count": len(gh_repos),
            "fix_available": gh_fixable,
            "priority_score": i["crit"] * 10 + i["high"] + len(g),
        })
    zone_a.sort(key=lambda x: (-x["priority_score"], x["cve"]))

    # Zone A — package overlap (Inspector pkgs that also appear in GitHub)
    zone_a_pkgs = insp_pkgs & gh_pkgs
    pkg_overlap = []
    for pkg in sorted(zone_a_pkgs):
        i = insp["by_pkg"][pkg]
        g = gh["by_pkg"][pkg]
        pkg_overlap.append({
            "package":    pkg,
            "insp_crit":  i["crit"],
            "insp_high":  i["high"],
            "gh_crit":    g["crit"],
            "gh_high":    g["high"],
            "gh_repos":   g["repos"],
            "combined_ch": i["crit"] + i["high"] + g["crit"] + g["high"],
        })
    pkg_overlap.sort(key=lambda x: (-x["combined_ch"], x["package"]))

    # Zone B — Inspector only (not in GitHub — transitive/build deps)
    zone_b_cves = insp_cves - gh_cves
    zone_b = [
        {"cve": c, **insp["by_cve"][c]}
        for c in zone_b_cves
    ]
    zone_b.sort(key=lambda x: (-(x["crit"] + x["high"]), x["cve"]))

    # Zone C — GitHub only (in source, not flagged by Inspector)
    zone_c_cves = gh_cves - insp_cves
    zone_c = []
    for cve in zone_c_cves:
        g = gh["by_cve"][cve]
        gh_repos = sorted(set(x["repo"] for x in g))
        zone_c.append({
            "cve":      cve,
            "package":  g[0]["package"] if g else "",
            "alerts":   len(g),
            "repos":    gh_repos,
            "severity": g[0]["severity"] if g else "",
        })
    zone_c.sort(key=lambda x: (-(x["alerts"]), x["cve"]))

    return {
        "zone_a_cve_overlap":     zone_a,
        "zone_a_pkg_overlap":     pkg_overlap,
        "zone_b_inspector_only":  zone_b[:30],
        "zone_c_github_only":     zone_c[:50],
        "summary": {
            "cves_in_both":          len(zone_a_cves),
            "cves_inspector_only":   len(zone_b_cves),
            "cves_github_only":      len(zone_c_cves),
            "pkgs_in_both":          len(zone_a_pkgs),
            "insp_cves_total":       len(insp_cves),
            "gh_cves_total":         len(gh_cves),
        },
    }


# ── Lens 1: Combined repo rankings ────────────────────────────────────────────

# Scoring weights — tunable
W_INSP_CRIT = 10   # Inspector CRITICAL (fan-out inflated but still a real CVE)
W_INSP_HIGH  = 3
W_GH_CRIT   = 50   # GitHub CRITICAL — no fan-out, confirmed in source, full weight
W_GH_HIGH   = 15
W_CODE_SCAN  = 5   # SAST error (code quality/logic issue)
W_SECRET     = 100 # Exposed credential — immediate risk regardless of volume


def norm_repo(name: str) -> str:
    """'<registry-namespace>/<repo>' → '<repo>'."""
    return name.split("/")[-1]


def build_repo_combined_ranking(insp_raw: dict, gh_raw: dict) -> list[dict]:
    """
    Join Inspector (images) + GitHub (source) + code scanning + secrets per repo.
    Returns list of repos sorted by combined risk score.
    """
    # Inspector repo names may carry a registry namespace prefix → normalise
    insp_repos: dict[str, dict] = {}
    for resp in insp_raw.get("repositories", []):
        a  = resp.get("repositoryAggregation", {})
        sc = a.get("severityCounts", {})
        name = norm_repo(a.get("repository", ""))
        if name:
            insp_repos[name] = {
                "crit":   sc.get("critical", 0),
                "high":   sc.get("high", 0),
                "med":    sc.get("medium", 0),
                "images": a.get("affectedImages", 0),
            }

    # GitHub vuln alerts per repo
    gh_vuln: dict[str, dict] = {}
    for r in gh_raw.get("vuln_agg", {}).get("top_repos", []):
        name = r.get("repo", "")
        gh_vuln[name] = {
            "crit": r.get("CRITICAL", 0),
            "high": r.get("HIGH", 0),
            "mod":  r.get("MODERATE", 0),
        }

    # Code scanning and secret scanning per repo
    cs_by_repo: dict[str, int] = defaultdict(int)
    for a in gh_raw.get("code_scanning", []):
        cs_by_repo[a.get("repo", "")] += 1

    ss_by_repo: dict[str, int] = defaultdict(int)
    for a in gh_raw.get("secret_scanning", []):
        ss_by_repo[a.get("repo", "")] += 1

    all_repos = (
        set(insp_repos) | set(gh_vuln) |
        set(cs_by_repo) | set(ss_by_repo)
    )

    result = []
    for repo in all_repos:
        i  = insp_repos.get(repo, {"crit": 0, "high": 0, "med": 0, "images": 0})
        g  = gh_vuln.get(repo,   {"crit": 0, "high": 0, "mod": 0})
        cs = cs_by_repo.get(repo, 0)
        ss = ss_by_repo.get(repo, 0)

        score = (
            i["crit"] * W_INSP_CRIT + i["high"] * W_INSP_HIGH +
            g["crit"] * W_GH_CRIT   + g["high"] * W_GH_HIGH   +
            cs * W_CODE_SCAN + ss * W_SECRET
        )

        # Flag repos appearing in 3+ categories (convergence)
        categories = sum([
            i["crit"] + i["high"] > 0,
            g["crit"] + g["high"] > 0,
            cs > 0,
            ss > 0,
        ])

        result.append({
            "repo":          repo,
            "insp_crit":     i["crit"],
            "insp_high":     i["high"],
            "insp_images":   i["images"],
            "gh_crit":       g["crit"],
            "gh_high":       g["high"],
            "code_scanning": cs,
            "secrets":       ss,
            "combined_score": round(score),
            "categories":    categories,   # how many of the 4 signals flagged this repo
        })

    return sorted(result, key=lambda x: (-x["combined_score"], x["repo"]))


# ── Lens 2: Package quick-win scoring ─────────────────────────────────────────

# Effort categories — mirrors Inspector's T/B/S/P.
# Tunable defaults: these are public npm packages with publicly documented
# no-fix/abandoned status. Extend per your stack as your scans surface more.
STRUCTURAL_PKGS = {"vm2"}            # abandoned — no fix ever; must migrate
NO_FIX_PKGS     = {"dicer", "xlsx", "lodash.set", "ip", "lodash.template",
                    "url-regex", "babel-traverse", "pdf-image", "hoek"}

# Repo-count threshold separating Trivial from Bounded.
# ≤ TRIVIAL_REPOS_MAX: one engineer can sweep all affected services in a day.
# > TRIVIAL_REPOS_MAX: coordinated work across multiple teams — a sprint item.
TRIVIAL_REPOS_MAX = 5

# Human-readable effort definitions — rendered verbatim in the report.
EFFORT_DEFINITIONS = [
    ("Trivial",    "1",
     f"Fix available. One version bump per service, no breaking change, no "
     f"coordination overhead. Affects ≤{TRIVIAL_REPOS_MAX} repos. One engineer, hours to a day."),
    ("Bounded",    "2",
     f"Fix available but used across many repos (>{TRIVIAL_REPOS_MAX}). Each fix is a version "
     "bump; the effort is coordinating the sweep across services. Days to one sprint."),
    ("Phantom",    "3",
     "No upstream patch exists. Suppress in Security Hub / GitHub with documented "
     "rationale and 90-day review date. Not a remediation item until a fix ships."),
    ("Structural", "4",
     "Package is abandoned or requires an architectural migration. A version bump "
     "cannot fix it. Engineering design required before execution. Sprint+."),
]


def build_package_quickwin(pkg_overlap: list[dict], gh_raw: dict) -> list[dict]:
    """
    Score Zone A packages by (combined_ch × repos_affected) / effort.

    Effort scale (see EFFORT_DEFINITIONS):
      1 = Trivial   — version bump, ≤5 repos
      2 = Bounded   — version bump, 6+ repos (multi-team sweep)
      3 = Phantom   — no fix available; suppress, don't remediate
      4 = Structural — abandoned package; migration required
    """
    # Build fix-available map from GitHub raw alerts
    fix_map: dict[str, dict] = {}
    for a in gh_raw.get("vuln_alerts_detail", []):
        pkg = (a.get("package") or "").lower()
        if pkg not in fix_map:
            fix_map[pkg] = {"fix": False, "patched": None}
        if a.get("fix_available"):
            fix_map[pkg]["fix"] = True
            if not fix_map[pkg]["patched"]:
                fix_map[pkg]["patched"] = a.get("patched")

    result = []
    for p in pkg_overlap:
        pkg         = p["package"]
        combined_ch = p["combined_ch"]
        gh_repos    = p["gh_repos"]
        fix_info    = fix_map.get(pkg, {"fix": False, "patched": None})

        if pkg in STRUCTURAL_PKGS:
            effort, effort_label = 4, "Structural"
        elif pkg in NO_FIX_PKGS or not fix_info["fix"]:
            effort, effort_label = 3, "Phantom"
        elif gh_repos > TRIVIAL_REPOS_MAX:
            effort, effort_label = 2, "Bounded"
        else:
            effort, effort_label = 1, "Trivial"

        # Quick-win score: (combined impact × repos it closes) / effort units
        qw_score = round((combined_ch * max(gh_repos, 1)) / effort)

        result.append({
            "package":        pkg,
            "insp_crit":      p["insp_crit"],
            "insp_high":      p["insp_high"],
            "gh_crit":        p["gh_crit"],
            "gh_high":        p["gh_high"],
            "gh_repos":       gh_repos,
            "combined_ch":    combined_ch,
            "fix_available":  fix_info["fix"],
            "patched":        fix_info["patched"],
            "effort":         effort,
            "effort_label":   effort_label,
            "quickwin_score": qw_score,
        })

    return sorted(result, key=lambda x: (-x["quickwin_score"], x["package"]))


# ── Lens 3: Offender convergence ──────────────────────────────────────────────

def build_offender_convergence(repo_ranking: list[dict], top_n: int = 15) -> list[dict]:
    """
    Repos that rank in the top tier across multiple signal categories.
    A repo scoring in top-15 on 3+ signals is the highest-priority fix target.
    """
    def top_set(score) -> set:
        # Only repos with a positive count in the signal qualify — slicing the
        # full ranking would pad small orgs' top lists with zero-count repos and
        # mint convergence badges no scanner actually issued.
        scored = [r for r in repo_ranking if score(r) > 0]
        return {r["repo"] for r in sorted(scored, key=lambda x: (-score(x), x["repo"]))[:top_n]}

    insp_top  = top_set(lambda x: x["insp_crit"] + x["insp_high"])
    gh_top    = top_set(lambda x: x["gh_crit"] + x["gh_high"])
    cs_top    = top_set(lambda x: x["code_scanning"])
    ss_top    = top_set(lambda x: x["secrets"])

    result = []
    for r in repo_ranking:
        repo   = r["repo"]
        badges = []
        if repo in insp_top: badges.append("Inspector")
        if repo in gh_top:   badges.append("Dependabot")
        if repo in cs_top:   badges.append("CodeScan")
        if repo in ss_top:   badges.append("Secrets")
        if len(badges) >= 2:
            result.append({**r, "signals": badges, "signal_count": len(badges)})

    return sorted(result, key=lambda x: (-x["signal_count"], -x["combined_score"], x["repo"]))


# ── Report ────────────────────────────────────────────────────────────────────

def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("|" + "|".join("---" for _ in headers) + "|")
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


def build_report(corr: dict, gh_raw: dict, ts: str) -> str:
    s           = corr["summary"]
    zone_a      = corr["zone_a_cve_overlap"]
    pkg_ov      = corr["zone_a_pkg_overlap"]
    zone_b      = corr["zone_b_inspector_only"]
    zone_c      = corr["zone_c_github_only"]
    repo_rank   = corr.get("repo_combined_ranking", [])
    pkg_qw      = corr.get("package_quickwin", [])
    convergence = corr.get("offender_convergence", [])

    cs_alerts = gh_raw.get("code_scanning", [])
    ss_count  = len(gh_raw.get("secret_scanning", []))

    lines = [
        "# Security Correlation Analysis",
        "",
        f"**Generated**: {ts}",
        "",
        "> Inspector V2 data covers deployed images (ECR) + EC2 instances.",
        "> GitHub data covers source code (Dependabot) + SAST (Code Scanning) + secrets.",
        "",
        "## Effort Categories",
        "",
        "Used throughout this document (Package Quick-Win table, remediation guidance).",
        "",
        md_table(
            ["Category", "Effort score", "Definition"],
            [(name, score, defn) for name, score, defn in EFFORT_DEFINITIONS]
        ),
        "",
        "> **Trivial/Bounded split**: the ≤5 / 6+ repo threshold is a coordination proxy, not a",
        "> severity distinction. A Bounded fix is the same operation repeated N times; the team",
        "> needs to plan a sweep sprint rather than one-off it.",
        "",
        "## Summary",
        "",
        md_table(
            ["Metric", "Value"],
            [
                ("Inspector CVEs (in title aggregation top-50)", str(s["insp_cves_total"])),
                ("GitHub CVEs (all Dependabot alerts)",           str(s["gh_cves_total"])),
                ("Zone A — CVE in BOTH sources",                  f"**{s['cves_in_both']}**"),
                ("Zone A — Package in BOTH sources",              f"**{s['pkgs_in_both']}**"),
                ("Zone B — Inspector only (build/transitive deps)", str(s["cves_inspector_only"])),
                ("Zone C — GitHub only (may be fixed in image)",  str(s["cves_github_only"])),
                ("Code scanning alerts",                          str(len(cs_alerts))),
                ("Secret scanning alerts (OPEN)",                 f"**{ss_count}** ← P0"),
            ],
        ),
        "",
        "> **Zone A = highest priority.** Same vulnerability confirmed in both the",
        "> deployed image AND the source code. Fix closes findings in both scanners.",
        "",
        "## Zone A — CVEs in Both Sources (top 25 by combined score)",
        "",
        "> Priority score = (Inspector CRITICAL × 10) + Inspector HIGH + GitHub alert count.",
        "",
    ]

    if zone_a:
        rows = [
            [
                a["cve"],
                a["package"][:30],
                a["insp_crit"],
                a["insp_high"],
                a["gh_alerts"],
                a["gh_repos_count"],
                "✓" if a["fix_available"] else "✗",
            ]
            for a in zone_a[:25]
        ]
        lines.append(md_table(
            ["CVE", "Package", "Insp CRIT", "Insp HIGH", "GH Alerts", "GH Repos", "Fix?"],
            rows,
        ))
    else:
        lines.append("> No CVE-level overlap found in top-50 Inspector CVEs.")

    lines += [
        "",
        "## Zone A — Package Overlap (top 30 by combined C+H)",
        "",
        "> Package name appears in both Inspector findings AND GitHub Dependabot.",
        "> Fix closes vulnerabilities in image AND source simultaneously.",
        "",
    ]
    if pkg_ov:
        rows = [
            [
                p["package"][:35],
                p["insp_crit"], p["insp_high"],
                p["gh_crit"],   p["gh_high"],
                p["gh_repos"],
                p["combined_ch"],
            ]
            for p in pkg_ov[:30]
        ]
        lines.append(md_table(
            ["Package", "Insp CRIT", "Insp HIGH", "GH CRIT", "GH HIGH", "GH Repos", "Combined C+H"],
            rows,
        ))

    # ── Lens 1: Combined repo rankings ───────────────────────────────────────
    if repo_rank:
        lines += [
            "",
            "## Combined Repo Rankings — All Four Signals",
            "",
            "> Score = Inspector(C×10 + H×3) + GitHub(C×50 + H×15) + CodeScan×5 + Secrets×100.",
            "> GitHub findings are weighted higher — no fan-out inflation; confirmed in source.",
            "> Secrets carry the heaviest weight: exposed credentials are P0 regardless of count.",
            "",
            md_table(
                ["Repository", "Insp C", "Insp H", "GH C", "GH H", "Code Scan", "Secrets", "Score"],
                [
                    [r["repo"], r["insp_crit"], r["insp_high"],
                     r["gh_crit"], r["gh_high"],
                     r["code_scanning"], r["secrets"],
                     f"{r['combined_score']:,d}"]
                    for r in repo_rank[:25]
                ],
            ),
        ]

    # ── Lens 3: Offender convergence ─────────────────────────────────────────
    if convergence:
        lines += [
            "",
            "## Top Offenders — Repos Flagged by Multiple Signals",
            "",
            "> Repos appearing in the top 15 of 2 or more signal categories.",
            "> These are the highest-confidence fix targets — verified across independent scanners.",
            "",
            md_table(
                ["Repository", "Signals", "Insp C+H", "GH C+H", "Code Scan", "Secrets"],
                [
                    [
                        r["repo"],
                        " · ".join(r["signals"]),
                        r["insp_crit"] + r["insp_high"],
                        r["gh_crit"] + r["gh_high"],
                        r["code_scanning"],
                        r["secrets"],
                    ]
                    for r in convergence
                ],
            ),
        ]

    # ── Lens 2: Package quick-win ─────────────────────────────────────────────
    if pkg_qw:
        trivial_count  = sum(1 for p in pkg_qw if p["effort"] == 1)
        bounded_count  = sum(1 for p in pkg_qw if p["effort"] == 2)
        phantom_count  = sum(1 for p in pkg_qw if p["effort"] == 3)
        struct_count   = sum(1 for p in pkg_qw if p["effort"] == 4)
        lines += [
            "",
            "## Package Quick-Win Ranking",
            "",
            f"> **{trivial_count} Trivial · {bounded_count} Bounded · "
            f"{phantom_count} Phantom · {struct_count} Structural** "
            f"(see Effort Categories section above for definitions).",
            ">",
            "> Score = (Inspector C+H + GitHub C+H) × repos_affected ÷ effort.",
            "> Higher score = more findings closed per unit of engineering work.",
            "",
            md_table(
                ["Package", "Effort", "Insp C+H", "GH C+H", "GH Repos", "Fix?", "QW Score"],
                [
                    [
                        p["package"][:35],
                        p["effort_label"],
                        p["insp_crit"] + p["insp_high"],
                        p["gh_crit"] + p["gh_high"],
                        p["gh_repos"],
                        "✓" if p["fix_available"] else "✗",
                        f"{p['quickwin_score']:,d}",
                    ]
                    for p in pkg_qw[:30]
                ],
            ),
        ]

    lines += [
        "",
        "## Zone B — Inspector Only (top 20 by C+H)",
        "",
        "> In the deployed image but not flagged by Dependabot.",
        "> Likely transitive / build-only dependencies, or packages not in source lock file.",
        "",
    ]
    if zone_b:
        rows = [
            [b["cve"], b.get("package","")[:35], b["crit"], b["high"], b["title"][:60]]
            for b in zone_b[:20]
        ]
        lines.append(md_table(["CVE", "Package", "CRIT", "HIGH", "Title"], rows))

    lines += [
        "",
        "## Zone C — GitHub Only (top 20 by alert count)",
        "",
        "> In source code, not flagged by Inspector.",
        "> Image may have been updated but source lock file not cleaned up,",
        "> or the package is not deployed to a scanned ECR image.",
        "",
    ]
    if zone_c:
        rows = [
            [c["cve"], c["package"][:35], c["severity"], c["alerts"],
             ", ".join(c["repos"][:4]) + ("…" if len(c["repos"]) > 4 else "")]
            for c in zone_c[:20]
        ]
        lines.append(md_table(["CVE", "Package", "Severity", "GH Alerts", "Repos"], rows))

    # Code scanning
    if cs_alerts:
        from collections import Counter
        by_sev  = Counter(a.get("severity", "?") for a in cs_alerts)
        by_repo = Counter(a.get("repo")           for a in cs_alerts)
        lines += [
            "",
            "## Code Scanning (SAST) Alerts",
            "",
            md_table(["Severity", "Count"],
                     sorted(by_sev.items(), key=lambda x: (-x[1], x[0]))),
            "",
            "### Top repos by code scanning alert count",
            "",
            md_table(["Repository", "Alerts"],
                     sorted(by_repo.items(), key=lambda x: (-x[1], x[0]))[:15]),
        ]

    # Secret scanning summary
    ss_alerts = gh_raw.get("secret_scanning", [])
    if ss_alerts:
        from collections import Counter
        by_type = Counter(a.get("secret_type") for a in ss_alerts)
        by_repo = Counter(a.get("repo")        for a in ss_alerts)
        lines += [
            "",
            "## Secret Scanning — Open Alerts ← P0",
            "",
            "> These are credential-level exposures, not vulnerability findings.",
            "> They require immediate triage and rotation — not a backlog item.",
            "",
            md_table(["Secret type", "Count"],
                     sorted(by_type.items(), key=lambda x: (-x[1], x[0] or ""))),
            "",
            "### Repos with exposed secrets",
            "",
            md_table(["Repository", "Secret count"],
                     sorted(by_repo.items(), key=lambda x: (-x[1], x[0] or ""))),
        ]

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Cross-source vulnerability correlation")
    parser.add_argument("--inspector", help="Inspector raw JSON (default: latest raw-*.json in reports_dir)")
    parser.add_argument("--github",    help="GitHub raw JSON (default: latest github-raw-*.json in reports_dir)")
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--raw",  action="store_true")
    parser.add_argument("--reports-dir", help="Directory for snapshot read/write (overrides $SECURITY_SNAPSHOT_REPORTS_DIR)")
    args = parser.parse_args()

    reports_dir = _resolve_reports_dir(args)

    insp_path = Path(args.inspector) if args.inspector else latest_file("raw.json",        reports_dir)
    gh_path   = Path(args.github)    if args.github    else latest_file("github-raw.json", reports_dir)

    if not insp_path or not insp_path.exists():
        sys.exit("Inspector raw JSON not found. Run: python3 posture_snapshot.py --raw")
    if not gh_path or not gh_path.exists():
        sys.exit("GitHub raw JSON not found. Run: python3 github_security_snapshot.py --raw")

    print(f"→ Loading Inspector data: {insp_path.name}", flush=True)
    insp_raw = load_json(insp_path)
    print(f"→ Loading GitHub data:    {gh_path.name}", flush=True)
    gh_raw   = load_json(gh_path)

    print("→ Building indexes ...", flush=True)
    insp_idx = build_inspector_index(insp_raw)
    gh_idx   = build_github_index(gh_raw)

    print(f"   Inspector: {len(insp_idx['by_cve'])} CVEs, {len(insp_idx['by_pkg'])} packages", flush=True)
    print(f"   GitHub:    {len(gh_idx['by_cve'])} CVEs, {len(gh_idx['by_pkg'])} packages", flush=True)

    print("→ Correlating (zone analysis) ...", flush=True)
    corr = correlate(insp_idx, gh_idx)
    s    = corr["summary"]
    print(f"   Zone A (both):            {s['cves_in_both']} CVEs, {s['pkgs_in_both']} packages", flush=True)
    print(f"   Zone B (Inspector only):  {s['cves_inspector_only']} CVEs", flush=True)
    print(f"   Zone C (GitHub only):     {s['cves_github_only']} CVEs", flush=True)

    print("→ Building combined repo rankings ...", flush=True)
    repo_ranking = build_repo_combined_ranking(insp_raw, gh_raw)
    corr["repo_combined_ranking"] = repo_ranking
    print(f"   {len(repo_ranking)} repos ranked", flush=True)

    print("→ Scoring package quick-wins ...", flush=True)
    pkg_qw = build_package_quickwin(corr["zone_a_pkg_overlap"], gh_raw)
    corr["package_quickwin"] = pkg_qw
    trivial = sum(1 for p in pkg_qw if p["effort"] == 1)
    print(f"   {len(pkg_qw)} Zone A packages scored — {trivial} Trivial (version bump)", flush=True)

    print("→ Building offender convergence ...", flush=True)
    convergence = build_offender_convergence(repo_ranking)
    corr["offender_convergence"] = convergence
    print(f"   {len(convergence)} repos appear in 2+ signal categories", flush=True)

    ts    = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    today = datetime.now(timezone.utc).strftime("%Y%m%d")

    report = build_report(corr, gh_raw, ts)
    print("\n" + report)

    # Outputs are co-located with their inputs — placement follows the data,
    # not the clock. Past dated folders are immutable history: if the latest
    # inputs are from a previous day, refuse to save rather than refresh a
    # past folder or mint a new folder with no collection behind it.
    date_dir = insp_path.parent
    if args.save or args.raw:
        if gh_path.parent != insp_path.parent:
            sys.exit(f"error: inputs live in different dated folders "
                     f"({insp_path.parent.name} vs {gh_path.parent.name}) — refusing to save.")
        if date_dir.name != today:
            sys.exit(f"error: latest inputs are from {date_dir.name}, not today ({today}). "
                     "Past snapshots are immutable — run posture_snapshot.py and "
                     "github_security_snapshot.py first for a fresh collection, "
                     "or run without --save/--raw to print the analysis only.")

    if args.save:
        path = date_dir / "correlation.md"
        path.write_text(report)
        print(f"\n✓ Saved → {path}", file=sys.stderr)

    if args.raw:
        out = {
            "generated_at": ts,
            # inputs are sibling files in the same date folder
            "inputs": {"inspector": insp_path.name, "github": gh_path.name},
            "correlation": corr,
        }
        path = date_dir / "correlation.json"
        path.write_text(json.dumps(out, indent=2, default=str, sort_keys=True))
        print(f"✓ Saved → {path}", file=sys.stderr)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
posture_snapshot.py — Inspector V2 full posture + fan-out analysis

Usage:
    python3 posture_snapshot.py             # print to stdout
    python3 posture_snapshot.py --save      # also write posture-YYYYMMDD.md here
    python3 posture_snapshot.py --raw       # also write raw-YYYYMMDD.json here
    python3 posture_snapshot.py --save --raw

AWS profile and region come from config.json (aws_profile / aws_region).
The account ID is derived at runtime via STS — never hardcoded.

Sections produced:
  1. Coverage (ECR images / EC2 / Lambda)
  2. Total findings (C / H / M)
  3. Fan-out summary (unique CVEs, avg fan-out, addressable estimate)
  4. Top CVEs by C+H (TITLE aggregation)
  5. Top packages by finding count
  6. Repositories ranked by C+H
  7. Dominant base layers (IMAGE_LAYER aggregation, deduplicated)
  8. EC2 AMI summary
"""
import argparse
import json
import os
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


def _load_config() -> dict:
    """Org-specific settings live in config.json next to this script."""
    path = Path(__file__).parent / "config.json"
    if not path.exists():
        sys.exit(f"error: {path} not found — see SKILL.md first-run configuration")
    return json.loads(path.read_text())


def _require(cfg: dict, key: str) -> str:
    val = (cfg.get(key) or "").strip()
    if not val:
        sys.exit(f"error: '{key}' is not set in scripts/config.json — "
                 "run the skill's first-run setup (it prompts for this), or edit the file directly")
    return val

try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError
except ImportError:
    sys.exit("boto3 not installed: pip install boto3")

_CFG    = _load_config()
PROFILE = _require(_CFG, "aws_profile")
REGION  = _require(_CFG, "aws_region")

# Kernel / no-fix package names — excluded from addressable estimate.
# These are OS-level packages that can't be patched individually;
# they close only with a base OS image upgrade.
KERNEL_PKGS = {"linux", "linux-libc-dev", "linux-headers"}


# ── AWS client ────────────────────────────────────────────────────────────────

def inspector_client():
    session = boto3.Session(profile_name=PROFILE, region_name=REGION)
    # Adaptive retries absorb transient Inspector throttling so it rarely
    # surfaces as a ClientError at all (see paginate_aggregations for what
    # happens when one does).
    return session.client("inspector2", config=Config(retries={"mode": "adaptive", "max_attempts": 8}))


# ── Aggregation helpers ───────────────────────────────────────────────────────

def paginate_aggregations(c, agg_type, agg_request, max_results=100, required=True):
    """
    Page through list_finding_aggregations, returning all responses.

    `required` sections fail the run on ClientError rather than continuing
    with partial pages: these aggregations feed the account-wide headline
    numbers and the immutable snapshot history, and a mid-pagination failure
    yields a count that looks complete while silently under-reporting.
    Optional sections (display-only) warn and degrade instead.
    """
    results = []
    kwargs = {
        "aggregationType": agg_type,
        "aggregationRequest": agg_request,
        "maxResults": max_results,
    }
    while True:
        try:
            resp = c.list_finding_aggregations(**kwargs)
        except ClientError as e:
            if required:
                sys.exit(f"error: {agg_type} aggregation failed after {len(results)} pages — "
                         f"refusing to report partial account-wide numbers; rerun the snapshot: {e}")
            print(f"  WARN: {agg_type} aggregation failed — section degraded: {e}", file=sys.stderr)
            break
        results.extend(resp.get("responses", []))
        token = resp.get("nextToken")
        if not token:
            break
        kwargs["nextToken"] = token
    return results


def get_coverage_counts(c):
    """Return {resource_type: count} for EC2, ECR, Lambda."""
    resource_types = [
        "AWS_EC2_INSTANCE",
        "AWS_ECR_CONTAINER_IMAGE",
        "AWS_LAMBDA_FUNCTION",
    ]
    counts = {}
    for rt in resource_types:
        total = 0
        kwargs = {
            "filterCriteria": {"resourceType": [{"comparison": "EQUALS", "value": rt}]},
            "maxResults": 200,
        }
        while True:
            resp = c.list_coverage(**kwargs)
            total += len(resp.get("coveredResources", []))
            token = resp.get("nextToken")
            if not token:
                break
            kwargs["nextToken"] = token
        counts[rt] = total
    return counts


def get_title_stats(responses):
    """
    Summarise TITLE aggregation responses.
    Returns a dict with unique_count, top CVEs, and package-level totals
    for computing the addressable estimate.
    """
    pkg_totals = defaultdict(lambda: {"c": 0, "h": 0, "m": 0, "titles": 0})
    all_titles = []

    for r in responses:
        t = r.get("titleAggregation", {})
        sc = t.get("severityCounts", {})
        c = sc.get("critical", 0)
        h = sc.get("high", 0)
        m = sc.get("medium", 0)
        title = t.get("title", "")

        # Extract package name from "CVE-XXXX - pkgname" pattern
        parts = title.split(" - ")
        pkg = parts[1].strip() if len(parts) > 1 else "unknown"

        pkg_totals[pkg]["c"] += c
        pkg_totals[pkg]["h"] += h
        pkg_totals[pkg]["m"] += m
        pkg_totals[pkg]["titles"] += 1
        all_titles.append({"title": title, "c": c, "h": h, "m": m})

    # Top 50 by CRITICAL+HIGH
    top = sorted(all_titles, key=lambda x: x["c"] + x["h"], reverse=True)[:50]

    # Addressable estimate: sum C+H for non-kernel packages
    addressable_ch = sum(
        v["c"] + v["h"]
        for pkg, v in pkg_totals.items()
        if pkg not in KERNEL_PKGS
    )

    return {
        "unique_count": len(responses),
        "pkg_count": len(pkg_totals),
        "top_by_ch": top,
        "addressable_ch_excl_kernel": addressable_ch,
    }


def get_layer_stats(responses):
    """
    Deduplicate IMAGE_LAYER aggregation by hash.
    Returns top layers sorted by CRITICAL+HIGH, each with affected repo/image counts.
    """
    by_hash = defaultdict(lambda: {"c": 0, "h": 0, "m": 0, "repos": set(), "images": set()})

    for r in responses:
        l = r.get("imageLayerAggregation", {})
        sc = l.get("severityCounts", {})
        h = l.get("layerHash", "")
        if not h:
            continue
        by_hash[h]["c"] += sc.get("critical", 0)
        by_hash[h]["h"] += sc.get("high", 0)
        by_hash[h]["m"] += sc.get("medium", 0)
        if l.get("repository"):
            by_hash[h]["repos"].add(l["repository"])
        if l.get("resourceId"):
            by_hash[h]["images"].add(l["resourceId"])

    result = [
        {
            "layer": k,
            "c": v["c"], "h": v["h"], "m": v["m"],
            "repos": len(v["repos"]),
            "repo_list": sorted(r for r in v["repos"] if r),
            "images": len(v["images"]),
        }
        for k, v in by_hash.items()
    ]
    return sorted(result, key=lambda x: x["c"] + x["h"], reverse=True)[:20]


# ── Report builder ────────────────────────────────────────────────────────────

def severity_counts(d):
    sc = d.get("severityCounts", {})
    return sc.get("critical", 0), sc.get("high", 0), sc.get("medium", 0)


def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("|" + "|".join("---" for _ in headers) + "|")
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


def build_report(raw):
    ts           = raw["generated_at"]
    totals       = raw["account_totals"]
    pkgs         = raw["packages"]
    repos        = raw["repositories"]
    amis         = raw["amis"]
    cov          = raw["coverage"]
    title_stats  = raw.get("title_stats", {})
    layer_stats  = raw.get("base_layers", [])

    c_total = totals.get("critical", 0)
    h_total = totals.get("high", 0)
    m_total = totals.get("medium", 0)
    raw_total = c_total + h_total + m_total

    unique_cves  = title_stats.get("unique_count", 0)
    fan_out      = round(raw_total / unique_cves, 1) if unique_cves else 0
    addressable  = title_stats.get("addressable_ch_excl_kernel", 0)

    lines = [
        "# AWS Inspector V2 Posture Snapshot",
        "",
        f"**Generated**: {ts}  |  **Account**: {raw.get('account', '—')}  |  **Region**: {raw.get('region', REGION)}",
        "",
        "## Coverage",
        "",
        md_table(
            ["Resource type", "Count"],
            [(k, f"{v:,d}") for k, v in cov.items()]
            + [("**Total**", f"**{sum(cov.values()):,d}**")],
        ),
        "",
        "## Total Findings",
        "",
        md_table(
            ["Severity", "Count"],
            [
                ("CRITICAL", f"{c_total:,d}"),
                ("HIGH",     f"{h_total:,d}"),
                ("MEDIUM",   f"{m_total:,d}"),
                ("**Total**", f"**{raw_total:,d}**"),
            ],
        ),
        "",
        "## Fan-out Summary",
        "",
    ]

    if unique_cves:
        lines += [
            md_table(
                ["Metric", "Value"],
                [
                    ("Raw findings (C+H+M)",               f"{raw_total:,d}"),
                    ("Unique CVE titles",                   f"{unique_cves:,d}"),
                    ("Average fan-out",                     f"~{fan_out:,.0f}×"),
                    ("Addressable C+H (excl. kernel pkgs)", f"~{addressable:,d}"),
                    ("Unique packages affected",            str(title_stats.get("pkg_count", "–"))),
                ],
            ),
            "",
            "> Addressable = CRITICAL+HIGH CVEs on packages where a fix exists or an upgrade",
            "> is possible. Kernel/libc CVEs are excluded — they close with a base OS image",
            "> upgrade, not individual patches.",
        ]
    else:
        lines.append("> Title aggregation not available in this run.")

    # Top CVEs
    if title_stats.get("top_by_ch"):
        lines += ["", "## Top CVEs by CRITICAL+HIGH", ""]
        cve_rows = [
            [t["title"][:80], f"{t['c']:,d}", f"{t['h']:,d}", f"{t['m']:,d}"]
            for t in title_stats["top_by_ch"][:25]
        ]
        lines.append(md_table(["CVE / Title", "CRITICAL", "HIGH", "MEDIUM"], cve_rows))

    # Top packages
    lines += ["", "## Top Packages by Finding Count", ""]
    pkg_rows = []
    for r in pkgs[:50]:
        p = r.get("packageAggregation", {})
        c, h, m = severity_counts(p)
        pkg_rows.append([p.get("packageName", ""), f"{c:,d}", f"{h:,d}", f"{m:,d}", f"{c+h+m:,d}"])
    lines.append(md_table(["Package", "CRITICAL", "HIGH", "MEDIUM", "Total"], pkg_rows))
    lines.append(f"\n> {len(pkgs)} packages total.")

    # Repositories
    lines += ["", "## Repositories (sorted by CRITICAL+HIGH)", ""]
    sorted_repos = sorted(
        repos,
        key=lambda x: sum(severity_counts(x.get("repositoryAggregation", {}))[:2]),
        reverse=True,
    )
    repo_rows = []
    for r in sorted_repos:
        a = r.get("repositoryAggregation", {})
        c, h, m = severity_counts(a)
        repo_rows.append([
            a.get("repository", ""),
            f"{c:,d}", f"{h:,d}", f"{m:,d}",
            str(a.get("affectedImages", 0)),
        ])
    lines.append(md_table(["Repository", "CRITICAL", "HIGH", "MEDIUM", "Images"], repo_rows))

    # Base layers
    if layer_stats:
        lines += ["", "## Dominant Base Layers", ""]
        lines += [
            "> Layers shared across many images. The top entry is typically the base OS layer.",
            "> One `FROM` change in the Dockerfile closes all findings tied to that layer.",
            "",
        ]
        layer_rows = [
            [
                l["layer"][:20] + "…",
                f"{l['repos']:,d}",
                f"{l['images']:,d}",
                f"{l['c']:,d}",
                f"{l['h']:,d}",
                f"{l['m']:,d}",
                f"{l['c']+l['h']+l['m']:,d}",
            ]
            for l in layer_stats[:15]
        ]
        lines.append(
            md_table(
                ["Layer (prefix)", "Repos", "Images", "CRITICAL", "HIGH", "MEDIUM", "Total"],
                layer_rows,
            )
        )

    # AMI summary
    lines += ["", "## EC2 AMI Summary", ""]
    ami_rows = []
    for r in amis:
        a = r.get("amiAggregation", {})
        c, h, m = severity_counts(a)
        instances = a.get("affectedInstances", 0)
        per = round((h + m) / instances, 1) if instances else 0
        ami_rows.append([
            a.get("ami", ""), str(instances),
            f"{c:,d}", f"{h:,d}", f"{m:,d}", str(per),
        ])
    lines.append(
        md_table(["AMI", "Instances", "CRITICAL", "HIGH", "MEDIUM", "H+M/instance"], ami_rows)
    )

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Inspector V2 posture + fan-out snapshot")
    parser.add_argument("--save", action="store_true", help="Write .md report to reports_dir")
    parser.add_argument("--raw",  action="store_true", help="Write raw .json to reports_dir")
    parser.add_argument("--reports-dir", help="Directory for snapshot read/write (overrides $SECURITY_SNAPSHOT_REPORTS_DIR)")
    args = parser.parse_args()

    c = inspector_client()
    now       = datetime.now(timezone.utc)   # one clock read — ts and date_slug must agree across midnight
    ts        = now.strftime("%Y-%m-%d %H:%M UTC")
    date_slug = now.strftime("%Y%m%d")

    # Account ID derived at runtime — keeps it out of source while still
    # appearing in reports and the dashboard header.
    session = boto3.Session(profile_name=PROFILE, region_name=REGION)
    account = session.client("sts").get_caller_identity()["Account"]

    print("→ account totals ...", flush=True)
    account_resp = paginate_aggregations(
        c, "ACCOUNT",
        {"accountAggregation": {"sortBy": "ALL", "sortOrder": "DESC"}},
    )
    totals = (
        account_resp[0].get("accountAggregation", {}).get("severityCounts", {})
        if account_resp else {}
    )

    print("→ title aggregation (unique CVEs) ...", flush=True)
    title_responses = paginate_aggregations(
        c, "TITLE",
        {"titleAggregation": {"sortBy": "ALL", "sortOrder": "DESC"}},
    )
    title_stats = get_title_stats(title_responses)
    print(f"   {title_stats['unique_count']:,d} unique CVE titles found", flush=True)

    print("→ image layer aggregation (base image identification) ...", flush=True)
    layer_responses = paginate_aggregations(
        c, "IMAGE_LAYER",
        {"imageLayerAggregation": {"sortBy": "ALL", "sortOrder": "DESC"}},
        max_results=100,
        required=False,   # display-only section — degrade rather than fail
    )
    base_layers = get_layer_stats(layer_responses)
    print(f"   {len(base_layers)} dominant layers identified", flush=True)

    print("→ package aggregations (all pages) ...", flush=True)
    packages = paginate_aggregations(
        c, "PACKAGE",
        {"packageAggregation": {"sortBy": "ALL", "sortOrder": "DESC"}},
    )

    print("→ repository aggregations ...", flush=True)
    repositories = paginate_aggregations(
        c, "REPOSITORY",
        {"repositoryAggregation": {"sortBy": "ALL", "sortOrder": "DESC"}},
    )

    print("→ AMI aggregations ...", flush=True)
    amis = paginate_aggregations(
        c, "AMI",
        {"amiAggregation": {"sortBy": "AFFECTED_INSTANCES", "sortOrder": "DESC"}},
        max_results=20,
        required=False,   # display-only section — degrade rather than fail
    )

    print("→ coverage counts ...", flush=True)
    coverage = get_coverage_counts(c)

    raw = {
        "generated_at":  ts,
        "account":       account,
        "region":        REGION,
        "account_totals": totals,
        "title_stats":   title_stats,
        "base_layers":   base_layers,
        "packages":      packages,
        "repositories":  repositories,
        "amis":          amis,
        "coverage":      coverage,
    }

    report = build_report(raw)
    print("\n" + report)

    date_dir = None
    if args.save or args.raw:
        date_dir = _resolve_reports_dir(args) / date_slug
        date_dir.mkdir(parents=True, exist_ok=True)

    if args.save:
        path = date_dir / "posture.md"
        path.write_text(report)
        print(f"\n✓ Saved report → {path}", file=sys.stderr)

    if args.raw:
        # Exclude the full title_responses (10K entries) from the JSON —
        # title_stats already contains the aggregated summary and top 50.
        path = date_dir / "raw.json"
        path.write_text(json.dumps(raw, indent=2, default=str))
        print(f"✓ Saved raw data → {path}", file=sys.stderr)


if __name__ == "__main__":
    main()

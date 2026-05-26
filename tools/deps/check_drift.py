#!/usr/bin/env python3
"""Report cross-file dependency drift in this repo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from drift_lib import Finding, scan_root


def format_human(findings: list[Finding]) -> str:
    """Format findings as a human-readable report."""
    drift = [f for f in findings if f.status == "drift"]
    if not drift:
        return "no drift\n"

    out: list[str] = [f"DRIFT FOUND ({len(drift)} findings):", ""]
    for f in drift:
        out.append(f.package)
        col_width = max(len(f"{s.file} {s.location}") for s in f.sightings) + 2
        for s in f.sightings:
            label = f"  {s.file} {s.location}".ljust(col_width + 2)
            out.append(f"{label}{s.version}")
        out.append(f"  -> {f.recommendation}")
        out.append("")
    return "\n".join(out) + "\n"


def format_json(findings: list[Finding]) -> str:
    """Format findings as a JSON report."""
    drift = [f for f in findings if f.status == "drift"]
    payload = [
        {
            "package": f.package,
            "status": f.status,
            "sightings": [{"file": s.file, "location": s.location, "version": s.version} for s in f.sightings],
            "recommendation": f.recommendation,
        }
        for f in drift
    ]
    return json.dumps(payload, indent=2) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Parse args, run scan, emit report; return 0 (clean), 1 (drift), or 2 (error)."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repo root (default: cwd)")
    parser.add_argument("--json", dest="as_json", action="store_true", help="emit JSON instead of human text")
    args = parser.parse_args(argv)

    try:
        findings = scan_root(args.root)
    except Exception as exc:  # BLE001 — broad catch intentional; surfacing parser errors via exit 2
        print(f"check_drift: failed to scan {args.root}: {exc}", file=sys.stderr)
        return 2

    if args.as_json:
        sys.stdout.write(format_json(findings))
    else:
        sys.stdout.write(format_human(findings))

    return 1 if any(f.status == "drift" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())

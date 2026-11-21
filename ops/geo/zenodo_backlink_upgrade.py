#!/usr/bin/env python3
"""Add missing DataCite backlink edges to CERN Zenodo record 21292799 (DOI: 10.5281/zenodo.21292799).

Live DataCite audit (2026-11-21) confirmed 10.5281/zenodo.21292799 currently has ONLY:
  - IsVersionOf -> 10.5281/zenodo.21292798
and ZERO IsDocumentedBy / IsSupplementTo edges pointing back to https://agentskillshub.top.

Usage:
  python3 ops/geo/zenodo_backlink_upgrade.py                # Safe dry-run (default)
  ZENODO_ACCESS_TOKEN=xxx python3 ops/geo/zenodo_backlink_upgrade.py --apply
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

RECORD_ID = "21292799"
NEW_RELATED_IDENTIFIERS = [
    {
        "identifier": "https://agentskillshub.top/how-we-grade/",
        "relation": "isDocumentedBy",
        "resource_type": "publication-technicalnote",
        "scheme": "url",
    },
    {
        "identifier": "https://agentskillshub.top",
        "relation": "isSupplementTo",
        "resource_type": "software",
        "scheme": "url",
    },
    {
        "identifier": "10.5281/zenodo.24387074",
        "relation": "isReferencedBy",
        "resource_type": "dataset",
        "scheme": "doi",
    },
]


def api_call(method: str, url: str, token: str, payload: dict | None = None) -> tuple[int, dict | str]:
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8", "ignore"))
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "ignore")


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch DataCite related_identifiers on Zenodo record 21292799")
    parser.add_argument("--apply", action="store_true", help="Actually unlock, update metadata, and republish on Zenodo")
    args = parser.parse_args()

    print(f"Target Zenodo record: https://zenodo.org/records/{RECORD_ID} (DOI: 10.5281/zenodo.{RECORD_ID})")
    print("Planned related_identifiers additions:")
    print(json.dumps(NEW_RELATED_IDENTIFIERS, indent=2))

    if not args.apply:
        print("\n[DRY-RUN] No changes sent. Run with ZENODO_ACCESS_TOKEN=... --apply to execute via Zenodo API,")
        print("or paste the 3 rows above into Zenodo Web UI -> Edit -> Related works -> Publish.")
        return 0

    token = os.getenv("ZENODO_ACCESS_TOKEN", "").strip()
    if not token:
        print("ERROR: ZENODO_ACCESS_TOKEN is required with --apply.", file=sys.stderr)
        return 2

    # Step 1: Unlock published deposition for metadata-only edit (keeps exact same DOI 21292799!)
    code, dep = api_call("POST", f"https://zenodo.org/api/deposit/depositions/{RECORD_ID}/actions/edit", token)
    if code not in (200, 201):
        print(f"Failed to unlock deposition {RECORD_ID}: HTTP {code} -> {dep}", file=sys.stderr)
        return 1

    meta = dep.get("metadata", {})
    existing = list(meta.get("related_identifiers") or [])
    existing_keys = {(x.get("identifier"), x.get("relation")) for x in existing}
    for item in NEW_RELATED_IDENTIFIERS:
        if (item["identifier"], item["relation"]) not in existing_keys:
            existing.append(item)
    meta["related_identifiers"] = existing

    # Step 2: PUT updated metadata
    code, updated = api_call("PUT", f"https://zenodo.org/api/deposit/depositions/{RECORD_ID}", token, {"metadata": meta})
    if code != 200:
        print(f"Failed to update metadata: HTTP {code} -> {updated}", file=sys.stderr)
        return 1

    # Step 3: Publish metadata update
    code, pub = api_call("POST", f"https://zenodo.org/api/deposit/depositions/{RECORD_ID}/actions/publish", token)
    if code not in (200, 202):
        print(f"Failed to publish metadata update: HTTP {code} -> {pub}", file=sys.stderr)
        return 1

    print(f"SUCCESS: Published metadata update for DOI {pub.get('doi')}. Verify DataCite in 5-10 min via:")
    print("  python3 ops/geo/entity_audit.py --mode molecule")
    return 0


if __name__ == "__main__":
    sys.exit(main())

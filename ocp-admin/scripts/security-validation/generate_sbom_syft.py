#!/usr/bin/env python3
"""Generate an SBOM using syft for images without official SBOMs."""

import argparse
import json
import re
import shutil
import subprocess
import sys


def run_cmd(cmd, timeout=300):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "command timed out (syft can be slow on large images)"
    except FileNotFoundError:
        return -1, "", f"command not found: {cmd[0]}"


def parse_syft_sbom(sbom):
    packages = []
    for pkg in sbom.get("packages", []):
        spdx_id = pkg.get("SPDXID", "")
        if spdx_id == "SPDXRef-DOCUMENT":
            continue

        name = pkg.get("name", "")
        version = pkg.get("versionInfo", "")
        purl = ""
        ecosystem = ""

        for ref in pkg.get("externalRefs", []):
            if ref.get("referenceType") == "purl":
                purl = ref.get("referenceLocator", "")
                ecosystem = _ecosystem_from_purl(purl)
                break

        packages.append({
            "name": name,
            "version": version,
            "purl": purl,
            "ecosystem": ecosystem,
            "spdx_id": spdx_id,
        })

    return packages


def _ecosystem_from_purl(purl):
    if not purl:
        return ""
    match = re.match(r"pkg:([^/]+)/", purl)
    return match.group(1) if match else ""


def main():
    parser = argparse.ArgumentParser(description="Generate SBOM using syft")
    parser.add_argument("image_ref", help="Container image reference")
    parser.add_argument("--platform", default="linux/amd64", help="Platform (default: linux/amd64)")
    args = parser.parse_args()

    if not shutil.which("syft"):
        json.dump({
            "image_ref": args.image_ref,
            "sbom_source": "syft_analyzed",
            "error": "syft not found in PATH. Install from https://github.com/anchore/syft",
            "packages": [],
            "errors": ["syft not installed"],
        }, sys.stdout, indent=2)
        print()
        sys.exit(1)

    cmd = ["syft", args.image_ref, "-o", "spdx-json", "--platform", args.platform]
    rc, stdout, stderr = run_cmd(cmd)

    if rc != 0:
        json.dump({
            "image_ref": args.image_ref,
            "sbom_source": "syft_analyzed",
            "packages": [],
            "errors": [f"syft failed (exit {rc}): {stderr.strip()}"],
        }, sys.stdout, indent=2)
        print()
        sys.exit(1)

    try:
        sbom = json.loads(stdout)
    except json.JSONDecodeError as e:
        json.dump({
            "image_ref": args.image_ref,
            "sbom_source": "syft_analyzed",
            "packages": [],
            "errors": [f"syft output is not valid JSON: {e}"],
        }, sys.stdout, indent=2)
        print()
        sys.exit(1)

    packages = parse_syft_sbom(sbom)

    relationships = []
    for rel in sbom.get("relationships", []):
        relationships.append({
            "element": rel.get("spdxElementId", ""),
            "type": rel.get("relationshipType", ""),
            "related": rel.get("relatedSpdxElement", ""),
        })

    result = {
        "image_ref": args.image_ref,
        "sbom_source": "syft_analyzed",
        "sbom_format": "spdx",
        "packages": packages,
        "image_metadata": {
            "tag": "",
            "digest": "",
            "name_from_purl": "",
        },
        "relationships": relationships,
        "errors": [],
    }

    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()

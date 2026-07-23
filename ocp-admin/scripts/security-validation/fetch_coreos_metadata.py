#!/usr/bin/env python3
"""Fetch OCP release metadata and extract CoreOS RPM package list.

Uses podman to read the release image's image-references manifest directly,
avoiding the need for the oc CLI (see MGMT-24450).
"""

import argparse
import json
import re
import shutil
import subprocess
import sys

OCP_VERSION_RE = re.compile(r"^4\.\d+\.\d+$")
RELEASE_IMAGE = "quay.io/openshift-release-dev/ocp-release"
TIMEOUT_RELEASE = 120
TIMEOUT_RPM = 300


def run_cmd(cmd, timeout=60):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"command timed out after {timeout}s"
    except FileNotFoundError:
        return -1, "", f"command not found: {cmd[0]}"


def parse_image_references(image_refs_json):
    """Extract release metadata from the image-references manifest."""
    info = {
        "created": "",
        "machine_os": "",
        "component_versions": {},
        "coreos_pullspec": "",
    }

    info["created"] = image_refs_json.get("metadata", {}).get("creationTimestamp", "")

    for tag in image_refs_json.get("spec", {}).get("tags", []):
        name = tag.get("name", "")
        pullspec = tag.get("from", {}).get("name", "")
        build_versions = tag.get("annotations", {}).get("io.openshift.build.versions", "")

        if name == "rhel-coreos":
            info["coreos_pullspec"] = pullspec
            for part in build_versions.split(","):
                part = part.strip()
                if part.startswith("machine-os="):
                    info["machine_os"] = part.split("=", 1)[1]

        if build_versions:
            for part in build_versions.split(","):
                part = part.strip()
                if "=" in part:
                    k, v = part.split("=", 1)
                    if k in ("kubernetes", "kubectl", "kubernetes-tests"):
                        info["component_versions"][k] = v

    return info


def classify_rpm(name, evr):
    name_lower = name.lower()
    evr_lower = evr.lower()
    combined = f"{name_lower} {evr_lower}"

    if "rhaos4" in combined or "rhaos-4" in combined:
        return "ocp"
    if "fast-datapath" in combined or "fdp" in combined or "openvswitch" in name_lower:
        return "fast_datapath"
    return "rhel"


def parse_coreos_version(machine_os, ocp_version):
    """Parse CoreOS version string handling both versioning schemes.

    OCP >= 4.19: RHEL-based versioning, e.g. "9.6.20250617-0"
      - 9.6 = RHEL version, 20250617 = build date
    OCP < 4.19: legacy versioning, e.g. "416.94.202410071428-0"
      - 416 = OCP 4.16, 94 = RHEL 9.4, 202410071428 = build date+time

    Returns dict with rhel_version, rhel_major, coreos_version_scheme, and
    coreos_build_id (for version comparison).
    """
    result = {
        "rhel_version": "",
        "rhel_major": "",
        "coreos_version_scheme": "",
        "coreos_build_id": "",
    }

    if not machine_os:
        return result

    ocp_minor = int(ocp_version.split(".")[1]) if "." in ocp_version else 0

    legacy_match = re.match(r"(\d{3})\.(\d{2})\.([\d]+)-?", machine_os)
    new_match = re.match(r"(\d+)\.(\d+)\.([\d]+)-?", machine_os)

    if legacy_match and ocp_minor < 19:
        ocp_code = legacy_match.group(1)
        rhel_code = legacy_match.group(2)
        build_id = legacy_match.group(3)

        rhel_major = rhel_code[0]
        rhel_minor = rhel_code[1:]
        result["rhel_version"] = f"{rhel_major}.{rhel_minor}"
        result["rhel_major"] = rhel_major
        result["coreos_version_scheme"] = "legacy"
        result["coreos_build_id"] = build_id
    elif new_match:
        major = new_match.group(1)
        minor = new_match.group(2)
        build_id = new_match.group(3)

        result["rhel_version"] = f"{major}.{minor}"
        result["rhel_major"] = major
        result["coreos_version_scheme"] = "rhel_based"
        result["coreos_build_id"] = build_id
    else:
        first_dot = machine_os.find(".")
        if first_dot > 0:
            result["rhel_major"] = machine_os[0]

    return result


def main():
    parser = argparse.ArgumentParser(description="Fetch OCP release and CoreOS RPM metadata")
    parser.add_argument("ocp_version", help="OCP version (e.g., 4.20.17)")
    parser.add_argument("--cache-dir", default="", help="Directory to cache results per OCP version")
    parser.add_argument("--authfile", default="", help="Path to pull secret file for podman authentication")
    args = parser.parse_args()

    if args.cache_dir:
        import os
        cache_file = os.path.join(args.cache_dir, f"coreos-{args.ocp_version}.json")
        if os.path.isfile(cache_file):
            with open(cache_file, "r") as f:
                sys.stdout.write(f.read())
            sys.exit(0)

    if not OCP_VERSION_RE.match(args.ocp_version):
        json.dump({
            "ocp_version": args.ocp_version,
            "error": f"Invalid OCP version format: '{args.ocp_version}'. Expected: 4.X.Y",
            "errors": ["Invalid OCP version format"],
        }, sys.stdout, indent=2)
        print()
        sys.exit(1)

    errors = []

    if not shutil.which("podman"):
        json.dump({
            "ocp_version": args.ocp_version,
            "error": "podman not found in PATH. Install podman before running.",
            "errors": ["podman not installed"],
        }, sys.stdout, indent=2)
        print()
        sys.exit(1)

    release_image = f"{RELEASE_IMAGE}:{args.ocp_version}-x86_64"
    image_refs_cmd = [
        "podman", "run", "--rm", "--entrypoint", "cat",
        release_image, "/release-manifests/image-references",
    ]

    rc, stdout, stderr = run_cmd(image_refs_cmd, timeout=TIMEOUT_RELEASE)
    if rc != 0:
        json.dump({
            "ocp_version": args.ocp_version,
            "error": f"Failed to read image-references from release image: {stderr.strip()}",
            "errors": [f"podman failed (exit {rc}): {stderr.strip()[:300]}"],
        }, sys.stdout, indent=2)
        print()
        sys.exit(1)

    try:
        image_refs_json = json.loads(stdout)
    except json.JSONDecodeError as e:
        json.dump({
            "ocp_version": args.ocp_version,
            "error": f"Invalid image-references JSON: {e}",
            "errors": ["Failed to parse image-references"],
        }, sys.stdout, indent=2)
        print()
        sys.exit(1)

    info = parse_image_references(image_refs_json)

    if not info["coreos_pullspec"]:
        json.dump({
            "ocp_version": args.ocp_version,
            "error": "Could not find rhel-coreos pullspec in image-references",
            "errors": ["rhel-coreos image not found in release"],
        }, sys.stdout, indent=2)
        print()
        sys.exit(1)

    coreos_info = parse_coreos_version(info["machine_os"], args.ocp_version)
    rhel_version = coreos_info["rhel_version"]
    rhel_major = coreos_info["rhel_major"]
    ocp_minor = ".".join(args.ocp_version.split(".")[:2])

    podman_cmd = ["podman", "run", "--rm"]
    if args.authfile:
        podman_cmd += ["--authfile", args.authfile]
    podman_cmd += ["--entrypoint", "/bin/rpm",
         info["coreos_pullspec"],
         "-qa", "--queryformat", "%{NAME}\\t%{EPOCH}:%{VERSION}-%{RELEASE}\\t%{ARCH}\\n"]

    rc, stdout_rpm, stderr_rpm = run_cmd(podman_cmd, timeout=TIMEOUT_RPM)

    if rc != 0:
        if any(s in stderr_rpm.lower() for s in ("unauthorized", "authentication", "denied", "auth")):
            json.dump({
                "ocp_version": args.ocp_version,
                "coreos_pullspec": info["coreos_pullspec"],
                "error": "Authentication failed pulling CoreOS image. Download your pull secret from https://console.redhat.com/openshift/downloads and re-run with --authfile <path-to-pull-secret>",
                "errors": ["Pull secret required for quay.io/openshift-release-dev/"],
            }, sys.stdout, indent=2)
            print()
            sys.exit(1)

        errors.append(f"podman rpm extraction failed (exit {rc}): {stderr_rpm.strip()[:300]}")
        json.dump({
            "ocp_version": args.ocp_version,
            "coreos_pullspec": info["coreos_pullspec"],
            "rpms": [],
            "errors": errors,
        }, sys.stdout, indent=2)
        print()
        sys.exit(1)

    rpms = []
    source_counts = {"rhel": 0, "ocp": 0, "fast_datapath": 0}

    for line in stdout_rpm.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue

        name = parts[0]
        evr = parts[1].replace("(none)", "0")
        arch = parts[2]
        source = classify_rpm(name, evr)
        source_counts[source] = source_counts.get(source, 0) + 1

        rpms.append({
            "name": name,
            "evr": evr,
            "arch": arch,
            "source": source,
        })

    rpms.sort(key=lambda r: r["name"])

    result = {
        "ocp_version": args.ocp_version,
        "created": info["created"],
        "machine_os": info["machine_os"],
        "rhel_version": rhel_version,
        "rhel_major": rhel_major,
        "coreos_pullspec": info["coreos_pullspec"],
        "coreos_version_scheme": coreos_info["coreos_version_scheme"],
        "coreos_build_id": coreos_info["coreos_build_id"],
        "cpes": {
            "rhel": f"cpe:/o:redhat:enterprise_linux:{rhel_major}" if rhel_major else "",
            "ocp": f"cpe:/a:redhat:openshift:{ocp_minor}",
        },
        "component_versions": info["component_versions"],
        "rpms": rpms,
        "rpm_count": len(rpms),
        "rpm_by_source": source_counts,
        "errors": errors,
    }

    output = json.dumps(result, indent=2)

    if args.cache_dir and not result["errors"]:
        import os
        os.makedirs(args.cache_dir, exist_ok=True)
        cache_file = os.path.join(args.cache_dir, f"coreos-{args.ocp_version}.json")
        with open(cache_file, "w") as f:
            f.write(output)
            f.write("\n")

    sys.stdout.write(output)
    print()


if __name__ == "__main__":
    main()

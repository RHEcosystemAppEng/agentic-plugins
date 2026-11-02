#!/usr/bin/env python3
"""Build a validated hcp.py profile.json, resolving the management kubeconfig
from the environment.

Kubeconfig resolution order:
  1. $HYPERSHIFT_CONFIG            (preferred; used if it points to a real file)
  2. $KUBECONFIG                   (used only after confirmation)

For (2) the user is prompted "Use KUBECONFIG=<path>? [y/N]". In a non-interactive
context (no TTY), pass --use-kubeconfig to accept $KUBECONFIG without a prompt, or
set $HYPERSHIFT_CONFIG so no fallback is needed.

The management context and kube_system_uid are derived from the resolved kubeconfig
with read-only `oc` calls (so the identity pin always matches the real cluster),
unless supplied explicitly with --context / --kube-system-uid. The resulting
profile is validated with hcp.load_profile before it is written.

This helper lives at the EDGE: it resolves env convenience and writes an explicit
absolute path into the profile. The skill itself still consumes an explicit
management.kubeconfig path and never reads an ambient kubeconfig — that boundary is
intentional and is preserved here.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hcp  # noqa: E402  (local sibling module; load_profile validates the result)


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def resolve_kubeconfig(assume_use_kubeconfig):
    """Return an absolute kubeconfig path per the documented resolution order."""
    hyper = os.environ.get("HYPERSHIFT_CONFIG")
    if hyper:
        path = Path(hyper).expanduser()
        if not path.is_file():
            fail(f"HYPERSHIFT_CONFIG is set but not a readable file: {hyper}")
        return str(path.resolve()), "HYPERSHIFT_CONFIG"

    kube = os.environ.get("KUBECONFIG")
    if not kube:
        fail("Neither HYPERSHIFT_CONFIG nor KUBECONFIG is set. "
             "Set HYPERSHIFT_CONFIG (preferred) to the management kubeconfig path.")
    # KUBECONFIG may be an os.pathsep-joined list; the skill needs a single file.
    first = kube.split(os.pathsep)[0]
    if len(kube.split(os.pathsep)) > 1:
        print(f"note: KUBECONFIG has multiple entries; using the first: {first}",
              file=sys.stderr)
    path = Path(first).expanduser()
    if not path.is_file():
        fail(f"KUBECONFIG does not point to a readable file: {first}")

    if assume_use_kubeconfig:
        use = True
    elif not sys.stdin.isatty():
        fail("HYPERSHIFT_CONFIG not set and no TTY to confirm KUBECONFIG. "
             f"Re-run with --use-kubeconfig to accept KUBECONFIG={first}, "
             "or set HYPERSHIFT_CONFIG.")
    else:
        answer = input(f"HYPERSHIFT_CONFIG not set. Use KUBECONFIG={first}? [y/N] ")
        use = answer.strip().lower() in ("y", "yes")
    if not use:
        fail("Declined KUBECONFIG. Set HYPERSHIFT_CONFIG to the intended management "
             "kubeconfig and re-run.")
    return str(path.resolve()), "KUBECONFIG"


def oc_query(kubeconfig, context, args):
    cmd = ["oc", f"--kubeconfig={kubeconfig}"]
    if context:
        cmd.append(f"--context={context}")
    cmd += ["--request-timeout=30s", *args]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        fail("oc not found on PATH; pass --context and --kube-system-uid explicitly "
             "to build a profile without contacting the cluster.")
    except subprocess.TimeoutExpired:
        fail("oc timed out contacting the management cluster.")
    if out.returncode != 0:
        fail(f"oc {' '.join(args)} failed: {out.stderr.strip().splitlines()[-1] if out.stderr.strip() else 'unknown error'}")
    return out.stdout.strip()


def main():
    p = argparse.ArgumentParser(description="Build a validated hcp.py profile.json.")
    p.add_argument("--out", required=True, help="Path to write profile.json")
    p.add_argument("--name", required=True)
    p.add_argument("--namespace", default="clusters")
    p.add_argument("--provider", required=True, choices=sorted(hcp.PROVIDERS))
    p.add_argument("--cli", default="hypershift", choices=("hypershift", "hcp"))
    p.add_argument("--release-image", required=True,
                   help="Release image pinned by @sha256:<digest>")
    p.add_argument("--pull-secret", required=True, help="Absolute path to pull secret")
    p.add_argument("--replicas", type=int, default=2)
    p.add_argument("--context", help="Management context (default: current-context of the kubeconfig)")
    p.add_argument("--kube-system-uid", help="Override; default is read from the cluster")
    p.add_argument("--create-arg", action="append", default=[],
                   help="Repeatable provider create arg, e.g. --create-arg=--region=us-west-1")
    p.add_argument("--destroy-arg", action="append", default=[])
    p.add_argument("--use-kubeconfig", action="store_true",
                   help="Accept $KUBECONFIG without prompting (for non-interactive use)")
    args = p.parse_args()

    kubeconfig, source = resolve_kubeconfig(args.use_kubeconfig)
    print(f"management kubeconfig: {kubeconfig}  (from {source})", file=sys.stderr)

    context = args.context or oc_query(kubeconfig, None, ["config", "current-context"])
    uid = args.kube_system_uid or oc_query(
        kubeconfig, context,
        ["get", "namespace", "kube-system", "-o", "jsonpath={.metadata.uid}"])
    if not uid:
        fail("Could not determine kube-system UID; pass --kube-system-uid explicitly.")

    profile = {
        "schema_version": 1,
        "name": args.name,
        "namespace": args.namespace,
        "provider": args.provider,
        "cli": args.cli,
        "management": {
            "kubeconfig": kubeconfig,
            "context": context,
            "kube_system_uid": uid,
        },
        "release_image": args.release_image,
        "pull_secret": str(Path(args.pull_secret).expanduser().resolve())
        if not os.path.isabs(args.pull_secret) else args.pull_secret,
        "replicas": args.replicas,
        "create_args": args.create_arg,
        "destroy_args": args.destroy_arg,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Write privately: atomic replace, refuse to follow a pre-existing symlink, and
    # mode 0600 (mkstemp default) — the profile carries management identity paths.
    # Reuses the skill's own private_write helper for a consistent security posture.
    try:
        hcp.private_write(out_path, json.dumps(profile, indent=2) + "\n")
    except hcp.Error as exc:
        fail(str(exc))
    # Validate what we just wrote; load_profile raises hcp.Error on any problem.
    try:
        hcp.load_profile(str(out_path))
    except hcp.Error as exc:
        out_path.unlink(missing_ok=True)
        fail(f"generated profile failed validation: {exc}")
    print(f"wrote validated profile: {out_path}  "
          f"(provider={args.provider}, context={context})")


if __name__ == "__main__":
    main()

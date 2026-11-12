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
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hcp  # noqa: E402  (local sibling module; load_profile validates the result)


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def readable_file(path):
    """A regular file the current user can actually open for reading."""
    try:
        if not path.is_file():
            return False
        with path.open("rb"):
            return True
    except OSError:
        return False


def resolve_kubeconfig(assume_use_kubeconfig):
    """Return an absolute kubeconfig path per the documented resolution order."""
    hyper = os.environ.get("HYPERSHIFT_CONFIG")
    if hyper:
        path = Path(hyper).expanduser()
        if not readable_file(path):
            fail(f"HYPERSHIFT_CONFIG is set but is not a readable file: {hyper}")
        return str(path.resolve()), "HYPERSHIFT_CONFIG"

    kube = os.environ.get("KUBECONFIG")
    if not kube:
        fail("Neither HYPERSHIFT_CONFIG nor KUBECONFIG is set. "
             "Set HYPERSHIFT_CONFIG (preferred) to the management kubeconfig path.")
    # KUBECONFIG may be an os.pathsep-joined list, but the profile pins one file.
    # Merging is context-dependent, so refuse a list rather than silently using
    # only the first entry and risking the wrong management cluster.
    entries = [entry for entry in kube.split(os.pathsep) if entry]
    if len(entries) != 1:
        fail("KUBECONFIG must name exactly one file so the profile pins the intended "
             "management cluster. Flatten the merged config first, for example:\n"
             "  oc config view --flatten --raw > /path/to/management.kubeconfig\n"
             "then set HYPERSHIFT_CONFIG=/path/to/management.kubeconfig and re-run.")
    first = entries[0]
    path = Path(first).expanduser()
    if not readable_file(path):
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
    credentials = p.add_mutually_exclusive_group(required=True)
    credentials.add_argument("--pull-secret", help="Absolute path to a local pull secret")
    credentials.add_argument("--secret-creds", help="Existing AWS Secret name in the management namespace; contains sts-creds, pull-secret, and base-domain")
    p.add_argument("--replicas", type=int, default=2)
    p.add_argument("--context", help="Management context (default: current-context of the kubeconfig)")
    p.add_argument("--kube-system-uid", help="Override; default is read from the cluster")
    p.add_argument("--cloud-account-id", help="Pinned cloud account/subscription ID (required for AWS)")
    p.add_argument("--cloud-region", help="Pinned cloud region (required for AWS)")
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
        "replicas": args.replicas,
        "create_args": args.create_arg,
        "destroy_args": args.destroy_arg,
    }
    if args.pull_secret:
        profile["pull_secret"] = str(Path(args.pull_secret).expanduser().resolve()) \
            if not os.path.isabs(args.pull_secret) else args.pull_secret
    else:
        if args.provider != "aws":
            fail("--secret-creds is currently supported only for the AWS provider.")
        profile["secret_creds"] = args.secret_creds
    if args.cloud_account_id or args.cloud_region:
        if args.provider != "aws":
            fail("--cloud-account-id/--cloud-region currently support the AWS provider.")
        if not (args.cloud_account_id and args.cloud_region):
            fail("Set both --cloud-account-id and --cloud-region for AWS.")
        profile["cloud_identity"] = {"kind": "aws", "account_id": args.cloud_account_id,
                                     "region": args.cloud_region}
    elif args.provider == "aws":
        fail("AWS requires --cloud-account-id and --cloud-region.")

    out_path = Path(args.out)
    # Create only missing parents, with 0700, before writing the profile.
    hcp.make_private_parents(out_path.parent)
    parent_info = out_path.parent.stat()
    if parent_info.st_uid != os.getuid() and not parent_info.st_mode & stat.S_ISVTX:
        fail(f"Output directory must be owned by you or sticky: {out_path.parent}")
    # Write the validated bytes directly, then atomically publish that exact file
    # with mode 0600 (mkstemp) — the profile carries management identity paths.
    generated = json.dumps(profile, indent=2) + "\n"
    fd, temporary_path = tempfile.mkstemp(prefix=f".{out_path.name}.", dir=out_path.parent)
    published = False
    try:
        os.fchmod(fd, 0o600)
        stream = os.fdopen(fd, "wb")
        fd = None
        try:
            stream.write(generated.encode())
        finally:
            stream.close()
        # Validate before replacement so an invalid profile cannot destroy an existing one.
        try:
            hcp.load_profile(temporary_path)
        except hcp.Error as exc:
            fail(f"generated profile failed validation: {exc}")
        if out_path.is_symlink():
            fail(f"Refusing symlink: {out_path}")
        try:
            os.replace(temporary_path, out_path)
        except OSError as exc:
            fail(f"Unable to write profile: {exc}")
        published = True
    finally:
        if fd is not None:
            os.close(fd)
        if not published:
            Path(temporary_path).unlink(missing_ok=True)
    print(f"wrote validated profile: {out_path}  "
          f"(provider={args.provider}, context={context})")


if __name__ == "__main__":
    main()

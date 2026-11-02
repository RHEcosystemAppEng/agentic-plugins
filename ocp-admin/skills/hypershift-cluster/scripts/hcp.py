#!/usr/bin/env python3
"""Explicit-target HyperShift lifecycle helper. Requires Python 3.10+ and PyYAML.

Provider setup stays in the upstream CLI; this helper pins cluster identities,
keeps credentials private, and confines ordinary application applies to the guest.
"""
import argparse
import base64
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlsplit

import yaml

import cleanup


HC = "hostedclusters.hypershift.openshift.io"
NP = "nodepools.hypershift.openshift.io"
PROVIDERS = {"agent", "aws", "azure", "gcp", "kubevirt", "none", "openstack", "powervs"}
RESERVED = {"name", "namespace", "kubeconfig", "context", "pull-secret", "release-image",
            "release-stream", "node-pool-replicas", "control-plane-availability-policy",
            "infra-availability-policy", "wait", "timeout", "render", "render-into",
            "render-sensitive", "help", "force", "infra-id", "cluster-grace-period"}


class Error(Exception):
    pass


def require(ok, message):
    if not ok:
        raise Error(message)


def private_write(path, data):
    """Atomic replacement; never follow an existing output symlink."""
    path = Path(path)
    require(not path.is_symlink(), f"Refusing symlink: {path}")
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".hcp-")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data.encode() if isinstance(data, str) else data)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def run(argv, *, data=None, log_dir=None, timeout=90, kubeconfig=None, include_stderr=False,
        pass_fds=(), env_overrides=None):
    # Never print CLI errors: Kubernetes admission errors can include Secret bodies.
    env = os.environ.copy()
    env["KUBECONFIG"] = str(kubeconfig) if kubeconfig else os.devnull
    for key, value in (env_overrides or {}).items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    try:
        result = subprocess.run(argv, input=data, text=True, capture_output=True,
                                timeout=timeout, env=env, check=False, pass_fds=pass_fds)
    except subprocess.TimeoutExpired as exc:
        suffix = ""
        if log_dir:
            def decoded(value):
                return value.decode(errors="replace") if isinstance(value, bytes) else value or ""
            fd, log = tempfile.mkstemp(dir=log_dir, prefix="timeout-", suffix=".log")
            with os.fdopen(fd, "w") as stream:
                stream.write(decoded(exc.stdout) + decoded(exc.stderr))
            suffix = f" Private diagnostic log: {log} (may contain credentials)."
        raise Error("Command observation timed out; inspect live state before resuming." + suffix) from None
    except OSError:
        raise Error(f"Cannot execute {Path(argv[0]).name}; check tool installation.") from None
    if result.returncode:
        suffix = ""
        if log_dir:
            fd, log = tempfile.mkstemp(dir=log_dir, prefix="error-", suffix=".log")
            with os.fdopen(fd, "w") as stream:
                stream.write(result.stdout + result.stderr)
            suffix = f" Private diagnostic log: {log} (may contain credentials)."
        raise Error(f"{Path(argv[0]).name} failed with exit {result.returncode}.{suffix}")
    return result.stdout + result.stderr if include_stderr else result.stdout


def json_run(argv, **kwargs):
    try:
        return json.loads(run(argv, **kwargs))
    except json.JSONDecodeError:
        raise Error("CLI returned invalid JSON.") from None


def flag_args(args):
    require(isinstance(args, list), "Provider arguments must be a list.")
    for arg in args:
        require(isinstance(arg, str) and re.fullmatch(r"--[a-zA-Z][a-zA-Z0-9-]*(=[^\r\n]*)?", arg),
                "Use separate --long-flag=value strings; no shell commands or short flags.")
        flag = arg[2:].split("=", 1)[0]
        require(flag not in RESERVED, f"Provider args cannot override --{flag}.")
    return args


def load_profile(path):
    p = json.loads(Path(path).read_text())
    require(isinstance(p, dict), "Profile must be an object.")
    allowed = {"schema_version", "name", "namespace", "provider", "cli", "management",
               "release_image", "pull_secret", "replicas", "create_args", "destroy_args", "infra_id",
               "node_pools", "aws_cleanup"}
    require(not p.keys() - allowed, "Unknown profile fields; check spelling before proceeding.")
    require(p.get("schema_version") == 1, "Unsupported profile schema_version.")
    for field in ("name", "namespace"):
        require(isinstance(p.get(field), str) and len(p[field]) <= 63 and
                re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", p[field]), f"Invalid {field}.")
    require(p.get("provider") in PROVIDERS, "Provider is not in the researched upstream provider set.")
    require(p.get("cli", "hypershift") in ("hypershift", "hcp"), "cli must be hypershift or hcp.")
    m = p.get("management", {})
    require(isinstance(m, dict) and not m.keys() - {"kubeconfig", "context", "kube_system_uid"},
            "Unknown management fields; check profile structure.")
    require(all(isinstance(m.get(k), str) and m[k] for k in ("kubeconfig", "context", "kube_system_uid")),
            "Set management kubeconfig, context, and kube_system_uid.")
    require(Path(m["kubeconfig"]).is_absolute(), "Use an absolute management kubeconfig path.")
    require(isinstance(p.get("pull_secret"), str) and Path(p["pull_secret"]).is_absolute(),
            "Use an absolute pull_secret file path.")
    require(isinstance(p.get("release_image"), str) and
            re.fullmatch(r"[^\s]+@sha256:[a-f0-9]{64}", p["release_image"]),
            "Pin a compatible release_image by sha256 digest.")
    require(type(p.get("replicas")) is int and p["replicas"] >= 0, "replicas must be a nonnegative integer.")
    if "infra_id" in p:
        require(isinstance(p["infra_id"], str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", p["infra_id"]),
                "Invalid infra_id; use the exact ID from the provider infrastructure inventory.")
    for field in ("create_args", "destroy_args"):
        flag_args(p.get(field, []))
    validate_pools(p.get("node_pools"))
    if "aws_cleanup" in p:
        require(p["provider"] == "aws", "aws_cleanup is only valid for AWS.")
        cleanup.validate_aws(p["aws_cleanup"], require)
    return p


def validate_pools(pools):
    if pools is None:
        return
    require(isinstance(pools, list) and bool(pools), "node_pools must be a nonempty list.")
    names = set()
    for pool in pools:
        require(isinstance(pool, dict) and not pool.keys() - {"name", "replicas", "node_selector", "resources"},
                "Unknown node_pools fields.")
        name = pool.get("name")
        require(isinstance(name, str) and re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", name)
                and len(name) <= 63 and name not in names, "Use distinct valid NodePool names.")
        names.add(name)
        require(type(pool.get("replicas")) is int and pool["replicas"] >= 0, "Invalid pool replicas.")
        selector = pool.get("node_selector", {"hypershift.openshift.io/nodePool": name})
        require(isinstance(selector, dict) and bool(selector) and
                all(isinstance(k, str) and k and isinstance(v, str) and v for k, v in selector.items()),
                "Use a nonempty node_selector identifying the pool's guest nodes.")
        require(selector.get("hypershift.openshift.io/nodePool") == name,
                "Pool selectors must retain the HyperShift nodePool label with the exact pool name.")
        resources = pool.get("resources", {})
        require(isinstance(resources, dict) and all(isinstance(k, str) and "/" in k and
                type(v) is int and v > 0 for k, v in resources.items()),
                "Pool resources must map extended resource names to positive integer minima per node.")


def worker_readiness(p, nodes, pools):
    def ready(n):
        return not n.get("metadata", {}).get("deletionTimestamp") and any(
            c.get("type") == "Ready" and c.get("status") == "True"
            for c in n.get("status", {}).get("conditions", []))
    ready_count = sum(ready(n) for n in nodes)
    if not p.get("node_pools"):
        return {"ready_nodes": ready_count, "expected_nodes": p["replicas"],
                "workers_ready": ready_count >= p["replicas"], "pools": []}
    actual = {v["metadata"]["name"]: v for v in pools if v.get("spec", {}).get("clusterName") == p["name"]}
    results, selected = [], set()
    for expected in p["node_pools"]:
        selector = expected.get("node_selector", {"hypershift.openshift.io/nodePool": expected["name"]})
        matches = [n for n in nodes if all(n.get("metadata", {}).get("labels", {}).get(k) == v
                                          for k, v in selector.items())]
        keys = {n["metadata"]["name"] for n in matches}
        require(not selected & keys, "Pool node selectors overlap; a node cannot satisfy two pools.")
        selected |= keys
        def usable(n):
            if not ready(n):
                return False
            alloc = n.get("status", {}).get("allocatable", {})
            return all(str(alloc.get(k, "0")).isdigit() and int(alloc.get(k, "0")) >= v
                       for k, v in expected.get("resources", {}).items())
        live = actual.get(expected["name"], {})
        count = sum(usable(n) for n in matches)
        ok = (bool(live) and not live["metadata"].get("deletionTimestamp") and
              live["spec"].get("replicas") == expected["replicas"] and count >= expected["replicas"])
        results.append({"name": expected["name"], "expected": expected["replicas"],
                        "observed_replicas": live.get("spec", {}).get("replicas"),
                        "exists": bool(live), "deleting": bool(live.get("metadata", {}).get("deletionTimestamp")),
                        "usable_nodes": count, "ready": ok})
    # An unlisted active pool would make the expected topology incomplete.
    complete = set(actual) == {v["name"] for v in results}
    return {"ready_nodes": ready_count, "expected_nodes": sum(v["replicas"] for v in p["node_pools"]),
            "workers_ready": complete and all(v["ready"] for v in results), "pools": results,
            "pool_inventory_complete": complete}


def lifecycle_command(p, action):
    argv = [p.get("cli", "hypershift"), action, "cluster", p["provider"],
            f"--namespace={p['namespace']}", f"--name={p['name']}"]
    if p.get("infra_id"):
        argv.append(f"--infra-id={p['infra_id']}")
    if action == "create":
        argv += [f"--release-image={p['release_image']}", f"--pull-secret={p['pull_secret']}",
                 f"--node-pool-replicas={p['replicas']}", "--control-plane-availability-policy=SingleReplica",
                 "--infra-availability-policy=SingleReplica"]
    return argv + p.get(f"{action}_args", [])


def check_guest_credentials(config):
    require(isinstance(config, dict) and isinstance(config.get("users", []), list),
            "Guest kubeconfig must contain embedded credentials.")
    # Repeat this check when reusing saved credentials, before invoking oc with them.
    for entry in config.get("users", []):
        require(isinstance(entry, dict) and isinstance(entry.get("user", {}), dict),
                "Guest kubeconfig must contain embedded credentials.")
        require(not ({"exec", "auth-provider", "tokenFile", "client-key", "client-certificate"} &
                     entry.get("user", {}).keys()),
                "Guest credentials must be embedded, without executable plugins or file references.")


class Session:
    def __init__(self, p, directory):
        self.p = p
        self.directory = Path(directory).absolute()
        require(not self.directory.is_symlink(), "State directory cannot be a symlink.")
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        require(self.directory.stat().st_uid == os.getuid(), "State directory belongs to another user.")
        os.chmod(self.directory, 0o700)
        self.binding_file = self.directory / "identity.json"
        self.binding = json.loads(self.binding_file.read_text()) if self.binding_file.exists() else {}

    def oc(self, *args, guest=False, **kwargs):
        if guest:
            base = ["oc", f"--kubeconfig={self.directory / 'guest.kubeconfig'}",
                    f"--context={self.binding['guest_context']}"]
        else:
            m = self.p["management"]
            base = ["oc", f"--kubeconfig={m['kubeconfig']}", f"--context={m['context']}"]
        return run(base + ["--request-timeout=30s", *args], log_dir=self.directory, **kwargs)

    def external(self, argv, **kwargs):
        return run(argv, log_dir=self.directory, **kwargs)

    def get(self, resource, name=None, guest=False, namespace=None, optional=False):
        args = ["get", resource]
        if name:
            args.append(name)
        if namespace:
            args += ["--namespace", namespace]
        args += ["-o", "json"]
        if optional:
            args += ["--ignore-not-found"]
        raw = self.oc(*args, guest=guest)
        return json.loads(raw) if raw.strip() else None

    def management(self):
        uid = self.get("namespace", "kube-system")["metadata"]["uid"]
        require(uid == self.p["management"]["kube_system_uid"], "Management cluster UID mismatch; stopping.")
        key = {"management_uid": uid, "namespace": self.p["namespace"], "name": self.p["name"]}
        require(all(self.binding.get(k, v) == v for k, v in key.items()),
                "State directory is bound to another cluster; use the correct directory.")
        self.binding.update(key)
        return uid

    def save(self):
        # Read-only status observations may run alongside lifecycle/access. Merge
        # under a short, separate lock so a stale observer cannot erase UID pins.
        with self.lock("identity.lock", blocking=True):
            current = json.loads(self.binding_file.read_text()) if self.binding_file.exists() else {}
            for key in ("management_uid", "namespace", "name", "hostedcluster_uid", "guest_context", "guest_uid"):
                require(key not in current or key not in self.binding or current[key] == self.binding[key],
                        "Saved identity changed during this operation; inspect before continuing.")
            merged = {**current, **self.binding}
            if current.get("create_attempted"):
                merged["create_attempted"] = True
            private_write(self.binding_file, json.dumps(merged, indent=2) + "\n")
            self.binding = merged

    @contextmanager
    def lock(self, name="lifecycle.lock", blocking=False):
        path = self.directory / name
        fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
            except BlockingIOError:
                raise Error("A lifecycle/inventory operation is active in this state directory.") from None
            yield fd
        finally:
            # Closing, rather than explicit LOCK_UN, retains the lock if a native
            # child survives its parent. The child inherits this same description.
            os.close(fd)

    def fingerprint(self):
        fields = {k: self.p.get(k) for k in ("name", "namespace", "provider", "cli", "management",
                                            "infra_id", "destroy_args", "aws_cleanup")}
        return hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest()

    def inventory(self, skip_guest=False):
        with self.lock():
            self.management()
            hc = self.hc()
            require(not hc["metadata"].get("deletionTimestamp"), "Deletion already started; retain the original inventory.")
            require(not (self.directory / "destroy-operation.json").exists(), "Destroy receipt exists; do not replace its inventory.")
            require(self.p.get("infra_id") == hc["spec"].get("infraID") and self.p.get("infra_id"),
                    "Set profile infra_id from the live HostedCluster before recording teardown inventory.")
            result = cleanup.capture(self, hc, skip_guest, require)
            result["fingerprint"] = self.fingerprint()
            private_write(self.directory / "teardown-inventory.json", json.dumps(result, indent=2) + "\n")
            self.save()
            return {"inventory_saved": True, "path": str(self.directory / "teardown-inventory.json"),
                    "guest_storage_observed": result["guest_storage_observed"],
                    "cloud_automated": result["cloud"] is not None,
                    "next": "Review owned/shared resources and coverage before destroy --execute."}

    def teardown_inventory(self):
        path = self.directory / "teardown-inventory.json"
        require(path.is_file(), "Record and review inventory before destroy or cleanup verification.")
        raw = path.read_bytes()
        data = json.loads(raw)
        require(data["fingerprint"] == self.fingerprint(), "Teardown profile changed; do not reuse the recorded ownership plan.")
        require(data["target"] == {"management_uid": self.binding["management_uid"],
                "namespace": self.p["namespace"], "name": self.p["name"],
                "hostedcluster_uid": self.binding.get("hostedcluster_uid"),
                "infra_id": self.p.get("infra_id"), "provider": self.p["provider"]},
                "Teardown inventory identity does not match the saved target.")
        return data, hashlib.sha256(raw).hexdigest()

    def verify_cleanup(self):
        with self.lock():
            self.management()
            inventory, digest = self.teardown_inventory()
            operation = self.directory / "destroy-operation.json"
            require(operation.is_file(), "No recorded destroy attempt; inspect the target before cleanup verification.")
            record = json.loads(operation.read_text())
            require(record["inventory_digest"] == digest and record["target"] == inventory["target"],
                    "Destroy inventory/receipt identity was modified.")
            result = cleanup.verify(self, inventory, require)
            private_write(self.directory / "cleanup-verification.json", json.dumps(result, indent=2) + "\n")
            if result["cleanup_verified"]:
                (self.directory / "guest.kubeconfig").unlink(missing_ok=True)
                result["guest_kubeconfig_removed"] = True
                private_write(self.directory / "cleanup-complete.json", json.dumps(result, indent=2) + "\n")
            return result

    def hc(self, optional=False):
        hc = self.get(HC, self.p["name"], namespace=self.p["namespace"], optional=optional)
        if hc:
            uid = hc["metadata"]["uid"]
            require(self.binding.get("hostedcluster_uid", uid) == uid,
                    "HostedCluster was replaced; the saved identity no longer matches.")
            expected = self.p["provider"].lower()
            require(hc["spec"]["platform"]["type"].lower() == expected, "HostedCluster provider mismatch.")
            require(not self.p.get("infra_id") or hc["spec"].get("infraID") == self.p["infra_id"],
                    "HostedCluster infra ID does not match the profile inventory.")
            self.binding["hostedcluster_uid"] = uid
        return hc

    def status(self):
        self.management()
        hc = self.hc(optional=True)
        if not hc:
            return {"exists": False, "name": self.p["name"]}
        self.save()
        pools = self.get(NP, namespace=self.p["namespace"])["items"]
        return summarize(hc, pools)

    def check_help(self, action, command=None):
        help_text = run([self.p.get("cli", "hypershift"), action, "cluster", self.p["provider"], "--help"],
                        log_dir=self.directory)
        # Check every requested flag, including helper-owned flags, against the installed CLI.
        for arg in (command or lifecycle_command(self.p, action))[4:]:
            name = arg.split("=", 1)[0]
            require(re.search(re.escape(name) + r"(?:[\s=]|$)", help_text),
                    f"Installed CLI does not advertise {name}; adapt the profile/CLI before mutation.")

    def lifecycle(self, action, resume=False, grace_period=None):
        with self.lock() as fd:
            return self._lifecycle(action, resume, grace_period, fd)

    def _lifecycle(self, action, resume, grace_period, lock_fd):
        self.management()
        hc = self.hc(optional=True)
        command = lifecycle_command(self.p, action)
        operation_path = self.directory / "destroy-operation.json"
        operation = None
        cloud_env = None
        if action == "create":
            require(not hc, "HostedCluster already exists; inspect status/access instead of recreating.")
            require(not self.binding.get("create_attempted") and not (self.directory / "create-attempt.json").exists(),
                    "A create was already attempted. Inspect management AND provider resources before an explicit retry.")
            require(Path(self.p["pull_secret"]).is_file(), "Pull-secret file is missing.")
            # Shared namespace provisioning is an administrator prerequisite.
            self.get("namespace", self.p["namespace"])
            self.get("customresourcedefinition", HC)
            self.get("customresourcedefinition", NP)
        else:
            if not resume:
                require(hc is not None, "HostedCluster missing; do not infer infrastructure cleanup from a name.")
                require(not hc["metadata"].get("deletionTimestamp"), "Deletion is already in progress; inspect status and the destroy receipt.")
                require(not operation_path.exists(), "Destroy already attempted; inspect its receipt and use --resume when appropriate.")
            inventory, digest = self.teardown_inventory()
            if hc:
                require(inventory["provider_spec_digest"] == cleanup.digest({"platform": hc["spec"]["platform"],
                        "dns": hc["spec"].get("dns")}), "HostedCluster provider/DNS specification changed since inventory.")
            if resume:
                require(operation_path.is_file(), "Resume requires a recorded destroy attempt for this target.")
                operation = json.loads(operation_path.read_text())
                require(operation["inventory_digest"] == digest and operation["target"] == inventory["target"],
                        "Destroy inventory/receipt identity was modified.")
                require(operation.get("attempts") and operation["attempts"][-1]["outcome"] != "cli_succeeded",
                        "CLI already succeeded; run verify-cleanup instead of repeating destroy.")
                require(not (self.directory / "cleanup-complete.json").exists(), "Cleanup is already verified; no destroy to resume.")
                require(hc is not None or (self.p["provider"] == "aws" and self.p.get("aws_cleanup")),
                        "Resume after HC disappearance requires the configured AWS ownership adapter; use a separate provider recovery plan.")
            else:
                operation = {"inventory_digest": digest, "target": inventory["target"], "attempts": []}
            if grace_period is not None:
                require(type(grace_period) is int and 0 < grace_period <= 86400, "Use a grace period of 1..86400 seconds.")
                command.append(f"--cluster-grace-period={grace_period}s")
            if self.p.get("aws_cleanup"):
                cfg = self.p["aws_cleanup"]
                require(cfg.get("ownership_reviewed", False), "Review the AWS ownership manifest before destroy.")
                options = {v.split("=", 1)[0]: v.split("=", 1)[1] if "=" in v else "true"
                           for v in self.p.get("destroy_args", [])}
                require(options.get("--region") == cfg["region"], "AWS destroy_args must explicitly match the cleanup region.")
                require(not {"--secret-creds", "--vpc-owner-aws-creds"} & options.keys(),
                        "Credential-secret/cross-account deletion needs a separate provider plan; the AWS adapter uses one account.")
                if "--role-arn" in options:
                    role = re.fullmatch(r"arn:[^:]+:iam::([0-9]{12}):role/.+", options["--role-arn"])
                    require(role and role.group(1) == cfg["account_id"], "Destroy role account does not match cleanup account.")
                cloud_env = cleanup.check_aws_account(self, cfg, require)
        self.check_help(action, command)
        # HyperShift's lifecycle CLI may not support --context. Give it a private,
        # flattened single-context config, never the caller's ambient current-context.
        raw = self.oc("config", "view", "--minify", "--flatten", "--raw", "-o", "json")
        config = json.loads(raw)
        require(config.get("current-context") == self.p["management"]["context"],
                "Minified management kubeconfig has an unexpected context.")
        with tempfile.TemporaryDirectory(prefix="management-", dir=self.directory) as tmp:
            kc = Path(tmp) / "config"
            private_write(kc, raw)
            if action == "create":
                self.binding["create_attempted"] = True
                private_write(self.directory / "create-attempt.json", json.dumps({
                    "at": cleanup.now(), "management_uid": self.binding["management_uid"],
                    "namespace": self.p["namespace"], "name": self.p["name"], "provider": self.p["provider"]}) + "\n")
            self.save()
            if operation is not None:
                operation["attempts"].append({"started_at": cleanup.now(), "outcome": "observation_lost",
                                              "grace_period_seconds": grace_period})
                private_write(operation_path, json.dumps(operation, indent=2) + "\n")
            # Output may include passwords or secrets. Retain it locally, not in the conversation.
            try:
                output = run(command, kubeconfig=kc, log_dir=self.directory,
                             timeout=max(3600, (grace_period or 0) + 1800), include_stderr=True,
                             pass_fds=(lock_fd,), env_overrides=cloud_env)
            except (Error, KeyboardInterrupt):
                if operation is not None:
                    operation["attempts"][-1].update(outcome="cli_failed", finished_at=cleanup.now())
                    private_write(operation_path, json.dumps(operation, indent=2) + "\n")
                raise
            if operation is not None:
                operation["attempts"][-1].update(outcome="cli_succeeded", finished_at=cleanup.now())
                private_write(operation_path, json.dumps(operation, indent=2) + "\n")
            private_write(self.directory / f"{action}.log", output)
        return {"submitted": action, "name": self.p["name"],
                "next": "Run verify-cleanup; CLI exit alone does not prove cleanup." if action == "destroy"
                        else "Inspect status; CLI exit alone does not prove readiness."}

    def access(self):
        self.management()
        hc = self.hc()
        require(not hc["metadata"].get("deletionTimestamp"), "HostedCluster is deleting.")
        secret_name = hc.get("status", {}).get("kubeconfig", {}).get("name")
        require(secret_name, "HostedCluster has not published status.kubeconfig.name yet.")
        secret = self.get("secret", secret_name, namespace=self.p["namespace"])
        try:
            raw = base64.b64decode(secret["data"]["kubeconfig"], validate=True)
            config = yaml.safe_load(raw)
        except (KeyError, ValueError, yaml.YAMLError):
            raise Error("The published Secret does not contain a valid kubeconfig.") from None
        check_guest_credentials(config)
        context = config.get("current-context")
        require(context, "Guest kubeconfig has no current-context.")
        require(not self.binding.get("guest_context") or self.binding["guest_context"] == context,
                "Guest context changed; inspect credentials before rebinding.")
        self.binding["guest_context"] = context
        private_write(self.directory / "guest.kubeconfig", raw)
        result = self.verify_guest(pin=True)
        self.save()
        return result

    def verify_guest(self, pin=False):
        management_uid = self.management()
        hc = self.hc()
        require(not hc["metadata"].get("deletionTimestamp"), "HostedCluster is deleting.")
        require(self.binding.get("guest_context"), "Run access first.")
        config = yaml.safe_load((self.directory / "guest.kubeconfig").read_text())
        check_guest_credentials(config)
        contexts = [c for c in config.get("contexts", []) if c["name"] == self.binding["guest_context"]]
        require(len(contexts) == 1, "Guest context is missing or ambiguous.")
        clusters = [c["cluster"] for c in config.get("clusters", [])
                    if c["name"] == contexts[0]["context"]["cluster"]]
        require(len(clusters) == 1, "Guest cluster configuration is missing or ambiguous.")
        cluster = clusters[0]
        endpoint = urlsplit(cluster.get("server", ""))
        expected = hc.get("status", {}).get("controlPlaneEndpoint", {})
        require(endpoint.scheme == "https" and endpoint.hostname == expected.get("host") and
                (endpoint.port or 443) == expected.get("port"),
                "Guest API does not match HostedCluster status.controlPlaneEndpoint.")
        require(not cluster.get("insecure-skip-tls-verify") and cluster.get("certificate-authority-data"),
                "Guest kubeconfig must embed the cluster CA and verify TLS.")
        uid = self.get("namespace", "kube-system", guest=True)["metadata"]["uid"]
        require(uid != management_uid, "Guest resolves to the management cluster; refusing application operations.")
        require(self.binding.get("guest_uid", uid if pin else None) == uid, "Guest UID mismatch; run access for initial verification.")
        self.binding["guest_uid"] = uid
        # A successful request through credentials taken from this exact HC is the
        # initial association; UID pins detect later credential/context replacement.
        self.oc("get", "--raw=/readyz", guest=True)
        nodes = self.get("nodes", guest=True)["items"]
        pools = self.get(NP, namespace=self.p["namespace"])["items"] if self.p.get("node_pools") else []
        return {"guest_verified": True, "guest_uid": uid, **worker_readiness(self.p, nodes, pools),
                "kubeconfig": str(self.directory / "guest.kubeconfig")}

    def deploy(self, manifest, namespace, execute):
        verification = self.verify_guest()
        require(verification["workers_ready"] and verification["ready_nodes"] >= 1,
                "Guest worker pools/resources are not ready for applications.")
        require(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", namespace) and len(namespace) <= 63,
                "Invalid application namespace.")
        require(not namespace.startswith(("kube-", "openshift", "hypershift")) and namespace != "default",
                "Use a dedicated application namespace.")
        docs = [doc for doc in yaml.safe_load_all(Path(manifest).read_text()) if doc is not None]
        require(docs and all(isinstance(d, dict) for d in docs), "Supply at least one rendered Kubernetes object.")
        discovery = {}
        for doc in docs:
            api = doc.get("apiVersion", "")
            require(re.fullmatch(r"[a-zA-Z0-9./-]+", api), "Invalid apiVersion.")
            if api not in discovery:
                endpoint = f"/api/{api}" if "/" not in api else f"/apis/{api}"
                discovery[api] = json.loads(self.oc("get", f"--raw={endpoint}", guest=True))["resources"]
            matches = [r for r in discovery[api] if r["kind"] == doc.get("kind") and "/" not in r["name"]]
            require(len(matches) == 1 and matches[0].get("namespaced"),
                    "Application helper only accepts discovered namespaced resources; separate platform changes need their own plan.")
            metadata = doc.setdefault("metadata", {})
            require(metadata.get("namespace", namespace) == namespace, "Manifest targets a different namespace.")
            require(not metadata.get("generateName") and metadata.get("name"), "Apply requires metadata.name.")
            metadata["namespace"] = namespace
        # Namespace creation is deliberate and guest-only. Dry-run validates both
        # namespace and workload, but does not claim an absent namespace can be used.
        ns = json.dumps({"apiVersion": "v1", "kind": "Namespace", "metadata": {"name": namespace}})
        self.oc("apply", "--dry-run=server", "-f", "-", guest=True, data=ns)
        if execute:
            self.oc("apply", "-f", "-", guest=True, data=ns)
        else:
            require(self.get("namespace", namespace, guest=True, optional=True),
                    "Guest namespace is absent. Use --execute after review; it creates the namespace before workload validation.")
        payload = yaml.safe_dump_all(docs)
        self.oc("apply", "--dry-run=server", "--validate=strict", "-f", "-", guest=True, data=payload)
        if execute:
            self.oc("apply", "--validate=strict", "-f", "-", guest=True, data=payload)
        return {"application_namespace": namespace, "objects": len(docs), "applied": execute,
                "next": "Verify rollout and application-specific smoke tests on the guest."}


def summarize(hc, pools):
    status = hc.get("status", {})
    # Exclude arbitrary condition messages, which may carry sensitive provider data.
    conditions = [{k: c[k] for k in ("type", "status", "reason", "observedGeneration") if k in c}
                  for c in status.get("conditions", [])]
    return {"exists": True, "name": hc["metadata"]["name"], "uid": hc["metadata"]["uid"],
            "deleting": bool(hc["metadata"].get("deletionTimestamp")),
            "generation": hc["metadata"].get("generation"), "conditions": conditions,
            "kubeconfig_published": bool(status.get("kubeconfig", {}).get("name")),
            "nodepools": [{"name": n["metadata"]["name"], "desired": n["spec"].get("replicas"),
                           "current": n.get("status", {}).get("replicas", 0)}
                          for n in pools if n.get("spec", {}).get("clusterName") == hc["metadata"]["name"]]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--state-dir", help="Private credentials and identity directory (default .hcp-runs/namespace-name)")
    subs = parser.add_subparsers(dest="command", required=True)
    plan = subs.add_parser("plan", help="Local command preview; never executes provider or cluster commands")
    plan.add_argument("--action", choices=("create", "destroy"), default="create")
    subs.add_parser("preflight", help="Read-only target, CRD, namespace, CLI, and RBAC checks")
    for command in ("create", "destroy"):
        sp = subs.add_parser(command)
        sp.add_argument("--execute", action="store_true", help="Perform the already-authorized operation")
        if command == "destroy":
            sp.add_argument("--resume", action="store_true", help="Resume only a recorded destroy attempt")
            sp.add_argument("--cluster-grace-period", type=int, help="Native CLI wait in seconds, checked against installed help")
    inventory = subs.add_parser("inventory", help="Record read-only ownership, storage and preservation inventory")
    inventory.add_argument("--skip-guest", action="store_true", help="Capture partial inventory when guest API is unavailable")
    subs.add_parser("verify-cleanup", help="Read-only API/cloud checks; removes local guest kubeconfig only after complete verification")
    subs.add_parser("status")
    subs.add_parser("access")
    subs.add_parser("verify-guest")
    wait = subs.add_parser("wait")
    wait.add_argument("--timeout", type=int, default=1800)
    wait.add_argument("--interval", type=int, default=20)
    deploy = subs.add_parser("deploy")
    deploy.add_argument("--manifest", required=True, help="Rendered YAML file (no Helm/Kustomize execution)")
    deploy.add_argument("--namespace", required=True)
    deploy.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    p = load_profile(args.profile)
    if args.command == "plan" or (args.command in ("create", "destroy") and not args.execute):
        action = args.action if args.command == "plan" else args.command
        command = lifecycle_command(p, action)
        if getattr(args, "cluster_grace_period", None) is not None:
            require(0 < args.cluster_grace_period <= 86400, "Use a grace period of 1..86400 seconds.")
            command.append(f"--cluster-grace-period={args.cluster_grace_period}s")
        print(json.dumps({"action": action, "command": shlex.join(command),
                          "resume": getattr(args, "resume", False),
                          "environment": {"KUBECONFIG": "<private-pinned-management-kubeconfig>"},
                          "management_context": p["management"]["context"],
                          "management_uid": p["management"]["kube_system_uid"],
                          "executed": False, "note": "Review provider infrastructure/IAM/DNS costs and ownership separately. No render/create command was run."}, indent=2))
        return
    s = Session(p, args.state_dir or f".hcp-runs/{p['namespace']}-{p['name']}")
    if args.command == "preflight":
        s.management()
        s.get("customresourcedefinition", HC)
        s.get("customresourcedefinition", NP)
        s.get("namespace", p["namespace"])
        s.check_help("create")
        for verb, resource in (("create", HC), ("get", HC), ("create", NP), ("get", "secrets")):
            require(s.oc("auth", "can-i", verb, resource, "--namespace", p["namespace"]).strip() == "yes",
                    "Missing management permissions; ask the administrator for scoped access.")
        require(Path(p["pull_secret"]).is_file(), "Pull-secret file is missing.")
        result = {"preflight": "passed", "provider_checks": "Agent must complete references/providers.md before create."}
    elif args.command in ("create", "destroy"):
        result = s.lifecycle(args.command, getattr(args, "resume", False), getattr(args, "cluster_grace_period", None))
    elif args.command == "inventory":
        result = s.inventory(args.skip_guest)
    elif args.command == "verify-cleanup":
        result = s.verify_cleanup()
    elif args.command == "status":
        result = s.status()
    elif args.command == "access":
        result = s.access()
    elif args.command == "verify-guest":
        result = s.verify_guest()
    elif args.command == "deploy":
        result = s.deploy(args.manifest, args.namespace, args.execute)
    elif args.command == "wait":
        require(args.timeout > 0 and 1 <= args.interval <= 60, "Use a positive timeout and interval 1..60 seconds.")
        deadline = time.monotonic() + args.timeout
        while True:
            status = s.status()
            print(json.dumps(status), flush=True)
            require(status["exists"] and not status["deleting"], "Cluster is missing or deleting; inspect before continuing.")
            available = any(c["type"] == "Available" and c["status"] == "True" and
                            c.get("observedGeneration") == status["generation"] for c in status["conditions"])
            if available and status["kubeconfig_published"]:
                # Do not suppress auth/network failures as ordinary pending state.
                result = s.access()
                if result["workers_ready"]:
                    break
            require(time.monotonic() < deadline, "Readiness deadline reached; cluster may still be reconciling. Inspect status; do not recreate.")
            time.sleep(min(args.interval, max(0, deadline - time.monotonic())))
    print(json.dumps(result, indent=2))
    if args.command == "verify-cleanup" and not result["cleanup_verified"]:
        sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except (Error, OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
        # Only Error strings are controlled; parser exceptions can echo credential data.
        print(f"error: {exc if isinstance(exc, Error) else 'Invalid input or unexpected API response; inspect private files locally.'}", file=sys.stderr)
        sys.exit(1)

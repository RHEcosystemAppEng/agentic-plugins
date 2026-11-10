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
import socket
import stat
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlsplit
import uuid

import yaml

import cleanup


HC = "hostedclusters.hypershift.openshift.io"
NP = "nodepools.hypershift.openshift.io"
PROVIDERS = {"agent", "aws", "azure", "gcp", "kubevirt", "none", "openstack", "powervs"}
RESERVED = {"name", "namespace", "kubeconfig", "context", "pull-secret", "secret-creds",
            "sts-creds", "aws-creds", "release-image",
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
        # mkstemp already uses 0600 on POSIX; enforce it explicitly so a
        # platform default or umask can never widen secret-bearing files.
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data.encode() if isinstance(data, str) else data)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


# Pass only ambient variables the provider/management CLIs need. This avoids
# handing unrelated host secrets (tokens, unrelated cloud accounts) to child
# processes while still supporting the documented ambient credential modes.
ENV_PASSTHROUGH = {
    "PATH", "HOME", "USER", "LOGNAME", "SHELL", "LANG", "LC_ALL", "LC_CTYPE", "TZ",
    "TMPDIR", "TEMP", "TMP", "SSL_CERT_FILE", "SSL_CERT_DIR",
    "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME",
    "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "ALL_PROXY",
    "http_proxy", "https_proxy", "no_proxy", "all_proxy", "KUBECONFIG",
}
ENV_PASSTHROUGH_PREFIXES = (
    "AWS_", "AZURE_", "ARM_", "GOOGLE_", "GCLOUD_", "CLOUDSDK_",
    "OS_", "OPENSTACK_", "IBMCLOUD_", "IC_", "HYPERSHIFT_",
)


def base_environment():
    return {key: value for key, value in os.environ.items()
            if key in ENV_PASSTHROUGH or key.startswith(ENV_PASSTHROUGH_PREFIXES)}


def run(argv, *, data=None, log_dir=None, timeout=90, kubeconfig=None, include_stderr=False,
        pass_fds=(), env_overrides=None):
    # Never print CLI errors: Kubernetes admission errors can include Secret bodies.
    env = base_environment()
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
            os.fchmod(fd, 0o600)
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
            os.fchmod(fd, 0o600)
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


ENVIRONMENT_REFERENCE = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))")


def expand_profile_values(value, active=None):
    """Expand environment references in profile strings without shell evaluation."""
    active = set() if active is None else active
    if isinstance(value, str):
        def replacement(match):
            name = match.group(1) or match.group(2)
            require(name in os.environ, f"Profile references unset environment variable: {name}")
            return os.environ[name]
        return ENVIRONMENT_REFERENCE.sub(replacement, value)
    if isinstance(value, list):
        require(id(value) not in active, "Profile contains a recursive YAML alias.")
        active.add(id(value))
        try:
            return [expand_profile_values(item, active) for item in value]
        finally:
            active.remove(id(value))
    if isinstance(value, dict):
        require(all(isinstance(key, str) for key in value),
                "Profile mapping keys must be strings.")
        require(id(value) not in active, "Profile contains a recursive YAML alias.")
        active.add(id(value))
        try:
            return {key: expand_profile_values(item, active) for key, item in value.items()}
        finally:
            active.remove(id(value))
    return value


def load_profile(path):
    profile_path = Path(path)
    try:
        raw = profile_path.read_text()
        document = yaml.safe_load(raw) if profile_path.suffix.lower() in (".yaml", ".yml") else json.loads(raw)
    except OSError as exc:
        raise Error(f"Unable to read profile: {exc}") from exc
    except (json.JSONDecodeError, yaml.YAMLError):
        raise Error("Profile is not valid JSON or YAML.") from None
    p = expand_profile_values(document)
    require(isinstance(p, dict), "Profile must be an object.")
    allowed = {"schema_version", "name", "namespace", "provider", "cli", "management", "cloud_identity",
               "release_image", "pull_secret", "secret_creds", "replicas", "create_args", "destroy_args", "infra_id",
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
    cloud_identity = p.get("cloud_identity")
    if cloud_identity is not None:
        require(isinstance(cloud_identity, dict) and not cloud_identity.keys() - {"kind", "account_id", "region", "project"},
                "Unknown cloud_identity fields; check profile structure.")
        require(isinstance(cloud_identity.get("kind"), str) and cloud_identity["kind"] in
                {"aws", "azure", "gcp", "openstack", "powervs"}, "Unsupported cloud_identity kind.")
        required = {"aws": ("account_id", "region"), "azure": ("account_id",),
                    "gcp": ("project",), "openstack": ("project",), "powervs": ("account_id",)}[cloud_identity["kind"]]
        require(all(isinstance(cloud_identity.get(k), str) and cloud_identity[k] for k in required),
                f"cloud_identity requires {', '.join(required)}.")
        if cloud_identity["kind"] == "aws":
            require(re.fullmatch(r"\d{12}", cloud_identity["account_id"]), "AWS cloud_identity account_id must contain 12 digits.")
    pull_secret = p.get("pull_secret")
    secret_creds = p.get("secret_creds")
    require((pull_secret is None) != (secret_creds is None),
            "Set exactly one of pull_secret or secret_creds.")
    if pull_secret is not None:
        require(isinstance(pull_secret, str) and Path(pull_secret).is_absolute(),
                "Use an absolute pull_secret file path.")
    else:
        require(p["provider"] == "aws", "secret_creds is currently supported only for the AWS provider.")
        require(isinstance(secret_creds, str) and
                re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", secret_creds),
                "Use a valid Kubernetes Secret name for secret_creds.")
    require(isinstance(p.get("release_image"), str) and
            re.fullmatch(r"[^\s]+@sha256:[a-f0-9]{64}", p["release_image"]),
            "Pin a compatible release_image by sha256 digest.")
    require(type(p.get("replicas")) is int and p["replicas"] >= 0, "replicas must be a nonnegative integer.")
    if "infra_id" in p:
        require(isinstance(p["infra_id"], str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", p["infra_id"]),
                "Invalid infra_id; use the exact ID from the provider infrastructure inventory.")
    for field in ("create_args", "destroy_args"):
        flag_args(p.get(field, []))
    if secret_creds:
        # The native AWS CLI requires an assumed role ARN when it takes
        # credentials from a management-cluster Secret instead of a file.
        for field in ("create_args", "destroy_args"):
            require(any(arg.startswith("--role-arn=") for arg in p.get(field, [])),
                    "AWS secret_creds mode requires --role-arn in create_args and destroy_args.")
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


def lifecycle_command(p, action, pull_secret=None, sts_creds=None):
    argv = [p.get("cli", "hypershift"), action, "cluster", p["provider"],
            f"--namespace={p['namespace']}", f"--name={p['name']}"]
    if p.get("infra_id"):
        argv.append(f"--infra-id={p['infra_id']}")
    if sts_creds:
        argv.append(f"--sts-creds={sts_creds}")
    if p.get("secret_creds"):
        argv.append(f"--secret-creds={p['secret_creds']}")
    if action == "create":
        # The native AWS CLI requires --pull-secret even when secret-creds
        # carries the pull-secret key, so materialize it from the Secret.
        if pull_secret:
            argv.append(f"--pull-secret={pull_secret}")
        argv += [f"--release-image={p['release_image']}",
                 f"--node-pool-replicas={p['replicas']}", "--control-plane-availability-policy=SingleReplica",
                 "--infra-availability-policy=SingleReplica"]
    return argv + p.get(f"{action}_args", [])


def check_guest_credentials(config):
    require(isinstance(config, dict), "Guest kubeconfig must contain embedded credentials.")
    users = config.get("users")
    require(isinstance(users, list) and users,
            "Guest kubeconfig must contain embedded credentials.")
    embedded = set()
    # Repeat this check when reusing saved credentials, before invoking oc with them.
    for entry in users:
        require(isinstance(entry, dict) and isinstance(entry.get("user"), dict),
                "Guest kubeconfig must contain embedded credentials.")
        user = entry["user"]
        require(not ({"exec", "auth-provider", "tokenFile", "client-key", "client-certificate"} &
                     user.keys()),
                "Guest credentials must be embedded, without executable plugins or file references.")
        if (user.get("token") or
                (user.get("client-certificate-data") and user.get("client-key-data")) or
                (user.get("username") and user.get("password"))):
            embedded.add(entry.get("name"))
    require(embedded, "Guest credentials must be embedded, without executable plugins or file references.")
    referenced = {c["context"].get("user") for c in config.get("contexts") or []
                  if isinstance(c, dict) and isinstance(c.get("context"), dict)
                  and c["context"].get("user")}
    require(not referenced - embedded,
            "Guest kubeconfig references a user without embedded credentials.")


def provider_options(args):
    return {value.split("=", 1)[0]: value.split("=", 1)[1] if "=" in value else "true"
            for value in args}


def reject_credential_overrides(provider, args):
    overrides = {
        "aws": {"--sts-creds", "--vpc-owner-aws-creds", "--aws-credentials-file", "--aws-creds"},
        "gcp": {"--service-account", "--service-account-key-file", "--impersonate-service-account"},
        "openstack": {"--openstack-credentials-file", "--openstack-cloud"},
    }.get(provider, set())
    require(not provider_options(args).keys() & overrides,
            "Unsupported provider credential override; use a validated ambient/mode-specific credential path.")


def make_private_parents(path):
    """Create missing ancestor directories 0700; never chmod existing ones."""
    missing = []
    current = path
    while not current.exists():
        missing.append(current)
        parent = current.parent
        if parent == current:
            break
        current = parent
    for item in reversed(missing):
        try:
            item.mkdir(mode=0o700)
        except FileExistsError:
            # Another actor created it concurrently; leave their permissions.
            pass


class Session:
    def __init__(self, p, directory):
        self.p = p
        self.directory = Path(directory).absolute()
        # Secret-bearing state must not live under a world-listable directory we
        # created ourselves; an existing user-chosen parent is left untouched.
        make_private_parents(self.directory.parent)
        try:
            os.mkdir(self.directory, 0o700)
        except FileExistsError:
            pass
        # Verify the directory we actually opened rather than a path that a
        # concurrent actor could have replaced with a symlink after the check.
        try:
            fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        except OSError:
            raise Error("State directory must be a real directory owned by this user, not a symlink.") from None
        try:
            info = os.fstat(fd)
            require(stat.S_ISDIR(info.st_mode), "State path is not a directory.")
            require(info.st_uid == os.getuid(), "State directory belongs to another user.")
            os.fchmod(fd, 0o700)
        finally:
            os.close(fd)
        self.binding_file = self.directory / "identity.json"
        self.binding = json.loads(self.binding_file.read_text()) if self.binding_file.exists() else {}
        self.shared_state = {}
        self.shared_lock_active = False
        self.lock_holder = None
        self._locks = {}

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

    def credential_secret(self):
        require(self.p.get("secret_creds"), "Secret credential mode is not selected.")
        secret = self.get("secret", self.p["secret_creds"], namespace=self.p["namespace"])
        data = secret.get("data")
        require(isinstance(data, dict) and data, "Credential Secret has no data.")
        return data

    def decode_secret_key(self, data, key):
        value = data.get(key)
        require(isinstance(value, str) and value, f"Credential Secret is missing {key}.")
        try:
            return base64.b64decode(value, validate=True).decode()
        except (ValueError, UnicodeDecodeError):
            raise Error(f"Credential Secret {key} is not valid base64 text.") from None

    def aws_session_credentials(self):
        data = self.credential_secret()
        if "aws_access_key_id" in data:
            # Native HyperShift credential Secret (multi-cluster engine format).
            access_key = self.decode_secret_key(data, "aws_access_key_id")
            secret_key = self.decode_secret_key(data, "aws_secret_access_key")
            session_token = self.decode_secret_key(data, "aws_session_token")
        else:
            try:
                payload = json.loads(self.decode_secret_key(data, "sts-creds"))
                credentials = payload.get("Credentials", payload)
                access_key = credentials["AccessKeyId"]
                secret_key = credentials["SecretAccessKey"]
                session_token = credentials["SessionToken"]
            except (KeyError, TypeError, json.JSONDecodeError):
                raise Error("Credential Secret sts-creds must contain AWS STS session JSON.") from None
        require(all(isinstance(v, str) and v for v in (access_key, secret_key, session_token)),
                "Credential Secret has incomplete AWS session credentials.")
        return access_key, secret_key, session_token

    def materialize_sts_creds(self, directory):
        # Current AWS CLIs discard the credential fields they read from
        # --secret-creds when creating infrastructure, so also hand the native
        # STS session file to --sts-creds. The Secret remains the source; the
        # caller-provided temporary directory removes the copy after the run.
        access_key, secret_key, session_token = self.aws_session_credentials()
        path = Path(directory) / "sts-creds.from-secret"
        private_write(path, json.dumps({"Credentials": {
            "AccessKeyId": access_key, "SecretAccessKey": secret_key, "SessionToken": session_token}}))
        return str(path)

    def aws_secret_environment(self):
        require(self.p["provider"] == "aws" and self.p.get("secret_creds"), "AWS Secret credential mode is not selected.")
        identity = self.p.get("cloud_identity")
        require(identity and identity.get("kind") == "aws", "AWS requires pinned cloud_identity account_id and region.")
        access_key, secret_key, session_token = self.aws_session_credentials()
        # Use the session credentials directly; no credential copy is needed for
        # account verification.
        env = {k: None for k in (
            "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_SECURITY_TOKEN",
            "AWS_PROFILE", "AWS_DEFAULT_PROFILE", "AWS_SHARED_CREDENTIALS_FILE", "AWS_ROLE_ARN",
            "AWS_ROLE_SESSION_NAME", "AWS_WEB_IDENTITY_TOKEN_FILE",
            "AWS_CONTAINER_CREDENTIALS_FULL_URI", "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI",
            "AWS_CONTAINER_AUTHORIZATION_TOKEN", "AWS_CONTAINER_AUTHORIZATION_TOKEN_FILE")}
        env.update(AWS_ACCESS_KEY_ID=access_key, AWS_SECRET_ACCESS_KEY=secret_key,
                   AWS_SESSION_TOKEN=session_token, AWS_REGION=identity["region"],
                   AWS_DEFAULT_REGION=identity["region"], AWS_CONFIG_FILE="/dev/null",
                   AWS_EC2_METADATA_DISABLED="true")
        value = json.loads(self.external(
            ["aws", "--region", identity["region"], "--no-cli-pager", "sts", "get-caller-identity", "--output", "json"],
            env_overrides=env, timeout=90))
        require(value["Account"] == identity["account_id"], "AWS Secret credential account mismatch.")
        return env

    def validate_aws_identity(self, options, for_destroy=False):
        identity = self.p.get("cloud_identity")
        require(identity and identity.get("kind") == "aws", "AWS requires pinned cloud_identity account_id and region.")
        require(options.get("--region") == identity["region"], "AWS provider region must match cloud_identity.region.")
        if self.p.get("secret_creds"):
            env = self.aws_secret_environment()
        elif self.p.get("aws_cleanup"):
            cfg = self.p["aws_cleanup"]
            require(cfg["account_id"] == identity["account_id"], "AWS cleanup and cloud identities must use the same account.")
            env = cleanup.check_aws_account(self, cfg, require)
        else:
            value = json.loads(self.external(
                ["aws", "--region", identity["region"], "--no-cli-pager", "sts", "get-caller-identity", "--output", "json"],
                timeout=90))
            require(value["Account"] == identity["account_id"], "AWS creation account mismatch.")
            env = None
        role = options.get("--role-arn")
        if role:
            match = re.fullmatch(r"arn:[^:]+:iam::([0-9]{12}):role/.+", role)
            require(match and match.group(1) == identity["account_id"],
                    "AWS role ARN must target the pinned cloud_identity account.")
        if for_destroy and self.p.get("aws_cleanup"):
            cfg = self.p["aws_cleanup"]
            require(cfg["account_id"] == identity["account_id"], "AWS cleanup and cloud identities must use the same account.")
        return env

    def validate_cloud_identity(self, action):
        provider = self.p["provider"]
        args = self.p.get(f"{action}_args", [])
        reject_credential_overrides(provider, args)
        options = provider_options(args)
        if provider == "aws":
            return self.validate_aws_identity(options, for_destroy=(action == "destroy"))
        if provider in {"kubevirt", "agent", "none"}:
            require(not self.p.get("cloud_identity"), f"{provider} uses the pinned management cluster, not a separate cloud_identity.")
            return None
        identity = self.p.get("cloud_identity")
        require(identity, f"{provider} requires a pinned cloud_identity before creation.")
        kind = identity.get("kind")
        if provider == "azure":
            require(kind == "azure", "Azure cloud_identity kind mismatch.")
            value = json.loads(self.external(["az", "account", "show", "--output", "json"], timeout=90))
            require(value["id"] == identity["account_id"], "Azure subscription mismatch.")
        elif provider == "gcp":
            require(kind == "gcp", "GCP cloud_identity kind mismatch.")
            value = self.external(["gcloud", "config", "get-value", "project"], timeout=90).strip()
            require(value == identity["project"], "GCP project mismatch.")
        elif provider == "openstack":
            require(kind == "openstack", "OpenStack cloud_identity kind mismatch.")
            value = json.loads(self.external(["openstack", "token", "issue", "-f", "json"], timeout=90))
            require(value["project_id"] == identity["project"], "OpenStack project mismatch.")
        elif provider == "powervs":
            require(kind == "powervs", "PowerVS cloud_identity kind mismatch.")
            value = json.loads(self.external(["ibmcloud", "account", "show", "--output", "json"], timeout=90))
            require(str(value.get("GUID", value.get("guid"))) == identity["account_id"], "IBM Cloud account mismatch.")
        return None

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
        shared = self.load_shared_state()
        identity = shared.get("identity", {})
        for key, value in (("management_uid", uid), ("namespace", self.p["namespace"]), ("name", self.p["name"])):
            require(key not in identity or identity[key] == value,
                    "Shared lifecycle state is bound to another target.")
            self.binding.setdefault(key, value)
            require(self.binding[key] == value, "State directory is bound to another cluster; use the correct directory.")
            self.binding[key] = value
        for key in ("hostedcluster_uid", "guest_context", "guest_uid"):
            if key in identity:
                require(key not in self.binding or self.binding[key] == identity[key],
                        "Saved identity changed during this operation; inspect before continuing.")
                self.binding[key] = identity[key]
        self.shared_state = shared
        key = {"management_uid": uid, "namespace": self.p["namespace"], "name": self.p["name"]}
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
            if self.shared_lock_active:
                self.save_shared_state({"identity": merged})
            self.binding = merged

    def state_configmap_name(self):
        return f"hypershift-lifecycle-{self.p['name']}"

    def state_target(self):
        return {"management_uid": self.p["management"]["kube_system_uid"],
                "namespace": self.p["namespace"], "name": self.p["name"]}

    def parse_shared_state(self, raw):
        """Parse and bind-check a state.json value read from the shared ConfigMap.

        An absent value is a legitimate pre-initialization record (a process may
        create the ConfigMap before its first update). Anything else must be a
        schema-1 object bound to this exact profile target, so malformed, stale,
        or hand-edited state can never be silently rebound or rewritten.
        """
        if not raw:
            return {}
        require(isinstance(raw, str), "Shared lifecycle ConfigMap has no state.json value.")
        try:
            state = json.loads(raw)
        except json.JSONDecodeError:
            raise Error("Shared lifecycle state is not valid JSON.") from None
        require(isinstance(state, dict), "Shared lifecycle state is not a JSON object.")
        if not state:
            return {}
        require(state.get("schema_version") == 1, "Unsupported shared lifecycle state.")
        require(state.get("target") == self.state_target(),
                "Shared lifecycle state is bound to another target.")
        return state

    def load_shared_state(self):
        obj = self.get("configmap", self.state_configmap_name(), namespace=self.p["namespace"], optional=True)
        if obj is None:
            return {}
        return self.parse_shared_state(obj.get("data", {}).get("state.json"))

    def save_shared_state(self, updates):
        target = self.state_target()
        name = self.state_configmap_name()
        for _ in range(5):
            current = self.get("configmap", name, namespace=self.p["namespace"], optional=True)
            if current is None:
                try:
                    self.oc("create", "configmap", name, "--namespace", self.p["namespace"])
                    current = self.get("configmap", name, namespace=self.p["namespace"])
                except Error:
                    current = self.get("configmap", name, namespace=self.p["namespace"], optional=True)
                    require(current is not None, "Unable to create shared lifecycle state.")
            previous = self.parse_shared_state(current.get("data", {}).get("state.json"))
            lock = previous.get("lock")
            if lock:
                if lock.get("holder") != self.lock_holder:
                    expires = lock.get("expires_at", 0)
                    require(type(expires) in (int, float) and time.time() >= expires,
                            "Another host holds the shared lifecycle lock.")
            # Rebase the requested updates on the freshly-read state on every
            # attempt so a concurrent host's unrelated fields are not erased.
            merged = {**previous, **updates, "schema_version": 1, "target": target}
            if lock and lock.get("holder") == self.lock_holder:
                merged["lock"] = lock
            else:
                merged.pop("lock", None)
            encoded = json.dumps(merged, indent=2, sort_keys=True) + "\n"
            require(len(encoded.encode()) < 900_000, "Shared lifecycle state exceeds the ConfigMap safety limit.")
            resource = {"apiVersion": "v1", "kind": "ConfigMap",
                        "metadata": {"name": name, "namespace": self.p["namespace"],
                                     "resourceVersion": current["metadata"]["resourceVersion"]},
                        "data": {"state.json": encoded}}
            try:
                self.oc("replace", "--namespace", self.p["namespace"], "-f", "-", data=json.dumps(resource))
                self.shared_state = merged
                return
            except Error:
                continue
        raise Error("Shared lifecycle state changed concurrently; retry the operation.")

    def release_shared_lock(self, name):
        for attempt in range(5):
            try:
                current = self.get("configmap", name, namespace=self.p["namespace"])
                state = self.parse_shared_state(current.get("data", {}).get("state.json"))
                if state.get("lock", {}).get("holder") != self.lock_holder:
                    return
                state.pop("lock", None)
                resource = {"apiVersion": "v1", "kind": "ConfigMap",
                            "metadata": {"name": name, "namespace": self.p["namespace"],
                                         "resourceVersion": current["metadata"]["resourceVersion"]},
                            "data": {"state.json": json.dumps(state, indent=2, sort_keys=True) + "\n"}}
                self.oc("replace", "--namespace", self.p["namespace"], "-f", "-", data=json.dumps(resource))
                self.shared_state = state
                return
            except (Error, json.JSONDecodeError):
                if attempt == 4:
                    raise Error("Failed to release the shared lifecycle lock; it will expire automatically.") from None
                time.sleep(0.5 * (attempt + 1))

    @contextmanager
    def shared_lock(self, seconds=93600):
        holder = f"{socket.gethostname()}-{os.getpid()}-{uuid.uuid4()}"
        name = self.state_configmap_name()
        acquired = False
        for _ in range(10):
            current = self.get("configmap", name, namespace=self.p["namespace"], optional=True)
            if current is None:
                try:
                    self.oc("create", "configmap", name, "--namespace", self.p["namespace"])
                    current = self.get("configmap", name, namespace=self.p["namespace"])
                except Error:
                    current = self.get("configmap", name, namespace=self.p["namespace"], optional=True)
                    require(current is not None, "Unable to create shared lifecycle lock.")
            previous = self.parse_shared_state(current.get("data", {}).get("state.json"))
            lock = previous.get("lock")
            if lock:
                expires = lock.get("expires_at", 0)
                require(type(expires) in (int, float) and time.time() >= expires,
                        "Another host holds the shared lifecycle lock.")
            previous["schema_version"] = 1
            previous["target"] = self.state_target()
            previous["lock"] = {"holder": holder, "expires_at": time.time() + seconds}
            resource = {"apiVersion": "v1", "kind": "ConfigMap",
                        "metadata": {"name": name, "namespace": self.p["namespace"],
                                     "resourceVersion": current["metadata"]["resourceVersion"]},
                        "data": {"state.json": json.dumps(previous, indent=2, sort_keys=True) + "\n"}}
            try:
                self.oc("replace", "--namespace", self.p["namespace"], "-f", "-", data=json.dumps(resource))
                self.shared_state = previous
                acquired = True
                break
            except Error:
                continue
        require(acquired, "Unable to acquire the shared lifecycle lock.")
        # Only publish lock ownership after it is confirmed; a failed acquire must
        # not leave callers believing they may mutate shared state.
        self.lock_holder = holder
        self.shared_lock_active = True
        try:
            yield
        finally:
            pending = sys.exc_info()[1]
            try:
                self.release_shared_lock(name)
            except Error:
                # Do not mask the operation's real failure; the lock expires.
                if pending is None:
                    raise
            finally:
                self.shared_lock_active = False
                self.lock_holder = None

    @contextmanager
    def lock(self, name="lifecycle.lock", blocking=False):
        held = self._locks.get(name)
        if held is not None:
            # Re-entrant for this process: access() -> save() must not deadlock
            # against the same advisory lock it already owns.
            held[1] += 1
            try:
                yield held[0]
            finally:
                held[1] -= 1
            return
        path = self.directory / name
        fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            info = os.fstat(fd)
            require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and info.st_nlink == 1,
                    "Lock file must be a private regular file owned by this user.")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
            except BlockingIOError:
                raise Error("A lifecycle/inventory operation is active in this state directory.") from None
            self._locks[name] = [fd, 1]
            try:
                yield fd
            finally:
                self._locks.pop(name, None)
        finally:
            # Closing, rather than explicit LOCK_UN, retains the lock if a native
            # child survives its parent. The child inherits this same description.
            os.close(fd)

    def fingerprint(self):
        aws = self.p.get("aws_cleanup")
        if aws is not None:
            aws = {k: aws.get(k) for k in ("account_id", "region", "owned", "preserve", "dns_records", "oidc_documents")}
        fields = {k: self.p.get(k) for k in ("name", "namespace", "provider", "cli", "infra_id", "destroy_args")}
        fields["management_uid"] = self.p["management"]["kube_system_uid"]
        fields["aws_cleanup"] = aws
        fields["cloud_identity"] = self.p.get("cloud_identity")
        return hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest()

    def inventory(self, skip_guest=False):
        with self.shared_lock(), self.lock():
            self.management()
            hc = self.hc()
            require(not hc["metadata"].get("deletionTimestamp"), "Deletion already started; retain the original inventory.")
            require(not (self.directory / "destroy-operation.json").exists() and
                    not self.shared_state.get("destroy_operation"), "Destroy receipt exists; do not replace its inventory.")
            require(self.p.get("infra_id") == hc["spec"].get("infraID") and self.p.get("infra_id"),
                    "Set profile infra_id from the live HostedCluster before recording teardown inventory.")
            result = cleanup.capture(self, hc, skip_guest, require)
            result["fingerprint"] = self.fingerprint()
            private_write(self.directory / "teardown-inventory.json", json.dumps(result, indent=2) + "\n")
            self.save_shared_state({"teardown_inventory": result})
            self.save()
            return {"inventory_saved": True, "path": str(self.directory / "teardown-inventory.json"),
                    "guest_storage_observed": result["guest_storage_observed"],
                    "cloud_automated": result["cloud"] is not None,
                    "next": "Review owned/shared resources and coverage before destroy --execute."}

    def teardown_inventory(self):
        path = self.directory / "teardown-inventory.json"
        if path.is_file():
            data = json.loads(path.read_text())
        else:
            data = self.shared_state.get("teardown_inventory")
            require(data is not None, "Record and review inventory before destroy or cleanup verification.")
        # Hash a canonical rendering regardless of source so the same inventory
        # read from a local file or the shared ConfigMap has the same digest.
        raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        require(data["fingerprint"] == self.fingerprint(), "Teardown profile changed; do not reuse the recorded ownership plan.")
        require(data["target"] == {"management_uid": self.binding["management_uid"],
                "namespace": self.p["namespace"], "name": self.p["name"],
                "hostedcluster_uid": self.binding.get("hostedcluster_uid"),
                "infra_id": self.p.get("infra_id"), "provider": self.p["provider"]},
                "Teardown inventory identity does not match the saved target.")
        return data, hashlib.sha256(raw).hexdigest()

    def verify_cleanup(self):
        with self.shared_lock(), self.lock():
            self.management()
            inventory, digest = self.teardown_inventory()
            operation = self.directory / "destroy-operation.json"
            if operation.is_file():
                record = json.loads(operation.read_text())
            else:
                record = self.shared_state.get("destroy_operation")
                require(record is not None, "No recorded destroy attempt; inspect the target before cleanup verification.")
            require(record["inventory_digest"] == digest and record["target"] == inventory["target"],
                    "Destroy inventory/receipt identity was modified.")
            result = cleanup.verify(self, inventory, require)
            private_write(self.directory / "cleanup-verification.json", json.dumps(result, indent=2) + "\n")
            if result["cleanup_verified"]:
                (self.directory / "guest.kubeconfig").unlink(missing_ok=True)
                result["guest_kubeconfig_removed"] = True
                private_write(self.directory / "cleanup-complete.json", json.dumps(result, indent=2) + "\n")
                self.save_shared_state({"cleanup_complete": result})
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
        with self.shared_lock(), self.lock() as fd:
            return self._lifecycle(action, resume, grace_period, fd)

    def materialize_pull_secret(self, directory):
        data = self.credential_secret()
        key = "pullSecret" if "pullSecret" in data else "pull-secret"
        content = self.decode_secret_key(data, key)
        path = Path(directory) / "pull-secret.from-secret"
        private_write(path, content)
        return str(path)

    def _lifecycle(self, action, resume, grace_period, lock_fd):
        self.management()
        hc = self.hc(optional=True)
        operation_path = self.directory / "destroy-operation.json"
        operation = None
        cloud_env = None
        if action == "create":
            require(not hc, "HostedCluster already exists; inspect status/access instead of recreating.")
            attempted = (self.shared_state.get("create_attempted") or self.binding.get("create_attempted") or
                         (self.directory / "create-attempt.json").exists())
            if attempted:
                require(resume, "A create was already attempted. Inspect management AND provider resources, then use --resume explicitly.")
            if self.p.get("pull_secret"):
                require(Path(self.p["pull_secret"]).is_file(), "Pull-secret file is missing.")
            # Shared namespace provisioning is an administrator prerequisite.
            self.get("namespace", self.p["namespace"])
            self.get("customresourcedefinition", HC)
            self.get("customresourcedefinition", NP)
            cloud_env = self.validate_cloud_identity("create")
        else:
            if not resume:
                require(hc is not None, "HostedCluster missing; do not infer infrastructure cleanup from a name.")
                require(not hc["metadata"].get("deletionTimestamp"), "Deletion is already in progress; inspect status and the destroy receipt.")
                # Receipts are mirrored in the shared ConfigMap; a fresh state
                # directory on another host must still see an existing attempt.
                require(not operation_path.exists() and not self.shared_state.get("destroy_operation"),
                        "Destroy already attempted; inspect its receipt and use --resume when appropriate.")
                require(not (self.directory / "cleanup-complete.json").exists() and
                        not self.shared_state.get("cleanup_complete"),
                        "Cleanup is already verified; no destroy to run.")
            inventory, digest = self.teardown_inventory()
            if hc:
                require(inventory["provider_spec_digest"] == cleanup.digest({"platform": hc["spec"]["platform"],
                        "dns": hc["spec"].get("dns")}), "HostedCluster provider/DNS specification changed since inventory.")
            if resume:
                if operation_path.is_file():
                    try:
                        operation = json.loads(operation_path.read_text())
                    except (OSError, json.JSONDecodeError):
                        raise Error("Recorded destroy receipt is unreadable; inspect it before resuming.") from None
                else:
                    # Receipts are mirrored in the shared ConfigMap, so a fresh
                    # state directory on another host can resume the same attempt.
                    operation = self.shared_state.get("destroy_operation")
                require(isinstance(operation, dict),
                        "Resume requires a recorded destroy attempt for this target.")
                require(operation.get("inventory_digest") == digest and
                        operation.get("target") == inventory["target"],
                        "Destroy inventory/receipt identity was modified.")
                require(operation.get("attempts") and operation["attempts"][-1]["outcome"] != "cli_succeeded",
                        "CLI already succeeded; run verify-cleanup instead of repeating destroy.")
                require(not (self.directory / "cleanup-complete.json").exists() and
                        not self.shared_state.get("cleanup_complete"),
                        "Cleanup is already verified; no destroy to resume.")
                require(hc is not None or (self.p["provider"] == "aws" and self.p.get("aws_cleanup")),
                        "Resume after HC disappearance requires the configured AWS ownership adapter; use a separate provider recovery plan.")
            else:
                operation = {"inventory_digest": digest, "target": inventory["target"], "attempts": []}
            if grace_period is not None:
                require(type(grace_period) is int and 0 < grace_period <= 86400, "Use a grace period of 1..86400 seconds.")
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
            cloud_env = self.validate_cloud_identity("destroy")
        # HyperShift's lifecycle CLI may not support --context. Give it a private,
        # flattened single-context config, never the caller's ambient current-context.
        raw = self.oc("config", "view", "--minify", "--flatten", "--raw", "-o", "json")
        config = json.loads(raw)
        require(config.get("current-context") == self.p["management"]["context"],
                "Minified management kubeconfig has an unexpected context.")
        with tempfile.TemporaryDirectory(prefix="management-", dir=self.directory) as tmp:
            tmpdir = Path(tmp)
            # Materialize Secret-derived credentials inside this per-run directory
            # so pull secrets and STS sessions disappear when the CLI returns.
            pull_secret_path = self.p.get("pull_secret")
            if action == "create" and not pull_secret_path and self.p.get("secret_creds"):
                pull_secret_path = self.materialize_pull_secret(tmpdir)
            sts_creds_path = self.materialize_sts_creds(tmpdir) if self.p.get("secret_creds") else None
            command = lifecycle_command(self.p, action, pull_secret_path, sts_creds_path)
            if grace_period is not None:
                command.append(f"--cluster-grace-period={grace_period}s")
            self.check_help(action, command)
            kc = tmpdir / "config"
            private_write(kc, raw)
            if action == "create":
                self.binding["create_attempted"] = True
                create_attempt = {
                    "at": cleanup.now(), "management_uid": self.binding["management_uid"],
                    "namespace": self.p["namespace"], "name": self.p["name"], "provider": self.p["provider"]}
                self.save_shared_state({"create_attempted": True, "create_attempt": create_attempt})
                private_write(self.directory / "create-attempt.json", json.dumps(create_attempt) + "\n")
            self.save()
            if operation is not None:
                operation["attempts"].append({"started_at": cleanup.now(), "outcome": "observation_lost",
                                              "grace_period_seconds": grace_period})
                private_write(operation_path, json.dumps(operation, indent=2) + "\n")
                self.save_shared_state({"destroy_operation": operation})
            # Output may include passwords or secrets. Retain it locally, not in the conversation.
            try:
                output = run(command, kubeconfig=kc, log_dir=self.directory,
                             timeout=max(3600, (grace_period or 0) + 1800), include_stderr=True,
                             pass_fds=(lock_fd,), env_overrides=cloud_env)
            except (Exception, KeyboardInterrupt):
                if operation is not None:
                    operation["attempts"][-1].update(outcome="cli_failed", finished_at=cleanup.now())
                    private_write(operation_path, json.dumps(operation, indent=2) + "\n")
                    self.save_shared_state({"destroy_operation": operation})
                raise
            if operation is not None:
                operation["attempts"][-1].update(outcome="cli_succeeded", finished_at=cleanup.now())
                private_write(operation_path, json.dumps(operation, indent=2) + "\n")
                self.save_shared_state({"destroy_operation": operation})
            private_write(self.directory / f"{action}.log", output)
        return {"submitted": action, "name": self.p["name"],
                "next": "Run verify-cleanup; CLI exit alone does not prove cleanup." if action == "destroy"
                        else "Inspect status; CLI exit alone does not prove readiness."}

    def access(self):
        with self.shared_lock():
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
            with self.lock("identity.lock", blocking=True):
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
        contexts = [c for c in config.get("contexts") or []
                    if isinstance(c, dict) and c.get("name") == self.binding["guest_context"]]
        require(len(contexts) == 1, "Guest context is missing or ambiguous.")
        context = contexts[0].get("context")
        require(isinstance(context, dict) and isinstance(context.get("cluster"), str) and context["cluster"],
                "Guest context has no cluster reference.")
        clusters = [c.get("cluster") for c in config.get("clusters") or []
                    if isinstance(c, dict) and c.get("name") == context["cluster"]]
        require(len(clusters) == 1 and isinstance(clusters[0], dict),
                "Guest cluster configuration is missing or ambiguous.")
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
        manifest_path = Path(manifest)
        require(manifest_path.is_file(), "Manifest path is not a readable file.")
        limit = 2 * 1024 * 1024
        try:
            with manifest_path.open("rb") as stream:
                raw = stream.read(limit + 1)
        except OSError:
            raise Error("Manifest path is not a readable file.") from None
        require(len(raw) <= limit, "Manifest exceeds the 2 MiB safety limit.")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise Error("Manifest must be UTF-8 text.") from None
        docs = [doc for doc in yaml.safe_load_all(text) if doc is not None]
        require(len(docs) <= 100, "Manifest contains too many documents (maximum 100).")
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
        # Namespace handling is least-privilege: an existing namespace needs no
        # cluster-scoped write, and a missing one is only dry-run during review.
        ns = json.dumps({"apiVersion": "v1", "kind": "Namespace", "metadata": {"name": namespace}})
        if self.get("namespace", namespace, guest=True, optional=True) is None:
            if execute:
                self.oc("apply", "-f", "-", guest=True, data=ns)
            else:
                self.oc("apply", "--dry-run=server", "-f", "-", guest=True, data=ns)
                raise Error("Guest namespace is absent. Use --execute after review; "
                            "it creates the namespace before workload validation.")
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
        sp.add_argument("--resume", action="store_true", help="Resume only a recorded operation after explicit review")
        if command == "destroy":
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
        pull_secret = p.get("pull_secret")
        sts_creds = None
        if p.get("secret_creds"):
            pull_secret = pull_secret or f"<pull-secret from Secret {p['secret_creds']}>"
            sts_creds = f"<sts-creds from Secret {p['secret_creds']}>"
        command = lifecycle_command(p, action, pull_secret, sts_creds)
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
        if p["provider"] == "aws":
            oidc = s.get("configmap", "oidc-storage-provider-s3-config", namespace="kube-public", optional=True)
            require(oidc is not None and oidc.get("data", {}).get("name") and
                    oidc.get("data", {}).get("region"),
                    "AWS management clusters need kube-public/oidc-storage-provider-s3-config "
                    "with name and region before guest creation.")
        if p.get("secret_creds"):
            secret = s.get("secret", p["secret_creds"], namespace=p["namespace"], optional=True)
            require(secret is not None,
                    f"Credential Secret {p['namespace']}/{p['secret_creds']} was not found.")
            keys = set(secret.get("data", {}))
            require(keys & {"aws_access_key_id", "sts-creds"},
                    f"Credential Secret {p['namespace']}/{p['secret_creds']} must contain the native AWS "
                    "credential keys or sts-creds.")
            if "aws_access_key_id" in keys:
                require({"aws_access_key_id", "aws_secret_access_key", "aws_session_token"} <= keys,
                        f"Credential Secret {p['namespace']}/{p['secret_creds']} must contain "
                        "aws_access_key_id, aws_secret_access_key, and aws_session_token.")
            require(keys & {"pullSecret", "pull-secret"},
                    f"Credential Secret {p['namespace']}/{p['secret_creds']} must contain pullSecret or pull-secret.")
            require(keys & {"baseDomain", "base-domain"},
                    f"Credential Secret {p['namespace']}/{p['secret_creds']} must contain baseDomain or base-domain.")
        for verb in ("get", "create", "update"):
            require(s.oc("auth", "can-i", verb, "configmaps", "--namespace", p["namespace"]).strip() == "yes",
                    "Missing shared lifecycle-state ConfigMap permissions.")
        s.validate_cloud_identity("create")
        s.check_help("create")
        for verb, resource in (("create", HC), ("get", HC), ("create", NP), ("get", "secrets")):
            require(s.oc("auth", "can-i", verb, resource, "--namespace", p["namespace"]).strip() == "yes",
                    "Missing management permissions; ask the administrator for scoped access.")
        if p.get("pull_secret"):
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
        while time.monotonic() < deadline:
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
            time.sleep(min(args.interval, max(0, deadline - time.monotonic())))
        else:
            raise Error("Readiness deadline reached; cluster may still be reconciling. Inspect status; do not recreate.")
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

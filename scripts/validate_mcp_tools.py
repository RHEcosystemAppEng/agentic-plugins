#!/usr/bin/env python3
"""Validate that allowed-tools declared in SKILL.md frontmatter match
the actual tools exposed by the MCP servers defined in mcps.json.

Starts each container-based MCP server via podman, performs JSON-RPC
initialize + tools/list, then cross-references against each skill's
allowed-tools declaration.

Platform: Linux and macOS only (uses select.select for non-blocking I/O).

Usage:
    python scripts/validate_mcp_tools.py [plugin1] [plugin2] ...
    python scripts/validate_mcp_tools.py --summary-only --log-file .validate/mcp-tools.log
    No args: validates all plugins that have mcps.json
"""

from __future__ import annotations

import argparse
import json
import os
import select
import subprocess
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

JSONRPC_TIMEOUT = 30
SERVER_START_TIMEOUT = 15
PODMAN_PULL_TIMEOUT = 120
DEFAULT_LOG_FILE = Path(".validate/mcp-tools.log")

INIT_MSG = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "mcp-tool-validator", "version": "1.0.0"},
    },
}

INITIALIZED_NOTIFICATION = {
    "jsonrpc": "2.0",
    "method": "notifications/initialized",
}


@dataclass
class Finding:
    skill: str
    plugin: str
    tool: str
    file_path: str
    line_number: int | None
    suggestion: str | None = None

    def __str__(self) -> str:
        loc = f"{self.file_path}"
        if self.line_number:
            loc += f":{self.line_number}"
        hint = f' (did you mean "{self.suggestion}"?)' if self.suggestion else ""
        return f'{loc}: tool "{self.tool}" not found in MCP servers{hint}'


@dataclass
class ValidationResult:
    total_skills: int = 0
    passed: int = 0
    skipped: int = 0
    warned: int = 0
    failed: int = 0
    findings: list[Finding] = field(default_factory=list)
    warnings: list[Finding] = field(default_factory=list)
    skipped_servers: list[str] = field(default_factory=list)
    has_skipped_servers: bool = False

    @property
    def success(self) -> bool:
        return self.failed == 0


class Reporter:
    """Route verbose validation output to a log file; emit summaries to stdout."""

    def __init__(self, log_path: Path | None = None, summary_only: bool = False) -> None:
        self.log_path = log_path
        self.summary_only = summary_only
        self._log_handle: TextIO | None = None
        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            self._log_handle = log_path.open("w", encoding="utf-8")

    def close(self) -> None:
        if self._log_handle is not None:
            self._log_handle.close()
            self._log_handle = None

    def detail(self, message: str = "") -> None:
        text = message if message.endswith("\n") else f"{message}\n"
        if self._log_handle is not None:
            self._log_handle.write(text)
            self._log_handle.flush()
        if not self.summary_only:
            sys.stdout.write(text if message.endswith("\n") else message + "\n")

    def summary(self, message: str = "") -> None:
        text = message if message.endswith("\n") else f"{message}\n"
        if self._log_handle is not None:
            self._log_handle.write(text)
            self._log_handle.flush()
        sys.stdout.write(text if message.endswith("\n") else message + "\n")

    def log_only(self, message: str = "") -> None:
        """Write to the log file without printing to stdout."""
        if self._log_handle is None:
            return
        text = message if message.endswith("\n") else f"{message}\n"
        self._log_handle.write(text)
        self._log_handle.flush()

    def __enter__(self) -> Reporter:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


def _write_full_findings_to_log(
    reporter: Reporter, heading: str, items: list[Finding],
) -> None:
    if not items:
        return
    reporter.log_only()
    reporter.log_only(heading)
    for item in items:
        reporter.log_only(f"  - {item}")


def print_validation_summary(combined: ValidationResult, reporter: Reporter) -> None:
    """Print a concise MCP validation summary for make validate."""
    if combined.failed:
        result_label = "FAILED"
    elif combined.warned > 0 or combined.skipped > 0:
        result_label = "PASSED WITH WARNINGS"
    else:
        result_label = "PASSED"

    _write_full_findings_to_log(
        reporter,
        f"WARNINGS (full list, {len(combined.warnings)} unverifiable tools):",
        combined.warnings,
    )
    _write_full_findings_to_log(
        reporter,
        f"FAILURES (full list, {len(combined.findings)} missing tools):",
        combined.findings,
    )

    reporter.summary()
    reporter.summary("=" * 66)
    reporter.summary(" MCP Tool Validation Summary")
    reporter.summary("=" * 66)
    reporter.summary(f" Result:   {result_label}")
    if reporter.log_path is not None:
        reporter.summary(f" Full log: {reporter.log_path}")
    reporter.summary()
    reporter.summary(
        f" Skills:   {combined.total_skills} total — "
        f"{combined.passed} passed, {combined.warned} warned, "
        f"{combined.skipped} skipped (no allowed-tools), {combined.failed} failed"
    )
    reporter.summary()

    if combined.skipped_servers:
        unique_servers = list(dict.fromkeys(combined.skipped_servers))
        reporter.summary(f" Skipped MCP servers ({len(unique_servers)}):")
        for server in unique_servers:
            reporter.summary(f"   • {server}")
        reporter.summary()

    if combined.warnings:
        skills_affected = len({(w.plugin, w.skill) for w in combined.warnings})
        by_plugin = Counter(w.plugin for w in combined.warnings)
        plugin_bits = ", ".join(f"{plugin} ({count})" for plugin, count in by_plugin.most_common())
        reporter.summary(
            f" Unverifiable tools: {len(combined.warnings)} tool reference(s) "
            f"in {skills_affected} skill(s)"
        )
        reporter.summary(f"   By plugin: {plugin_bits}")
        if reporter.log_path is not None:
            reporter.summary(f"   Details: see {reporter.log_path}")
        reporter.summary()

    if combined.findings:
        reporter.summary(f" Missing tools: {len(combined.findings)} failure(s) — fix before merge")
        for finding in combined.findings:
            reporter.summary(f"   • {finding}")
        reporter.summary()

    if not combined.success:
        reporter.summary(" MCP tool validation failed — fix tool names or mcps.json.")
    elif combined.warned > 0:
        reporter.summary(
            " Some tools could not be verified because MCP servers did not start."
        )
    elif combined.skipped > 0:
        reporter.summary(" Some skills have no allowed-tools declaration.")
    else:
        reporter.summary(" All declared MCP tools verified.")
    reporter.summary("=" * 66)
    reporter.summary()


def levenshtein(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (c1 != c2)))
        prev = curr
    return prev[len(s2)]


def suggest_tool(name: str, available: set[str], max_distance: int = 3) -> str | None:
    best: tuple[str, float] | None = None

    for tool in available:
        lev = levenshtein(name, tool)
        if lev <= max_distance:
            score = lev
            if best is None or score < best[1]:
                best = (tool, score)

        name_lower, tool_lower = name.lower(), tool.lower()
        if name_lower in tool_lower or tool_lower in name_lower:
            score = 0.5 if name_lower == tool_lower else 1.0
            if best is None or score < best[1]:
                best = (tool, score)

        name_parts = set(name_lower.replace("-", "_").split("_"))
        tool_parts = set(tool_lower.replace("-", "_").split("_"))
        overlap = name_parts & tool_parts
        if overlap and len(overlap) >= len(name_parts) * 0.5:
            score = 2.0 - len(overlap) / max(len(tool_parts), 1)
            if best is None or score < best[1]:
                best = (tool, score)

    return best[0] if best else None


def read_response(proc: subprocess.Popen, expected_id: int, timeout: int = JSONRPC_TIMEOUT) -> dict | None:
    """Read JSON-RPC responses from proc.stdout until one matches expected_id."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        remaining = deadline - time.time()
        if remaining <= 0:
            break

        if proc.poll() is not None:
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    if msg.get("id") == expected_id:
                        return msg
                except json.JSONDecodeError:
                    continue
            return None

        ready, _, _ = select.select([proc.stdout], [], [], min(remaining, 0.5))
        if not ready:
            continue

        line = proc.stdout.readline()
        if not line:
            continue
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if msg.get("id") == expected_id:
            return msg
    return None


def send_jsonrpc(proc: subprocess.Popen, msg: dict) -> None:
    proc.stdin.write(json.dumps(msg) + "\n")
    proc.stdin.flush()


def pull_image(image: str, reporter: Reporter) -> bool:
    """Pull a container image, returning True on success."""
    reporter.detail(f"    Pulling image: {image[:80]}...")
    try:
        result = subprocess.run(
            ["podman", "pull", image],
            capture_output=True, text=True, timeout=PODMAN_PULL_TIMEOUT,
        )
        if result.returncode != 0:
            reporter.detail(f"    WARNING: podman pull failed: {result.stderr.strip()[:200]}")
            return False
        return True
    except subprocess.TimeoutExpired:
        reporter.detail(f"    WARNING: podman pull timed out after {PODMAN_PULL_TIMEOUT}s")
        return False


def extract_image_from_args(args: list[str]) -> str | None:
    """Find the container image reference in podman run args."""
    skip_next = False
    for arg in args:
        if skip_next:
            skip_next = False
            continue
        if arg.startswith("-"):
            if arg in ("-v", "-e", "--env", "--entrypoint", "--name", "--network",
                        "--userns", "--user", "-p", "--publish", "-w", "--workdir"):
                skip_next = True
            continue
        if arg == "run":
            continue
        if arg in ("--rm", "-i", "-t", "--interactive", "--tty", "-d", "--detach"):
            continue
        return arg
    return None


def query_mcp_tools(
    command: str, args: list[str], kubeconfig: str, reporter: Reporter,
) -> list[str] | None:
    """Start an MCP server and query its tools via JSON-RPC."""
    expanded_args = [a.replace("${KUBECONFIG}", kubeconfig) for a in args]

    proc = subprocess.Popen(
        [command] + expanded_args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    try:
        for _ in range(10):
            if proc.poll() is not None:
                stderr = proc.stderr.read()[:300] if proc.stderr else ""
                reporter.detail(
                    f"    Server exited immediately (code {proc.returncode}): {stderr.strip()}"
                )
                return None
            time.sleep(0.1)

        send_jsonrpc(proc, INIT_MSG)
        resp = read_response(proc, expected_id=1, timeout=SERVER_START_TIMEOUT)
        if resp is None:
            reporter.detail("    WARNING: no response to initialize")
            return None

        if "error" in resp:
            reporter.detail(f"    WARNING: initialize error: {resp['error']}")
            return None

        server_info = resp.get("result", {}).get("serverInfo", {})
        reporter.detail(f"    Server: {server_info.get('name', 'unknown')}")

        send_jsonrpc(proc, INITIALIZED_NOTIFICATION)

        all_tools: list[str] = []
        cursor = None
        page = 0

        while True:
            page += 1
            tools_msg = {
                "jsonrpc": "2.0",
                "id": 100 + page,
                "method": "tools/list",
                "params": {},
            }
            if cursor:
                tools_msg["params"]["cursor"] = cursor

            send_jsonrpc(proc, tools_msg)
            resp = read_response(proc, expected_id=100 + page)
            if resp is None:
                reporter.detail(f"    WARNING: no response to tools/list (page {page})")
                return all_tools if all_tools else None

            if "error" in resp:
                reporter.detail(f"    WARNING: tools/list error: {resp['error']}")
                return all_tools if all_tools else None

            result = resp.get("result", {})
            tools = result.get("tools", [])
            all_tools.extend(t["name"] for t in tools)

            next_cursor = result.get("nextCursor")
            if next_cursor:
                cursor = next_cursor
            else:
                break

        return all_tools

    finally:
        proc.stdin.close()
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


def parse_frontmatter(skill_path: Path) -> tuple[str, int | None]:
    """Extract allowed-tools value and its line number from SKILL.md frontmatter."""
    in_fm = False
    with open(skill_path) as f:
        for line_num, line in enumerate(f, 1):
            stripped = line.strip()
            if stripped == "---":
                if not in_fm:
                    in_fm = True
                    continue
                break
            if in_fm and stripped.startswith("allowed-tools:"):
                value = stripped[len("allowed-tools:"):].strip()
                return value, line_num
    return "", None


def find_plugins(repo_root: Path) -> list[str]:
    """Find all plugins that have both mcps.json and a skills directory."""
    plugins = []
    for mcps_file in sorted(repo_root.glob("*/mcps.json")):
        plugin_dir = mcps_file.parent
        if (plugin_dir / "skills").is_dir():
            plugins.append(plugin_dir.name)
    return plugins


def validate_plugin(
    plugin: str, repo_root: Path, kubeconfig: str, reporter: Reporter,
) -> ValidationResult:
    """Validate all skills in a single plugin against its MCP servers."""
    result = ValidationResult()
    plugin_dir = repo_root / plugin
    mcps_file = plugin_dir / "mcps.json"

    if not mcps_file.exists():
        reporter.detail(f"  WARNING: {plugin}/mcps.json not found, skipping plugin")
        return result

    try:
        with open(mcps_file) as f:
            config = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        reporter.detail(f"  ERROR: failed to parse {plugin}/mcps.json: {e}")
        result.failed += 1
        return result

    servers = config.get("mcpServers", {})
    all_available_tools: set[str] = set()

    for server_name, server_config in servers.items():
        command = server_config.get("command", "")

        if command not in ("podman", "docker"):
            reason = f"non-container command '{command}'"
            reporter.detail(f"  SKIP server '{server_name}': {reason}")
            result.skipped_servers.append(f"{server_name} ({reason})")
            continue

        args = server_config.get("args", [])
        reporter.detail(f"  Starting MCP server '{server_name}'...")

        image = extract_image_from_args(args)
        if image:
            if not pull_image(image, reporter):
                reporter.detail("    WARNING: could not pull image, attempting to start anyway")

        tools = query_mcp_tools(command, args, kubeconfig, reporter)

        if tools is None:
            reporter.detail("    WARNING: no tools returned (server may require credentials)")
            result.skipped_servers.append(f"{server_name} (no tools returned)")
            continue

        reporter.detail(f"    {len(tools)} tools available")
        for t in sorted(tools):
            reporter.detail(f"      - {t}")
        all_available_tools.update(tools)

    result.has_skipped_servers = len(result.skipped_servers) > 0

    if all_available_tools:
        reporter.detail(f"  Combined tool pool: {len(all_available_tools)} unique tools")

    skills_dir = plugin_dir / "skills"
    if not skills_dir.exists():
        return result

    for skill_dir in sorted(skills_dir.iterdir()):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue

        skill_name = skill_dir.name
        result.total_skills += 1

        allowed_tools_str, line_number = parse_frontmatter(skill_file)

        if not allowed_tools_str:
            result.skipped += 1
            reporter.detail(f"  SKIP {plugin}/{skill_name}: no allowed-tools declared")
            continue

        declared_tools = allowed_tools_str.split()
        missing = [t for t in declared_tools if t not in all_available_tools]

        if not missing:
            result.passed += 1
            reporter.detail(
                f"  PASS {plugin}/{skill_name}: all {len(declared_tools)} tools validated"
            )
        elif result.has_skipped_servers:
            verified = [t for t in declared_tools if t in all_available_tools]
            result.warned += 1
            rel_path = str(skill_file.relative_to(repo_root))
            for tool in missing:
                suggestion = suggest_tool(tool, all_available_tools)
                finding = Finding(
                    skill=skill_name,
                    plugin=plugin,
                    tool=tool,
                    file_path=rel_path,
                    line_number=line_number,
                    suggestion=suggestion,
                )
                result.warnings.append(finding)
            reporter.detail(
                f"  WARN {plugin}/{skill_name}: {len(verified)}/{len(declared_tools)} tools verified, "
                f"{len(missing)} unverifiable (MCP server not started)"
            )
        else:
            result.failed += 1
            rel_path = str(skill_file.relative_to(repo_root))
            for tool in missing:
                suggestion = suggest_tool(tool, all_available_tools)
                finding = Finding(
                    skill=skill_name,
                    plugin=plugin,
                    tool=tool,
                    file_path=rel_path,
                    line_number=line_number,
                    suggestion=suggestion,
                )
                result.findings.append(finding)
                reporter.detail(f"  FAIL {plugin}/{skill_name}: {finding}")

    return result


def check_prerequisites() -> str | None:
    """Return an error message if prerequisites are missing, or None if all OK."""
    try:
        subprocess.run(
            ["podman", "--version"], capture_output=True, text=True, timeout=5,
        )
    except FileNotFoundError:
        return "podman not found on PATH"
    except subprocess.TimeoutExpired:
        return "podman --version timed out"

    kubeconfig = os.environ.get("KUBECONFIG", "")
    if not kubeconfig:
        default = Path.home() / ".kube" / "config"
        if not default.exists():
            return "KUBECONFIG not set and ~/.kube/config not found"
    return None


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate allowed-tools in SKILL.md against live MCP servers",
    )
    parser.add_argument(
        "plugins",
        nargs="*",
        help="Plugin names to validate (default: all plugins with mcps.json)",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=None,
        help="Write full validation output to this file",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print only the summary section on stdout (requires --log-file for details)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    repo_root = Path(__file__).resolve().parent.parent
    plugins = args.plugins or None

    skip_reason = check_prerequisites()
    if skip_reason:
        print(f"SKIP: {skip_reason} -- MCP tool validation requires podman and a cluster")
        return 0

    kubeconfig = os.environ.get("KUBECONFIG", "")
    if not kubeconfig:
        default = Path.home() / ".kube" / "config"
        if default.exists():
            kubeconfig = str(default)

    if not plugins:
        plugins = find_plugins(repo_root)

    if not plugins:
        print("No plugins with mcps.json found")
        return 0

    log_path = args.log_file
    summary_only = args.summary_only
    if summary_only and log_path is None:
        log_path = repo_root / DEFAULT_LOG_FILE

    with Reporter(log_path=log_path, summary_only=summary_only) as reporter:
        reporter.detail()
        reporter.detail("=" * 66)
        reporter.detail("           MCP Tool Validation Report")
        reporter.detail("    Verifying allowed-tools against live MCP servers")
        reporter.detail("=" * 66)
        reporter.detail()
        reporter.detail(f"Plugins to validate: {', '.join(plugins)}")
        reporter.detail(f"KUBECONFIG: {kubeconfig}")
        reporter.detail()

        combined = ValidationResult()

        for plugin in plugins:
            reporter.detail(f"-- {plugin} --")
            result = validate_plugin(plugin, repo_root, kubeconfig, reporter)
            combined.total_skills += result.total_skills
            combined.passed += result.passed
            combined.skipped += result.skipped
            combined.warned += result.warned
            combined.failed += result.failed
            combined.findings.extend(result.findings)
            combined.warnings.extend(result.warnings)
            combined.skipped_servers.extend(result.skipped_servers)
            reporter.detail()

        print_validation_summary(combined, reporter)

    return 0 if combined.success else 1


if __name__ == "__main__":
    sys.exit(main())

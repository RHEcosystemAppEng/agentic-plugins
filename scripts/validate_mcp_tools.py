#!/usr/bin/env python3
"""Validate that allowed-tools declared in SKILL.md frontmatter match
the actual tools exposed by the MCP servers defined in mcps.json.

Starts each container-based MCP server via podman, performs JSON-RPC
initialize + tools/list, then cross-references against each skill's
allowed-tools declaration.

Platform: Linux and macOS only (uses select.select for non-blocking I/O).

Usage:
    python scripts/validate_mcp_tools.py [pack1] [pack2] ...
    No args: validates all packs that have mcps.json
"""

from __future__ import annotations

import json
import os
import select
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

JSONRPC_TIMEOUT = 30
SERVER_START_TIMEOUT = 15
PODMAN_PULL_TIMEOUT = 120

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
    pack: str
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
    failed: int = 0
    findings: list[Finding] = field(default_factory=list)
    skipped_servers: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.failed == 0


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


def pull_image(image: str) -> bool:
    """Pull a container image, returning True on success."""
    print(f"    Pulling image: {image[:80]}...")
    try:
        result = subprocess.run(
            ["podman", "pull", image],
            capture_output=True, text=True, timeout=PODMAN_PULL_TIMEOUT,
        )
        if result.returncode != 0:
            print(f"    WARNING: podman pull failed: {result.stderr.strip()[:200]}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"    WARNING: podman pull timed out after {PODMAN_PULL_TIMEOUT}s")
        return False


def extract_image_from_args(args: list[str]) -> str | None:
    """Find the container image reference in podman run args."""
    skip_next = False
    for i, arg in enumerate(args):
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


def query_mcp_tools(command: str, args: list[str], kubeconfig: str) -> list[str] | None:
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
                print(f"    Server exited immediately (code {proc.returncode}): {stderr.strip()}")
                return None
            time.sleep(0.1)

        send_jsonrpc(proc, INIT_MSG)
        resp = read_response(proc, expected_id=1, timeout=SERVER_START_TIMEOUT)
        if resp is None:
            print("    WARNING: no response to initialize")
            return None

        if "error" in resp:
            print(f"    WARNING: initialize error: {resp['error']}")
            return None

        server_info = resp.get("result", {}).get("serverInfo", {})
        print(f"    Server: {server_info.get('name', 'unknown')}")

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
                print(f"    WARNING: no response to tools/list (page {page})")
                return all_tools if all_tools else None

            if "error" in resp:
                print(f"    WARNING: tools/list error: {resp['error']}")
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
                else:
                    break
            if in_fm and stripped.startswith("allowed-tools:"):
                value = stripped[len("allowed-tools:"):].strip()
                return value, line_num
    return "", None


def find_packs(repo_root: Path) -> list[str]:
    """Find all packs that have both mcps.json and a skills directory."""
    packs = []
    for mcps_file in sorted(repo_root.glob("*/mcps.json")):
        pack_dir = mcps_file.parent
        if (pack_dir / "skills").is_dir():
            packs.append(pack_dir.name)
    return packs


def validate_pack(pack: str, repo_root: Path, kubeconfig: str) -> ValidationResult:
    """Validate all skills in a single pack against its MCP servers."""
    result = ValidationResult()
    pack_dir = repo_root / pack
    mcps_file = pack_dir / "mcps.json"

    if not mcps_file.exists():
        print(f"  WARNING: {pack}/mcps.json not found, skipping pack")
        return result

    try:
        with open(mcps_file) as f:
            config = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"  ERROR: failed to parse {pack}/mcps.json: {e}")
        result.failed += 1
        return result

    servers = config.get("mcpServers", {})
    all_available_tools: set[str] = set()

    for server_name, server_config in servers.items():
        command = server_config.get("command", "")

        if command not in ("podman", "docker"):
            reason = f"non-container command '{command}'"
            print(f"  SKIP server '{server_name}': {reason}")
            result.skipped_servers.append(f"{server_name} ({reason})")
            continue

        args = server_config.get("args", [])
        print(f"  Starting MCP server '{server_name}'...")

        image = extract_image_from_args(args)
        if image:
            if not pull_image(image):
                print(f"    WARNING: could not pull image, attempting to start anyway")

        tools = query_mcp_tools(command, args, kubeconfig)

        if tools is None:
            print(f"    WARNING: no tools returned (server may require credentials)")
            result.skipped_servers.append(f"{server_name} (no tools returned)")
            continue

        print(f"    {len(tools)} tools available")
        all_available_tools.update(tools)

    if all_available_tools:
        print(f"  Combined tool pool: {len(all_available_tools)} unique tools")

    skills_dir = pack_dir / "skills"
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
            print(f"  SKIP {pack}/{skill_name}: no allowed-tools declared")
            continue

        declared_tools = allowed_tools_str.split()
        missing = [t for t in declared_tools if t not in all_available_tools]

        if not missing:
            result.passed += 1
            print(f"  PASS {pack}/{skill_name}: all {len(declared_tools)} tools validated")
        else:
            result.failed += 1
            rel_path = str(skill_file.relative_to(repo_root))
            for tool in missing:
                suggestion = suggest_tool(tool, all_available_tools)
                finding = Finding(
                    skill=skill_name,
                    pack=pack,
                    tool=tool,
                    file_path=rel_path,
                    line_number=line_number,
                    suggestion=suggestion,
                )
                result.findings.append(finding)
                print(f"  FAIL {pack}/{skill_name}: {finding}")

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


def main(packs: list[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parent.parent

    skip_reason = check_prerequisites()
    if skip_reason:
        print(f"SKIP: {skip_reason} -- MCP tool validation requires podman and a cluster")
        return 0

    kubeconfig = os.environ.get("KUBECONFIG", "")
    if not kubeconfig:
        default = Path.home() / ".kube" / "config"
        if default.exists():
            kubeconfig = str(default)

    if not packs:
        packs = find_packs(repo_root)

    if not packs:
        print("No packs with mcps.json found")
        return 0

    print()
    print("=" * 66)
    print("           MCP Tool Validation Report")
    print("    Verifying allowed-tools against live MCP servers")
    print("=" * 66)
    print()
    print(f"Packs to validate: {', '.join(packs)}")
    print(f"KUBECONFIG: {kubeconfig}")
    print()

    combined = ValidationResult()

    for pack in packs:
        print(f"-- {pack} --")
        result = validate_pack(pack, repo_root, kubeconfig)
        combined.total_skills += result.total_skills
        combined.passed += result.passed
        combined.skipped += result.skipped
        combined.failed += result.failed
        combined.findings.extend(result.findings)
        combined.skipped_servers.extend(result.skipped_servers)
        print()

    print("=" * 66)
    print()
    print("VALIDATION SUMMARY")
    print("-" * 66)
    print(f"  Total skills:                {combined.total_skills}")
    print(f"  Passed:                      {combined.passed}")
    print(f"  Skipped (no allowed-tools):  {combined.skipped}")
    print(f"  Failed:                      {combined.failed}")
    print()

    if combined.skipped_servers:
        print("Skipped MCP servers:")
        for s in combined.skipped_servers:
            print(f"  - {s}")
        print()

    if combined.findings:
        print("FINDINGS:")
        for f in combined.findings:
            print(f"  - {f}")
        print()

    if not combined.success:
        print("VALIDATION FAILED - tool name mismatches detected")
        print("Check mcps.json for the correct tool names.")
        return 1
    elif combined.skipped > 0:
        print("PASSED WITH WARNINGS - some skills have no allowed-tools")
    else:
        print("ALL SKILLS PASSED")

    return 0


if __name__ == "__main__":
    sys.exit(main(packs=sys.argv[1:] if len(sys.argv) > 1 else None))

#!/usr/bin/env python3
"""
Validate skills against SKILL_DESIGN_PRINCIPLES.md.

This is the single Tier 2 validator for the repository (CI runs it via
ci-validate-changed-skills.sh).  Tier 1 (agentskills.io spec) is handled
separately by scripts/validate_skills_tier1.py.

Design principles checked:
  Frontmatter: model mandatory (inherit/sonnet/haiku), color mandatory
  Frontmatter: description should include 'NOT for' anti-pattern (WARNING)
  Heading:     first heading should follow '# /<name> Skill' format
  Heading:     overview paragraph after heading (WARNING)
  DP0: Plugin layout (Lola format) - mcps.json only, error if .mcp.json exists
  DP1: Document Consultation - correct format (Action: Read, Output to user)
  DP2: Parameter order - Document Consultation before MCP Tool/Parameters
  DP3: Conciseness - description length, "Use when" examples
  DP4: Dependencies - section with Required MCP Servers/Tools, Related Skills, Reference Docs
  DP5: Human-in-the-Loop - critical skills should have this section + confirmation reqs
  DP6: Mandatory sections - Prerequisites, When to Use This Skill, Workflow
  DP6 (extended): Late section order - Dependencies → Human-in-the-Loop → Example Usage
  DP7: Credential security - no echo $VAR (except in anti-pattern examples)
  DP7: Hardcoded credentials - password/secret/token with literal values (ERROR)
  When to Use: must include 'Do NOT use' anti-patterns (ERROR)
  When to Use: anti-patterns should reference alternative skills (WARNING)
  When to Use: should list 'Use when' scenarios (WARNING)
  Prerequisites content: MCP servers, verification, notification, credentials
  Workflow content: numbered steps, MCP Tools, Parameters, Error Handling
  File size: warn if SKILL.md exceeds 20 KB

Cannot validate: runtime behavior (AI actually reading docs), parameter correctness vs MCP schemas.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import yaml

# Design principle constants
MAX_DESCRIPTION_TOKENS = 500
# Rough token estimate: ~4 chars per token for English
CHARS_PER_TOKEN = 4
MAX_DESCRIPTION_CHARS = MAX_DESCRIPTION_TOKENS * CHARS_PER_TOKEN

VALID_MODELS = {"inherit", "sonnet", "haiku"}
VALID_COLORS = {"red", "blue", "green", "yellow", "cyan", "magenta"}

# Skills that perform critical operations (require Human-in-the-Loop section)
CRITICAL_SKILL_KEYWORDS = [
    "create",
    "delete",
    "update",
    "restore",
    "execute",
    "executor",
    "modify",
    "run",
    "deploy",
    "clone",
    "playbook-executor",
    "job-template-creator",
    "remediation",
]

# Required sections (DP6)
REQUIRED_SECTIONS = [
    "When to Use This Skill",
    "Workflow",
]
# Expected order when all present
ORDERED_SECTIONS = [
    "Prerequisites",
    "When to Use This Skill",
    "Workflow",
]

# Late sections: Dependencies → Human-in-the-Loop → Example Usage (when present)
# Human-in-the-Loop matches "Critical: Human-in-the-Loop Requirements" or "Human-in-the-Loop Requirements"
LATE_ORDERED_SECTIONS = [
    "Dependencies",
    "Human-in-the-Loop",
    "Example Usage",
]
LATE_SECTION_PATTERNS = {
    "Dependencies": r"^Dependencies$",
    "Human-in-the-Loop": r"Human-in-the-Loop",
    "Example Usage": r"^Example Usage$",
}
# Need at least 2 late sections present to validate their order
MIN_LATE_SECTIONS_FOR_ORDER_CHECK = 2

# Dependencies subsections (DP4)
DEPENDENCY_SUBSECTIONS = [
    "Required MCP Servers",
    "Required MCP Tools",
    "Related Skills",
    "Reference Documentation",
]

# Credential exposure patterns (DP7)
CREDENTIAL_EXPOSURE_PATTERN = re.compile(
    r"echo\s+\$\{?[A-Za-z_][A-Za-z0-9_]*\}?",
    re.MULTILINE,
)

# Anti-pattern context: if echo $VAR appears near these, it may be documenting the wrong way
ANTI_PATTERN_MARKERS = ["WRONG", "NEVER", "❌", "don't", "do not", "exposes credentials"]

# Hardcoded credential patterns (DP7)
HARDCODED_CREDENTIAL_PATTERN = re.compile(
    r"""(?:password|secret|token|api_key|apikey)\s*[=:]\s*["'][^$\s{]""",
    re.IGNORECASE,
)
# Values that are clearly placeholders, not real credentials
CREDENTIAL_PLACEHOLDER_PATTERNS = re.compile(
    r"\[REDACTED\]|\[placeholder\]|<your[-_]|xxx|changeme|replace[-_]me|example",
    re.IGNORECASE,
)

# Plugin layout (Lola format)
MCP_FILENAME = "mcps.json"
MCP_DEPRECATED = ".mcp.json"


def validate_plugin_layout(plugin_dir: Path) -> list[str]:
    """
    DP0: Plugin layout (Lola format).
    Error if .mcp.json exists; validate mcps.json structure if present.
    """
    errors = []
    deprecated = plugin_dir / MCP_DEPRECATED
    mcp_file = plugin_dir / MCP_FILENAME

    if deprecated.exists():
        errors.append(
            f"DP0: deprecated {MCP_DEPRECATED} found; rename to {MCP_FILENAME}"
        )
        return errors

    if not mcp_file.exists():
        return errors

    try:
        data = json.loads(mcp_file.read_text(encoding="utf-8"))
        if "mcpServers" not in data:
            errors.append(f"DP0: {MCP_FILENAME} missing 'mcpServers' key")
        elif not isinstance(data.get("mcpServers"), dict):
            errors.append(f"DP0: {MCP_FILENAME} 'mcpServers' must be an object")
    except Exception as e:
        errors.append(f"DP0: Invalid {MCP_FILENAME}: {e}")

    return errors


@dataclass
class ValidationResult:
    """Result of validating a single skill."""

    path: Path
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


def find_skill_files(plugin_dirs: list[str]) -> Iterator[Path]:
    """Yield paths to all SKILL.md files in plugin directories."""
    for plugin_dir in plugin_dirs:
        skills_dir = Path(plugin_dir) / "skills"
        if skills_dir.exists():
            yield from skills_dir.glob("*/SKILL.md")


def extract_frontmatter(content: str) -> tuple[dict | None, str]:
    """Extract YAML frontmatter and body from markdown content."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return None, content
    try:
        frontmatter = yaml.safe_load(match.group(1))
        body = content[match.end() :]
        return frontmatter, body
    except yaml.YAMLError:
        return None, content


def check_dp1_document_consultation(body: str, result: ValidationResult) -> None:
    """
    DP1: Document Consultation Transparency.
    - If Document Consultation appears, it must have Action: Read and Output to user.
    - Flag 'Transparency Theater' (output-only without Action).
    """
    doc_consult_blocks = re.findall(
        r"\*\*Document Consultation\*\*[^*]*(?:\*\*[^*]*\*\*[^*]*)*",
        body,
        re.DOTALL,
    )

    for block in doc_consult_blocks:
        has_action_read = "Read [" in block or "Read [" in block.replace("\n", " ")
        has_output = "Output to user" in block or "I consulted" in block

        # Transparency Theater: has output declaration but no Action
        if "Output to user" in block or "output to user" in block.lower():
            if not has_action_read and "Action" not in block:
                result.warnings.append(
                    "DP1: Document Consultation may be 'Transparency Theater' "
                    "(output declared but no 'Action: Read' - ensure AI actually reads the file)"
                )

        if has_action_read and not has_output:
            result.warnings.append(
                "DP1: Document Consultation has Action but missing 'Output to user' declaration"
            )


def check_dp2_parameter_order(body: str, result: ValidationResult) -> None:
    """
    DP2: Document consultation must appear BEFORE MCP Tool/Parameters.
    Check workflow steps that have both.
    """
    # Find workflow steps (### Step N or #### Option)
    step_pattern = re.compile(
        r"(###+ [^\n]+\n)(.*?)(?=###+ |\Z)",
        re.DOTALL,
    )

    for match in step_pattern.finditer(body):
        step_content = match.group(2)
        has_mcp_tool = "MCP Tool" in step_content or "**MCP Tool**" in step_content
        has_params = "**Parameters**" in step_content or "Parameters:" in step_content
        has_doc_consult = "Document Consultation" in step_content

        if (has_mcp_tool or has_params) and has_doc_consult:
            doc_pos = step_content.find("Document Consultation")
            tool_pos = step_content.find("MCP Tool")
            params_pos = step_content.find("Parameters")

            if tool_pos >= 0 and doc_pos > tool_pos:
                result.errors.append(
                    "DP2: Document Consultation must appear BEFORE MCP Tool in workflow step"
                )
            if params_pos >= 0 and doc_pos > params_pos and "Parameters" in step_content:
                result.errors.append(
                    "DP2: Document Consultation must appear BEFORE Parameters in workflow step"
                )


def check_dp3_conciseness(frontmatter: dict | None, result: ValidationResult) -> None:
    """
    DP3: Skill Precedence and Conciseness.
    - Description under 500 tokens.
    - Focus on 'when to use' with 3-5 examples.
    """
    if not frontmatter or "description" not in frontmatter:
        return

    desc = frontmatter["description"]
    if isinstance(desc, list):
        desc = "\n".join(desc)
    desc_str = str(desc).strip()

    # Token estimate
    char_count = len(desc_str)
    if char_count > MAX_DESCRIPTION_CHARS:
        result.warnings.append(
            f"DP3: Description may exceed 500 tokens "
            f"(~{char_count // CHARS_PER_TOKEN} tokens, {char_count} chars). "
            "Keep frontmatter concise; defer details to skill body."
        )

    # Use when examples
    if "Use when" not in desc_str and "use when" not in desc_str.lower():
        result.warnings.append(
            "DP3: Description should include 'Use when' with 3-5 concrete examples"
        )


def check_dp4_dependencies(body: str, result: ValidationResult) -> None:
    """
    DP4: Dependencies Declaration.
    Must have ## Dependencies with required subsections.
    """
    if "## Dependencies" not in body:
        result.errors.append("DP4: Missing '## Dependencies' section")
        return

    # Use (?=\n## |\Z) to avoid matching "## " inside "### " (subsection headers)
    deps_section = re.search(
        r"## Dependencies\s*\n(.*?)(?=\n## |\Z)",
        body,
        re.DOTALL,
    )
    if not deps_section:
        return

    section_content = deps_section.group(1)
    for subsection in DEPENDENCY_SUBSECTIONS:
        if subsection not in section_content:
            result.warnings.append(
                f"DP4: Dependencies section should include '### {subsection}'"
            )


def check_dp5_human_in_loop(
    name: str, body: str, result: ValidationResult
) -> None:
    """
    DP5: Human-in-the-Loop Requirements.
    Critical skills (executor, playbook, etc.) must have this section.
    When the section exists, it must specify confirmation requirements.
    """
    is_critical = any(kw in name.lower() for kw in CRITICAL_SKILL_KEYWORDS)
    has_section = "Human-in-the-Loop" in body or "Human-in-the-Loop Requirements" in body

    if is_critical and not has_section:
        result.warnings.append(
            "DP5: Skill performs critical operations (execution/modification). "
            "Consider adding '## Critical: Human-in-the-Loop Requirements' section."
        )

    if has_section:
        hitl_match = re.search(
            r"## (?:Critical: )?Human-in-the-Loop[^\n]*\n(.*?)(?=\n## |\Z)",
            body,
            re.DOTALL,
        )
        if hitl_match:
            hitl_content = hitl_match.group(1).lower()
            if (
                "confirmation" not in hitl_content
                and "confirm" not in hitl_content
                and "approval" not in hitl_content
                and "never assume" not in hitl_content
            ):
                result.warnings.append(
                    "DP5: Human-in-the-Loop section should specify confirmation requirements"
                )


def check_when_to_use_content(body: str, result: ValidationResult) -> None:
    """
    'When to Use This Skill' section checks:
    - Must include 'Do NOT use' anti-patterns (ERROR).
    - Anti-patterns should reference alternative skills (WARNING).
    - Should list 'Use when' scenarios (WARNING).
    """
    if "## When to Use This Skill" not in body:
        return

    wtu_match = re.search(
        r"## When to Use This Skill\s*\n(.*?)(?=\n## |\Z)", body, re.DOTALL
    )
    if not wtu_match:
        return

    content = wtu_match.group(1)
    content_lower = content.lower()

    if not re.search(r"use.*when|trigger.*when|invoke.*when", content_lower):
        result.warnings.append(
            "'When to Use' section should list specific scenarios (use when / trigger when)"
        )

    has_anti = (
        "do not" in content_lower
        or "not for" in content_lower
        or "not when" in content_lower
    )
    if not has_anti:
        result.warnings.append(
            "'When to Use' section must include 'Do NOT use' anti-patterns"
        )
    else:
        if not re.search(r"use.*skill|instead|alternative", content_lower):
            result.warnings.append(
                "'When to Use' anti-patterns should reference alternative skills by name"
            )


def check_description_anti_pattern(
    frontmatter: dict | None, result: ValidationResult
) -> None:
    """Description should include 'NOT for' anti-pattern (WARNING)."""
    if not frontmatter or "description" not in frontmatter:
        return

    desc = str(frontmatter["description"]).strip().lower()
    if "not for" not in desc and "do not" not in desc and "not for" not in desc:
        result.warnings.append(
            "Description should include 'NOT for' anti-pattern for routing"
        )


def check_dp6_mandatory_sections(body: str, result: ValidationResult) -> None:
    """
    DP6: Mandatory Skill Sections.
    Must have When to Use This Skill, Workflow. Prerequisites is optional.
    When present, sections must appear in order: Prerequisites, When to Use, Workflow.
    """
    section_headings = re.findall(r"^## ([^\n#]+)", body, re.MULTILINE)

    for required in REQUIRED_SECTIONS:
        if required not in section_headings:
            result.errors.append(f"DP6: Missing required section '## {required}'")
            return

    # Check order for sections that are present (Prerequisites, When to Use, Workflow)
    indices = []
    for i, heading in enumerate(section_headings):
        for req in ORDERED_SECTIONS:
            if req in heading or heading.strip() == req:
                indices.append((ORDERED_SECTIONS.index(req), i))
                break

    if len(indices) >= 2:
        indices.sort(key=lambda x: x[0])
        for i in range(1, len(indices)):
            if indices[i][1] < indices[i - 1][1]:
                result.warnings.append(
                    f"DP6: Sections should appear in order: "
                    f"{', '.join(ORDERED_SECTIONS)}"
                )
                break


def check_dp6_late_section_order(body: str, result: ValidationResult) -> None:
    """
    DP6 (extended): Late section order.
    When present, these sections must appear in order: Dependencies → Human-in-the-Loop → Example Usage.
    """
    section_headings = re.findall(r"^## ([^\n#]+)", body, re.MULTILINE)

    # Build (order_index, position) for each present late section
    indices = []
    for i, heading in enumerate(section_headings):
        heading_stripped = heading.strip()
        for section_key, pattern in LATE_SECTION_PATTERNS.items():
            if re.search(pattern, heading_stripped, re.IGNORECASE):
                order_idx = LATE_ORDERED_SECTIONS.index(section_key)
                indices.append((order_idx, i, section_key))
                break

    if len(indices) < MIN_LATE_SECTIONS_FOR_ORDER_CHECK:
        return

    # Sort by document position, then verify order_index is non-decreasing
    indices_by_pos = sorted(indices, key=lambda x: x[1])
    for i in range(1, len(indices_by_pos)):
        if indices_by_pos[i][0] < indices_by_pos[i - 1][0]:
            result.warnings.append(
                f"DP6: Late sections should appear in order: "
                f"{' → '.join(LATE_ORDERED_SECTIONS)} "
                f"(found {indices_by_pos[i - 1][2]} before {indices_by_pos[i][2]})"
            )
            break


def check_dp7_credential_exposure(body: str, result: ValidationResult) -> None:
    """
    DP7: MCP Server Availability Verification - no credential exposure.
    Flag echo $VAR unless it's in an anti-pattern example (WRONG, NEVER, ❌).
    """
    lines = body.split("\n")
    in_code_block = False
    code_block_context = ""

    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            if in_code_block:
                code_block_context = ""
            continue

        if in_code_block:
            code_block_context += line + "\n"
        else:
            code_block_context = line

        match = CREDENTIAL_EXPOSURE_PATTERN.search(line)
        if match:
            # Check if this is in a "wrong example" context
            context_before = "\n".join(lines[max(0, i - 10) : i]).lower()
            is_anti_pattern = any(
                marker.lower() in context_before for marker in ANTI_PATTERN_MARKERS
            )
            if not is_anti_pattern:
                result.errors.append(
                    f"DP7: Potential credential exposure at line {i + 1}: "
                    f"'{match.group().strip()}'. "
                    "Never echo env vars; use 'test -n \"$VAR\"' or report presence/absence only."
                )


def check_hardcoded_credentials(body: str, result: ValidationResult) -> None:
    """
    DP7: Detect hardcoded credentials (ERROR).
    Flags password="value", secret="value", token="value" etc. with literal values.
    Skips lines inside anti-pattern examples (WRONG, NEVER, ❌).
    """
    lines = body.split("\n")
    in_code_block = False

    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue

        if HARDCODED_CREDENTIAL_PATTERN.search(line):
            if CREDENTIAL_PLACEHOLDER_PATTERNS.search(line):
                continue
            context_before = "\n".join(lines[max(0, i - 10) : i]).lower()
            is_anti_pattern = any(
                marker.lower() in context_before for marker in ANTI_PATTERN_MARKERS
            )
            if not is_anti_pattern:
                result.errors.append(
                    f"DP7: Possible hardcoded credentials at line {i + 1}: "
                    f"'{line.strip()[:80]}'. "
                    "Never hardcode credentials; use ${{ENV_VAR}} references."
                )


def check_frontmatter_fields(
    frontmatter: dict | None,
    result: ValidationResult,
) -> None:
    """Check required frontmatter fields (name, description, model, color)."""
    if not frontmatter:
        result.errors.append("Missing or invalid YAML frontmatter")
        return

    required = ["name", "description", "model", "color"]
    for field_name in required:
        if field_name not in frontmatter:
            result.errors.append(f"Frontmatter missing required field: {field_name}")

    if "model" in frontmatter:
        model_val = str(frontmatter["model"]).strip().lower()
        if model_val not in VALID_MODELS:
            result.errors.append(
                f"Frontmatter 'model' must be one of: {', '.join(sorted(VALID_MODELS))} "
                f"(got '{frontmatter['model']}')"
            )

    if "color" in frontmatter:
        color_val = str(frontmatter["color"]).strip().lower()
        if color_val not in VALID_COLORS:
            result.errors.append(
                f"Frontmatter 'color' must be one of: {', '.join(sorted(VALID_COLORS))} "
                f"(got '{frontmatter['color']}')"
            )

    if "metadata" in frontmatter:
        meta = frontmatter["metadata"]
        if not isinstance(meta, dict):
            result.warnings.append(
                "Frontmatter 'metadata' should be a key-value map (dict), not a string or list"
            )


def check_heading_format(
    frontmatter: dict | None, body: str, result: ValidationResult
) -> None:
    """Check that the first heading follows '# /<name> Skill' or '# [Name] Skill' format.
    Also checks for an overview paragraph (1-2 sentences) after the heading."""
    heading_match = re.search(r"^# (.+)$", body, re.MULTILINE)
    if not heading_match:
        result.warnings.append(
            "Missing level 1 heading (# ) after frontmatter"
        )
        return

    heading_text = heading_match.group(1).strip()
    if not heading_text.endswith("Skill"):
        skill_name = frontmatter.get("name", "") if frontmatter else ""
        result.warnings.append(
            f"Heading '{heading_text}' should follow format: "
            f"'/{skill_name} Skill' or '[Skill Name] Skill'"
        )

    after_heading = body[heading_match.end():]
    first_nonblank = ""
    for line in after_heading.split("\n"):
        stripped = line.strip()
        if stripped:
            first_nonblank = stripped
            break
    if not first_nonblank or first_nonblank.startswith("#"):
        result.warnings.append(
            "Missing overview paragraph (1-2 sentences) immediately after heading"
        )


def check_prerequisites_content(body: str, result: ValidationResult) -> None:
    """Check Prerequisites section content when present."""
    if "## Prerequisites" not in body:
        return

    prereqs_match = re.search(
        r"## Prerequisites\s*\n(.*?)(?=\n## |\Z)", body, re.DOTALL
    )
    if not prereqs_match:
        return

    content = prereqs_match.group(1).lower()

    if "mcp server" not in content and "mcp_server" not in content:
        result.warnings.append(
            "Prerequisites should list Required MCP Servers"
        )
    if "verification" not in content and "verify" not in content:
        result.warnings.append(
            "Prerequisites should include verification steps"
        )
    if "human notification" not in content and "error protocol" not in content:
        result.warnings.append(
            "Prerequisites should include human notification protocol"
        )
    has_cred_warning = (
        ("never" in content and ("display" in content or "expose" in content))
        or "credential" in content
    )
    if not has_cred_warning:
        result.warnings.append(
            "Prerequisites should warn against exposing credentials"
        )


def check_workflow_content(body: str, result: ValidationResult) -> None:
    """Check Workflow section has numbered steps, MCP tools, parameters, error handling."""
    if "## Workflow" not in body:
        return

    workflow_match = re.search(
        r"## Workflow\s*\n(.*?)(?=\n## |\Z)", body, re.DOTALL
    )
    if not workflow_match:
        return

    content = workflow_match.group(1)

    if not re.search(r"^### Step\s+\d|^### \d+[.:]", content, re.MULTILINE):
        result.warnings.append(
            "Workflow should have numbered steps (### Step N: or ### 1.)"
        )

    has_mcp_tool = "**MCP Tool**" in content or "MCP Tool" in content
    if not has_mcp_tool:
        result.warnings.append(
            "Workflow should specify MCP Tools used"
        )

    if has_mcp_tool and "**Parameters**" not in content and "Parameters:" not in content:
        result.warnings.append(
            "Workflow steps with MCP Tools should specify parameters"
        )

    if "error handling" not in content.lower() and "error_handling" not in content.lower():
        result.warnings.append(
            "Workflow steps should include error handling"
        )


def validate_skill(skill_path: Path) -> ValidationResult:
    """Run all design principle checks on a skill file."""
    result = ValidationResult(path=skill_path)

    try:
        content = skill_path.read_text(encoding="utf-8")
    except Exception as e:
        result.errors.append(f"Could not read file: {e}")
        return result

    frontmatter, body = extract_frontmatter(content)

    content_bytes = len(content.encode("utf-8"))
    if content_bytes > 20480:
        result.warnings.append(
            f"SKILL.md is large ({content_bytes} bytes). "
            "Consider moving content to references/"
        )

    check_frontmatter_fields(frontmatter, result)
    check_heading_format(frontmatter, body, result)
    check_description_anti_pattern(frontmatter, result)
    check_dp1_document_consultation(body, result)
    check_dp2_parameter_order(body, result)
    check_dp3_conciseness(frontmatter, result)
    check_dp4_dependencies(body, result)
    check_dp5_human_in_loop(
        frontmatter.get("name", "") if frontmatter else "", body, result
    )
    check_dp6_mandatory_sections(body, result)
    check_dp6_late_section_order(body, result)
    check_dp7_credential_exposure(body, result)
    check_hardcoded_credentials(body, result)
    check_when_to_use_content(body, result)
    check_prerequisites_content(body, result)
    check_workflow_content(body, result)

    return result


RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
BLUE = "\033[0;34m"
BOLD = "\033[1m"
NC = "\033[0m"

SEPARATOR = "=" * 70


def _rel(path: Path) -> Path:
    cwd = Path.cwd()
    return path.relative_to(cwd) if path.is_relative_to(cwd) else path


def _plugin_name(skill_path: Path) -> str:
    """Extract plugin name from a skill path like rh-sre/skills/cve-impact/SKILL.md."""
    if skill_path.parent.parent.name == "skills":
        return str(skill_path.parent.parent.parent)
    return str(skill_path.parent)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate skills against SKILL_DESIGN_PRINCIPLES.md"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["rh-sre", "rh-developer", "ocp-admin", "rh-virt", "rh-ai-engineer", "rh-automation", "rh-basic"],
        help="Plugin directories or specific SKILL.md paths to validate",
    )
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Treat warnings as errors",
    )
    args = parser.parse_args()

    # Resolve paths to skill files
    skill_files: list[Path] = []
    for p in args.paths:
        path = Path(p)
        if path.is_file() and path.name == "SKILL.md":
            skill_files.append(path)
        elif path.is_dir():
            skills_dir = path / "skills"
            if skills_dir.exists():
                skill_files.extend(skills_dir.glob("*/SKILL.md"))
        else:
            plugin_path = Path(p)
            if (plugin_path / "skills").exists():
                skill_files.extend((plugin_path / "skills").glob("*/SKILL.md"))

    all_errors: list[tuple[Path, str]] = []
    all_warnings: list[tuple[Path, str]] = []

    # Collect plugin dirs for layout validation
    plugin_dirs: set[Path] = set()
    for p in args.paths:
        path = Path(p)
        if path.is_dir() and path.exists():
            plugin_dirs.add(path)
    for sf in skill_files:
        if sf.parent.parent.name == "skills":
            plugin_dirs.add(sf.parent.parent.parent)

    # DP0: Plugin layout (Lola format)
    for plugin_dir in sorted(plugin_dirs):
        if plugin_dir.exists():
            layout_errors = validate_plugin_layout(plugin_dir)
            for err in layout_errors:
                all_errors.append((plugin_dir, err))

    if not skill_files:
        if all_errors:
            print(f"{RED}❌ Plugin layout validation failed:{NC}")
            for path, err in all_errors:
                print(f"  • {path}: {err}")
            return 1
        print("No SKILL.md files found to validate.")
        return 0

    print(SEPARATOR)
    print(f"{BOLD}  Skill Design Principles Validator (Tier 2){NC}")
    print(SEPARATOR)
    print()

    # Validate and group results by plugin
    results_by_plugin: dict[str, list[tuple[Path, ValidationResult]]] = {}
    for skill_path in sorted(skill_files):
        result = validate_skill(skill_path)
        plugin = _plugin_name(skill_path)
        results_by_plugin.setdefault(plugin, []).append((skill_path, result))

        if result.errors:
            for err in result.errors:
                all_errors.append((skill_path, err))
        if result.warnings:
            for warn in result.warnings:
                all_warnings.append((skill_path, warn))
                if args.warnings_as_errors:
                    all_errors.append((skill_path, f"[WARN] {warn}"))

    # Print results grouped by plugin
    total_skills = 0
    passed_skills = 0
    warned_skills = 0
    failed_skills = 0

    for plugin, plugin_results in sorted(results_by_plugin.items()):
        print(SEPARATOR)
        print(f"{BOLD}  Plugin: {plugin}{NC}")
        print(SEPARATOR)

        for skill_path, result in plugin_results:
            skill_name = skill_path.parent.name
            total_skills += 1

            if result.errors:
                failed_skills += 1
                print(f"  {RED}❌{NC} {skill_name}")
                for err in result.errors:
                    print(f"     {RED}•{NC} {err}")
                for warn in result.warnings:
                    print(f"     {YELLOW}•{NC} {warn}")
            elif result.warnings:
                warned_skills += 1
                print(f"  {YELLOW}⚠{NC}  {skill_name}")
                for warn in result.warnings:
                    print(f"     {YELLOW}•{NC} {warn}")
            else:
                passed_skills += 1
                print(f"  {GREEN}✓{NC}  {skill_name}")

        print()

    # DP0 plugin layout errors
    if all_errors and any(e.startswith("DP0:") for _, e in all_errors):
        layout_errs = [(p, e) for p, e in all_errors if e.startswith("DP0:")]
        print(SEPARATOR)
        print(f"{BOLD}  Plugin Layout (DP0){NC}")
        print(SEPARATOR)
        for path, err in layout_errs:
            print(f"  {RED}❌{NC} {_rel(path)}: {err}")
        print()

    # Summary
    print(SEPARATOR)
    print(f"{BOLD}  Summary{NC}")
    print(SEPARATOR)
    print(f"  Total skills:  {total_skills}")
    print(f"  {GREEN}✓{NC}  Passed:     {passed_skills}")
    print(f"  {YELLOW}⚠{NC}  Warnings:   {warned_skills}")
    print(f"  {RED}❌{NC} Failed:     {failed_skills}")
    print(SEPARATOR)

    if all_errors or (args.warnings_as_errors and all_warnings):
        print(f"{RED}{BOLD}❌ Validation failed{NC}")
        return 1

    if all_warnings:
        print(f"{GREEN}{BOLD}✅ Validation passed{NC} {YELLOW}(with warnings){NC}")
    else:
        print(f"{GREEN}{BOLD}✅ All skills validated successfully{NC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

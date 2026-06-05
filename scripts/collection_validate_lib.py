"""
Shared validation for <pack>/.catalog/collection.yaml (JSON Schema in catalog/schema.yaml, roster, banners,
#fragment refs on top-level prose fields, JSON mirror).
Used by validate_collection_schema.py and validate_collection_compliance.py.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml
from jsonschema import Draft202012Validator

import pack_registry

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_YAML_PATH = REPO_ROOT / "catalog" / "schema.yaml"

YAML_BANNER_MARKERS = ("create-collection", "Golden sources")

FORBIDDEN_WORKFLOW_TOKENS = ("TODO:", "TBD", "FIXME:", "Extract from README")

# Inline prose in collection.yaml longer than this must move to a sibling .md and use a #fragment ref.
CATALOG_INLINE_CHAR_LIMIT = 500

# Top-level keys: if present as inline strings, length is checked (skills blocks excluded).
# File refs use the same `#name.md` form as deploy_and_use — not counted as "inline" for length.
CATALOG_INLINE_LENGTH_KEYS = ("documentation_section", "mcp_section", "security_model", "summary")

# Deprecated: use documentation_section / mcp_section / security_model with inline or #fragment.md (same as deploy_and_use).
DEPRECATED_CATALOG_FILE_KEYS = (
    "documentation_section_file",
    "mcp_section_file",
    "security_model_file",
)

# Top-level fields that may be inline markdown or a one-line `#fragment.md` (validation + site bundle).
CATALOG_FRAGMENT_FIELD_KEYS = (
    "documentation_section",
    "mcp_section",
    "security_model",
    "deploy_and_use",
)

_SCHEMA_CACHE: Optional[Dict[str, Any]] = None
_VALIDATOR_CACHE: Optional[Draft202012Validator] = None


def normalize_external_file_ref(ref: str) -> str:
    """Strip leading ``#`` and optional ``.catalog/`` prefix; remainder is a path under ``<pack>/.catalog/``."""
    s = ref.strip()
    if s.startswith("#"):
        s = s[1:].lstrip()
    if len(s) >= 9 and s[:9].lower() == ".catalog/":
        s = s[9:]
    return s


def catalog_fragment_rel_path(value: str) -> Optional[str]:
    """If ``value`` is a one-line ``#name.md`` ref (sibling of ``collection.yaml``), return relative path; else ``None``."""
    s = value.strip()
    if "\n" in s or "\r" in s:
        return None
    m = re.fullmatch(r"#\s*(?:\.catalog/)?([\w./-]+\.md)\s*", s, flags=re.IGNORECASE)
    if not m:
        return None
    rel = m.group(1)
    if ".." in rel or rel.startswith("/"):
        return None
    return rel


def deploy_and_use_external_rel_path(value: str) -> Optional[str]:
    """If ``deploy_and_use`` is file-ref flavor, return path under ``.catalog/``; else ``None`` (inline markdown)."""
    return catalog_fragment_rel_path(value)


def _load_schema() -> Dict[str, Any]:
    global _SCHEMA_CACHE, _VALIDATOR_CACHE
    if _SCHEMA_CACHE is not None:
        return _SCHEMA_CACHE
    path = SCHEMA_YAML_PATH if SCHEMA_YAML_PATH.exists() else None
    if not path:
        raise FileNotFoundError(f"Missing catalog schema at {SCHEMA_YAML_PATH}")
    with open(path, "r", encoding="utf-8") as f:
        _SCHEMA_CACHE = yaml.safe_load(f)
    Draft202012Validator.check_schema(_SCHEMA_CACHE)
    _VALIDATOR_CACHE = Draft202012Validator(_SCHEMA_CACHE)
    return _SCHEMA_CACHE


def get_validator() -> Draft202012Validator:
    _load_schema()
    assert _VALIDATOR_CACHE is not None
    return _VALIDATOR_CACHE


def collection_json_dumps(data: Any) -> str:
    """Deterministic JSON text for collection.json (must match committed file)."""
    return json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def read_yaml_catalog(pack_dir: str, root: Optional[Path] = None) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    root = root or REPO_ROOT
    p = root / pack_dir / ".catalog" / "collection.yaml"
    if not p.exists():
        return None, [f"{pack_dir}: missing {p.relative_to(root)}"]
    try:
        with open(p, "r", encoding="utf-8") as f:
            raw = f.read()
        data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            return None, [f"{pack_dir}: collection.yaml must parse to a mapping"]
        return data, []
    except Exception as e:
        return None, [f"{pack_dir}: failed to parse collection.yaml: {e}"]


def catalog_yaml_path(pack_dir: str, root: Optional[Path] = None) -> Path:
    root = root or REPO_ROOT
    return root / pack_dir / ".catalog" / "collection.yaml"


def _parse_yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _find_top_level_key_line(yaml_path: Path, key: str) -> Optional[int]:
    pattern = re.compile(rf"^{re.escape(key)}:\s")
    for line_no, line in enumerate(yaml_path.read_text(encoding="utf-8").splitlines(), 1):
        if pattern.match(line):
            return line_no
    return None


def catalog_skill_name_line_map(yaml_path: Path) -> Dict[str, int]:
    """Map skill name to 1-based line number in contents.skills / orchestration_skills."""
    lines = yaml_path.read_text(encoding="utf-8").splitlines()
    section: Optional[str] = None
    result: Dict[str, int] = {}
    for line_no, line in enumerate(lines, 1):
        if re.match(r"^  skills:\s*$", line):
            section = "skills"
            continue
        if re.match(r"^  orchestration_skills:\s*$", line):
            section = "orchestration_skills"
            continue
        if section and re.match(r"^  \S", line) and not line.startswith("    "):
            section = None
        match = re.match(r"^    - name:\s*(.+?)\s*$", line)
        if match and section in {"skills", "orchestration_skills"}:
            result[_parse_yaml_scalar(match.group(1))] = line_no
    return result


def catalog_decision_guide_skill_line_map(yaml_path: Path) -> Dict[str, int]:
    """Map skill_to_use value to 1-based line number in skills_decision_guide."""
    lines = yaml_path.read_text(encoding="utf-8").splitlines()
    in_guide = False
    result: Dict[str, int] = {}
    for line_no, line in enumerate(lines, 1):
        if re.match(r"^  skills_decision_guide:\s*$", line):
            in_guide = True
            continue
        if in_guide and re.match(r"^  \S", line) and not line.startswith("    "):
            in_guide = False
        match = re.match(r"^      skill_to_use:\s*(.+?)\s*$", line)
        if match and in_guide:
            result[_parse_yaml_scalar(match.group(1))] = line_no
    return result


def _yaml_loc(pack_dir: str, yaml_path: Path, line: Optional[int], root: Path) -> str:
    rel = yaml_path.relative_to(root)
    return f"{rel}:{line}" if line else str(rel)


def describe_json_mirror_drift(
    pack_dir: str, yaml_data: Dict[str, Any], root: Optional[Path] = None,
) -> List[str]:
    """Explain how collection.json differs from collection.yaml with field paths and line numbers."""
    root = root or REPO_ROOT
    yaml_path = catalog_yaml_path(pack_dir, root)
    json_path = root / pack_dir / ".catalog" / "collection.json"
    try:
        json_data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{pack_dir}: .catalog/collection.json is invalid JSON: {exc}"]

    errs: List[str] = []
    skill_lines = catalog_skill_name_line_map(yaml_path)
    reg_y, orch_y = catalog_skill_names(yaml_data)
    reg_j, orch_j = catalog_skill_names(json_data)

    for group, ylist, jlist in (
        ("contents.skills", reg_y, reg_j),
        ("contents.orchestration_skills", orch_y, orch_j),
    ):
        if ylist == jlist:
            continue
        max_len = max(len(ylist), len(jlist))
        for i in range(max_len):
            yn = ylist[i] if i < len(ylist) else None
            jn = jlist[i] if i < len(jlist) else None
            if yn == jn:
                continue
            line = skill_lines.get(str(yn or "")) or skill_lines.get(str(jn or ""))
            loc = _yaml_loc(pack_dir, yaml_path, line, root)
            errs.append(
                f"{pack_dir}: {loc} {group}[{i}].name out of sync: "
                f"collection.yaml={yn!r}, collection.json={jn!r}"
            )

    for key in ("version", "description", "name", "id", "maturity"):
        yv = yaml_data.get(key)
        jv = json_data.get(key)
        if yv != jv:
            line = _find_top_level_key_line(yaml_path, key)
            loc = _yaml_loc(pack_dir, yaml_path, line, root)
            errs.append(
                f"{pack_dir}: {loc} {key} out of sync: "
                f"collection.yaml={yv!r}, collection.json={jv!r}"
            )

    if not errs:
        errs.append(
            f"{pack_dir}: .catalog/collection.json content differs from collection.yaml "
            "(run diff or regenerate JSON to inspect)"
        )
    errs.append(
        f"{pack_dir}: regenerate mirror with: "
        f"uv run python scripts/catalog_yaml_to_json.py --pack {pack_dir}"
    )
    return errs


def validate_yaml_banner(pack_dir: str, root: Optional[Path] = None) -> List[str]:
    root = root or REPO_ROOT
    p = root / pack_dir / ".catalog" / "collection.yaml"
    if not p.exists():
        return []
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as e:
        return [f"{pack_dir}: cannot read collection.yaml: {e}"]
    head = "\n".join(text.splitlines()[:40])
    missing = [m for m in YAML_BANNER_MARKERS if m not in head]
    if missing:
        return [
            f"{pack_dir}: collection.yaml must start with a # comment banner mentioning: "
            + ", ".join(YAML_BANNER_MARKERS)
        ]
    return []


def validate_deprecated_catalog_file_keys(pack_dir: str, data: Dict[str, Any]) -> List[str]:
    """Reject legacy ``*_file`` split keys; prose fields use the same key for inline or ``#fragment.md``."""
    errs: List[str] = []
    for k in DEPRECATED_CATALOG_FILE_KEYS:
        if k in data and data[k] is not None and str(data[k]).strip() != "":
            base = k[: -len("_file")]
            errs.append(
                f"{pack_dir}: deprecated key {k!r}; use {base!r} with inline markdown or "
                f"a one-line fragment ref like '#{base}.md' (same pattern as deploy_and_use; see COLLECTION_SPEC.md)."
            )
    return errs


def _collect_top_level_catalog_fragment_refs(data: Dict[str, Any]) -> List[str]:
    """Fragment refs on top-level fields that may be inline markdown or #sibling.md (like deploy_and_use)."""
    refs: List[str] = []
    for key in CATALOG_FRAGMENT_FIELD_KEYS:
        v = data.get(key)
        if isinstance(v, str) and v.strip() and catalog_fragment_rel_path(v):
            refs.append(v.strip())
    return refs


def validate_file_refs(pack_dir: str, data: Dict[str, Any], root: Optional[Path] = None) -> List[str]:
    root = root or REPO_ROOT
    refs = _collect_top_level_catalog_fragment_refs(data)
    errs: List[str] = []
    pack_root = root / pack_dir
    catalog_dir = (pack_root / ".catalog").resolve()
    for ref in refs:
        if not ref.strip().startswith("#"):
            errs.append(
                f"{pack_dir}: fragment ref must start with '#' (e.g. #install.md), got {ref!r}"
            )
            continue
        path_part = normalize_external_file_ref(ref)
        if not path_part:
            errs.append(f"{pack_dir}: empty fragment path after normalizing {ref!r}")
            continue
        if ".." in path_part or path_part.startswith("/"):
            errs.append(f"{pack_dir}: invalid fragment path {ref!r}")
            continue
        target = (catalog_dir / path_part).resolve()
        try:
            target.relative_to(catalog_dir)
        except ValueError:
            errs.append(f"{pack_dir}: fragment {ref!r} escapes .catalog/ directory")
            continue
        if not target.is_file():
            errs.append(f"{pack_dir}: missing fragment file {path_part} (from {ref!r})")
    return errs


def validate_embedded_docs(pack_dir: str, data: Dict[str, Any], root: Optional[Path] = None) -> List[str]:
    root = root or REPO_ROOT
    errs: List[str] = []
    pack_root = root / pack_dir
    for i, r in enumerate(data.get("resources") or []):
        if not isinstance(r, dict):
            continue
        ed = r.get("embedded_doc")
        if not ed or not str(ed).strip():
            continue
        rel = str(ed).strip()
        target = (pack_root / rel).resolve()
        if not target.is_file():
            errs.append(f"{pack_dir}: resources[{i}].embedded_doc missing file {rel}")
    return errs


def list_disk_skill_names(pack_dir: str, root: Optional[Path] = None) -> List[str]:
    root = root or REPO_ROOT
    skills_dir = root / pack_dir / "skills"
    if not skills_dir.is_dir():
        return []
    names = sorted(p.name for p in skills_dir.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())
    return names


def list_external_pack_skill_names(pack_root: Path) -> List[str]:
    """Return skill directory names from an external pack checkout."""
    skills_dir = pack_root / "skills"
    if not skills_dir.is_dir():
        return []
    return sorted(
        p.name for p in skills_dir.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()
    )


def validate_external_skill_roster(
    label: str,
    data: Dict[str, Any],
    external_skills: Set[str],
    yaml_path: Optional[Path] = None,
    root: Optional[Path] = None,
) -> List[str]:
    """Compare catalog YAML skill names to skills present in an external pack checkout."""
    root = root or REPO_ROOT
    reg, orch = catalog_skill_names(data)
    yaml_names = reg + orch
    errs: List[str] = []
    skill_lines = catalog_skill_name_line_map(yaml_path) if yaml_path and yaml_path.is_file() else {}
    guide_lines = (
        catalog_decision_guide_skill_line_map(yaml_path) if yaml_path and yaml_path.is_file() else {}
    )

    if len(yaml_names) != len(set(yaml_names)):
        errs.append(f"{label}: duplicate skill name in contents.skills / orchestration_skills")

    seen = set(reg) | set(orch)
    for n in reg + orch:
        if n not in external_skills:
            line = skill_lines.get(n)
            loc = _yaml_loc(label, yaml_path, line, root) if yaml_path and line else label
            expected = sorted(external_skills)
            hint = f" (external pack skills at ref: {', '.join(expected)})" if expected else ""
            errs.append(
                f"{label}: {loc} lists skill {n!r} but external pack has no skills/{n}/SKILL.md at ref{hint}"
            )

    for d in external_skills:
        if d not in seen:
            errs.append(
                f"{label}: external pack skill {d!r} missing from collection.yaml "
                f"contents.skills / orchestration_skills"
            )

    contents = data.get("contents") or {}
    guide = (contents or {}).get("skills_decision_guide") or []
    if not external_skills and guide:
        errs.append(f"{label}: skills_decision_guide must be empty when the external pack has no skills/")
    for i, row in enumerate(guide):
        if not isinstance(row, dict):
            continue
        st = row.get("skill_to_use")
        if external_skills and st and st not in external_skills:
            line = guide_lines.get(str(st))
            loc = _yaml_loc(label, yaml_path, line, root) if yaml_path and line else label
            errs.append(
                f"{label}: {loc} skills_decision_guide[{i}] skill_to_use {st!r} "
                f"not in external pack skills/ at ref"
            )
        if external_skills and st and st not in seen:
            line = guide_lines.get(str(st))
            loc = _yaml_loc(label, yaml_path, line, root) if yaml_path and line else label
            errs.append(
                f"{label}: {loc} skills_decision_guide[{i}] skill_to_use {st!r} "
                f"not listed in contents.skills / orchestration_skills"
            )
    return errs


def catalog_skill_names(data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    contents = data.get("contents") or {}
    if not isinstance(contents, dict):
        return [], []
    reg: List[str] = []
    orch: List[str] = []
    for s in contents.get("skills") or []:
        if isinstance(s, dict) and s.get("name"):
            reg.append(str(s["name"]))
    for s in contents.get("orchestration_skills") or []:
        if isinstance(s, dict) and s.get("name"):
            orch.append(str(s["name"]))
    return reg, orch


def validate_skill_roster(pack_dir: str, data: Dict[str, Any], root: Optional[Path] = None) -> List[str]:
    disk = set(list_disk_skill_names(pack_dir, root))
    reg, orch = catalog_skill_names(data)
    yaml_names = reg + orch
    errs: List[str] = []

    if len(yaml_names) != len(set(yaml_names)):
        errs.append(f"{pack_dir}: duplicate skill name in contents.skills / orchestration_skills")

    seen = set(reg) | set(orch)
    for n in reg + orch:
        if n not in disk:
            errs.append(f"{pack_dir}: YAML lists skill {n!r} with no skills/{n}/SKILL.md on disk")

    for d in disk:
        if d not in seen:
            errs.append(f"{pack_dir}: on-disk skill {d!r} missing from collection.yaml contents")
    return errs


def validate_json_mirror(pack_dir: str, data: Dict[str, Any], root: Optional[Path] = None) -> List[str]:
    root = root or REPO_ROOT
    json_path = root / pack_dir / ".catalog" / "collection.json"
    if not json_path.exists():
        return [f"{pack_dir}: missing .catalog/collection.json (run make catalog-mirror-json)"]
    expected = collection_json_dumps(data)
    actual = json_path.read_text(encoding="utf-8")
    if actual != expected:
        return describe_json_mirror_drift(pack_dir, data, root)
    return []


def validate_schema_instance(pack_dir: str, data: Dict[str, Any]) -> List[str]:
    v = get_validator()
    errs = [f"{pack_dir}: schema: {'/'.join(str(x) for x in e.path)}: {e.message}" for e in v.iter_errors(data)]
    return errs


def validate_pack_iteration3(
    pack_dir: str, root: Optional[Path] = None, check_banner: bool = True,
    is_federated: bool = False,
) -> List[str]:
    """Iteration 3: schema + fragment refs + roster + optional YAML banner (no collection.json mirror).

    When *is_federated* is ``True`` the roster check is skipped because
    federated modules store their skills in an external repository.
    """
    root = root or REPO_ROOT
    data, errs = read_yaml_catalog(pack_dir, root)
    if errs or data is None:
        return errs
    out: List[str] = []
    out.extend(validate_deprecated_catalog_file_keys(pack_dir, data))
    out.extend(validate_schema_instance(pack_dir, data))
    out.extend(validate_file_refs(pack_dir, data, root))
    if not is_federated:
        out.extend(validate_skill_roster(pack_dir, data, root))
    if check_banner:
        out.extend(validate_yaml_banner(pack_dir, root))
    return out


def validate_pack_iteration5(
    pack_dir: str, root: Optional[Path] = None, is_federated: bool = False,
) -> List[str]:
    """Full collection compliance: Iteration 3 + semantic rules + JSON mirror drift."""
    root = root or REPO_ROOT
    errs = validate_pack_iteration3(pack_dir, root, check_banner=True, is_federated=is_federated)
    data, e = read_yaml_catalog(pack_dir, root)
    errs.extend(e)
    if data:
        errs.extend(validate_pack_catalog_compliance_extra(pack_dir, data, root, is_federated=is_federated))
        errs.extend(validate_json_mirror(pack_dir, data, root))
    return errs


def validate_pack_catalog_compliance_extra(
    pack_dir: str, data: Dict[str, Any], root: Optional[Path] = None,
    is_federated: bool = False,
) -> List[str]:
    """Iteration 5 semantic checks.

    When *is_federated* is ``True``, on-disk skill existence and decision-guide
    cross-checks are skipped (skills live in the external repository).
    """
    root = root or REPO_ROOT
    errs: List[str] = []
    contents = data.get("contents")
    if isinstance(contents, dict):
        for group, label in (
            (contents.get("skills") or [], "contents.skills"),
            (contents.get("orchestration_skills") or [], "contents.orchestration_skills"),
        ):
            for i, s in enumerate(group):
                if not isinstance(s, dict):
                    continue
                name = s.get("name")
                desc = (s.get("description") or "").strip()
                sm = (s.get("summary_markdown") or "").strip()
                if not name or not desc:
                    errs.append(f"{pack_dir}: {label}[{i}] requires name and description")
                if len(sm) < 20:
                    errs.append(f"{pack_dir}: {label}[{i}] summary_markdown too short (<20 chars)")
                if not is_federated:
                    skill_md = (root / pack_dir / "skills" / str(name) / "SKILL.md")
                    if not skill_md.is_file():
                        errs.append(
                            f"{pack_dir}: {label}[{i}] name {name!r} must match skills/<name>/ directory "
                            f"(missing {skill_md.relative_to(root)})"
                        )

    if not is_federated:
        disk_skill_names = set(list_disk_skill_names(pack_dir, root))
        guide = (contents or {}).get("skills_decision_guide") or []
        if not disk_skill_names and guide:
            errs.append(f"{pack_dir}: skills_decision_guide must be empty when the pack has no skills/")
        for i, row in enumerate(guide):
            if not isinstance(row, dict):
                continue
            st = row.get("skill_to_use")
            if disk_skill_names and st and st not in disk_skill_names:
                errs.append(f"{pack_dir}: skills_decision_guide[{i}] skill_to_use {st!r} not a known skill dir")

    for i, wf in enumerate(data.get("sample_workflows") or []):
        if not isinstance(wf, dict):
            continue
        w = (wf.get("workflow") or "")
        for tok in FORBIDDEN_WORKFLOW_TOKENS:
            if tok in w:
                errs.append(f"{pack_dir}: sample_workflows[{i}] contains forbidden token {tok!r}")
        if "User:" not in w and 'User: "' not in w:
            errs.append(f"{pack_dir}: sample_workflows[{i}] workflow must include User: line")
        if "-" not in w:
            errs.append(f"{pack_dir}: sample_workflows[{i}] workflow must use bullet lines (-)")

    errs.extend(validate_embedded_docs(pack_dir, data, root))
    errs.extend(validate_catalog_inline_length(pack_dir, data))
    return errs


def validate_catalog_inline_length(pack_dir: str, data: Dict[str, Any]) -> List[str]:
    """Require long prose to use a #fragment .md ref (sibling of collection.yaml), not huge inline strings."""
    errs: List[str] = []
    for key in CATALOG_INLINE_LENGTH_KEYS:
        val = data.get(key)
        if not isinstance(val, str):
            continue
        if catalog_fragment_rel_path(val):
            continue
        if len(val) > CATALOG_INLINE_CHAR_LIMIT:
            errs.append(
                f"{pack_dir}: {key} is {len(val)} chars (limit {CATALOG_INLINE_CHAR_LIMIT}); "
                f"move prose to a sibling .md under .catalog/ and set {key}: '#<filename>.md' "
                f"(same pattern as deploy_and_use)."
            )
    dau = data.get("deploy_and_use")
    if isinstance(dau, str) and not deploy_and_use_external_rel_path(dau):
        if len(dau) > CATALOG_INLINE_CHAR_LIMIT:
            errs.append(
                f"{pack_dir}: deploy_and_use is {len(dau)} chars inline (limit {CATALOG_INLINE_CHAR_LIMIT}); "
                "use markdown in a sibling .md and deploy_and_use: #<filename>.md"
            )
    return errs


def validate_all_iteration3(root: Optional[Path] = None, check_banner: bool = True) -> List[str]:
    root = root or REPO_ROOT
    all_errs: List[str] = []
    for pack in pack_registry.get_union_pack_dirs(root):
        cat = root / pack / ".catalog" / "collection.yaml"
        if not cat.exists():
            all_errs.append(f"{pack}: missing .catalog/collection.yaml")
            continue
        all_errs.extend(validate_pack_iteration3(pack, root, check_banner=check_banner))
    for fed in pack_registry.get_federation_module_dirs(root):
        all_errs.extend(validate_pack_iteration3(fed, root, check_banner=check_banner, is_federated=True))
    return all_errs


def validate_all_iteration5(root: Optional[Path] = None) -> List[str]:
    root = root or REPO_ROOT
    all_errs: List[str] = []
    for pack in pack_registry.get_union_pack_dirs(root):
        cat = root / pack / ".catalog" / "collection.yaml"
        if not cat.exists():
            all_errs.append(f"{pack}: missing .catalog/collection.yaml")
            continue
        all_errs.extend(validate_pack_iteration5(pack, root))
    for fed in pack_registry.get_federation_module_dirs(root):
        all_errs.extend(validate_pack_iteration5(fed, root, is_federated=True))
    return all_errs

#!/usr/bin/env python3
"""Regression tests for skill references/ layout validation."""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = Path(__file__).resolve().parent


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, _SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


compass = _load_module("validate_compass_manifests", "validate_compass_manifests.py")
docs_tree = _load_module("validate_docs_tree_links", "validate_docs_tree_links.py")
skill_links = _load_module("validate_skill_doc_links", "validate_skill_doc_links.py")
tier1 = _load_module("validate_skills_tier1", "validate_skills_tier1.py")


def _minimal_skill_md(name: str) -> str:
    return f"""---
name: {name}
description: Test skill for layout validation.
license: Apache-2.0
model: inherit
color: cyan
---

# /{name}

## Workflow

Read [target.md](references/target.md) before acting.
"""


class _RepoFixtureTestCase(unittest.TestCase):
    """Create plugin fixtures under the repo so compass checks can build rel paths."""

    fixture_root: Path

    def setUp(self) -> None:
        self.fixture_root = _REPO_ROOT / ".validate" / "layout-fixtures" / self.id().split(".")[-1]
        if self.fixture_root.exists():
            for path in sorted(self.fixture_root.rglob("*"), reverse=True):
                if path.is_file() or path.is_symlink():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()
        self.fixture_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        if not self.fixture_root.exists():
            return
        for path in sorted(self.fixture_root.rglob("*"), reverse=True):
            if path.is_file() or path.is_symlink():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        self.fixture_root.rmdir()


class TestCompassSkillDocsLayout(_RepoFixtureTestCase):
    def test_leftover_docs_directory_flagged(self) -> None:
        skill_dir = self.fixture_root / "skills" / "demo-skill"
        (skill_dir / "docs").mkdir(parents=True)
        (skill_dir / "docs" / "stale.md").write_text("# stale\n", encoding="utf-8")

        errors: list[str] = []
        compass._check_skill_docs_layout(skill_dir, errors)

        self.assertTrue(errors)
        self.assertIn("docs", errors[0])

    def test_nested_references_references_flagged(self) -> None:
        skill_dir = self.fixture_root / "skills" / "demo-skill"
        nested = skill_dir / "references" / "references"
        nested.mkdir(parents=True)
        (nested / "nested.md").write_text("# nested\n", encoding="utf-8")

        errors: list[str] = []
        compass._check_skill_docs_layout(skill_dir, errors)

        self.assertTrue(errors)
        self.assertIn("references/references/", errors[0])

    def test_missing_shared_script_symlink_flagged(self) -> None:
        plugin_dir = self.fixture_root
        group_dir = plugin_dir / "scripts" / "demo-group"
        group_dir.mkdir(parents=True)
        (group_dir / "run.py").write_text("# run\n", encoding="utf-8")
        (group_dir / "config.yaml").write_text("key: value\n", encoding="utf-8")

        scripts_dir = plugin_dir / "skills" / "demo-skill" / "scripts"
        scripts_dir.mkdir(parents=True)
        os.symlink("../../../scripts/demo-group/run.py", scripts_dir / "run.py")

        errors: list[str] = []
        compass._check_skill_scripts_layout(
            plugin_dir.name, plugin_dir / "skills" / "demo-skill", errors
        )

        self.assertTrue(errors)
        self.assertIn("config.yaml", errors[0])

    def test_forbidden_plugin_scripts_path_in_skill_markdown_flagged(self) -> None:
        plugin_dir = self.fixture_root
        plugin = plugin_dir.name
        skill_dir = plugin_dir / "skills" / "demo-skill"
        group_dir = plugin_dir / "scripts" / "demo-group"
        group_dir.mkdir(parents=True)
        (group_dir / "run.py").write_text("# run\n", encoding="utf-8")

        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(parents=True)
        os.symlink("../../../scripts/demo-group/run.py", scripts_dir / "run.py")

        refs = skill_dir / "references"
        refs.mkdir(parents=True)
        (refs / "guide.md").write_text(
            f"Run python3 {plugin}/scripts/demo-group/run.py\n",
            encoding="utf-8",
        )

        errors: list[str] = []
        compass._check_skill_scripts_layout(plugin, skill_dir, errors)

        self.assertTrue(errors)
        self.assertTrue(
            any(f"{plugin}/scripts/" in err and "authoring-repo" in err for err in errors),
            msg=f"expected plugin scripts path error, got: {errors}",
        )

    def test_shared_script_symlinks_complete_passes(self) -> None:
        plugin_dir = self.fixture_root
        plugin = plugin_dir.name
        skill_dir = plugin_dir / "skills" / "demo-skill"
        group_dir = plugin_dir / "scripts" / "demo-group"
        group_dir.mkdir(parents=True)
        (group_dir / "run.py").write_text("# run\n", encoding="utf-8")
        (group_dir / "config.yaml").write_text("key: value\n", encoding="utf-8")
        (group_dir / "test_extra.py").write_text("# test\n", encoding="utf-8")

        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(parents=True)
        os.symlink("../../../scripts/demo-group/run.py", scripts_dir / "run.py")
        os.symlink(
            "../../../scripts/demo-group/config.yaml", scripts_dir / "config.yaml"
        )

        refs = skill_dir / "references"
        refs.mkdir(parents=True)
        (refs / "guide.md").write_text(
            "Run `python3 scripts/run.py` and `oc apply -f scripts/config.yaml`.\n",
            encoding="utf-8",
        )

        errors: list[str] = []
        compass._check_skill_scripts_layout(plugin, skill_dir, errors)

        self.assertEqual(errors, [])

    def test_forbidden_docs_markdown_link_flagged(self) -> None:
        skill_dir = self.fixture_root / "skills" / "demo-skill"
        refs = skill_dir / "references"
        refs.mkdir(parents=True)
        (refs / "ok.md").write_text("# ok\n", encoding="utf-8")
        (skill_dir / "SKILL.md").write_text(
            "# Skill\n\nSee [stale](docs/stale.md).\n", encoding="utf-8"
        )

        errors: list[str] = []
        compass._check_skill_docs_layout(skill_dir, errors)

        self.assertTrue(errors)
        self.assertIn("docs/", errors[0])

    def test_tier1_rejects_docs_subdirectory(self) -> None:
        skill_dir = self.fixture_root / "demo-skill"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "docs").mkdir()
        skill_path = skill_dir / "SKILL.md"
        skill_path.write_text(_minimal_skill_md("demo-skill"), encoding="utf-8")

        result = tier1.validate_skill(skill_path)
        self.assertTrue(any("docs/" in err for err in result.errors))


class TestDocsTreeLinks(unittest.TestCase):
    def test_readme_docs_link_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin = Path(tmp) / "demo-plugin"
            (plugin / "skills" / "demo-skill").mkdir(parents=True)
            readme = plugin / "README.md"
            readme.write_text(
                "See [docs index](docs/INDEX.md) for navigation.\n", encoding="utf-8"
            )

            errors = docs_tree.validate_file(readme, plugin)
            self.assertTrue(errors)
            self.assertIn("docs/INDEX.md", errors[0])


class TestSkillDocLinks(unittest.TestCase):
    def test_symlink_chain_detected_without_premature_resolve(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin = Path(tmp) / "demo-plugin"
            skill_dir = plugin / "skills" / "demo-skill"
            refs = skill_dir / "references"
            refs.mkdir(parents=True)
            (refs / "leaf.md").write_text("# leaf\n", encoding="utf-8")
            os.symlink("mid.md", refs / "entry.md")
            os.symlink("leaf.md", refs / "mid.md")

            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(_minimal_skill_md("demo-skill"), encoding="utf-8")
            skill_md.write_text(
                skill_md.read_text(encoding="utf-8").replace(
                    "references/target.md", "references/entry.md"
                ),
                encoding="utf-8",
            )

            result = skill_links.ValidationResult(scanned_files=1)
            skill_links.validate_skill_file(skill_md, result)

            self.assertTrue(
                any("symlink chain" in err for err in result.errors),
                msg=f"expected symlink chain error, got: {result.errors}",
            )


class TestPluginDualWriteIncludes(unittest.TestCase):
    _PLUGIN_REF = "airesource:ai5-marketplace/rh-basic"
    _PLUGIN_PATH = _REPO_ROOT / "rh-basic" / "rh-basic-plugin.yaml"
    _PLUGIN_DATA = {"metadata": {"labels": {"distribution": "external"}}}
    _DISK = frozenset({"skill-a"})

    def _errors(self, plugin_spec: dict) -> list[str]:
        errors: list[str] = []
        compass._validate_plugin_dual_write(
            self._PLUGIN_PATH,
            self._PLUGIN_REF,
            self._PLUGIN_DATA,
            plugin_spec,
            set(self._DISK),
            {},
            errors,
        )
        return errors

    def _base_spec(self, **overrides: object) -> dict:
        spec = {
            "skills": ["airesource:ai5-marketplace/skill-a"],
            "includes": [
                {"entityRef": "airesource:ai5-marketplace/skill-a", "type": "skill"},
            ],
            "dependsOn": [],
        }
        spec.update(overrides)
        return spec

    def test_empty_includes_rejected(self) -> None:
        errors = self._errors(self._base_spec(includes=[]))
        self.assertTrue(any("includes must not be empty" in e for e in errors))

    def test_empty_skills_rejected(self) -> None:
        errors = self._errors(self._base_spec(skills=[]))
        self.assertTrue(any("spec.skills must not be empty" in e for e in errors))

    def test_empty_disk_rejected(self) -> None:
        errors: list[str] = []
        compass._validate_plugin_dual_write(
            self._PLUGIN_PATH,
            self._PLUGIN_REF,
            self._PLUGIN_DATA,
            self._base_spec(),
            set(),
            {},
            errors,
        )
        self.assertTrue(any("plugin has no skills on disk" in e for e in errors), msg=errors)

    def test_duplicate_entity_ref_rejected(self) -> None:
        spec = self._base_spec(
            includes=[
                {"entityRef": "airesource:ai5-marketplace/skill-a", "type": "skill"},
                {"entityRef": "airesource:ai5-marketplace/skill-a", "type": "skill"},
            ],
        )
        errors = self._errors(spec)
        self.assertTrue(any("duplicate includes entityRef" in e for e in errors))

    def test_self_include_rejected(self) -> None:
        spec = self._base_spec(
            includes=[
                {"entityRef": "airesource:ai5-marketplace/skill-a", "type": "skill"},
                {"entityRef": self._PLUGIN_REF, "type": "skill"},
            ],
        )
        errors = self._errors(spec)
        self.assertTrue(any("must not self-reference the plugin" in e for e in errors))
        self.assertFalse(
            any("unknown skills" in e for e in errors),
            msg=errors,
        )

    def test_plugin_typed_member_rejected(self) -> None:
        spec = self._base_spec(
            includes=[
                {"entityRef": "airesource:ai5-marketplace/skill-a", "type": "skill"},
                {
                    "entityRef": "airesource:ai5-marketplace/other-plugin",
                    "type": "plugin",
                },
            ],
        )
        errors = self._errors(spec)
        self.assertTrue(any("must not include a plugin member" in e for e in errors))
        self.assertFalse(
            any("unknown skills" in e for e in errors),
            msg=errors,
        )
        self.assertFalse(
            any("type must be skill or mcp-server" in e for e in errors),
            msg=errors,
        )

    def test_string_includes_entry_rejected(self) -> None:
        spec = self._base_spec(
            includes=["airesource:ai5-marketplace/skill-a"],
        )
        errors = self._errors(spec)
        self.assertTrue(any("must be a mapping, not a string" in e for e in errors))

    def test_omitted_plugin_dependencyOf_skill_roster_ok(self) -> None:
        errors = self._errors(self._base_spec())
        depof_errors = [e for e in errors if "dependencyOf" in e]
        self.assertEqual(depof_errors, [], msg=errors)

    def test_canonical_default_mcp_rejected_from_includes(self) -> None:
        spec = self._base_spec(
            includes=[
                {"entityRef": "airesource:ai5-marketplace/skill-a", "type": "skill"},
                {
                    "entityRef": "mcpserver:default/security-mcp-server",
                    "type": "mcp-server",
                },
            ],
        )
        errors = self._errors(spec)
        self.assertTrue(
            any(
                "canonical MCP" in e and "mcpserver:default/security-mcp-server" in e
                for e in errors
            ),
            msg=errors,
        )

    def test_malformed_skills_still_checked_against_disk(self) -> None:
        spec = self._base_spec(skills=["mcpserver:redhat/not-a-skill"])
        errors = self._errors(spec)
        self.assertTrue(any("must be airesource refs" in e for e in errors), msg=errors)
        self.assertTrue(any("spec.skills missing" in e for e in errors), msg=errors)
        self.assertTrue(
            any("spec.skills and spec.includes skill rosters must match" in e for e in errors),
            msg=errors,
        )

    def test_null_plugin_spec_does_not_crash(self) -> None:
        errors: list[str] = []
        compass._validate_plugin_dual_write(
            self._PLUGIN_PATH,
            self._PLUGIN_REF,
            self._PLUGIN_DATA,
            None,  # YAML `spec:` parses to None
            set(self._DISK),
            {},
            errors,
        )
        self.assertTrue(any("missing spec.skills" in e for e in errors), msg=errors)
        self.assertTrue(any("missing spec.includes" in e for e in errors), msg=errors)

    def test_includes_type_required(self) -> None:
        spec = self._base_spec(
            includes=[{"entityRef": "airesource:ai5-marketplace/skill-a"}],
        )
        errors = self._errors(spec)
        self.assertTrue(any("type is required" in e for e in errors), msg=errors)
        self.assertFalse(any("unknown skills" in e for e in errors), msg=errors)
        self.assertFalse(any("spec.includes missing skills" in e for e in errors), msg=errors)

    def test_non_string_includes_type_rejected(self) -> None:
        spec = self._base_spec(
            includes=[
                {"entityRef": "airesource:ai5-marketplace/skill-a", "type": ["skill"]},
            ],
        )
        errors = self._errors(spec)
        self.assertTrue(
            any("type must be skill or mcp-server" in e for e in errors),
            msg=errors,
        )

    def test_includes_type_must_match_entity_ref(self) -> None:
        spec = self._base_spec(
            includes=[
                {"entityRef": "airesource:ai5-marketplace/skill-a", "type": "mcp-server"},
                {"entityRef": "mcpserver:ai5-marketplace/owned-mcp", "type": "skill"},
            ],
        )
        errors = self._errors(spec)
        self.assertTrue(
            any("type must be skill to match entityRef" in e for e in errors),
            msg=errors,
        )
        self.assertTrue(
            any("type must be mcp-server to match entityRef" in e for e in errors),
            msg=errors,
        )
        self.assertFalse(any("unknown skills" in e for e in errors), msg=errors)
        self.assertFalse(any("spec.includes missing skills" in e for e in errors), msg=errors)


class TestSkillConventions(unittest.TestCase):
    _PATH = _REPO_ROOT / "rh-basic" / "skills" / "skill-a" / "catalog-info.yaml"

    def _errors(self, data: dict) -> list[str]:
        errors: list[str] = []
        compass._check_skill_conventions(self._PATH, data, errors)
        return errors

    def _skill_data(self, **spec_overrides: object) -> dict:
        spec: dict[str, object] = {
            "type": "skill",
            "owner": compass._EXPECTED_OWNER,
            "agents": [],
        }
        spec.update(spec_overrides)
        return {
            "metadata": {
                "namespace": compass._EXPECTED_NAMESPACE,
                "labels": {"distribution": "external"},
            },
            "spec": spec,
        }

    def test_plugin_only_fields_rejected_on_skills(self) -> None:
        data = self._skill_data(
            includes=[{"entityRef": "airesource:ai5-marketplace/skill-a", "type": "skill"}],
            skills=["airesource:ai5-marketplace/skill-a"],
            system="default/agentic-plugins",
        )
        errors = self._errors(data)
        for key in ("includes", "skills", "system"):
            self.assertTrue(
                any(f"spec.{key} is plugin-only" in e for e in errors),
                msg=errors,
            )

    def test_valid_skill_spec_has_no_plugin_only_errors(self) -> None:
        errors = self._errors(self._skill_data())
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()

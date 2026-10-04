#!/usr/bin/env python3
"""Unit tests for the Compass lifecycle validator."""

from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

_SCRIPTS = Path(__file__).resolve().parent


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, _SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


lifecycle_ceiling = _load_module("validate_lifecycle_ceiling", "validate_lifecycle_ceiling.py")


def _write_manifest(
    path: Path,
    *,
    name: str,
    kind: str = "AiResource",
    lifecycle: str | None = "__unset__",
    distribution: str | None = None,
) -> None:
    """Write a minimal Compass manifest. lifecycle='__unset__' omits the field entirely."""
    data: dict = {
        "apiVersion": "backstage.io/v1alpha1",
        "kind": kind,
        "metadata": {"name": name},
        "spec": {},
    }
    if distribution is not None:
        data["metadata"]["labels"] = {"distribution": distribution}
    if lifecycle != "__unset__":
        data["spec"]["lifecycle"] = lifecycle
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _write_root_catalog(root: Path, packs: list[str]) -> None:
    data = {
        "apiVersion": "backstage.io/v1alpha1",
        "kind": "Location",
        "metadata": {"name": "agentic-plugins"},
        "spec": {"targets": [f"./{pack}/catalog-info.yaml" for pack in packs] + ["./mcps/catalog-info.yaml"]},
    }
    (root / "catalog-info.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    (root / "mcps").mkdir(parents=True, exist_ok=True)
    (root / "mcps" / "catalog-info.yaml").write_text(
        yaml.safe_dump({"apiVersion": "backstage.io/v1alpha1", "kind": "Location", "spec": {"targets": []}}),
        encoding="utf-8",
    )


def _write_mcp(root: Path, name: str, *, lifecycle: str, distribution: str | None = None) -> None:
    path = root / "mcps" / f"{name}.yaml"
    _write_manifest(
        path,
        name=name,
        kind="MCPServer",
        lifecycle=lifecycle,
        distribution=distribution,
    )
    catalog = root / "mcps" / "catalog-info.yaml"
    data = yaml.safe_load(catalog.read_text(encoding="utf-8"))
    targets = data.setdefault("spec", {}).setdefault("targets", [])
    target = f"./{name}.yaml"
    if target not in targets:
        targets.append(target)
    catalog.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _write_pack(
    root: Path,
    pack: str,
    *,
    plugin_lifecycle: str | None = "__unset__",
    skills: dict[str, str | None] | None = None,
    plugin_distribution: str | None = None,
    skill_distributions: dict[str, str] | None = None,
) -> None:
    """Create <pack>/<pack>-plugin.yaml and <pack>/skills/<skill>/catalog-info.yaml files."""
    pack_dir = root / pack
    _write_manifest(
        pack_dir / f"{pack}-plugin.yaml",
        name=pack,
        lifecycle=plugin_lifecycle,
        distribution=plugin_distribution,
    )
    for skill_name, skill_lifecycle in (skills or {}).items():
        dist = (skill_distributions or {}).get(skill_name)
        _write_manifest(
            pack_dir / "skills" / skill_name / "catalog-info.yaml",
            name=skill_name,
            lifecycle=skill_lifecycle,
            distribution=dist,
        )
    (root / pack / "catalog-info.yaml").write_text(
        yaml.safe_dump({"apiVersion": "backstage.io/v1alpha1", "kind": "Location", "spec": {"targets": []}}),
        encoding="utf-8",
    )


class _TempRepoTestCase(unittest.TestCase):
    repo_root: Path

    def setUp(self) -> None:
        self.repo_root = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.repo_root, ignore_errors=True)


class TestLifecycleRank(unittest.TestCase):
    def test_known_lifecycles_ordered(self) -> None:
        self.assertEqual(lifecycle_ceiling.lifecycle_rank("development"), 0)
        self.assertEqual(lifecycle_ceiling.lifecycle_rank("beta"), 1)
        self.assertEqual(lifecycle_ceiling.lifecycle_rank("GA"), 2)

    def test_ga_case_insensitive(self) -> None:
        self.assertEqual(lifecycle_ceiling.lifecycle_rank("ga"), 2)
        self.assertEqual(lifecycle_ceiling.normalize_lifecycle("Ga"), "GA")

    def test_missing_lifecycle_defaults_to_development(self) -> None:
        self.assertEqual(
            lifecycle_ceiling.lifecycle_rank(None),
            lifecycle_ceiling.lifecycle_rank("development"),
        )

    def test_unknown_lifecycle_raises(self) -> None:
        with self.assertRaises(ValueError):
            lifecycle_ceiling.lifecycle_rank("production")
        with self.assertRaises(ValueError):
            lifecycle_ceiling.lifecycle_rank("preview")

    def test_is_deprecated(self) -> None:
        self.assertTrue(lifecycle_ceiling.is_deprecated("deprecated"))
        self.assertTrue(lifecycle_ceiling.is_deprecated("Deprecated"))
        self.assertFalse(lifecycle_ceiling.is_deprecated("beta"))
        self.assertFalse(lifecycle_ceiling.is_deprecated(None))

    def test_is_ceiling_exempt(self) -> None:
        self.assertTrue(lifecycle_ceiling.is_ceiling_exempt("deprecated"))
        self.assertTrue(lifecycle_ceiling.is_ceiling_exempt("archived"))
        self.assertFalse(lifecycle_ceiling.is_ceiling_exempt("GA"))
        self.assertFalse(lifecycle_ceiling.is_ceiling_exempt("beta"))

    def test_is_allowed_lifecycle(self) -> None:
        for value in ("development", "beta", "GA", "deprecated", "archived", "ga"):
            self.assertTrue(lifecycle_ceiling.is_allowed_lifecycle(value), value)
        self.assertTrue(lifecycle_ceiling.is_allowed_lifecycle(None))
        self.assertFalse(lifecycle_ceiling.is_allowed_lifecycle("production"))
        self.assertFalse(lifecycle_ceiling.is_allowed_lifecycle("preview"))


class TestPassingCases(_TempRepoTestCase):
    def test_skill_equal_to_plugin_passes(self) -> None:
        _write_pack(self.repo_root, "rh-demo", plugin_lifecycle="beta", skills={"demo-skill": "beta"})

        errors: list[str] = []
        lifecycle_ceiling.check_pack(self.repo_root, "rh-demo", errors)

        self.assertEqual(errors, [])

    def test_skill_less_mature_than_plugin_passes(self) -> None:
        _write_pack(
            self.repo_root, "rh-demo", plugin_lifecycle="GA", skills={"demo-skill": "development"}
        )

        errors: list[str] = []
        lifecycle_ceiling.check_pack(self.repo_root, "rh-demo", errors)

        self.assertEqual(errors, [])

    def test_missing_lifecycles_default_to_development_and_pass(self) -> None:
        _write_pack(
            self.repo_root,
            "rh-demo",
            plugin_lifecycle="__unset__",
            skills={"demo-skill": "__unset__"},
        )

        errors: list[str] = []
        lifecycle_ceiling.check_pack(self.repo_root, "rh-demo", errors)

        self.assertEqual(errors, [])

    def test_multiple_skills_all_within_ceiling(self) -> None:
        _write_pack(
            self.repo_root,
            "rh-demo",
            plugin_lifecycle="beta",
            skills={"skill-a": "development", "skill-b": "beta"},
        )

        errors: list[str] = []
        lifecycle_ceiling.check_pack(self.repo_root, "rh-demo", errors)

        self.assertEqual(errors, [])


class TestFailCase(_TempRepoTestCase):
    def test_skill_more_mature_than_plugin_fails(self) -> None:
        _write_pack(self.repo_root, "rh-demo", plugin_lifecycle="development", skills={"demo-skill": "beta"})

        errors: list[str] = []
        lifecycle_ceiling.check_pack(self.repo_root, "rh-demo", errors)

        self.assertEqual(len(errors), 1)
        self.assertIn("demo-skill", errors[0])
        self.assertIn("'beta'", errors[0])
        self.assertIn("'development'", errors[0])

    def test_ga_skill_under_beta_plugin_fails(self) -> None:
        _write_pack(self.repo_root, "rh-demo", plugin_lifecycle="beta", skills={"demo-skill": "GA"})

        errors: list[str] = []
        lifecycle_ceiling.check_pack(self.repo_root, "rh-demo", errors)

        self.assertEqual(len(errors), 1)

    def test_only_offending_skill_is_reported(self) -> None:
        _write_pack(
            self.repo_root,
            "rh-demo",
            plugin_lifecycle="development",
            skills={"ok-skill": "development", "bad-skill": "GA"},
        )

        errors: list[str] = []
        lifecycle_ceiling.check_pack(self.repo_root, "rh-demo", errors)

        self.assertEqual(len(errors), 1)
        self.assertIn("bad-skill", errors[0])
        self.assertNotIn("ok-skill", errors[0])


class TestDeprecatedSkipLogic(_TempRepoTestCase):
    def test_deprecated_skill_is_skipped_even_if_more_mature(self) -> None:
        _write_pack(self.repo_root, "rh-demo", plugin_lifecycle="development", skills={"demo-skill": "deprecated"})

        errors: list[str] = []
        lifecycle_ceiling.check_pack(self.repo_root, "rh-demo", errors)

        self.assertEqual(errors, [])

    def test_archived_skill_is_skipped(self) -> None:
        _write_pack(self.repo_root, "rh-demo", plugin_lifecycle="development", skills={"demo-skill": "archived"})

        errors: list[str] = []
        lifecycle_ceiling.check_pack(self.repo_root, "rh-demo", errors)

        self.assertEqual(errors, [])

    def test_deprecated_plugin_skips_all_skills(self) -> None:
        _write_pack(
            self.repo_root,
            "rh-demo",
            plugin_lifecycle="deprecated",
            skills={"demo-skill": "GA"},
        )

        errors: list[str] = []
        lifecycle_ceiling.check_pack(self.repo_root, "rh-demo", errors)

        self.assertEqual(errors, [])

    def test_archived_plugin_skips_all_skills(self) -> None:
        _write_pack(
            self.repo_root,
            "rh-demo",
            plugin_lifecycle="archived",
            skills={"demo-skill": "GA"},
        )

        errors: list[str] = []
        lifecycle_ceiling.check_pack(self.repo_root, "rh-demo", errors)

        self.assertEqual(errors, [])

    def test_deprecated_skill_among_others_only_skips_itself(self) -> None:
        _write_pack(
            self.repo_root,
            "rh-demo",
            plugin_lifecycle="development",
            skills={"deprecated-skill": "deprecated", "bad-skill": "beta"},
        )

        errors: list[str] = []
        lifecycle_ceiling.check_pack(self.repo_root, "rh-demo", errors)

        self.assertEqual(len(errors), 1)
        self.assertIn("bad-skill", errors[0])
        self.assertNotIn("deprecated-skill", errors[0])


class TestAllowedValuesAndWarnings(_TempRepoTestCase):
    def test_invalid_lifecycle_on_skill_is_rejected(self) -> None:
        _write_root_catalog(self.repo_root, ["rh-demo"])
        _write_pack(self.repo_root, "rh-demo", plugin_lifecycle="beta", skills={"bad-skill": "production"})

        errors, warnings = lifecycle_ceiling.validate_all(self.repo_root)

        self.assertTrue(any("production" in err for err in errors))
        self.assertEqual(warnings, [])

    def test_invalid_lifecycle_on_mcp_is_rejected(self) -> None:
        _write_root_catalog(self.repo_root, [])
        _write_mcp(self.repo_root, "demo-mcp", lifecycle="production")

        errors, warnings = lifecycle_ceiling.validate_all(self.repo_root)

        self.assertTrue(any("production" in err for err in errors))
        self.assertEqual(warnings, [])

    def test_valid_ga_on_mcp_passes(self) -> None:
        _write_root_catalog(self.repo_root, [])
        _write_mcp(self.repo_root, "demo-mcp", lifecycle="GA")

        errors, warnings = lifecycle_ceiling.validate_all(self.repo_root)

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_external_development_warns_but_does_not_fail(self) -> None:
        _write_root_catalog(self.repo_root, ["rh-demo"])
        _write_pack(
            self.repo_root,
            "rh-demo",
            plugin_lifecycle="development",
            skills={"demo-skill": "development"},
            skill_distributions={"demo-skill": "external"},
        )

        errors, warnings = lifecycle_ceiling.validate_all(self.repo_root)

        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("demo-skill", warnings[0])
        self.assertIn("will not be published externally", warnings[0])

    def test_external_beta_does_not_warn(self) -> None:
        _write_root_catalog(self.repo_root, ["rh-demo"])
        _write_pack(
            self.repo_root,
            "rh-demo",
            plugin_lifecycle="beta",
            skills={"demo-skill": "beta"},
            skill_distributions={"demo-skill": "external"},
        )

        errors, warnings = lifecycle_ceiling.validate_all(self.repo_root)

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])


class TestValidateAll(_TempRepoTestCase):
    def test_validate_all_discovers_registered_packs_from_root_catalog(self) -> None:
        _write_root_catalog(self.repo_root, ["rh-good", "rh-bad"])
        _write_pack(self.repo_root, "rh-good", plugin_lifecycle="beta", skills={"good-skill": "beta"})
        _write_pack(self.repo_root, "rh-bad", plugin_lifecycle="development", skills={"bad-skill": "GA"})

        errors, warnings = lifecycle_ceiling.validate_all(self.repo_root)

        self.assertEqual(len(errors), 1)
        self.assertIn("bad-skill", errors[0])
        self.assertEqual(warnings, [])

    def test_validate_all_ignores_unregistered_packs(self) -> None:
        _write_root_catalog(self.repo_root, ["rh-good"])
        _write_pack(self.repo_root, "rh-good", plugin_lifecycle="beta", skills={"good-skill": "beta"})
        _write_pack(self.repo_root, "rh-bad", plugin_lifecycle="development", skills={"bad-skill": "GA"})

        errors, warnings = lifecycle_ceiling.validate_all(self.repo_root)

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_validate_all_missing_root_catalog_reports_error(self) -> None:
        errors, warnings = lifecycle_ceiling.validate_all(self.repo_root)

        self.assertEqual(len(errors), 1)
        self.assertIn("catalog-info.yaml", errors[0])
        self.assertEqual(warnings, [])

    def test_pack_missing_plugin_manifest_reports_error(self) -> None:
        _write_root_catalog(self.repo_root, ["rh-orphan"])
        (self.repo_root / "rh-orphan").mkdir(parents=True)

        errors, warnings = lifecycle_ceiling.validate_all(self.repo_root)

        self.assertEqual(len(errors), 1)
        self.assertIn("rh-orphan", errors[0])
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()

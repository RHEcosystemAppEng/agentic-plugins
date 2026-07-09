#!/usr/bin/env python3
"""Package skill packs into self-contained ZIPs."""

import argparse
import logging
import os
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PACK_EXCLUDE = {"scripts", "catalog", ".claude", ".github", ".lola", "docs", "eval"}


@dataclass
class PackageReport:
    total_packs: int = 0
    total_skills: int = 0
    total_size_bytes: int = 0
    broken_symlinks: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def discover_packs(root: Path) -> list[str]:
    return sorted(
        d.name for d in root.iterdir()
        if d.is_dir() and d.name not in _PACK_EXCLUDE and not d.name.startswith(".")
        and ((d / "AGENTS.md").exists() or (d / "skills").is_dir())
    )


def discover_skills(pack_dir: Path) -> list[Path]:
    skills_dir = pack_dir / "skills"
    if not skills_dir.is_dir():
        return []
    return sorted(
        d for d in skills_dir.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists()
    )


def create_pack_zip(pack_dir: Path, output_path: Path) -> tuple[int, int, list[str]]:
    """Create a single ZIP containing all skills for a pack. Returns (skill_count, file_count, broken_symlinks)."""
    skills = discover_skills(pack_dir)
    if not skills:
        return 0, 0, []

    broken_symlinks: list[str] = []
    file_count = 0

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for skill_dir in skills:
            skill_name = skill_dir.name
            for file_path in sorted(skill_dir.rglob("*")):
                if file_path.is_dir():
                    continue

                arcname = f"{skill_name}/{file_path.relative_to(skill_dir)}"

                if file_path.is_symlink():
                    resolved = file_path.resolve()
                    if not resolved.exists():
                        logger.warning("Broken symlink: %s -> %s", file_path, os.readlink(file_path))
                        broken_symlinks.append(str(file_path))
                        continue
                    zf.write(resolved, arcname)
                else:
                    zf.write(file_path, arcname)

                file_count += 1

    return len(skills), file_count, broken_symlinks


def package_all(
    root: Path,
    output_dir: Path,
    packs: list[str] | None = None,
) -> PackageReport:
    report = PackageReport()

    all_packs = discover_packs(root)
    target_packs = [p for p in all_packs if p in packs] if packs else all_packs
    report.total_packs = len(target_packs)

    for pack_name in target_packs:
        pack_dir = root / pack_name
        zip_path = output_dir / f"{pack_name}.zip"

        try:
            skill_count, file_count, broken = create_pack_zip(pack_dir, zip_path)
            if skill_count == 0:
                logger.info("Pack %s has no skills, skipping", pack_name)
                continue
            report.broken_symlinks.extend(broken)
            report.total_skills += skill_count
            zip_size = zip_path.stat().st_size
            report.total_size_bytes += zip_size
            logger.info("Packaged %s (%d skills, %d files, %d KB)", pack_name, skill_count, file_count, zip_size // 1024)
        except Exception as e:
            report.errors.append(f"{pack_name}: {e}")
            logger.error("Failed to package %s: %s", pack_name, e)

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Package skill packs into self-contained ZIPs")
    parser.add_argument("--output-dir", default="dist", help="Output directory (default: dist)")
    parser.add_argument("--packs", nargs="+", help="Only package these packs (default: all)")
    parser.add_argument("--root", default=str(_REPO_ROOT), help="Repository root (default: auto-detect)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    root = Path(args.root).resolve()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = root / output_dir

    report = package_all(root=root, output_dir=output_dir, packs=args.packs)

    print(f"\nPackaging complete: {report.total_packs} packs, {report.total_skills} skills, {report.total_size_bytes // 1024} KB")
    if report.broken_symlinks:
        print(f"  Warnings: {len(report.broken_symlinks)} broken symlinks skipped")
    if report.errors:
        print(f"  Errors: {len(report.errors)}")
        for err in report.errors:
            print(f"    - {err}")

    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())

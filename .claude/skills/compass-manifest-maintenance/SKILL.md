---
name: compass-manifest-maintenance
description: |
  Author and maintain Compass catalog-info.yaml manifests for agentic packs (skills, plugins, Locations, MCP inverse relations). Use when:
  - Adding or updating a skill and its Compass manifest
  - Registering an existing pack in Compass (manifests only; not creating a new agentic pack)
  - MCP usage or orchestration changed in SKILL.md
  - Auditing bidirectional dependsOn/dependencyOf drift against repo Compass conventions

  File-based only: Read/Glob/Grep/Bash. For `.catalog/` marketplace metadata use create-collection.

  NOT for: `.catalog/` metadata (use create-collection) or automated Compass registration.
model: inherit
color: magenta
license: Apache-2.0
allowed-tools: Read Glob Grep Bash
---

# /compass-manifest-maintenance Skill

**Audience:** Maintainers updating `catalog-info.yaml` manifests for Red Hat Compass (Backstage) registration.

**Goal:** Keep Compass manifests aligned with golden sources (`SKILL.md`, `mcps.json`, `AGENTS.md`)

## Prerequisites

**Required MCP Servers:** None — file-based skill. Do not use Compass MCP tools (`validate-entity`, `register-entity`, `get-catalog-entity`, `query-entity-graph`).

- Repository root as cwd.
- Read [CLAUDE.md](../../CLAUDE.md) Compass / Backstage Manifests section.
- Read [references/relationship-rules.md](references/relationship-rules.md) and [references/mcp-mapping.md](references/mcp-mapping.md).
- Templates: [assets/](assets/).

**Verification:**
```bash
test -f CLAUDE.md && echo "✓ repo root" || echo "✗ wrong directory"
```

**Human Notification Protocol:** If drift audit finds violations, report file path and fix per workflow §1.

**Security:** Never display or expose credentials or token values.

## When to Use This Skill

**Use when:**
- New skill needs `skills/<name>/catalog-info.yaml` and Location / inverse updates.
- Skill `allowed-tools` or orchestration changed → MCP or skill `dependsOn` must change.
- Register an existing pack in Compass (plugin, Location, root index, `system.yaml` manifests).
- Drift audit: skill on disk without manifest, stale `dependencyOf`, or dangling entity refs.
- After `agentic-contribution-skill` creates a skill (run before opening PR).

**Do not use when:** `.catalog/collection.yaml` (use **create-collection** instead), generic Compass platform tasks, or automated Compass registration.

## Workflow

**MCP Tool:** None — file-based; uses Read, Glob, Grep, Bash only (see `allowed-tools` in frontmatter).

**Parameters:** N/A — no MCP tools; inputs are `<pack>`, `<skill-name>`, and on-disk manifest paths.

### 1. Add or update a skill manifest

1. **Resolve** `<pack>` and `<skill-name>` — confirm `<pack>/skills/<skill-name>/SKILL.md` exists.

2. **Read golden sources** (precedence):
   - `<pack>/<pack>-plugin.yaml` — `spec.lifecycle` (default for new skill manifest; see [LIFECYCLE.md](../../../LIFECYCLE.md) and [relationship-rules.md](references/relationship-rules.md) Lifecycle)
   - `SKILL.md` frontmatter: `name`, `description`, `allowed-tools`
   - `SKILL.md` body: `Required MCP Servers`, `/skill-name` invocations, Dependencies, validator prerequisites
   - `<pack>/mcps.json` — server keys (map via [mcp-mapping.md](references/mcp-mapping.md))
   - `<pack>/AGENTS.md` — tags/disciplines hints only (not orchestration inference)

3. **Derive `dependsOn`** for the skill manifest:
   - Always: `airesource:ai5-marketplace/<pack>`
   - MCP: only servers the skill **actually uses** (tool prefixes + body); see [mcp-mapping.md](references/mcp-mapping.md)
   - Other skills: orchestration or documented `/other-skill` invocations in `SKILL.md`
   - Script-only skills: no `mcpserver:` entries

4. **Set `spec.lifecycle`** (do not hardcode `beta`):
   - Read `spec.lifecycle` from `<pack>/<pack>-plugin.yaml` — use as the **default** for the skill.
   - **Human in the loop:** ask whether to change it. The skill may match the plugin or use a **less mature** value only (e.g. plugin `beta` → skill `development` is OK; plugin `development` → skill `beta` is **not** allowed).
   - Allowed values: `development`, `beta`, `GA`, `deprecated`, `archived` — see [LIFECYCLE.md](../../../LIFECYCLE.md).

5. **Write** `<pack>/skills/<skill-name>/catalog-info.yaml` from [assets/skill-catalog-info.yaml](assets/skill-catalog-info.yaml):
   - `namespace: ai5-marketplace`
   - `labels.distribution: external`
   - `agents: []`
   - `lifecycle:` value from step 4 (typically matches the plugin)
   - `owner: group:redhat/ai5-marketplace`
   - `backstage.io/source-location` → GitHub `main` branch SKILL.md URL
   - `dependencyOf`: list orchestrators that `dependsOn` this skill (scan pack or update when editing orchestrator)

6. **Update inverse manifests** ([relationship-rules.md](references/relationship-rules.md)):
   - `<pack>/catalog-info.yaml` — `./skills/<skill-name>/catalog-info.yaml` in `spec.targets`
   - `<pack>/<pack>-plugin.yaml` — `dependencyOf: airesource:ai5-marketplace/<skill-name>`
   - Each `mcpserver:` in skill `dependsOn` → matching `mcps/*.yaml` `dependencyOf`
   - Each skill in skill `dependsOn` → that skill's `dependencyOf` includes orchestrator

7. **Reconcile plugin MCP deps** — plugin `dependsOn` = union of all `mcpserver:` refs across pack skill manifests.

8. **Verify skill documentation layout** ([agent-plugins.org](https://agent-plugins.org/specification) / agentskills.io):
   - Skill-local documentation belongs in `skills/<skill-name>/references/`, not `docs/`.
   - **Allowed locations only:** pack-level `<pack>/references/` or skill-level `skills/<name>/references/`. **No** `references/references/` nesting inside a skill.
   - **Scan** every `skills/<skill-name>/` for a `docs/` directory.
   - **If `docs/` exists:**
     1. Rename or merge into `references/` (merge file-by-file when both exist).
     2. If `docs/references/` existed, flatten into `skills/<name>/references/` (not `references/references/`).
     3. Update markdown links in `SKILL.md` and all files under the skill directory: `docs/...` → `references/...` (also `./docs/...` and relative `../docs/...` segments).
     4. **Delete** the `docs/` directory after migration — do not leave an empty or stale `docs/` folder.
     5. Update symlinks under `references/` that still target `docs/` paths to `references/`.
   - Shared reference pools (e.g. `common-issues.md`, `live-doc-lookup.md`) symlinked into multiple skills must use link targets that resolve when opened through the symlink (same-directory or `references/...` paths from the symlink location).
   - Run `uv run python scripts/validate_compass_manifests.py` to confirm (includes manifest roster, bidirectional refs, and references layout).

### 2. Register a new pack in Compass

1. Create `<pack>/<pack>-plugin.yaml` from [assets/plugin-catalog-info.yaml](assets/plugin-catalog-info.yaml) with **`spec.lifecycle: development`** (default for new packs; confirm with user before raising maturity).
2. Create `<pack>/catalog-info.yaml` from [assets/pack-location.yaml](assets/pack-location.yaml).
3. Add `./<pack>/catalog-info.yaml` to root `catalog-info.yaml`.
4. Add `airesource:ai5-marketplace/<pack>` to `system.yaml` `spec.dependencyOf`.
5. Run **create-collection** for `<pack>/.catalog/` separately.

### 3. Drift / compliance audit

Run `uv run python scripts/validate_compass_manifests.py` (or `make validate-compass-manifests`). It enforces manifest roster, bidirectional refs, and skill references layout:

| Check | Rule |
|-------|------|
| Roster parity | Every `skills/*/SKILL.md` has `catalog-info.yaml` and pack Location target |
| Inverse parity | Plugin `dependencyOf` = full skill set; each skill `dependsOn` includes plugin |
| MCP inverse | Each skill `mcpserver:` in `dependsOn` → MCP `dependencyOf` includes skill |
| Skill inverse | Each skill→skill `dependsOn` → target `dependencyOf` includes source |
| Dangling refs | Every ref resolves to on-disk manifest or documented canonical MCP |
| Forbidden | No `partOf`/`hasPart` on AiResource/MCPServer; no redundant `dependsOn: system:default/agentic-plugins` on plugins |
| Namespace | Refs use `ai5-marketplace` except `mcpserver:redhat/*` and `default/agentic-plugins` |
| Skill docs layout | No `skills/<name>/docs/` (delete after migrate); no `references/references/` nesting; links use `references/...` or `./references/...`, not `docs/...` |

Report violations with file path and fix per workflow §1. Do not weaken checks.

### 4. Validate (file-based)

1. Compare YAML against [assets/](assets/) and a known-good manifest in the same pack.
2. Run `uv run python scripts/validate_compass_manifests.py` (included in `make validate` and `make validate-structure`).
3. Tier 1 on this skill if edited: `uv run python scripts/validate_skills_tier1.py .claude/skills/compass-manifest-maintenance/SKILL.md`.
4. Post-merge: maintainer may register in Compass UI manually (out of scope for this skill).

**Error Handling:**
- If skill on disk has no manifest → create from `assets/skill-catalog-info.yaml` and add Location target.
- If inverse `dependencyOf` missing on plugin or MCP → update per [relationship-rules.md](references/relationship-rules.md).
- If MCP ref cannot be resolved → grep pack manifests; do not invent new `mcpserver:` refs.
- If `skills/<name>/docs/` exists or markdown links use `docs/...` → rename/merge to `references/`, flatten any `references/references/`, update link paths, **delete** `docs/`, fix symlinks; re-run `validate_compass_manifests.py`.

## Self-review checklist

- [ ] Skill `spec.lifecycle` matches plugin default or a less mature value (never above the plugin).
- [ ] Manifest conventions: `agents: []`, `labels.distribution: external`, `namespace: ai5-marketplace`, `owner: group:redhat/ai5-marketplace`.
- [ ] MCP deps derived from `SKILL.md` usage, not copied from sibling skills.
- [ ] Every new `dependsOn` has matching `dependencyOf` on the target entity.
- [ ] Pack Location lists every skill manifest path.
- [ ] Plugin `dependencyOf` lists every skill in the pack.
- [ ] No `partOf`/`hasPart` on custom kinds.
- [ ] Skill documentation uses `references/` only — no leftover `docs/` directory, no `references/references/` nesting; links use `references/...` or `./references/...`.

## Dependencies

### Required MCP Servers

None — file-based manifest maintenance only.

### Required MCP Tools

None — uses Read, Glob, Grep, Bash.

### Related Skills

- **create-collection** — for `.catalog/` marketplace metadata (not Compass manifests)
- **agentic-contribution-skill** — run before this skill when creating a new skill

### Reference Documentation

- `scripts/validate_compass_manifests.py` — CI roster and bidirectional ref checks
- [references/relationship-rules.md](references/relationship-rules.md)
- [references/mcp-mapping.md](references/mcp-mapping.md)

## Common Issues

- **COMPASS-1288 drift** — updated skill `dependsOn` but forgot plugin or MCP `dependencyOf`.
- **Blanket MCP deps** — declaring every MCP in `mcps.json` instead of per-skill `allowed-tools` usage.
- **Orchestration gaps** — `remediation`-style skills missing skill→skill edges or inverse `dependencyOf` on depended skills.
- **Canonical vs owned** — Lightspeed and Security use `mcpserver:redhat/...`; do not register duplicates in `mcps/`.
- **Unregistered packs** — `rh-developer`, `rh-ai-engineer`, `rh-automation` exist on disk but are not in root Location until explicitly added.
- **`docs/` vs `references/`** — agent-plugins.org expects `references/` for skill-local docs; rename/merge, flatten `references/references/`, update links, **delete** `docs/`, then run `make validate-compass-manifests`.

## Example usage

```bash
# CI structural validation (roster + bidirectional refs + references layout)
uv run python scripts/validate_compass_manifests.py
# or: make validate-compass-manifests

# Roster: skills on disk missing from Location (example: rh-sre)
comm -23 \
  <(find rh-sre/skills -name SKILL.md | sed 's|.*/skills/||;s|/SKILL.md||' | sort) \
  <(grep -oP 'skills/\K[^/]+(?=/catalog-info)' rh-sre/catalog-info.yaml | sort)

# Tier 1 lint for this maintenance skill
uv run python scripts/validate_skills_tier1.py .claude/skills/compass-manifest-maintenance/SKILL.md

# Full repo validation
make validate
```

Audit all four registered packs:

```bash
for pack in ocp-admin rh-sre rh-virt rh-basic; do
  echo "=== $pack ==="
  comm -23 \
    <(find "$pack/skills" -name SKILL.md 2>/dev/null | sed 's|.*/skills/||;s|/SKILL.md||' | sort) \
    <(grep -oP 'skills/\K[^/]+(?=/catalog-info)' "$pack/catalog-info.yaml" 2>/dev/null | sort)
done
```

# Compass relationship rules (agentic-plugins)

**Phase C H.4 / H.5:** H.4 drops legacy plugin `spec.skills` once Analyze accepts `includes` without `skills`. H.5 drops skill→plugin `dependsOn` once pipeline child detection is proven on includes-only entities. Until then, dual-write both membership fields and keep the one-sided skill→plugin edge.

## Membership vs functional deps

| What | Where | Notes |
|------|-------|-------|
| Plugin membership | Plugin `spec.includes` (`{ entityRef, type }`) **and** legacy `spec.skills` (skill refs as strings) | Same skill set. Owned MCP (`mcpserver:ai5-marketplace/*`) goes in `includes` only, not in `spec.skills`. Canonical `mcpserver:redhat/*` goes in neither. Never `includes: []` or `skills: []`. No `gitRef`. Do **not** list skills on plugin `dependencyOf`. |
| Skill→plugin (until Phase C H.5) | Skill `dependsOn` plugin | Leftover pack-roster edge. **The** exception to the bidirectional rule below: one-sided — do **not** write a plugin `dependencyOf` inverse. |
| Functional dependency | `dependsOn` | Skill→MCP, skill→skill, plugin MCP union. Dual-write the inverse on the target. |
| Inverse of functional `dependsOn` | Target `dependencyOf` | Compass does **not** auto-generate inverses for custom kinds (COMPASS-1288). Dual-write both sides for **functional** edges (MCP and skill→skill). Skill→plugin is the exception in the row above. |

Do **not** author `partOf` / `hasPart` on `AiResource` or `MCPServer`. Compass may **generate** those from `includes` when plugin processing ships. Still do not write the keys.

## COMPASS-1288 bidirectional policy (functional edges)

Every **functional** relationship must be declared on **both** sides.

**Exception — skill→plugin:** keep skill `dependsOn` plugin until Phase C H.5, and do **not** add the plugin `dependencyOf` inverse (that roster is retired). This is the only `dependsOn` edge that is one-sided.

| Origin | Field | Target | Inverse on target |
|--------|-------|--------|-------------------|
| Skill | `dependsOn` | Plugin | **None** — bidirectional exception (until Phase C H.5) |
| Skill | `dependsOn` | MCP | MCP `dependencyOf` skill |
| Skill | `dependsOn` | Other skill | Other skill `dependencyOf` orchestrator |
| Plugin | `dependsOn` | MCP | MCP `dependencyOf` plugin |
| MCP | `dependsOn` | System | System `dependencyOf` MCP |

**Also:** Plugin and owned MCP → System use `spec.system: default/agentic-plugins`. Compass generates `partOf` automatically. Do **not** add `dependsOn: system:default/agentic-plugins` on plugins (redundant).

## What does NOT work for custom kinds

- Authored `partOf` / `hasPart` on `AiResource` or `MCPServer` — do not write these keys.
- `includes` / `spec.skills` / `spec.system` on **skills** — plugins only for the first two; skills omit `spec.system`.
- Canonical MCP in plugin `includes`.
- Plugin `dependencyOf` skill roster — membership is `spec.includes` (and legacy `spec.skills` until H.4).

## Entity reference formats

| Entity | Ref format |
|--------|------------|
| Skill | `airesource:ai5-marketplace/<skill-name>` |
| Plugin | `airesource:ai5-marketplace/<plugin-name>` |
| Owned MCP | `mcpserver:ai5-marketplace/<mcp-name>` |
| Canonical MCP | `mcpserver:redhat/<mcp-name>` |
| System | `default/agentic-plugins` (in `spec.system` only) |

All skills, plugins, and owned MCPs use `metadata.namespace: ai5-marketplace`.

## Lifecycle (`spec.lifecycle`)

- **New skill:** copy `spec.lifecycle` from `<plugin>/<plugin>-plugin.yaml` (ask before changing). Skill must not exceed plugin maturity (`development` < `beta` < `production`).
- **New plugin:** default plugin to `development`.

## Files to touch when adding a skill

1. `skills/<skill-name>/catalog-info.yaml` — new or updated entity (skill→plugin `dependsOn`; no `includes`)
2. `<plugin>/catalog-info.yaml` — Location `targets` entry
3. `<plugin>/<plugin>-plugin.yaml` — matching `spec.skills` string **and** `spec.includes` `{ entityRef, type: skill }` (not plugin `dependencyOf`)
4. Each `mcps/*.yaml` referenced — `dependencyOf` skill (and plugin if plugin depends on MCP)
5. Each depended-on skill manifest — `dependencyOf` orchestrator (skill→skill)
6. Reconcile plugin `dependsOn` MCP union if MCP usage changed plugin-wide
7. If the skill uses an **owned** MCP, that MCP is also a plugin `includes` entry (`type: mcp-server`). Canonical MCP is `dependsOn` only.

## Files to touch when adding a plugin

1. `<plugin>/<plugin>-plugin.yaml` — from `assets/plugin-catalog-info.yaml` (`includes`, `skills`, license, provider, `distribution: external`)
2. `<plugin>/catalog-info.yaml`
3. Root `catalog-info.yaml` — add plugin Location target
4. `system.yaml` — `dependencyOf` plugin entry
5. Register owned MCPs in `mcps/` if new (and `mcps/catalog-info.yaml`, `system.yaml` for MCP)

## Orchestration skill detection

Add skill→skill `dependsOn` when `SKILL.md` documents:

- `Execute the `/other-skill` skill`
- Skill tool invocation of another skill in workflow
- Explicit prerequisite validator skills (`/mcp-lightspeed-validator`, etc.)

Do **not** infer orchestration from `AGENTS.md` routing alone.

## Registered plugins (Compass Location in root)

Currently indexed: `ocp-admin`, `rh-sre`, `rh-virt`, `rh-basic`. Plugins on disk without root Location targets (`rh-developer`, `rh-ai-engineer`, `rh-automation`) are out of scope until added to root `catalog-info.yaml`.

# Compass relationship rules (agentic-plugins)

## COMPASS-1288 bidirectional policy

Compass does **not** auto-generate inverse relations for custom kinds (`AiResource`, `MCPServer`). Every relationship must be declared on **both sides**:

| Origin | Field | Target | Inverse on target |
|--------|-------|--------|-------------------|
| Skill | `dependsOn` | Plugin | Plugin `dependencyOf` skill |
| Skill | `dependsOn` | MCP | MCP `dependencyOf` skill |
| Skill | `dependsOn` | Other skill | Other skill `dependencyOf` orchestrator |
| Plugin | `dependsOn` | MCP | MCP `dependencyOf` plugin |
| MCP | `dependsOn` | System | System `dependencyOf` MCP |

**Exception:** Plugin and owned MCP → System use `spec.system: default/agentic-plugins`. Compass generates `partOf` automatically. Do **not** add `dependsOn: system:default/agentic-plugins` on plugins (redundant).

## What does NOT work for custom kinds

- `partOf` / `hasPart` on `AiResource` or `MCPServer` — stored in spec but **not** in the relation graph (validated Aug 2026).
- Use `dependsOn` / `dependencyOf` for all membership and technical dependencies.

## Entity reference formats

| Entity | Ref format |
|--------|------------|
| Skill | `airesource:ai5-marketplace/<skill-name>` |
| Plugin plugin | `airesource:ai5-marketplace/<plugin-name>` |
| Owned MCP | `mcpserver:ai5-marketplace/<mcp-name>` |
| Canonical MCP | `mcpserver:redhat/<mcp-name>` |
| System | `default/agentic-plugins` (in `spec.system` only) |

All skills, plugins, and owned MCPs use `metadata.namespace: ai5-marketplace`.

## Lifecycle (`spec.lifecycle`)

- **New skill:** copy `spec.lifecycle` from `<plugin>/<plugin>-plugin.yaml` (ask before changing). Skill must not exceed plugin maturity (`development` < `beta` < `production`).
- **New plugin:** default plugin to `development`.

## Files to touch when adding a skill

1. `skills/<skill-name>/catalog-info.yaml` — new or updated entity
2. `<plugin>/catalog-info.yaml` — Location `targets` entry
3. `<plugin>/<plugin>-plugin.yaml` — `dependencyOf` skill
4. Each `mcps/*.yaml` referenced — `dependencyOf` skill (and plugin if plugin depends on MCP)
5. Each depended-on skill manifest — `dependencyOf` orchestrator (skill→skill)
6. Reconcile plugin `dependsOn` MCP union if MCP usage changed plugin-wide

## Files to touch when adding a plugin

1. `<plugin>/<plugin>-plugin.yaml`
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

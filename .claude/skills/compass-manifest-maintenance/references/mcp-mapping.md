# Deriving MCP `dependsOn` for skill manifests

Map **only** MCP servers the skill **actually uses**. Never copy a sibling manifest and never declare every key in `<plugin>/mcps.json`.

## Step 1 — Detect MCP usage in the skill

From `<plugin>/skills/<skill>/SKILL.md`:

- `allowed-tools` in frontmatter (tool names / prefixes)
- `Required MCP Servers` / `Required MCP Tools` in the body
- Workflow steps that name an MCP server key or tool

If none of the above reference MCP tools → **no** `mcpserver:` in `dependsOn` (script-only, `WebFetch`, or public API skills).

## Step 2 — Match usage to `mcps.json` keys

Read `<plugin>/mcps.json`. Note which **server keys** the skill documents (e.g. `openshift-administration`, `lightspeed-mcp`, `aap-mcp-job-management`).

When `allowed-tools` lists tools but SKILL.md does not name a key, infer the server from context in the skill body (which MCP block documents those tools).

## Step 3 — Resolve each key to a Compass entity ref

For each MCP the skill uses:

### A. Owned MCP (manifest in this repo)

1. List `mcps/*.yaml` (exclude `catalog-info.yaml`).
2. Open manifests and read `metadata.name` and `metadata.namespace` (typically `ai5-marketplace`).
3. Entity ref: `mcpserver:<namespace>/<metadata.name>`.
4. **Deduplication:** Several `mcps.json` keys may share one Compass entity (same image/technology). Compare `mcps.json` entries (image URL, upstream repo in manifest `links`) to pick the correct owned manifest — do not create one ref per key if they map to the same `mcps/*.yaml`.
5. Confirm the skill’s tools appear in that manifest’s `spec.primitives` (or match the server described in SKILL.md) when ambiguous.

### B. Canonical MCP (registered upstream, not in `mcps/`)

If the plugin references an MCP that **no** file under `mcps/` covers:

1. Search existing skill manifests in the same plugin (or repo) for the same `mcps.json` key or the same upstream product.
2. Reuse the `mcpserver:` ref already used there (often `mcpserver:redhat/<name>`).
3. Do **not** add a duplicate MCPServer manifest in `mcps/`.

When unsure, grep the repo for the `mcps.json` key or tool prefix in other `catalog-info.yaml` files under the same plugin.

## Step 4 — Update inverse relations

For each `mcpserver:` added to the skill’s `dependsOn`:

- Add `airesource:ai5-marketplace/<skill-name>` to that MCP manifest’s `spec.dependencyOf` (owned MCPs only — canonical MCPs are maintained by their owners).

## Step 5 — Plugin MCP union

The plugin plugin’s `dependsOn` MCP list = **union** of all `mcpserver:` refs across skill manifests in that plugin — not the full set of keys in `mcps.json`.

## Sanity checks

- Fewer MCP refs than keys in `mcps.json` is normal (per-skill usage).
- More MCP refs than the skill uses is wrong (blanket template deps).
- Canonical refs (`mcpserver:redhat/...`) do not get new files under `mcps/`.

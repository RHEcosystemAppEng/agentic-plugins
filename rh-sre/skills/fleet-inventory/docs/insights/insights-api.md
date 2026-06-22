---
title: Lightspeed Inventory API Patterns for Fleet Discovery
category: insights
tags: [lightspeed, inventory, list_hosts, pagination]
last_updated: 2026-06-22
---

# Lightspeed Inventory API Patterns

Fleet discovery and listing use **`inventory__list_hosts`**, not `inventory__get_host_details`. The latter requires known host UUIDs.

## Tool routing by intent

| User intent | Tool | Key parameters |
|-------------|------|----------------|
| List or discover the fleet; filter by tag, name, staleness | `inventory__list_hosts` | `per_page=10` (first call), `page`, `display_name`, `tags`, `staleness` |
| Resolve hostname → UUID | `inventory__find_host_by_name` | `hostname` |
| Full details for known host(s) | `inventory__get_host_details` | `host_ids` (comma-separated UUIDs) |
| Systems affected by a CVE | `vulnerability__get_cve_systems` | `cve`, `limit`, `offset`; optional `system_uuid` |

## inventory__list_hosts pagination

- **First call**: always use `per_page=10` (integer). The MCP tool description requires this default to avoid performance and context issues.
- **Subsequent pages**: increment `page` (`1`, `2`, `3`, …) while keeping the same filters.
- **Stop condition**: when a page returns fewer hosts than `per_page`, or an empty result set.

```
inventory__list_hosts(per_page=10, page=1, display_name="")
inventory__list_hosts(per_page=10, page=2, display_name="")
```

Use `per_page`, not `page_size`. Lightspeed inventory uses different pagination parameter names than AAP MCP.

## Response fields (list_hosts)

Extract from each host record:

- `id` — host UUID (use for `inventory__get_host_details` and remediation workflows)
- `display_name` / `fqdn` — human-readable hostname
- `system_profile.operating_system.version` or equivalent — RHEL version (for version filtering)
- `tags` — environment labels
- `stale` / staleness indicators — whether the host recently checked in
- `updated` — last inventory update timestamp

Exact field paths may vary by API version; inspect the response and map to the fields above.

## Enriching specific hosts

After listing or CVE queries produce host UUIDs, call:

```
inventory__get_host_details(host_ids="uuid-1,uuid-2")
```

`host_ids` is **required** and must be a comma-separated UUID string.

## CVE-affected systems pagination

Use `vulnerability__get_cve_systems` with parameter **`cve`** (not `cve_id`):

```
vulnerability__get_cve_systems(cve="CVE-2024-1234", limit=100, offset=0)
```

Paginate with `offset += limit` until the page returns fewer records than `limit`.

## Related references

- [01-parameter-reference.md](../../references/01-parameter-reference.md) — parameter tables for all fleet-inventory tools
- [lightspeed-mcp-parameters.md](../../../cve-impact/docs/references/lightspeed-mcp-parameters.md) — shared Lightspeed MCP parameter reference (inventory and vulnerability tools)

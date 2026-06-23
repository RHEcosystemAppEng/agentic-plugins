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
| Inventory metadata for known host(s) | `inventory__get_host_details` | `host_ids` (comma-separated UUIDs) |
| OS version / system profile for known host(s) | `inventory__get_host_system_profile` | `host_ids` (one or two UUIDs at a time) |
| Systems affected by a CVE | `vulnerability__get_cve_systems` | `cve`, `limit`, `offset`; optional `system_uuid` |

## Response envelope (list_hosts, get_host_details, get_host_system_profile)

All three inventory tools return the same top-level shape:

| Field | Meaning |
|-------|---------|
| `total` | Total hosts matching the query |
| `count` | Hosts in this page |
| `page` | Current page number |
| `per_page` | Page size |
| `results` | Array of host records |

## inventory__list_hosts pagination

- **First call**: always use `per_page=10` (integer). The MCP tool description requires this default to avoid performance and context issues.
- **Subsequent pages**: increment `page` (`1`, `2`, `3`, …) while keeping the same filters.
- **Stop condition**: when `count` is less than `per_page`, or `results` is empty.

```
inventory__list_hosts(per_page=10, page=1, display_name="")
inventory__list_hosts(per_page=10, page=2, display_name="")
```

Use `per_page`, not `page_size`. Lightspeed inventory uses different pagination parameter names than AAP MCP.

## Response fields (list_hosts / get_host_details)

Extract from each `results[]` host record:

- `id` — host UUID (use for enrichment and remediation workflows)
- `display_name` / `fqdn` — human-readable hostname
- `updated` — last inventory record update
- `last_check_in` — last reporter check-in (prefer for active/stale display)
- `stale_timestamp`, `stale_warning_timestamp`, `culled_timestamp` — staleness thresholds
- `per_reporter_staleness` — per-reporter check-in detail
- `groups` — inventory groups (when present)
- `facts` — limited rhsm facts when profile data is sparse

**When present** (not guaranteed on every host): `tags`

`list_hosts` and `get_host_details` do **not** reliably return `system_profile`. Do not expect RHEL version from fleet listing alone.

## OS version (get_host_system_profile)

When the user asks for RHEL version distribution or version-based filtering, call:

```
inventory__get_host_system_profile(host_ids="68ce32aa-57da-49b7-8ded-dc4ad54e520a")
```

Use **one or two UUIDs at a time** — responses are large.

Extract RHEL version from `results[].system_profile`:

- `system_profile.operating_system.version` or equivalent
- Equivalents: `operating_system.major` / `operating_system.minor`, `os_release`, `operating_system.name`

Example live shape: `"operating_system": {"name": "RHEL", "major": 10, "minor": 1}`, `"os_release": "10.1"`

## CVE-affected systems pagination

Use `vulnerability__get_cve_systems` with parameter **`cve`** (not `cve_id`):

```
vulnerability__get_cve_systems(cve="CVE-2024-1234", limit=100, offset=0)
```

Paginate with `offset += limit` until the page returns fewer records than `limit`.

## Related references

- [01-parameter-reference.md](../../references/01-parameter-reference.md) — parameter tables for all fleet-inventory tools
- [lightspeed-mcp-parameters.md](../../../cve-impact/docs/references/lightspeed-mcp-parameters.md) — shared Lightspeed MCP parameter reference (inventory and vulnerability tools)

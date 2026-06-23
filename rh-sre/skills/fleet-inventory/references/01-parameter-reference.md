# Fleet Inventory Parameter Reference

Read when calling inventory or vulnerability tools to ensure correct parameters.

## inventory__list_hosts

**Purpose**: List and discover hosts. Use for fleet queries, tag filters, and environment scoping.

| Parameter | Type | Required | Example | Notes |
|-----------|------|----------|---------|-------|
| `per_page` | integer | No | `10` | **Use 10 on first call.** Not `page_size`. |
| `page` | integer | No | `1` | Increment for pagination. |
| `display_name` | string | No | `""` | Filter by display name. Empty string = no filter. |
| `hostname_or_id` | string | No | `""` | Filter by display_name, fqdn, or id. |
| `fqdn` | string | No | `""` | Filter by FQDN. |
| `tags` | string | No | `"ns1/key1=val1"` | Tag filter string (not an array). |
| `staleness` | string | No | `"fresh"` | One of `fresh`, `stale`, `stale_warning`, `unknown`. |
| `order_by` | string | No | `"display_name"` | Sort field: `display_name`, `updated`, `created`. |
| `order_how` | string | No | `"ASC"` | `ASC` or `DESC`. |

**Correct**:
```
inventory__list_hosts(per_page=10, page=1, display_name="")
inventory__list_hosts(per_page=10, page=1, tags="insights-client/owner=staging")
```

**Wrong**:
```
inventory__list_hosts()                    # Missing per_page guidance; always pass per_page=10 first
inventory__list_hosts(page_size=100)     # Use per_page, not page_size
inventory__list_hosts(tags=["production"])  # tags is a string, not an array
```

**Response envelope**: `{ total, count, page, per_page, results[] }`

**Response fields** (per host in `results[]`): `id`, `display_name`, `fqdn`, `updated`, `last_check_in`, `stale_timestamp`, `per_reporter_staleness`, `groups`, `facts`. Tags when present. No `system_profile` — use `get_host_system_profile` for OS version.

## inventory__find_host_by_name

**Purpose**: Resolve a hostname or display name to a host record.

| Parameter | Type | Required | Example |
|-----------|------|----------|---------|
| `hostname` | string | Yes | `"web-server-01"` |

```
inventory__find_host_by_name(hostname="web-server-01")
```

## inventory__get_host_details

**Purpose**: Retrieve full details for **known** host UUIDs. Not for fleet enumeration.

| Parameter | Type | Required | Example |
|-----------|------|----------|---------|
| `host_ids` | string | Yes | `"uuid-1,uuid-2"` |

```
inventory__get_host_details(host_ids="68ce32aa-57da-49b7-8ded-dc4ad54e520a")
```

**Response**: Same envelope as `list_hosts`; host shape is similar (inventory metadata, not guaranteed to include `system_profile`).

**Wrong**:
```
inventory__get_host_details()                        # host_ids is required
inventory__get_host_details(system_id="abc-123")     # Use host_ids
inventory__get_host_details(hostname_pattern="web-*")  # Not supported; use list_hosts
inventory__get_host_details(tags=["production"])     # Not supported; use list_hosts
```

## inventory__get_host_system_profile

**Purpose**: Retrieve OS version and full system profile for **known** host UUIDs. Use when RHEL version distribution or version-based filtering is required.

| Parameter | Type | Required | Example | Notes |
|-----------|------|----------|---------|-------|
| `host_ids` | string | No | `"uuid-1"` or `"uuid-1,uuid-2"` | Comma-separated UUIDs. **One or two at a time** — MCP warns of very large responses. Default `""`. |

```
inventory__get_host_system_profile(host_ids="68ce32aa-57da-49b7-8ded-dc4ad54e520a")
```

**Response envelope**: `{ total, count, page, per_page, results[] }` (same as `list_hosts`).

**Each `results[]` item** (live shape): `id` + `system_profile` only — not the full inventory record from `list_hosts`.

**`system_profile` fields** (live; OS version equivalents):
- `operating_system.name` — e.g. `"RHEL"`
- `operating_system.major` / `operating_system.minor` — e.g. `10` / `1` (no `operating_system.version` string in live responses)
- `os_release` — e.g. `"10.1"`
- `installed_packages`, `enabled_services`, `installed_services`
- Hardware/infrastructure: `cpu_model`, `number_of_cpus`, `system_memory_bytes`, `network_interfaces`, etc.

Use `system_profile.operating_system.version` in docs as the canonical name; at runtime read `major`/`minor`, `os_release`, or `operating_system.name` when `version` is absent.

## vulnerability__get_cve_systems

**Purpose**: List systems affected by a CVE.

| Parameter | Type | Required | Example | Notes |
|-----------|------|----------|---------|-------|
| `cve` | string | Yes | `"CVE-2024-1234"` | Required. Not `cve_id`. |
| `limit` | integer | No | `100` | Records per page (default 10). |
| `offset` | integer | No | `0` | Pagination offset. |
| `sort` | string | No | `"-updated"` | Prefix `-` for descending. |
| `filter_` | string | No | `""` | Full-text filter on system display name. |
| `system_uuid` | string | No | `"68ce32aa-..."` | Check if a specific system is affected. |

**Correct**:
```
vulnerability__get_cve_systems(cve="CVE-2024-1234", limit=100, offset=0)
```

**Wrong**:
```
vulnerability__get_cve_systems(cve_id="CVE-2024-1234")  # Use cve, not cve_id
```

**Response fields**: affected systems with id, display_name, status, remediation_available; paginate with limit/offset for large result sets.

**Status values**: Vulnerable (patch needed), Patched (no action), Not Affected (exclude)

## Client-side filtering and sorting

When API filters are insufficient, filter after listing or after fetching profiles:

**By RHEL major** (requires `get_host_system_profile` data): `[h for h in profiles if h.get('system_profile', {}).get('operating_system', {}).get('major') == 8]`
**By tag** (when present on host): `[h for h in hosts if any("production" in t for t in h.get('tags', []))]`
**By stale** (from list_hosts): compare `last_check_in` to `stale_timestamp`, or use `staleness` filter on `list_hosts`
**Sort by last check-in**: `sorted(hosts, key=lambda h: h.get('last_check_in', ''), reverse=True)`
**Sort by updated**: `sorted(hosts, key=lambda h: h.get('updated', ''), reverse=True)`

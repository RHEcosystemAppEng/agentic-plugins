# Fleet Inventory Examples

## Example 1: General Fleet Query

**User Request**: "Show the managed fleet"

1. Invoke mcp-lightspeed-validator (Step 0) → PASSED
2. Call `inventory__list_hosts(per_page=10, page=1, display_name="")`
3. Paginate: increment `page` until a page returns fewer than `per_page` hosts
4. Consult fleet-management.md for grouping
5. Group by environment (`groups` or `tags` when present); for RHEL version breakdown, call `inventory__get_host_system_profile(host_ids="<uuid>")` per host (one or two UUIDs at a time)
6. Generate Template 1 output
7. Offer next steps (CVE analysis, remediation)

## Example 2: CVE Impact Query

**User Request**: "What systems are affected by CVE-2024-1234?"

1. Invoke mcp-lightspeed-validator (Step 0) → PASSED
2. Call `vulnerability__get_cve_systems(cve="CVE-2024-1234", limit=100, offset=0)`
3. Paginate with `offset += limit` until fewer records than `limit` are returned
4. Separate vulnerable vs. patched systems
5. Generate Template 2 output
6. Suggest /remediation for next steps

## Example 3: Environment Filter

**User Request**: "Show me staging systems"

1. Invoke mcp-lightspeed-validator (Step 0) → PARTIAL
2. Ask user: "Proceed? (yes/no)" → yes
3. Call `inventory__list_hosts(per_page=10, page=1, tags="insights-client/owner=staging")` (adjust tag string to match your environment), or list all and filter client-side by tag
4. Paginate through results
5. Group by tier (hostname patterns)
6. Generate Template 3 output

## Example 4: Hostname Lookup

**User Request**: "Find web-server-01 in the fleet"

1. Invoke mcp-lightspeed-validator (Step 0) → PASSED
2. Call `inventory__find_host_by_name(hostname="web-server-01")`
3. If inventory metadata needed, call `inventory__get_host_details(host_ids="<uuid-from-step-2>")`
4. If OS version needed, call `inventory__get_host_system_profile(host_ids="<uuid-from-step-2>")`
5. Present host summary

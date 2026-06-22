---
title: Lightspeed MCP Tool Failures — Handling and Workarounds
category: references
tags: [lightspeed, mcp, troubleshooting, errors]
last_updated: 2026-03-02
---

# Lightspeed MCP Tool Failures

When Lightspeed MCP tools fail with cryptic backend errors (e.g. KeyError, missing keys), follow this pattern instead of exposing the raw error.

## Generic Pattern

1. **Do NOT** expose the raw error to the user (e.g. `'dnf_modules'`, `KeyError: 'xyz'`)
2. **Show** a user-friendly message explaining what happened and what we know
3. **Use** alternative tools to achieve the same goal when possible
4. **Do NOT** retry the failing tool—backend errors typically persist for the same request

## Known Failures and Workarounds

### vulnerability__get_cves — `limit_` Unexpected keyword argument

**Error**: `1 validation error for call[get_cves] limit_ Unexpected keyword argument [type=unexpected_keyword_argument]`

**Cause**: Some MCP clients incorrectly serialize the `limit` parameter as `limit_`. The Lightspeed MCP server expects `limit` (no underscore).

**Workaround**: Call with **no parameters**—the tool uses default `limit=10`:
```
vulnerability__get_cves()
```
Or pass only parameters that don't trigger the bug (e.g. `impact`, `sort`, `advisory_available`). Avoid passing `limit` when the client may serialize it as `limit_`.

**Skills affected**: cve-impact (account-level CVE queries). For MCP connectivity validation, use `/mcp-lightspeed-validator` which calls `get_mcp_version` instead.

### vulnerability__explain_cves — `'dnf_modules'` (or similar KeyError)

**Error**: `Error calling tool 'explain_cves': 'dnf_modules'`

**Cause**: Backend expects a `dnf_modules` key in the system profile; some systems don't include it.

**User-friendly message**:
```
⚠️ CVE explanation unavailable for this system

The detailed "why this CVE affects your system" explanation could not be retrieved.
This sometimes happens when the system profile is missing module data.

**What we know** (from other sources):
- CVE: [CVE-ID]
- Affected system: [hostname]
- Severity: [from get_cve]
- Affected packages: [from get_cve]

**Next steps**: Proceeding with available data. The playbook will still address the CVE correctly.
```

**Workaround**: Synthesize from `get_cve` + `get_host_details`:
1. `get_cve(cve_id)` → affected_packages, severity, advisory
2. `get_host_details(system_id)` → installed_packages
3. Match and explain: "CVE-X affects system Y because [package] is installed at [version]. Fix: [advisory]."

**Skills**: cve-impact (if explaining why CVE affects system); remediation and system-context do NOT use explain_cves.

### Other Tool Failures

When a different tool fails with a similar cryptic error:
1. Apply the generic pattern (no raw error, user-friendly message)
2. Identify alternative tools that provide equivalent data
3. Add the failure and workaround to this doc for future reference

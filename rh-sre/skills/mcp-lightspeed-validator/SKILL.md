---
name: mcp-lightspeed-validator
description: |
  Validate Red Hat Lightspeed MCP server connectivity. Use when the user asks to "validate Lightspeed MCP", "check Lightspeed connection", or when other skills need to verify lightspeed-mcp availability before CVE operations.
model: haiku
color: yellow
license: Apache-2.0
allowed-tools: get_cves
---

# MCP Lightspeed Validator

Validates connectivity to the Red Hat Lightspeed MCP server by running a lightweight tool call.

## When to Use This Skill

Use when validating Lightspeed MCP before CVE operations, troubleshooting connection issues, or when other skills (e.g. remediation) need to verify availability. Do NOT use for actual CVE queries—use cve-impact or cve-validation.

## Workflow

1. **Test connectivity**: Call `vulnerability__get_cves` with **no parameters** (uses default limit=10). Do NOT pass `limit`—some MCP clients incorrectly serialize it as `limit_`, causing validation errors.
2. **If it fails**: Provide a comprehensive message with possible root causes (see below).
3. **Report**: Output a table with validated servers and outcome (emojis).

## Failure Message (Root Causes)

When the tool call fails, include:

```
❌ Lightspeed MCP connection failed

**Possible root causes:**
- **Credentials**: LIGHTSPEED_CLIENT_ID or LIGHTSPEED_CLIENT_SECRET not set or invalid
- **Expired credentials**: Red Hat Console tokens may have expired
- **Server not running**: MCP server/container may be stopped
- **Network**: Firewall or proxy blocking console.redhat.com
- **Configuration**: mcps.json misconfigured or server not registered

**Troubleshooting:**
1. Verify env vars: LIGHTSPEED_CLIENT_ID, LIGHTSPEED_CLIENT_SECRET (never echo values)
2. Check credentials at: https://console.redhat.com/settings/integrations
3. Restart MCP server or host after config changes
4. Check container logs if using podman/docker
```

## Report Format

Always end with a table:

| Server | Outcome |
|--------|---------|
| lightspeed-mcp | ✅ PASSED |
| lightspeed-mcp | ❌ FAILED |

Use ✅ for success, ❌ for failure, ⚠️ for partial (e.g. connected but error on tool).

## Dependencies

### Required MCP Servers
- `lightspeed-mcp` - Red Hat Lightspeed vulnerability and inventory data

### Required MCP Tools
- `vulnerability__get_cves` or `get_cves` (from lightspeed-mcp) - Connectivity test

### Related Skills
- `/remediation` - Requires Lightspeed MCP validation before CVE operations
- `/cve-validation`, `/cve-impact`, `/fleet-inventory` - All require Lightspeed MCP

### Reference Documentation
- [Red Hat Lightspeed Documentation Overview](../../docs/insights/README.md) - Lightspeed setup, CVE assessment, vulnerability logic

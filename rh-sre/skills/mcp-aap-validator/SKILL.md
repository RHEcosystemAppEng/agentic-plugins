---
name: mcp-aap-validator
description: |
  Validate AAP (Ansible Automation Platform) MCP server connectivity. Use when the user asks to "validate AAP MCP", "check AAP connection", or when other skills need to verify AAP MCP availability before job management or inventory operations.
model: haiku
color: yellow
license: Apache-2.0
allowed-tools: job_templates_list inventories_list
---

# MCP AAP Validator

Validates connectivity to AAP MCP servers by running lightweight tool calls.

## When to Use This Skill

Use when validating AAP MCP before job template operations, troubleshooting connection issues, or when other skills (e.g. playbook-executor) need to verify availability. Do NOT use for creating templates—use job-template-creator.

## Workflow

1. **Test connectivity**: Call these tools to verify each server responds:
   - `job_templates_list` (page_size: 10) from aap-mcp-job-management
   - `inventories_list` (page_size: 10) from aap-mcp-inventory-management
2. **If any fails**: Provide a comprehensive message with possible root causes (see below).
3. **Report**: Output a table with validated servers and outcome (emojis).

## Failure Message (Root Causes)

When a tool call fails, include:

```
❌ AAP MCP connection failed

**Possible root causes:**
- **Credentials**: AAP_MCP_SERVER or AAP_API_TOKEN not set or invalid
- **401 Unauthorized**: Token expired or invalid → regenerate in AAP Web UI
- **403 Forbidden**: Token lacks RBAC permissions (need Job Templates, Inventories)
- **404 Not Found**: Wrong AAP_MCP_SERVER URL (must point to MCP gateway, not main AAP UI)
- **Connection timeout**: Server unreachable, firewall, or network issue
- **SSL/TLS error**: Certificate verification problem

**Troubleshooting:**
1. Verify env vars: AAP_MCP_SERVER, AAP_API_TOKEN (never echo values)
2. Get token: AAP Web UI → Users → [Your User] → Tokens → Create
3. Ensure AAP_MCP_SERVER points to MCP gateway endpoint
4. Restart host after config changes
```

## Report Format

Always end with a table:

| Server | Outcome |
|--------|---------|
| aap-mcp-job-management | ✅ PASSED |
| aap-mcp-inventory-management | ✅ PASSED |

Use ✅ for success, ❌ for failure, ⚠️ for partial (e.g. one server OK, one failed).

## Dependencies

### Required MCP Servers
- `aap-mcp-job-management` - AAP job template and execution
- `aap-mcp-inventory-management` - AAP inventory management

### Required MCP Tools
- `job_templates_list` (from aap-mcp-job-management) - Connectivity test
- `inventories_list` (from aap-mcp-inventory-management) - Connectivity test

### Related Skills
- `/playbook-executor` - Requires AAP MCP validation before execution
- `/job-template-creator` - Requires AAP MCP validation before template operations

### Reference Documentation
- [AAP Integration Test Guide](../../docs/testing/aap-integration-test-guide.md) - AAP MCP setup, env vars, connectivity verification

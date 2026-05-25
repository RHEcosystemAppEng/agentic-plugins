---
name: aap-mcp-validator
description: |
  Validate that required AAP MCP servers are accessible before executing automation skills.

  Use when:
  - Before any skill that requires AAP MCP access
  - "Validate AAP MCP", "Check if AAP is configured"
  - "Verify AAP connection", "Test AAP MCP servers"

  NOT for: actual automation tasks (use specialized skills instead).
model: inherit
color: blue
license: Apache-2.0
allowed-tools: job_templates_list inventories_list notification_templates_list credentials_list instance_groups_list users_list
---

# AAP MCP Validator

## Prerequisites

**Required MCP Servers**: One or more of the 6 AAP MCP servers (depending on the `servers` parameter):
- `aap-mcp-job-management`
- `aap-mcp-inventory-management`
- `aap-mcp-configuration`
- `aap-mcp-security-compliance`
- `aap-mcp-system-monitoring`
- `aap-mcp-user-management`

**Environment Variables**: `AAP_MCP_SERVER`, `AAP_API_TOKEN`

## When to Use This Skill

Use this skill when:
- A skill or agent needs to verify AAP MCP server availability before proceeding
- User asks to validate or check AAP MCP connectivity
- As the first step in any governed workflow (assessment, execution, troubleshooting)

Do NOT use when:
- The actual analysis, execution, or troubleshooting step (use the specialized skill)
- Checking non-AAP MCP servers

## Workflow

### Step 1: Determine Required Servers

The calling skill or agent specifies which MCP servers it needs. Map common workflows to required servers:

| Workflow | Required Servers |
|---|---|
| Governance Assessment | All 6 servers |
| Execution | `aap-mcp-job-management`, `aap-mcp-inventory-management` |
| Troubleshooting | `aap-mcp-job-management`, `aap-mcp-inventory-management` |
| RBAC Check | `aap-mcp-user-management` |

If no specific servers are requested, validate all 6.

### Step 2: Validate Each Server

For each required server, make a minimal list call to verify connectivity.

**MCP Tool**: `job_templates_list` (from aap-mcp-job-management)
**Parameters**:
- `page_size`: `1`

**MCP Tool**: `inventories_list` (from aap-mcp-inventory-management)
**Parameters**:
- `page_size`: `1`

**MCP Tool**: `notification_templates_list` (from aap-mcp-configuration)
**Parameters**:
- `page_size`: `1`

**MCP Tool**: `credentials_list` (from aap-mcp-security-compliance)
**Parameters**:
- `page_size`: `1`

**MCP Tool**: `instance_groups_list` (from aap-mcp-system-monitoring)
**Parameters**:
- `page_size`: `1`

**MCP Tool**: `users_list` (from aap-mcp-user-management)
**Parameters**:
- `page_size`: `1`

### Step 3: Report Results

**Output format**:

```
## AAP MCP Validation Results

| Server | Status | Response |
|---|---|---|
| aap-mcp-job-management | ✅ Connected | [count] job templates found |
| aap-mcp-inventory-management | ✅ Connected | [count] inventories found |
| aap-mcp-configuration | ✅ Connected | [count] notification templates found |
| aap-mcp-security-compliance | ✅ Connected | [count] credentials found |
| aap-mcp-system-monitoring | ✅ Connected | [count] instance groups found |
| aap-mcp-user-management | ✅ Connected | [count] users found |

**Result**: [X]/[Y] required servers validated successfully.
```

If any server fails:

```
| aap-mcp-[name] | ❌ Failed | [error message] |
```

### Step 4: Determine Proceed/Stop

- If ALL required servers are validated: proceed to the calling skill
- If ANY required server fails: report failure and ask user how to proceed

## Dependencies

### Required MCP Servers
- All 6 AAP MCP servers (as configured in `mcps.json`)

### Required MCP Tools
- `job_templates_list` (from aap-mcp-job-management)
- `inventories_list` (from aap-mcp-inventory-management)
- `notification_templates_list` (from aap-mcp-configuration)
- `credentials_list` (from aap-mcp-security-compliance)
- `instance_groups_list` (from aap-mcp-system-monitoring)
- `users_list` (from aap-mcp-user-management)

### Related Skills
- All skills requiring AAP MCP access (this skill validates connectivity before they run)

### Reference Documentation
- AAP MCP server configuration in `mcps.json`

## Example Usage

**User**: "Validate AAP MCP for a governance assessment"

**Agent**: Validates all 6 servers with `page_size: 1` calls, reports:

```
## AAP MCP Validation Results

| Server | Status | Response |
|---|---|---|
| aap-mcp-job-management | ✅ Connected | 5 job templates found |
| aap-mcp-inventory-management | ✅ Connected | 3 inventories found |
| aap-mcp-configuration | ✅ Connected | 0 notification templates found |
| aap-mcp-security-compliance | ✅ Connected | 2 credentials found |
| aap-mcp-system-monitoring | ✅ Connected | 1 instance groups found |
| aap-mcp-user-management | ✅ Connected | 2 users found |

**Result**: 6/6 required servers validated successfully. Ready to proceed.
```

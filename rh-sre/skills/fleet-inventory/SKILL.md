---
name: fleet-inventory
description: |
  Query and display Red Hat Lightspeed managed system inventory. This skill focuses on discovery and listing only - for remediation actions, transition to the `/remediation` skill.

  Use when:
  - "Show the managed fleet"
  - "List all systems registered in Lightspeed"
  - "What systems are affected by CVE-X?"
  - "How many RHEL 8 systems do we have?"
  - "Show me production systems"

  **When NOT to use this skill** (use `/remediation` skill instead):
  - "Remediate CVE-X on these systems"
  - "Create a playbook for..."
  - "Patch system Y"

  This skill orchestrates MCP tools from lightspeed-mcp for fleet visibility and system inventory management.
model: inherit
color: blue
license: Apache-2.0
allowed-tools: get_host_details get_cve_systems
---

# Fleet Inventory Skill

This skill queries Red Hat Lightspeed to retrieve and display information about managed systems, registered hosts, and fleet inventory.

## Prerequisites

**Required MCP Servers**: `lightspeed-mcp` ([setup guide](https://console.redhat.com/))

**Required MCP Tools**:
- `get_host_details` (from lightspeed-mcp) - Retrieve system inventory
- `get_cve_systems` (from lightspeed-mcp) - Find CVE-affected systems

**Required Environment Variables**:
- `LIGHTSPEED_CLIENT_ID` - Red Hat Lightspeed service account client ID
- `LIGHTSPEED_CLIENT_SECRET` - Red Hat Lightspeed service account secret

### Prerequisite Validation

**CRITICAL**: Before executing any operations, execute the `/mcp-lightspeed-validator` skill to verify MCP server availability.

See **Step 0** in the Workflow section below for implementation details.

**Validation freshness**: Can skip if already validated in this session. See [Validation Freshness Policy](../mcp-lightspeed-validator/SKILL.md#validation-freshness-policy).

## When to Use This Skill

**Use this skill directly when you need**:
- List all systems registered in Red Hat Lightspeed
- Show systems affected by specific CVEs
- Display system details (OS version, tags, last check-in)
- Filter systems by environment, RHEL version, or tags
- Count systems matching criteria
- Verify system registration status

**Use the `/remediation` skill when you need**:
- Remediate vulnerabilities on systems
- Generate or execute playbooks
- Perform infrastructure changes
- End-to-end CVE remediation workflows

**How they work together**: Use this skill for discovery ("What systems are affected?"), then transition to the `/remediation` skill for action ("Remediate those systems").

## Workflow

### Step 0: Validate Lightspeed MCP Prerequisites

**Action**: Execute the `/mcp-lightspeed-validator` skill

**Note**: Can skip if validation was performed earlier in this session and succeeded. See [Validation Freshness Policy](../mcp-lightspeed-validator/SKILL.md#validation-freshness-policy).

**How to invoke**: Execute the `/mcp-lightspeed-validator` skill

**Handle validation result**:
- **If validation PASSED**: Continue to Step 1
- **If validation PARTIAL** (connectivity test unavailable):
  - Warn user: "Configuration appears correct but connectivity could not be tested"
  - Ask: "Do you want to proceed? (yes/no)"
  - If yes: Continue to Step 1
  - If no: Stop execution
- **If validation FAILED**:
  - The validator provides error details and setup instructions
  - Wait for user decision (setup/skip/abort)
  - If user chooses "skip": Attempt Step 1 anyway (may fail)
  - If user chooses "setup" or "abort": Stop execution

**Example**:
```
Before retrieving fleet inventory, I'll validate the Lightspeed MCP server configuration.

[Invoke mcp-lightspeed-validator skill]

✓ Lightspeed MCP validation successful.
Proceeding with fleet inventory query...
```

### Step 1: Retrieve System Inventory

**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [insights-api.md](../../docs/insights/insights-api.md) using the Read tool to understand the `get_host_details` response format and pagination handling
2. **Output to user**: "I consulted [insights-api.md](../../docs/insights/insights-api.md) to understand the `get_host_details` response format and pagination handling."

**MCP Tool**: `get_host_details` (from lightspeed-mcp)

**Purpose**: Query Lightspeed for comprehensive system information

**Parameters**: See [references/01-parameter-reference.md](references/01-parameter-reference.md) for get_host_details/get_cve_systems parameters and response fields.

**Verification Checklist**:
- ✓ Systems list returned with metadata
- ✓ Total count matches expectation
- ✓ System details include RHEL version, tags, status
- ✓ No authentication errors (401/403)

**Key Fields to Extract**:
- `id`: Unique system identifier (use for remediation workflows)
- `display_name` / `fqdn`: Human-readable hostname
- `rhel_version`: OS version (critical for remediation compatibility)
- `tags`: Environment labels (production, staging, dev)
- `stale`: Whether system recently checked in (< 7 days)
- `last_seen`: Last Lightspeed client run timestamp

### Step 2: Filter and Organize Systems

**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [fleet-management.md](../../docs/insights/fleet-management.md) using the Read tool to understand fleet inventory reporting structure and best practices
2. **Output to user**: "I consulted [fleet-management.md](../../docs/insights/fleet-management.md) to structure this inventory report."

Apply user-requested filters and grouping. See [references/01-parameter-reference.md](references/01-parameter-reference.md) for filtering and sorting patterns.

### Step 3: Query CVE-Affected Systems

**MCP Tool**: `get_cve_systems` (from lightspeed-mcp)

**Purpose**: Find systems affected by specific CVEs

**Parameters**: `cve_id` (CVE-YYYY-NNNNN, uppercase). See [references/01-parameter-reference.md](references/01-parameter-reference.md).

**Verification Checklist**:
- ✓ CVE ID matches request exactly
- ✓ System list includes remediation status for each
- ✓ Counts are accurate (affected, remediated, still vulnerable)
- ✓ `remediation_available` flag is present

**Status Interpretation**:
```
Status: "Vulnerable"
→ CVE affects this system, patch not applied
→ Action: Suggest remediation via `/remediation` skill

Status: "Patched"
→ CVE previously affected, now remediated
→ Action: No action needed, informational only

Status: "Not Affected"
→ System not vulnerable to this CVE
→ Action: Exclude from affected count
```

### Step 4: Generate Fleet Summary

Create organized output. **Read [references/03-output-templates.md](references/03-output-templates.md)** for report format (Overview, RHEL/Environment breakdown, System Details, Stale Systems).

### Step 5: Offer Remediation Transition

When appropriate, suggest transitioning to the `/remediation` skill:

```markdown
## Next Steps

**For CVE Remediation**:
If you need to remediate vulnerabilities on any of these systems, I can help using the `/remediation` skill:

Examples:
- "Remediate CVE-2024-1234 on web-server-01"
- "Create playbook for all RHEL 8 production systems affected by CVE-2024-5678"
- "Batch remediate critical CVEs on staging environment"

**For System Investigation**:
- "Show CVEs affecting web-server-01" (use cve-impact skill)
- "Analyze risk for production systems" (use cve-impact skill)
- "List critical vulnerabilities across the fleet" (use cve-impact skill)
```

## Dependencies

### Required MCP Servers
- `lightspeed-mcp` - Red Hat Lightspeed platform access for system inventory and CVE data

### Required MCP Tools
- `get_host_details` (from lightspeed-mcp) - Retrieve all registered systems with metadata
  - Parameters: Optional filters (system_id, hostname_pattern, tags, operating_system)
  - Returns: List of systems with id, display_name, fqdn, rhel_version, tags, stale status

- `get_cve_systems` (from lightspeed-mcp) - Find systems affected by specific CVEs
  - Parameters: cve_id (string, format: CVE-YYYY-NNNNN)
  - Returns: List of affected systems with vulnerability and remediation status

### Related Skills
- `mcp-lightspeed-validator` - **PREREQUISITE** - Validates Lightspeed MCP server configuration and connectivity
  - Use before: ALL fleet-inventory operations (Step 0 in workflow)
  - Purpose: Ensures MCP server is available before attempting tool calls
  - Prevents errors from missing configuration or credentials

- `cve-impact` - Analyze CVE severity and risk after identifying affected systems
  - Use after: "What systems are affected by CVE-X?" → "What's the risk of CVE-X?"

- `cve-validation` - Validate CVE IDs before querying affected systems
  - Use before: If CVE ID format is unclear, validate first

- `system-context` - Get detailed system configuration for specific hosts
  - Use after: Fleet discovery identifies systems needing deeper investigation

- `/remediation` (skill) - Transition to remediation workflows after discovery
  - Use after: "Show affected systems" → "Remediate those systems"

### Reference Documentation
- [insights-api.md](../../docs/insights/insights-api.md) - Red Hat Lightspeed API patterns and response formats
- [fleet-management.md](../../docs/insights/fleet-management.md) - System inventory best practices and filtering strategies

### Skill Orchestration Pattern

**Information-First Workflow**:
```
User Query: "Show the managed fleet"
    ↓
fleet-inventory skill (discovery)
    ↓
Systems identified: 42 total, 15 affected by CVE-2024-1234
    ↓
User: "What's the risk of CVE-2024-1234?"
    ↓
cve-impact skill (analysis)
    ↓
CVSS 8.1, Critical severity, affects httpd package
    ↓
User: "Remediate CVE-2024-1234 on all production systems"
    ↓
`/remediation` skill (action)
    ↓
Playbook generated and executed
```

**Key Principle**: Always start with discovery before taking remediation actions. This ensures informed decisions based on actual fleet state.

## Output, Examples, Error Handling

**Read [references/03-output-templates.md](references/03-output-templates.md)** for report format.
**Read [references/04-examples.md](references/04-examples.md)** for fleet, CVE-affected, and environment-filter examples.
**Read [references/05-error-handling.md](references/05-error-handling.md)** for no-results, API errors, and stale system handling.

## Best Practices

Start broad then filter; group by environment/RHEL/tier; highlight stale systems; offer `/remediation` transitions; use tables and percentages; declare document consultations; verify prerequisites first.

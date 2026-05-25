---
name: job-template-creator
description: |
  Create AAP (Ansible Automation Platform) job templates for executing playbooks. Use when users request:
  - "Create a job template for this playbook"
  - "Set up a template to run remediation playbooks"
  - "Configure AAP to execute this playbook"
  - "Add a new job template for CVE remediation"
  
  This skill guides through adding playbooks to Git projects and creating job templates via AAP Web UI.
model: inherit
color: blue
license: Apache-2.0
allowed-tools: job_templates_list job_templates_retrieve projects_list inventories_list job_templates_launch_retrieve
---

# AAP Job Template Creator Skill

This skill helps SREs create AAP job templates for executing Ansible playbooks, particularly for CVE remediation workflows.

## Prerequisites

**Required AAP Components**:
- AAP (Ansible Automation Platform) instance with API access
- Projects configured with playbooks
- Inventories with target hosts
- Credentials for authentication

**Required MCP Servers**: `aap-mcp-job-management` ([setup guide](https://docs.redhat.com/))

**Currently Available MCP Tools** (read-only):
- `job_templates_list` - List existing templates
- `job_templates_retrieve` - Get template details
- `projects_list` - List available projects
- `inventories_list` - List available inventories

**Missing MCP Tools** (needed for creation):
- ⚠️ `job_templates_create` - **NOT CURRENTLY AVAILABLE**
- ⚠️ `job_templates_update` - **NOT CURRENTLY AVAILABLE**

**Required Environment Variables**:
- `AAP_MCP_SERVER` - Base URL for the MCP endpoint of the AAP server (must point to the AAP MCP gateway)
- `AAP_API_TOKEN` - AAP API authentication token

### Prerequisite Validation

**CRITICAL**: Before executing operations, execute the `/mcp-aap-validator` skill to verify AAP MCP server availability.

**Validation freshness**: Can skip if already validated in this session. See [Validation Freshness Policy](../mcp-aap-validator/SKILL.md#validation-freshness-policy).

**How to invoke**: Execute the `/mcp-aap-validator` skill

**Handle validation result**:
- **If validation PASSED**: Continue with job template creation workflow
- **If validation PARTIAL**: Warn user and ask to proceed
- **If validation FAILED**: Stop execution, provide setup instructions from validator

## Current Limitation: No Create Tools Available

⚠️ **IMPORTANT**: The current AAP MCP implementation does **NOT** include tools to create job templates programmatically. The available MCP tools are read-only (list, retrieve, launch).

**Current Approach**:
- Job templates must be created through the **AAP Web UI**
- This skill provides step-by-step instructions for Web UI creation
- Future MCP tool additions will enable programmatic template creation

This skill documents both the **current manual workflow** and the **intended automated workflow** for when creation tools become available.

## When to Use This Skill

**Use this skill when you need**:
- Create a new job template for a remediation playbook
- Configure AAP to execute dynamically generated playbooks
- Set up templates for CVE remediation workflows
- Automate job template creation as part of remediation setup

**Do NOT use this skill when**:
- Job templates already exist (use `/playbook-executor` skill instead)
- Only need to execute existing templates (use `job_templates_launch_retrieve`)
- Need to modify existing templates (requires AAP Web UI currently)

## Invocation from playbook-executor

When invoked from the [playbook-executor](../playbook-executor/SKILL.md) skill (Scenario 3 - No suitable template), this skill receives playbook content in context. The playbook-executor invokes with an instruction such as:

```
Create a job template for this remediation playbook. Playbook: [content]. Filename: [filename]. Path: [our_playbook_path]. CVE: [cve_id]. Target systems: [list].
```

**When playbook content is provided**:
- Use the provided content for Phase 1 (Prepare Playbook in Git) instead of asking the user to supply it
- Write the playbook to the specified path in the user's Git repository (ask for repo path if not provided)
- Follow the Git flow: add, commit (with checkpoint for confirmation), push
- Then guide template creation via AAP Web UI (Phase 4)
- **Output**: Include the created template ID and name in the final report so playbook-executor can retrieve and validate it

**Phase 0 - Check context**: If playbook content is provided by the invoking skill, execute the git flow (write, add, commit with confirmation checkpoint, push) before guiding template creation. Otherwise, use the existing manual flow where the user supplies the playbook.

## Workflow

### Phase 0: Validate AAP MCP Prerequisites

**Action**: Execute the `/mcp-aap-validator` skill

**Note**: Can skip if validation was performed earlier in this session and succeeded. See [Validation Freshness Policy](../mcp-aap-validator/SKILL.md#validation-freshness-policy).

**How to invoke**: Execute the `/mcp-aap-validator` skill

**Handle validation result**:
- **If validation PASSED**: Continue to Phase 1
- **If validation PARTIAL**: Warn user and ask to proceed
- **If validation FAILED**: Stop execution, user must set up AAP MCP servers

### Phase 1: Prepare Playbook in Git Project

**Goal**: Add playbook to a Git repository AAP can access.

**Read [references/01-git-setup.md](references/01-git-setup.md)** for Option A (existing repo) and Option B (new repo).

**Verification**: Playbook committed, pushed, AAP synced, playbook path noted.

### Phase 2: Gather Required Information

Before creating a job template, collect:

1. **Playbook Information**:
   - Playbook name/path (e.g., `remediation-CVE-2025-49794.yml`)
   - Project where playbook is stored
   - Required variables/parameters

2. **Target Information**:
   - Inventory containing target hosts
   - Host groups or specific hosts to target
   - Any host limits or filters

3. **Credentials**:
   - SSH credentials for host access
   - Vault passwords (if playbook uses Ansible Vault)
   - Cloud credentials (if targeting cloud resources)

4. **Execution Settings**:
   - Job type (run/check)
   - Verbosity level
   - Concurrent execution limits
   - Timeout settings

### Phase 3: Verify Prerequisites

**Step 1: List Available Projects**

**MCP Tool**: `projects_list` (from aap-mcp-job-management)

**Parameters**:
- `page_size`: 50 (retrieve up to 50 projects)
- `search`: "remediation" (optional - filter by keyword)

**Expected Output**:
```json
{
  "count": 1,
  "results": [
    {
      "id": 6,
      "name": "Remediation Playbooks",
      "scm_type": "git",
      "scm_url": "https://github.com/org/playbooks.git",
      "status": "successful"
    }
  ]
}
```

**Action**: Identify the project ID where your playbook is stored.

**Step 2: List Available Inventories**

**MCP Tool**: `inventories_list` (from aap-mcp-inventory-management)

**Parameters**:
- `page_size`: 50
- `search`: "production" (optional - filter by keyword)

**Expected Output**:
```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "name": "Production Inventory",
      "total_hosts": 150,
      "has_active_failures": false
    }
  ]
}
```

**Action**: Identify the inventory ID containing your target hosts.

**Step 3: Verify Credentials**

**Note**: The current AAP MCP doesn't expose credential listing tools. You'll need credential IDs from AAP Web UI or administrator.

### Phase 4: Create Job Template via AAP Web UI

⚠️ **CURRENT LIMITATION**: AAP MCP has no create tools. Template creation must be done via AAP Web UI.

**Read [references/02-web-ui-form.md](references/02-web-ui-form.md)** for form fields and steps.

**Required**: Name, Inventory, Project, Playbook, Credentials. Enable Privilege Escalation. Prompt on Launch: Job Type (REQUIRED), Variables, Limit.

### Phase 5: Verify Template Creation

**MCP Tool**: `job_templates_list` (from aap-mcp-job-management)

**Parameters**:
- `search`: "CVE-2025-49794" (search for your template)
- `page_size`: 10

**Expected Output**:
```json
{
  "results": [
    {
      "id": 42,
      "name": "Remediate CVE-2025-49794",
      "playbook": "remediation-CVE-2025-49794.yml",
      "project": 6,
      "inventory": 1,
      "status": "never updated"
    }
  ]
}
```

**Success Criteria**:
- ✓ Template appears in search results
- ✓ Playbook path matches your playbook
- ✓ Project and inventory IDs are correct
- ✓ Template status is valid

### Phase 6: Test Template Execution (Optional)

**MCP Tool**: `job_templates_launch_retrieve` (from aap-mcp-job-management)

**Parameters**:
- `id`: "42" (template ID from Phase 5)

**Expected Output**:
```json
{
  "job": 1234,
  "status": "pending",
  "url": "/api/controller/v2/jobs/1234/"
}
```

**Follow-up**: Use `playbook-executor` skill to track job execution.

## Output and Examples

**Read [references/03-output-template.md](references/03-output-template.md)** for report format.
**Read [references/04-examples.md](references/04-examples.md)** for CVE remediation and dynamic variable examples.

## Dependencies

### Required MCP Servers
- `aap-mcp-job-management` - AAP job management API access

### Required MCP Tools (Current)
- `job_templates_list` - List existing templates (verification)
- `job_templates_retrieve` - Get template details (verification)
- `projects_list` - List available projects (prerequisite)
- `inventories_list` (from aap-mcp-inventory-management) - List inventories (prerequisite)

### Missing MCP Tools (Needed for Full Automation)
- `job_templates_create` - Create new job templates
- `job_templates_update` - Modify existing templates
- `credentials_list` - List available credentials

### Related Skills
- `mcp-aap-validator` - **PREREQUISITE** - Validates AAP MCP server before creation (invoke in Phase 0 if not validated in session)
- `job-template-remediation-validator` - Validates created template meets remediation requirements
- `playbook-executor` - Execute templates after creation
- `playbook-generator` - Generate remediation playbooks for templates
- `system-context` - Identify target systems for inventory selection

### Reference Documentation
- [AAP 2.6 Job Templates Documentation](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/using_automation_execution/controller-job-templates)
- [AAP 2.6 Creating Projects](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/using_automation_execution/controller-projects)

## Best Practices

1. **Use descriptive template names** - Include CVE ID or purpose: "Remediate CVE-2025-49794"
2. **Enable variable prompts for flexibility** - Check "Variables" in the "Prompt on Launch" section for dynamic values
3. **Set appropriate timeouts** - CVE remediation can take time; set generous timeouts
4. **Use privilege escalation** - Most remediation requires sudo/root access
5. **Document template purpose** - Use description field to explain usage
6. **Version playbooks** - Keep playbooks in Git for change tracking
7. **Test templates first** - Use check mode or test inventory before production
8. **Set concurrent limits** - Prevent overwhelming infrastructure with simultaneous jobs
9. **Enable notifications** - Configure email/webhook alerts for job completion
10. **Regular template audits** - Review and update templates as playbooks evolve

## Human-in-the-Loop Requirements

This skill requires user confirmation for:

1. **Git Operations** (adding playbook to repository):
   - Display: "I'll help you add the playbook to your Git repository"
   - Ask: "Proceed with Git operations (clone, commit, push)?"
   - Wait for confirmation

2. **Manual Template Creation** (AAP Web UI):
   - Display: "Template creation requires using the AAP Web UI"
   - Ask: "I'll provide step-by-step instructions. Ready to proceed?"
   - Wait for confirmation

3. **Test Execution** (optional verification):
   - Ask: "Should I test the template by launching a job?"
   - Wait for confirmation before launching

**Never assume approval** - always wait for explicit user confirmation.

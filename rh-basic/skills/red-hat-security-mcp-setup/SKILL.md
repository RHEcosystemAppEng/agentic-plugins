---
name: red-hat-security-mcp-setup
description: |
  Configure the Red Hat Security MCP server for CVE and advisory lookups across different AI agents (Claude Code, VS Code extensions). Guides through server addition, verification, SSO authentication, and testing with agent-specific instructions.
  
  Use when:
  - User asks to "add Red Hat Security MCP server"
  - User wants to "set up CVE lookup" or "enable security advisory tools"
  - User mentions "Red Hat MCP configuration" or "MCP server setup"
  
  Don't use for:
  - CVE analysis (use /red-hat-cve-explainer instead)
  - Support ticket severity (use /red-hat-support-severity instead)
  - Product lifecycle queries (use /red-hat-product-lifecycle instead)
license: Apache-2.0
user_invocable: true
model: inherit
color: blue
allowed-tools:
---

# Red Hat Security MCP Setup

Configure the Red Hat Security MCP server to enable live CVE and security advisory lookups in your AI agent environment.

## Prerequisites

**Required:**
- A Red Hat account at [console.redhat.com](https://console.redhat.com)
- One of the supported AI agents: Claude Code, VS Code, Cursor, Continue, or any MCP-compatible agent
- Internet connectivity to `security-mcp.api.redhat.com`

**Verification Steps:**
1. Verify Red Hat account is active at [console.redhat.com](https://console.redhat.com)
2. Confirm AI agent supports MCP HTTP servers (check agent documentation)
3. Test internet connectivity to `security-mcp.api.redhat.com`

**Human Notification Protocol:**

If prerequisites fail:
1. **Stop immediately** - No configuration changes
2. **Report error:**
   ```
   ❌ Cannot execute skill: [prerequisite] unavailable
   📋 Setup required: [instructions]
   ```
3. **Request decision:** "How to proceed? (setup/skip/abort)"
4. **Wait for user input**

**Security:** This skill does not require or use credentials directly. SSO authentication is handled via browser with no manual credential entry.

## When to Use This Skill

Use when the user wants to:
- Add the Red Hat Security MCP server for CVE and advisory data
- Enable the `/red-hat-cve-explainer` skill to use live MCP tools instead of web fallback

NOT for:
- CVE analysis (use `/red-hat-cve-explainer` instead)
- Support ticket guidance (use `/red-hat-support-severity` instead)

## Workflow

This skill follows a 4-step workflow that is agent-agnostic. Agent-specific implementation details are stored in [references/](references/) directory.

1. **Add MCP Server** — Configure the Red Hat Security MCP server endpoint
2. **Verify MCP Server** — Confirm server is registered and enabled
3. **Trigger SSO Authentication** — Initiate Red Hat Customer Portal browser login flow
4. **Test Authenticated Access** — Validate full functionality with live CVE query

## Dependencies

### Required MCP Servers
- `red-hat-security` - Red Hat Security API for CVE and advisory data (configured by this skill)

### Required MCP Tools
None - this skill configures the MCP server; it does not invoke MCP tools directly.

### Related Skills
- `/red-hat-cve-explainer` - Analyzes CVE severity and impact (uses the server configured by this skill)

### Reference Documentation
**Internal:**
- [references/claude.md](references/claude.md) - Claude Code setup instructions with CLI
- [references/generic-mcp-json.md](references/generic-mcp-json.md) - Generic mcp.json configuration for VS Code, Cursor, Continue, Windsurf

**Official:**
- [Red Hat Customer Portal](https://console.redhat.com) - Account management and SSO authentication

---

## Step 1: Add MCP Server

**Document Consultation** (REQUIRED - Execute FIRST):

1. **Action**: Detect the current AI agent environment
2. **Action**: Read the corresponding guide from [references/](references/):
   - [references/claude.md](references/claude.md) for Claude Code (has dedicated CLI)
   - [references/generic-mcp-json.md](references/generic-mcp-json.md) for VS Code, Cursor, Continue, Windsurf, and all other MCP-compatible agents
3. **Output to user**: "I consulted [references/{guide}.md](references/{guide}.md) for {agent} setup instructions."

**Implementation**:

Follow the "Step 1: Add MCP Server" instructions from the agent-specific guide. Prefer CLI methods over configuration file editing when available.

**Expected Output**:
- MCP server `red-hat-security` is added to agent configuration
- Configuration specifies HTTP transport to `https://security-mcp.api.redhat.com/mcp`

**Error Handling**:
- If agent cannot be detected: Ask user to specify their AI agent
- If agent-specific guide doesn't exist: Inform user that agent is not yet supported; suggest Claude Code or VS Code
- If CLI command fails: Fall back to configuration file method documented in agent guide

---

## Step 2: Verify MCP Server

**Document Consultation**: Continue using the agent-specific guide from Step 1.

**Implementation**:

Follow the "Step 2: Verify MCP Server" instructions from the agent-specific guide. Prefer CLI/UI verification methods over file inspection.

**Expected Output**:
- `red-hat-security` appears in MCP server list
- Server status is `enabled` or `connected`

**Error Handling**:
- If server not listed: Re-run Step 1; check for typos in configuration
- If server status is `error` or `disabled`: Check agent logs for details; verify URL is correct
- If verification command not available: Fall back to file inspection method

---

## Step 3: Trigger SSO Authentication

**Document Consultation**: Continue using the agent-specific guide from Step 1.

**Implementation**:

Follow the "Step 3: Trigger SSO Authentication" instructions from the agent-specific guide.

The Red Hat Security MCP server uses browser-based SSO. Authentication is triggered on first tool use.

**Expected Behavior**:
1. Agent sends a query that requires `red-hat-security` tools (e.g., "List CVEs for Red Hat Enterprise Linux 9")
2. Browser window opens automatically to Red Hat SSO login page
3. User authenticates with Red Hat account credentials
4. Session token is stored; subsequent requests proceed without prompting

**Error Handling**:
- If browser doesn't open: Check agent output/logs for authentication URL; open manually
- If authentication fails: Verify Red Hat account is active at [console.redhat.com](https://console.redhat.com)
- If session token not stored: Check agent has write access to token storage location
- If agent doesn't support MCP SSO: Inform user their agent version may not support HTTP MCP servers with SSO

---

## Step 4: Test Authenticated Access

**Document Consultation**: Continue using the agent-specific guide from Step 1.

**Implementation**:

Follow the "Step 4: Test Authenticated Access" instructions from the agent-specific guide.

Send a test query to verify full MCP server functionality: "Give me the latest 5 CVEs for Red Hat Enterprise Linux 9"

**Expected Output**:
- List of CVE IDs with severity, publication date, and description
- Response generated using `red-hat-security` MCP tools (not web fallback)
- No authentication or network errors

**Error Handling**:
- If authentication timeout: Re-run Step 3 to re-authenticate
- If network errors: Check firewall rules for `security-mcp.api.redhat.com`; verify internet connectivity
- If empty results: Red Hat account may lack subscription; check access at [console.redhat.com](https://console.redhat.com)
- If agent uses web fallback instead of MCP: Verify agent configuration includes `red-hat-security` and restart agent

---

## Example Usage

**User Query:**
```
Set up the Red Hat Security MCP server so I can analyze CVEs
```

**Skill Response:**
```
I'll help you set up the Red Hat Security MCP server for CVE analysis.

I consulted references/claude.md for Claude Code setup instructions.

Step 1: Adding MCP Server
Running: claude mcp add --transport http red-hat-security https://security-mcp.api.redhat.com/mcp
✓ MCP server added successfully

Step 2: Verifying MCP Server
Running: claude mcp get red-hat-security
✓ Server registered: red-hat-security (HTTP)
  URL: https://security-mcp.api.redhat.com/mcp

Step 3: Triggering SSO Authentication
Sending test query to trigger authentication...
🌐 Browser window opened for Red Hat SSO login
⏳ Waiting for authentication...
✓ Authentication complete

Step 4: Verifying Authentication
Running: claude mcp get red-hat-security
✓ Server status: authenticated
✓ Red Hat Security MCP server is ready

Red Hat Security MCP server setup complete!

Next steps:
- Use /red-hat-cve-explainer to analyze CVE severity and impact
- CVE queries will now use live Red Hat security data
- Session tokens are stored; re-authentication may be required after restart
```

---

## Post-Setup Notes

Tell the user:

```
Red Hat Security MCP server setup complete!

Next steps:
- Use /red-hat-cve-explainer to analyze CVE severity and impact
- CVE queries will now use live Red Hat security data instead of web fallback
- Session tokens are stored; re-authentication may be required after agent restart

For issues:
- Check agent-specific guide: references/{agent}.md
- Verify Red Hat account status: https://console.redhat.com
- Restart agent if MCP server changes don't take effect
```

## Notes

- **Subscription**: An active Red Hat subscription is recommended for full dataset access
- **No manual credentials**: Do NOT add `headers`, `env`, or API keys—SSO handles all authentication
- **Multi-agent support**: This skill supports multiple agents; implementation details are in agent-specific guides
- **Security data**: Server provides CVEs, advisories, errata used by `/red-hat-cve-explainer`
- **Extensibility**: To add support for additional agents, create a new guide in [references/](references/) following the 4-step workflow
- **Learn more**: https://catalog.redhat.com/en/software/container-stacks/detail/6a0488e942b089e6e3b952b0

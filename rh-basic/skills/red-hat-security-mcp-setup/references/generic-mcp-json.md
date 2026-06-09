# Generic MCP Configuration - Red Hat Security MCP Setup

Agent-agnostic instructions for configuring the Red Hat Security MCP server using `mcp.json` configuration file format. Use for AI agents that don't have a dedicated CLI (VS Code extensions, Cursor, Windsurf, etc.).

## Step 1: Add MCP Server

**Choose ONE Configuration File:**

Select the appropriate configuration file for your agent. **Create only ONE file** - do not create multiple:

| Agent | Configuration File (choose ONE) |
|-------|--------------------------------|
| **VS Code** | `.vscode/settings.json` (workspace) |
| **Cursor** | `.cursor/mcp.json` (project root) |
| **Continue** | `.continue/config.json` |
| **Windsurf** | `mcp.json` (project root) |
| **Other** | `mcp.json` (project root) |

**Add Configuration:**

Create or edit the appropriate file and add:

```json
{
  "mcpServers": {
    "red-hat-security": {
      "transport": "http",
      "url": "https://security-mcp.api.redhat.com/mcp"
    }
  }
}
```

**Alternative Field Names (if needed):**

If the above configuration doesn't work, some agents may use `type` instead of `transport`:

```json
{
  "mcpServers": {
    "red-hat-security": {
      "type": "http",
      "url": "https://security-mcp.api.redhat.com/mcp"
    }
  }
}
```

**After Adding:**
- Save the file
- **Do NOT create additional MCP configuration files** - only one is needed
- Restart or reload your AI agent/editor to apply changes

## Step 2: Verify MCP Server

**Configuration File Verification:**

Read the configuration file to confirm the entry was added correctly:

```bash
cat mcp.json
# or
cat .vscode/settings.json
# or
cat .cursor/mcp.json
```

**Expected Output:**
- File contains `red-hat-security` server entry
- Transport/type is `http`
- URL is `https://security-mcp.api.redhat.com/mcp`

**Agent UI Verification (if available):**

Some agents provide UI to view MCP servers:
- Check agent's settings/preferences panel for MCP server list
- Look for "MCP Servers", "Tools", or "Extensions" section
- Verify `red-hat-security` appears as enabled/connected

## Step 3: Trigger SSO Authentication

The Red Hat Security MCP server uses Red Hat Customer Portal SSO authentication. Authentication is triggered on first tool use.

**Method 1: Direct Prompt (Preferred)**

Send this prompt to your AI agent:

```
Give me the latest 5 CVEs for Red Hat Enterprise Linux 9
```

**Method 2: Explicit Tool Invocation (if supported)**

If your agent supports direct tool calls, invoke any tool from the `red-hat-security` server.

**Expected Behavior:**
1. Agent attempts to use `red-hat-security` MCP server tools
2. Browser window opens automatically to Red Hat SSO login page
3. User authenticates with Red Hat account credentials
4. Session token is stored automatically
5. Original query completes with live CVE data

**Troubleshooting:**
- **Browser doesn't open**: Check agent logs/output for authentication URL; copy and open manually in browser
- **No prompt appears**: Verify MCP server configuration is correct; restart agent
- **Authentication fails**: Verify Red Hat account is active at [console.redhat.com](https://console.redhat.com)

## Step 4: Verify Authentication Status

**Method 1: Test Query**

Send a test query to verify the MCP server is authenticated and functional:

```
Give me the latest 5 CVEs for Red Hat Enterprise Linux
```

**Expected Output:**
- List of CVE IDs with severity and details
- Response indicates use of `red-hat-security` MCP tools
- No authentication errors

**Method 2: Agent Logs (if available)**

Check agent logs/output panel for:
- Successful HTTP requests to `security-mcp.api.redhat.com`
- MCP tool invocations from `red-hat-security` server
- No authentication errors or 401/403 responses

**Common Issues:**
- **Authentication timeout**: Re-run Step 3 to re-authenticate
- **Network errors**: Check internet connectivity and firewall rules for `security-mcp.api.redhat.com`
- **Empty/generic responses**: Agent may not support HTTP MCP servers; check agent documentation
- **"Server not found" errors**: Restart agent to reload MCP configuration

## Configuration Examples by Agent

**IMPORTANT**: Only create ONE configuration file per project.

### VS Code
**File**: `.vscode/settings.json` (workspace settings)

```json
{
  "mcpServers": {
    "red-hat-security": {
      "type": "http",
      "url": "https://security-mcp.api.redhat.com/mcp"
    }
  }
}
```

### Cursor
**File**: `mcp.json` (project root)

**Do NOT create**: `.cursor/mcp.json` or `.mcp.json` (these may cause conflicts)

```json
{
  "mcpServers": {
    "red-hat-security": {
      "transport": "http",
      "url": "https://security-mcp.api.redhat.com/mcp"
    }
  }
}
```

### Continue
**File**: `.continue/config.json`

```json
{
  "mcp": {
    "servers": {
      "red-hat-security": {
        "transport": "http",
        "url": "https://security-mcp.api.redhat.com/mcp"
      }
    }
  }
}
```

### Windsurf / Other Agents
**File**: `mcp.json` (project root)

```json
{
  "mcpServers": {
    "red-hat-security": {
      "transport": "http",
      "url": "https://security-mcp.api.redhat.com/mcp"
    }
  }
}
```

## Notes

- **One file only**: Create only ONE MCP configuration file per project to avoid conflicts
- **No credentials required**: SSO authentication is handled automatically via browser - do NOT add API keys, tokens, or headers
- **Session persistence**: Tokens are stored by the MCP client; may require re-authentication after agent restart
- **Subscription**: An active Red Hat subscription is recommended for full dataset access
- **Agent compatibility**: Verify your agent supports HTTP-based MCP servers (not all do)
- **Restart requirement**: Most agents require restart/reload after adding MCP server configuration
- **File cleanup**: If you created multiple MCP files (`.cursor/mcp.json`, `.mcp.json`, `mcp.json`), delete all except the correct one for your agent

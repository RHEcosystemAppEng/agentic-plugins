# Claude Code - Red Hat Security MCP Setup

Agent-specific instructions for configuring the Red Hat Security MCP server in Claude Code.

## Step 1: Add MCP Server

```bash
claude mcp add --transport http red-hat-security https://security-mcp.api.redhat.com/mcp
```

## Step 2: Verify MCP Server

```bash
claude mcp get red-hat-security
```

**Expected Output:**
- Server configuration details
- Transport: `http`
- URL: `https://security-mcp.api.redhat.com/mcp`
- Status: `enabled` or `connected`

## Step 3: Trigger SSO Authentication

The Red Hat Security MCP server uses Red Hat Customer Portal SSO authentication. Authentication is triggered on first tool use.

```bash
claude prompt "List CVEs for Red Hat Enterprise Linux"
```

**Expected Behavior:**
- A browser window opens automatically pointing to Red Hat SSO login
- User authenticates with Red Hat account credentials
- Session token is stored for subsequent requests
- No further authentication required for this session

**Troubleshooting:**
- If browser doesn't open automatically, look for authentication URL in the command output and open it manually

## Step 4: Verify Authentication Status

Check that the MCP server is registered and authenticated:

```bash
claude mcp get red-hat-security
```

**Expected Output:**
- Server configuration is displayed
- Status shows `connected` or `authenticated`
- No authentication errors

**Common Issues:**
- **Server not found**: Re-run Step 1 to add the MCP server
- **Not authenticated**: Re-run Step 3 to trigger SSO authentication
- **Network errors**: Check internet connectivity and firewall rules for `security-mcp.api.redhat.com`
- **Invalid credentials**: Verify Red Hat account is active at [console.redhat.com](https://console.redhat.com)

## Notes

- **Subscription**: An active Red Hat subscription is recommended for full dataset access
- **Session persistence**: Authentication tokens are stored per session; restart may require re-authentication
- **No manual credentials**: Do NOT add `headers`, `env`, or API keys to configuration—SSO handles all authentication
- **Restart requirement**: After adding the MCP server, restart Claude Code or reload MCP servers for changes to take effect

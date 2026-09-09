---
name: red-hat-security-mcp-setup
description: Add the Red Hat Security MCP server at the project or user level for the current tool. Configures the HTTP transport endpoint and explains the Red Hat Customer Portal SSO browser login flow.
license: Apache-2.0
user_invocable: true
model: inherit
color: blue
allowed-tools:
---

# Red Hat Security MCP Setup

Add the Red Hat Security MCP server to the current tool's MCP configuration,
at either the project or user level.

## Prerequisites

A Red Hat account at [console.redhat.com](https://console.redhat.com).

## When to Use This Skill

When the user wants to add the Red Hat Security MCP server to their project to enable live CVE and advisory lookups.

## Workflow

1. Ask the user whether to install at the **project level** (this workspace
   only) or the **user level** (every workspace opened with the current tool).
2. Detect the current agentic tool and resolve the target config file for
   the chosen level.
3. Locate the source `red-hat-security` entry: prefer this plugin's
   vendor-specific `com.<vendor>/mcp.json`, falling back to the plugin-root
   `mcp.json`, then to the inline skeleton.
4. Merge that entry into the target file without removing existing servers.
5. Explain the browser SSO authentication flow to the user.

## Dependencies

- Write access to the target MCP configuration file (project- or
  user-level, per the user's choice in Step 1).
- Read access to this plugin's directory, to locate `com.<vendor>/mcp.json`.

## Step 1 — Ask the user where to install

Ask the user to choose one:

- **Project-level** — only the current workspace gets the server.
- **User-level** — every workspace opened with the current tool gets the
  server.

## Step 2 — Detect the current tool and resolve the target file

1. State which agentic tool you are: You already know this from your system context (e.g., "I am Claude Code", "I am Cursor", etc.). State it explicitly.
2. Look up the target file path in the table below based on:
   - The tool you identified in substep 1
   - The installation level the user chose in Step 1 (project or user)

┌─────────────────┬───────────────────────────┬────────────────────────────┬─────────────────────┐
│  Current tool   │   Vendor namespace dir    │    Project-level target    │  User-level target  │
├─────────────────┼───────────────────────────┼────────────────────────────┼─────────────────────┤
│ Claude Code     │ com.anthropic.claude-code │ <project>/.mcp.json        │ ~/.claude/.mcp.json │
├─────────────────┼───────────────────────────┼────────────────────────────┼─────────────────────┤
│ Cursor          │ com.cursor.editor         │ <project>/.cursor/mcp.json │ ~/.cursor/mcp.json  │
├─────────────────┼───────────────────────────┼────────────────────────────┼─────────────────────┤
│ Other / unknown │ (plugin root)             │ <project>/.mcp.json        │ ~/.mcp.json         │
└─────────────────┴───────────────────────────┴────────────────────────────┴─────────────────────┘

3. Resolve <project> to an absolute path: If the target path contains <project>, determine the git repository root:
git rev-parse --show-toplevel 2>/dev/null || pwd
   Note: <project> means the git repository root (where .git/ lives), not your current working directory. The || pwd fallback only applies if you're not inside a git repository at all.

This makes it crystal clear that:
- <project> = git repository root
- Current working directory is irrelevant if you're in a git repo
- pwd is only used when there's no git repo

If the current tool isn't in the table, use the "Other / unknown" row and tell the user the target location is a best-effort default they should verify for their tool.

## Step 3 — Locate the source server config

Look for the `red-hat-security` entry to merge, in this order:

1. `$PLUGIN_ROOT/com.<vendor>/mcp.json` — the namespace dir for the
   currently executing tool (e.g. `./com.cursor.editor/mcp.json`,
   `./com.anthropic.claude-code/mcp.json`).
2. `$PLUGIN_ROOT/mcp.json` — the plugin-root fallback.
3. If neither file exists, use this skeleton:

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

Treat whichever source is found as read-only reference material — do not
edit it in place.

## Step 4 — Merge the entry into the target file

If `$MCP_FILE` (resolved in Step 2) exists: read it and merge in the
`red-hat-security` entry found in Step 3, without removing any other
servers already present.
If it does not exist: create it, wrapping the entry in `{"mcpServers": {...}}`.

Write the result back to `$MCP_FILE`.

## Step 5 — Explain authentication to the user

Tell the user:

```
Red Hat Security MCP server added.

Authentication: Red Hat Customer Portal SSO

The first time any tool from this server is called, a browser window will
open automatically so you can log in with your Red Hat account. After you
complete login, the session token is stored and subsequent calls proceed
without prompting.

If the browser does not open automatically, look for an authentication URL
printed in the MCP server output and open it manually.

Restart the agentic tool (or reload MCP servers) for the new configuration
to take effect.
```

## Notes

- This server exposes Red Hat security data (CVEs, advisories, errata). It
  is the backend used by `/red-hat-cve-explainer` when `get_cve_by_id` and
  related tools are available.
- An active Red Hat subscription is required to access the full dataset.
- Do not add `headers` or `env` auth fields to the target MCP config -- the
  server handles authentication itself via the browser SSO flow.
- The table in Step 2 covers the tools this plugin ships instructions for.
  If a tool's exact config path is unconfirmed, say so explicitly instead
  of guessing silently.

---
name: red-hat-security-mcp-setup
description: Configure the Red Hat Security MCP server in the current project or user-level MCP config file.
license: Apache-2.0
user_invocable: true
model: inherit
allowed-tools:
# allowed-tools is intentionally empty. Populate it with the file read/write
# tool names for your client before use. Claude Code uses Read and Write;
# consult your client's documentation for equivalents in Cursor or Copilot.
---


# Setup MCP server for Red Hat security content

Add the MCP server for Red Hat security content to the current project.

## Prerequisites

A Red Hat account at [console.redhat.com](https://console.redhat.com).

## When to Use This Skill

When the user wants to add the Red Hat Security MCP server to their project to enable live CVE and advisory lookups.

## Server details

| Field | Value |
|---|---|
| Key | `red-hat-security` |
| Transport | HTTP |
| URL | `https://security-mcp.api.redhat.com/mcp` |

## Instructions

1. Determine the MCP configuration file supported by this client. 
2. If this client supports project scope, ask the user:
   "Install the Red Hat Security MCP server for this project only or globally for all projects?"
   Wait for the user's answer before proceeding.
   Do not infer scope from context.
3. Add or update the `red-hat-security` server entry with:
   - `type: http`
   - `url: https://security-mcp.api.redhat.com/mcp`
4. If the config already contains a `red-hat-security` entry, update that entry in place instead of adding a duplicate.
5. Do not add `headers` or `env` auth fields; the server handles authentication itself via browser SSO.
6. If the chosen file cannot be written or the client does not expose a writable MCP config path, stop and report: `Could not write MCP configuration because the client does not support writable MCP config files or the file is not writable.`
7. Report the absolute path to the file you updated.


## After installation

Tell the user:
- Red Hat Security MCP server added to <absolute path to MCP config file>.
- Authentication is required to use: When the MCP server is first loaded, a
    browser window will open for you to log in with your Red Hat account.
    Complete the SSO login and you will be redirected back to your client. If
    the browser does not open automatically or SSO login fails, use the client’s
    reconnect button and retry.
- Restart your client or reload MCP servers for the new configuration to take
  effect.
- After restart, open your client's MCP server list and enable the Red Hat Security server if it is not already active.


## Notes

- Provided by Red Hat for Red Hat customers and partners.
- An active Red Hat subscription is required to access the full dataset.
- Learn more: https://catalog.redhat.com/en/software/container-stacks/detail/6a0488e942b089e6e3b952b0
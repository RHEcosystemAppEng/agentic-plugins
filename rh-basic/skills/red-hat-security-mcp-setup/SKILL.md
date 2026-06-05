---
name: red-hat-security-mcp-setup
description: Surface real-time CVE intelligence, errata, and remediation guidance for Red Hat products directly in your AI agent or developer workflow.
license: Apache-2.0
user_invocable: true
model: inherit
allowed-tools:
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

Using your knowledge of the current client, install the MCP server using the details above. Prefer project scope when running inside a project. Report the exact file path where the configuration was written.

Do not add `headers` or `env` auth fields — the server handles authentication itself via browser SSO.

## After installation

Tell the user:
- Red Hat Security MCP server added to <exact file path>.
- Authentication is required to use: When the MCP server is first loaded, a
    browser window will open for you to log in with your Red Hat account.
    Complete the SSO login and you will be redirected back to your client. If
    the browser does not open automatically, look for a connect or reconnect
    button in your client's MCP server list and click it to trigger the flow.
- Restart your client or reload MCP servers for the new configuration to take
  effect.
- After restart, open your client's MCP server list and enable the Red Hat Security server if it is not already active.


## Notes

- Provided by Red Hat for Red Hat customers and partners.
- An active Red Hat subscription is required to access the full dataset.
- Learn more: https://catalog.redhat.com/en/software/container-stacks/detail/6a0488e942b089e6e3b952b0
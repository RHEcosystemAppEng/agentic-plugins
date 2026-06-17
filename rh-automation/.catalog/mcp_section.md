<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, AGENTS.md, marketplace/rh-agentic-collection.yml
-->

| Server | Role |
|--------|------|
| **aap-mcp-job-management** | Job templates, launches, events, workflows, approvals. |
| **aap-mcp-inventory-management** | Inventories, hosts, groups, host facts. |
| **aap-mcp-configuration** | Execution environments, notifications, platform settings. |
| **aap-mcp-security-compliance** | Credentials, credential types, compliance checks. |
| **aap-mcp-system-monitoring** | Instance groups, activity, mesh topology, platform status. |
| **aap-mcp-user-management** | Users, teams, organizations, RBAC. |

Configure servers through **`mcps.json`**; skills must be invoked instead of calling MCP tools directly from the agent.

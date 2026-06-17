<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, AGENTS.md, marketplace/rh-agentic-collection.yml
-->

| Server | Role |
|--------|------|
| **lightspeed-mcp** | CVEs, inventory, remediation inputs, playbook-related Lightspeed workflows. |
| **aap-mcp-job-management** | Job templates, projects, launches, execution status. |
| **aap-mcp-inventory-management** | Inventories and hosts for execution planning. |

Configure servers through **`mcps.json`**; skills must be invoked instead of calling MCP tools directly from the agent.

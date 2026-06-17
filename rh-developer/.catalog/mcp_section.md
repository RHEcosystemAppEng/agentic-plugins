<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, AGENTS.md, marketplace/rh-agentic-collection.yml
-->

| Server | Role |
|--------|------|
| **openshift** | Cluster CRUD, logs, events, Helm — primary for OpenShift deploy and debug skills. |
| **podman** | Local image/build workflows used by S2I and container skills. |
| **github** | Repository analysis for `/detect-project` when sources are on GitHub. |
| **lightspeed-mcp** | Optional Insights-style data for RHEL-focused flows. |

Configure in **`mcps.json`**; invoke skills rather than MCP tools directly from the agent.

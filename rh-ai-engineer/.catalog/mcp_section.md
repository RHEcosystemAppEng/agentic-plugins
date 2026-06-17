<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, AGENTS.md, marketplace/rh-agentic-collection.yml
-->

| Server | Role |
|--------|------|
| **openshift** | Kubernetes resource operations, pod logs, events — baseline cluster access. |
| **rhoai** | RHOAI-focused convenience APIs; skills may fall back to **openshift** when needed. |
| **ai-observability** | GPU metrics, vLLM analysis, tracing — optional when configured. |

Configure servers through **`mcps.json`**; skills must be invoked instead of calling MCP tools directly from the agent.

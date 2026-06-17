<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, AGENTS.md, marketplace/rh-agentic-collection.yml
-->

| Server | Role |
|--------|------|
| **openshift-virtualization** | KubeVirt and OpenShift Virtualization VM, snapshot, and migration workflows via the Kubernetes/OpenShift API. |

Configure servers through **`mcps.json`** (e.g. **`KUBECONFIG`**); skills must be invoked instead of calling MCP tools directly from the agent.

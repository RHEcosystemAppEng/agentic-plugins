<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, AGENTS.md, marketplace/rh-agentic-collection.yml
-->

| Server | Role |
|--------|------|
| **openshift-self-managed** | Assisted Installer API for self-managed cluster lifecycle (OCP, SNO). |
| **openshift-ocm-managed** | OpenShift Cluster Manager API for managed service clusters (ROSA, ARO, OSD). |
| **openshift-administration** | Kubernetes/OpenShift operations for multi-context fleet reports; read-only where applicable. |

Configure servers through **`mcps.json`**; skills must be invoked instead of calling MCP tools directly from the agent.

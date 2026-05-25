---
name: cluster-report
description: |
  Generate a consolidated health report across multiple OpenShift clusters.
  Verifies each kubeconfig context is a genuine OpenShift cluster before
  reporting. Non-OpenShift contexts are skipped by default.
  Collects node resources (CPU, memory, GPUs), namespace counts, and pod
  status into a single comparison view.
  Use when:
  - "Show me a report across all clusters"
  - "Compare cluster health"
  - "Multi-cluster status overview"
  - "How are my clusters doing?"
  - "Include all clusters including non-OpenShift" (override default filter)
  NOT for single-cluster deep-dives or troubleshooting specific pods.
license: Apache-2.0
model: inherit
color: cyan
allowed-tools: configuration_contexts_list resources_get nodes_top resources_list namespaces_list pods_list
metadata:
  mcp_server: openshift-administration
  mcp_tools_priority: true
  environment_vars:
    - KUBECONFIG
  destructive: false
---

# cluster-report

**MCP-First Approach**: This skill uses MCP tools from `openshift-administration` server. MCP tools have **absolute priority**.

**CLI Tools Policy**:
- ✅ **ALWAYS use MCP tools** when available
- ⚠️ **Last resort only**: CLI commands (`oc`, `kubectl`) may be attempted if no MCP alternative exists
- ⚠️ **Assume unavailable**: CLI tools are likely not installed in the execution environment

Generate a unified health and resource report across multiple OpenShift/Kubernetes clusters using the openshift-administration MCP server's multi-cluster capabilities.

## Prerequisites

**Required MCP Servers**: `openshift-administration` ([setup guide](../../README.md#environment-setup))

**MCP Server Architecture**:
This skill uses `openshift-administration` MCP server exclusively. This server provides multi-cluster administration and reporting capabilities for both OpenShift and Kubernetes clusters.

| MCP Server | Used By This Skill? | Purpose | Cluster Types |
|------------|---------------------|---------|---------------|
| `openshift-administration` | ✅ YES | Multi-cluster reporting, resource queries via KUBECONFIG | OpenShift, Kubernetes |
| `openshift-self-managed` | ❌ NO (used by cluster-creator) | Cluster creation via Assisted Installer | OCP, SNO |
| `openshift-ocm-managed` | ❌ NO (used by cluster-inventory) | Managed service cluster listing | ROSA, ARO, OSD |

**Required MCP Tools** (all from `openshift-administration` server):
- `configuration_contexts_list` — list all kubeconfig contexts and server URLs
- `resources_get` — get a single Kubernetes resource by apiVersion/kind/name
- `nodes_top` — node CPU and memory usage from Metrics Server
- `resources_list` — list Kubernetes resources by apiVersion/kind
- `namespaces_list` — list all namespaces in a cluster
- `projects_list` — list all OpenShift projects
- `pods_list` — list all pods across namespaces

**Required Environment Variables**: `KUBECONFIG` — must contain at least one cluster context. Two or more recommended for comparison.

**Multi-Cluster Setup**: For large-scale deployments using service account tokens instead of interactive `oc login`, see [multi-cluster-auth.md](../../docs/multi-cluster-auth.md) and the [build-kubeconfig.py](../../scripts/cluster-report/build-kubeconfig.py) helper script.

**Helper Scripts** (Python 3, stdlib only — auditable, do not reimplement):
- [`assemble.py`](../../scripts/cluster-report/assemble.py) — resolves `$file` references into complete raw data JSON
- [`aggregate.py`](../../scripts/cluster-report/aggregate.py) — aggregates raw data into structured report JSON

**Script Usage Rules**:
- Invoke scripts via the documented pipeline (Step 3) — do NOT reimplement their logic inline
- Do NOT write ad-hoc Python to parse or transform MCP output — the scripts handle all parsing
- You MAY read the scripts for debugging if the pipeline returns errors

**Verification**:
1. Check `openshift-administration` in `mcps.json`
2. Verify `KUBECONFIG` set: `test -n "$KUBECONFIG"`
3. Test connection: Call `configuration_contexts_list` to verify MCP server responsive

**On Failure**: Stop immediately, display setup instructions, ask "How to proceed? (setup/skip/abort)", wait for user input.

**Security**: Never expose KUBECONFIG path, contents, or any credential values in output.

## When to Use This Skill

**Use when**:
- Comparing resource utilization across clusters
- Getting a fleet-wide health overview
- Preparing capacity planning reports

**Do NOT use when**:
- Debugging a specific pod or workload (use `/debug-pod`)

## Workflow

### Step 0: Prerequisites Check

**Execute verification from Prerequisites section.**

**If MCP server unavailable**:
1. Stop immediately
2. Display: "Cannot execute skill: openshift-administration MCP server not configured"
3. Display: "Setup: Configure openshift-administration in mcps.json (see README.md#environment-setup)"
4. Ask: "How to proceed? (setup/skip/abort)"
5. Wait for user input

**If KUBECONFIG not set**:
1. Stop immediately
2. Display: "Cannot execute skill: KUBECONFIG environment variable not set"
3. Display: "Setup: export KUBECONFIG=/path/to/kubeconfig (see credentials-management.md)"
4. Ask: "How to proceed? (setup/skip/abort)"
5. Wait for user input

**Security**: Never expose KUBECONFIG path or contents.

### Step 1: Discover and Verify Clusters

#### Step 1a: List Contexts

**MCP Tool**: `configuration_contexts_list`

Collect all context names and server URLs. Do NOT present results to the user yet.

**Expected Output**: List of context names with associated server URLs.

**Error Handling**:
- If no contexts found: Stop and instruct user to verify KUBECONFIG points to a valid file with cluster contexts
- If tool call fails: Report MCP server connectivity issue, suggest checking `mcps.json` configuration

#### Step 1b: Verify OpenShift Clusters

For **each** context discovered in Step 1a, probe for the OpenShift `ClusterVersion` resource:

**MCP Tool**: `resources_get`

| Parameter | Value |
|---|---|
| `apiVersion` | `config.openshift.io/v1` |
| `kind` | `ClusterVersion` |
| `name` | `version` |
| `context` | `<context-name>` |

**Classification rules**:

| Probe Result | Classification | Default Behavior |
|---|---|---|
| Success (resource returned) | **OpenShift** — extract version from `.status.desired.version` | Include |
| 403 Forbidden | **OpenShift (unverified)** — API group exists, RBAC restricts access | Include (version shown as "unknown") |
| 404 / resource not found | **Non-OpenShift** (vanilla Kubernetes or other distribution) | Exclude |
| Timeout / connection refused / 401 | **Unreachable** | Always exclude |

**Performance**: Issue all `resources_get` calls in parallel (one per context) since they are independent.

#### Step 1c: Present Verification Results

Present a categorized summary to the user:

```markdown
## Cluster Discovery Results

### OpenShift Clusters (will be included in report)

| Context | Server | OpenShift Version |
|---------|--------|-------------------|
| prod-us | https://api.prod-us.example.com:6443 | 4.16.3 |
| staging | https://api.staging.example.com:6443 | 4.15.12 |

### Non-OpenShift Clusters (excluded by default)

| Context | Server | Reason |
|---------|--------|--------|
| dev-k8s | https://dev-k8s.example.com:6443 | No ClusterVersion resource (vanilla Kubernetes) |

### Unreachable Clusters (excluded)

| Context | Server | Error |
|---------|--------|-------|
| old-cluster | https://old.example.com:6443 | Connection refused |

**Proceeding with 2 OpenShift clusters.** To include non-OpenShift clusters, say "include all clusters".
```

**Presentation rules**:
- Omit any section that has no entries (e.g., skip "Non-OpenShift" section if all contexts are OpenShift).
- If ALL contexts are OpenShift, simplify to: "All N contexts are verified OpenShift clusters."
- If ALL contexts are non-OpenShift, inform the user: "No OpenShift clusters found. To include non-OpenShift clusters, say 'include all clusters'."

**User override handling**:

If the user responds with "include all clusters", "include non-OpenShift", "report on all clusters", or any clear intent to include non-OpenShift contexts, add them back into the selected set. Unreachable clusters are always excluded.

If the user's **original prompt** (before the skill started) already contains phrases like "all clusters", "including non-OpenShift", or "all contexts", pre-select the override and present verification results as: "Including all clusters as requested."

**WAIT**: Do not proceed until user confirms cluster selection.

### Step 2: Collect Cluster Data

For each selected cluster, pass `context=<context-name>` to every tool call. Collect data using:

| Manifest Key | MCP Tool | Extra Parameters | Fallback |
|---|---|---|---|
| `nodes_top` | `nodes_top` | — | Set null if Metrics Server unavailable |
| `nodes_list` | `resources_list` | `apiVersion=v1`, `kind=Node` | — |
| `projects` | `projects_list` | — | OpenShift only; use `namespaces_list` for Kubernetes or if `projects_list` fails |
| `pods` | `pods_list` | — | — |

**Namespace/Project Logic**:
- **OpenShift clusters**: Use `projects_list` (OpenShift-specific)
- **Kubernetes clusters**: Use `namespaces_list` (standard Kubernetes API)
- **Fallback**: If `projects_list` fails on a cluster classified as OpenShift, fall back to `namespaces_list`

**Error policy**: Skip unreachable clusters. Set failed fields to `null` and append the error to the cluster's `errors` array. Never abort the entire report.

#### Persist MCP Output to Files

For each MCP tool call, **immediately save the output to a file** under `/tmp/cluster-report/`.
Files are created with default permissions restricted by the `chmod 700` on the parent directory.
This ensures data is available for the assembly pipeline regardless of output size.

**Naming convention**: `/tmp/cluster-report/<context-short>-<field>.txt`

Use a sanitized short name for the context (e.g., `prod-us`, `dev-eu`). Create the directory first:

```bash
mkdir -p /tmp/cluster-report && chmod 700 /tmp/cluster-report
```

**How to save**: After each MCP tool call, use Bash to write the output to disk. `$file` references
accept **both plain text and JSON files** — no special formatting is required.

If Claude Code auto-persisted the output to a file (shown as `persisted-output` in the tool result),
reference that file path directly.

#### Assemble Manifest

Write the manifest to `/tmp/cluster-report-manifest.json` with `$file` references to the saved files:

```json
{
  "generated_at": "2026-03-03T14:30:00Z",
  "clusters": {
    "<context-name>": {
      "context": "<context-name>",
      "server": "<server-url>",
      "cluster_type": "openshift",
      "openshift_version": "4.16.3",
      "nodes_top": {"$file": "/tmp/cluster-report/<ctx>-nodes_top.txt"} or null,
      "nodes_list": {"$file": "/tmp/cluster-report/<ctx>-nodes_list.txt"} or null,
      "projects": {"$file": "/tmp/cluster-report/<ctx>-projects.txt"} or null,
      "namespaces": {"$file": "/tmp/cluster-report/<ctx>-namespaces.txt"} or null,
      "pods": {"$file": "/tmp/cluster-report/<ctx>-pods.txt"} or null,
      "errors": ["<error messages for failed tools>"]
    }
  }
}
```

**Manifest fields from verification**:
- `cluster_type`: `"openshift"` or `"kubernetes"`. Determined during Step 1b verification.
- `openshift_version`: The OpenShift version string (e.g., `"4.16.3"`) or `null` for non-OpenShift clusters.

Fields may also be inlined as raw text strings or set to `null` for failed/unavailable data.

### Step 3: Aggregate Data

Run the assembly and aggregation pipeline:

```bash
python3 ocp-admin/scripts/cluster-report/assemble.py --aggregate < /tmp/cluster-report-manifest.json
```

If the pipeline exits with code 1, display the error JSON to the user and stop.

### Step 4: Render Report

Render the structured JSON output as markdown using this template:

```markdown
# Multi-Cluster Report

**Generated**: YYYY-MM-DDTHH:MM:SSZ
**Clusters**: <clusters_reported> clusters reporting

---

## Cluster Overview

| Cluster | Version | Nodes | CPU (used/total) | Memory (used/total) | GPUs | Projects | Pods (Running/Total) |
|---------|---------|-------|-------------------|---------------------|------|----------|---------------------|
| prod-us | OCP 4.16.3 | 12 | 48/96 cores (50%) | 192/384 GiB (50%) | 8    | 45       | 312/320             |
| dev-eu  | OCP 4.15.12 | 4  | 8/32 cores (25%)  | 32/128 GiB (25%)  | 0    | 12       | 87/92               |
| **Total** | | **16** | **56/128 cores (44%)** | **224/512 GiB (44%)** | **8** | **57** | **399/412** |

---

## Per-Cluster Details

### <cluster> (<server>) — OpenShift <version>

#### Node Resources

| Node | Role | CPU Used | CPU Total | Memory Used | Memory Total | GPUs |
|------|------|----------|-----------|-------------|--------------|------|
| node-1 | worker | 4 cores | 8 cores | 16 GiB | 32 GiB | 2 |

#### Pod Status

| Status | Count |
|--------|-------|
| Running | 312 |
| Pending | 5 |
| Succeeded | 0 |
| Failed | 3 |
| Unknown | 0 |

#### Top Namespaces (by pod count)

| Namespace | Pods | Running | Pending | Failed |
|-----------|------|---------|---------|--------|
| openshift-monitoring | 24 | 24 | 0 | 0 |

[Repeat for each cluster]

---

## Attention Required

[Render each item from the `attention` array]

### Operational Alerts

⚠️ **etcd**: If any cluster reports etcd fragmentation ratio > 4.0 or DB size approaching quota, see [etcd-maintenance.md](../../docs/etcd-maintenance.md) for defragmentation procedure.

⚠️ **PVC Capacity**: If any PVC usage exceeds 80% or `predict_linear` forecasts capacity exhaustion within 24h, see [pvc-capacity-planning.md](../../docs/pvc-capacity-planning.md) for expansion workflow.

⚠️ **Database Connections**: If PostgreSQL active connections exceed 80% of `max_connections`, see [database-connection-management.md](../../docs/database-connection-management.md) for saturation diagnosis and connection pooling.
```

### Step 5: Cleanup

After rendering the report, remove temporary files:

```bash
rm -rf /tmp/cluster-report /tmp/cluster-report-manifest.json
```

### Step 6: Offer Next Steps

```markdown
## Next Steps

Would you like to:
1. **Drill down** into a specific cluster or namespace
2. **Check alerts** — query Prometheus/Alertmanager for active alerts
3. **Refresh** — re-run the report with updated data
```

## Dependencies

### Required MCP Servers
- `openshift-administration` - Multi-cluster administration and reporting ([setup](../../README.md#environment-setup))

**Important**: This skill uses ONLY `openshift-administration` MCP server for querying existing cluster resources via KUBECONFIG. The cluster creation/inventory servers (`openshift-self-managed`, `openshift-ocm-managed`) are not needed for this skill as it operates on already-configured clusters.

### Required MCP Tools
- `configuration_contexts_list` (from openshift-administration) — list all kubeconfig contexts and server URLs
- `resources_get` (from openshift-administration) — get a single Kubernetes resource by apiVersion/kind/name
  - Parameters: `apiVersion`, `kind`, `name`, `context`
- `nodes_top` (from openshift-administration) — node CPU and memory usage from Metrics Server
  - Parameters: `context`
- `resources_list` (from openshift-administration) — list Kubernetes resources by apiVersion/kind
  - Parameters: `apiVersion`, `kind`, `context`
- `namespaces_list` (from openshift-administration) — list all namespaces in a cluster
  - Parameters: `context`
- `projects_list` (from openshift-administration) — list all OpenShift projects
  - Parameters: `context`
- `pods_list` (from openshift-administration) — list all pods across namespaces
  - Parameters: `context`

### Helper Scripts
- [`ocp-admin/scripts/cluster-report/assemble.py`](../../scripts/cluster-report/assemble.py)
- [`ocp-admin/scripts/cluster-report/aggregate.py`](../../scripts/cluster-report/aggregate.py)

### Related Skills
- `/cluster-inventory` - List and inspect individual clusters

### Reference Documentation
- [Credentials Management](../../docs/credentials-management.md) - KUBECONFIG setup and multi-cluster contexts
- [Multi-Cluster Auth](../../docs/multi-cluster-auth.md) - Service account token configuration for large deployments
- [etcd Maintenance](../../docs/etcd-maintenance.md) - Consult when etcd fragmentation ratio appears elevated in cluster metrics
- [PVC Capacity Planning](../../docs/pvc-capacity-planning.md) - Consult when PVC usage is high or approaching capacity
- [Database Connection Management](../../docs/database-connection-management.md) - Consult when PostgreSQL connection usage is high
- **[Documentation Index](../../docs/INDEX.md)** - Complete guide to all ocp-admin documentation (consult for topics not explicitly referenced above)

## Error Handling

| Error | Behavior |
|---|---|
| ClusterVersion probe succeeds | Classify as OpenShift, include by default |
| ClusterVersion probe 404/not found | Classify as non-OpenShift, exclude by default |
| ClusterVersion probe 403 Forbidden | Classify as OpenShift (unverified), include by default with version "unknown" |
| ClusterVersion probe timeout/unreachable | Classify as unreachable, always exclude |
| All contexts are non-OpenShift | Inform user, suggest "include all clusters" override |
| User overrides to include non-OpenShift | Proceed normally; `projects_list` may fail (use `namespaces_list` fallback) |
| Cluster unreachable | Skip, continue with remaining clusters |
| Metrics Server missing | Set `nodes_top` to null, show N/A for CPU/memory usage |
| Auth expired (401) | Skip cluster, suggest: "Re-authenticate cluster context (see credentials-management.md)" |
| No GPUs found | Display 0 (not an error) |
| Empty cluster | Report with all zeros (valid data) |

## Example Usage

### Multi-Cluster Report (Default: OpenShift Only)

**User**: "Show me a report across all clusters"

**Execution**:
1. Validate KUBECONFIG — OK
2. `configuration_contexts_list()` discovers: prod-us, dev-eu, dev-k8s
3. Verify each context with `resources_get(apiVersion="config.openshift.io/v1", kind="ClusterVersion", name="version", context=<ctx>)`
4. Results: prod-us (OCP 4.16.3), dev-eu (OCP 4.15.12), dev-k8s (non-OpenShift)
5. Present: "2 OpenShift clusters found. dev-k8s excluded (non-OpenShift). Include all?"
6. User confirms default selection
7. Collect data for prod-us and dev-eu only
8. Write manifest with `cluster_type` and `openshift_version` fields
9. Run `assemble.py --aggregate` pipeline
10. Render report with OpenShift version column
11. Flag attention items

### Multi-Cluster Report (Include All)

**User**: "Report on all my clusters including non-OpenShift"

**Execution**:
1. Validate KUBECONFIG — OK
2. `configuration_contexts_list()` discovers: prod-us, dev-eu, dev-k8s
3. Verify each context (same as above)
4. Results: prod-us (OCP 4.16.3), dev-eu (OCP 4.15.12), dev-k8s (non-OpenShift)
5. User's initial message indicates "include all" — present verification results and confirm
6. User confirms all clusters including dev-k8s
7. Collect data for all three clusters (`projects_list` fails on dev-k8s, falls back to `namespaces_list`)
8. Write manifest; dev-k8s has `cluster_type: "kubernetes"`, `openshift_version: null`
9. Run pipeline, render report
10. dev-k8s shown as "K8s" in version column

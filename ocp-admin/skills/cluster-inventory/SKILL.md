---
name: cluster-inventory
description: |
  List and inspect OpenShift clusters across self-managed (OCP, SNO) and managed service (ROSA, ARO, OSD) deployments.

  Returns cluster name, ID, version, status, platform, and creation date.

  Use when:
  - "List all clusters"
  - "Show cluster status"
  - "What clusters are available?"
  - "Get details of cluster [name]"
  - "Show cluster events for diagnostics"

  Read-only operations. Does NOT modify clusters.
license: Apache-2.0
model: inherit
color: cyan
allowed-tools: list_clusters get_cluster_hosts cluster_info cluster_events cluster_logs_download_url
metadata:
  mcp_servers:
    - openshift-self-managed
    - openshift-ocm-managed
  mcp_tools:
    - list_clusters
    - cluster_info
    - cluster_events
    - cluster_logs_download_url
  environment_vars:
    - OFFLINE_TOKEN
  destructive: false
  categories:
    - cluster-management
    - monitoring
---

# cluster-inventory

**MCP-First Approach**: This skill uses MCP tools from `openshift-self-managed` and `openshift-ocm-managed` servers. MCP tools have **absolute priority**.

**CLI Tools Policy**:
- ✅ **ALWAYS use MCP tools** when available
- ⚠️ **Last resort only**: CLI commands (`oc`, `kubectl`) may be attempted if no MCP alternative exists
- ⚠️ **Assume unavailable**: CLI tools are likely not installed in the execution environment

List and inspect OpenShift clusters across all types (OCP, SNO, ROSA, ARO, OSD).

## Prerequisites

**Required MCP Servers**: `openshift-self-managed`, `openshift-ocm-managed` ([setup guide](../../README.md))

**Required MCP Tools**:
- `list_clusters` (from both servers) - Lists clusters (auto-routes to correct API)
- `cluster_info` (from both servers) - Gets cluster details
- `cluster_events` (from openshift-self-managed only) - Gets events for self-managed clusters
- `cluster_logs_download_url` (from openshift-self-managed only) - Gets log download URL for diagnostics

**Environment Variables**: `OFFLINE_TOKEN` - Red Hat authentication token

**Verification Steps**:
1. Verify both MCP servers exist in `mcps.json`
2. Check `OFFLINE_TOKEN` is set: `test -n "$OFFLINE_TOKEN" && echo "✓" || echo "✗"`
3. If missing → Stop and report error with setup instructions

**Prerequisite Failure Handling**: If prerequisites fail, report the missing requirement and stop execution.

**Security**: Never display credential values.

## When to Use This Skill

Use when:
- "List all clusters" / "Show my clusters" / "What clusters do I have?"
- User wants cluster status or installation progress
- User needs detailed cluster info (version, config, hosts)
- User wants to inspect cluster events for troubleshooting

**Cluster Types**: OCP, SNO, ROSA, ARO, OSD (all supported)

Do NOT use when:
- Create cluster → Use `/cluster-creator` skill
- Modify cluster → Use cluster management skills
- Delete cluster → Use cluster deletion skill

---

## Filtering Capabilities

**Optional Filters** (apply when user requests):
- `cluster_type`: Filter by type - "all" (default), "self-managed", "managed", "rosa", "aro", "osd", "ocp", "sno"
- `status_filter`: Filter by status - "all" (default), "ready", "installed", "installing", "error", "pending-for-input"
- `name_search`: Partial match on cluster name (case-insensitive)

**Examples**:
- "List only ROSA clusters" → cluster_type="rosa"
- "Show clusters in error state" → status_filter="error"
- "Find clusters with 'prod' in name" → name_search="prod"

**Query Strategy**: ALWAYS query BOTH MCP servers by default unless user explicitly filters by cluster type.

**Performance Guidance**:
- **>20 clusters**: Display summary only, ask user before fetching detailed info for all
- **Parallel calls**: When fetching cluster_info for multiple clusters, limit to 5 concurrent calls
- **Large accounts**: Consider filtering by type or status to reduce output

## Output Formatting

**Summary Header** (always first):
```
📊 Found X cluster(s): Y installed ✅, Z installing ⏳, ...
```

**Single cluster (1)**: Detailed bullet list with all fields:
```
**Cluster: cluster-name**
- ID: full-uuid
- Status: ✅ ready
- Type: ROSA
- Version: 4.21.5
- Provider: AWS
- Region: us-east-1
```

**Multiple clusters (≥2)**: Table format with full cluster IDs:
```
| Name | ID | Status | Type | Version | Provider | Region |
|------|----|-----------------------|------|---------|----------|--------|
| name | full-uuid | ✅ ready | ROSA | 4.21.5 | AWS | us-east-1 |
```

**Status Icons**: ✅ ready/installed, ⏳ installing, ⚠️ pending-for-input, ❌ error

**Cluster Type Detection**:
- OCM clusters: Check `cloud_provider.id` → aws=ROSA, azure=ARO, gcp=OSD
- Self-managed: Check `platform` → none+single_node=SNO, else=OCP

**Sorting**: Sort by type (OCP→ROSA→ARO→OSD→SNO), then by creation date (newest first)

## Workflow

### Step 1: List All Clusters

**MCP Tools**: Call BOTH in parallel (unless user explicitly filters by type)
- `list_clusters` (from `openshift-self-managed`) → Gets OCP, SNO clusters
- `list_clusters` (from `openshift-ocm-managed`) → Gets ROSA, ARO, OSD clusters

**Parameters**: None (MCP tools have no parameters)

**Apply Filters** (post-processing after fetching results):
- If user specified `cluster_type`: Filter results to matching types
- If user specified `status_filter`: Filter results to matching statuses
- If user specified `name_search`: Filter results containing search string (case-insensitive)

**Expected Output**: Combined list with name, ID, version, status, platform, creation date

**Merge & Display**:
1. Merge results from both APIs
2. Detect cluster type (see Output Formatting section)
3. Sort by type (OCP→ROSA→ARO→OSD→SNO), then date (newest first)
4. Display with summary header + list/table format

**Dashboard presentation**: After receiving the `list_clusters` response, the Cluster Inventory dashboard opens automatically on UI-capable clients. On text-only clients, format the results as described in Output Formatting.

**Error Handling**:
- Both APIs fail → Verify OFFLINE_TOKEN and connectivity
- One API fails → Show partial results with note
- No clusters → Report "No clusters found"

### Step 2: Get Detailed Cluster Information (Optional)

Execute when user requests details for specific cluster.

**MCP Tool**: `cluster_info` (from correct server based on cluster source)
**Parameters**: `cluster_id` - UUID from list_clusters

**Server Selection**: Use cluster's `source` field from Step 1:
- `source: "ocm"` → Call via `openshift-ocm-managed`
- `source: "assisted-installer"` → Call via `openshift-self-managed`

**Expected Output**: Cluster details (ID, version, status, network config, hosts/nodes)

**Error Handling**:
- Cluster not found → Verify cluster exists
- Wrong MCP instance → Try other instance
- Permission denied → User lacks access

### Step 3: Get Diagnostics (Optional - Self-Managed Only)

**NOTE**: Only for OCP/SNO clusters. ROSA/ARO/OSD use cloud provider consoles for events and logs.

Execute when user requests events, troubleshoots errors, or needs installation logs.

#### 3a. Get Cluster Events

**MCP Tool**: `cluster_events` (from `openshift-self-managed`)
**Parameters**: `cluster_id` - UUID of self-managed cluster

**Expected Output**: Chronological events with timestamps, severity, messages

**When to use**:
- Diagnosing installation failures
- Understanding cluster state transitions
- Investigating validation errors

**Error Handling**:
- Cluster not found → Verify exists
- No events → Report no history yet
- Permission denied → User lacks access

#### 3b. Get Cluster Logs

**MCP Tool**: `cluster_logs_download_url` (from `openshift-self-managed`)
**Parameters**: `cluster_id` - UUID of self-managed cluster

**Expected Output**: Presigned download URL for logs bundle (installation, validation, host discovery, diagnostics)

**When to use**:
- Cluster status is "error"
- Events don't provide enough detail
- Deep troubleshooting needed

**Error Handling**:
- Cluster not found → Verify exists
- Logs unavailable → Too early in lifecycle
- URL generation fails → Cluster not ready

## Dependencies

### Required MCP Servers
- `openshift-self-managed` - Assisted Installer service for OCP/SNO ([setup](../../README.md))
- `openshift-ocm-managed` - OCM service for ROSA/ARO/OSD ([setup](../../README.md))

### Required MCP Tools
- `list_clusters` (from both servers) - Lists clusters and opens the Cluster Inventory dashboard on UI-capable clients. Falls back to text on others.
- `get_cluster_hosts` (from openshift-self-managed) - Opens the Cluster Setup dashboard for a specific cluster on UI-capable clients.
- `cluster_info` (from both servers) - Gets cluster details (auto-routes to correct API)
- `cluster_events` (from openshift-self-managed only) - Gets events for self-managed clusters
- `cluster_logs_download_url` (from openshift-self-managed only) - Gets log download URL

### Related Skills
- `/cluster-creator` - Create new clusters
- Future: cluster-installer, cluster-deletion

### Reference Documentation
- [troubleshooting.md](docs/troubleshooting.md) - Cluster status and error diagnosis
- [PVC Capacity Planning](docs/pvc-capacity-planning.md) - Consult when cluster storage details show high PVC usage or approaching capacity
- [Database Connection Management](docs/database-connection-management.md) - Consult when cluster workloads include PostgreSQL with high connection usage
- **[Documentation Index](docs/INDEX.md)** - Complete guide to all ocp-admin documentation (consult for topics not explicitly referenced above)

## Example Usage

### Example 1: List All Clusters

**User**: "List all my OpenShift clusters"

**Output**:
```
📊 Found 5 cluster(s): 3 ready ✅, 1 installing ⏳, 1 pending ⚠️

| Name | ID | Status | Type | Version | Provider | Region |
|------|----|--------|------|---------|----------|--------|
| prod-ocp | 762df996-acba-4a42-9fe9-edb0a8ec8bee | ⏳ installing | OCP | 4.21.0 | Baremetal | - |
| dev-ocp | a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5a6b7 | ✅ ready | OCP | 4.20.5 | vSphere | - |
| rosa-prod | 2o2gevtk4bohdu41ff4jps0dl8rrshb6 | ✅ ready | ROSA | 4.21.0 | AWS | us-east-1 |
| aro-dev | 20ekbvg1jkaqssc47mmc0irlvhf59c0p | ✅ ready | ARO | 4.20.0 | Azure | - |
| edge-01 | 8e5d3e45-77c6-440b-9cfa-9f88187535c6 | ⚠️ pending-for-input | SNO | 4.21.0 | Self-managed | - |
```

### Example 2: List Single Cluster

**User**: "Show me my edge cluster"

**Output**:
```
📊 Found 1 cluster

**Cluster: edge-01**
- ID: 8e5d3e45-77c6-440b-9cfa-9f88187535c6
- Status: ⚠️ pending-for-input
- Type: SNO
- Version: 4.21.0
- Provider: Self-managed
- Region: -
```

### Example 3: Filter by Type

**User**: "List only ROSA clusters"

**Output**:
```
📊 Found 2 ROSA cluster(s): 2 ready ✅

| Name | ID | Status | Type | Version | Provider | Region |
|------|----|--------|------|---------|----------|--------|
| rosa-prod | 2o2gevtk4bohdu41ff4jps0dl8rrshb6 | ✅ ready | ROSA | 4.21.0 | AWS | us-east-1 |
| rosa-dev | 2nm4er0dk4a8lcs23foq6ug50v4onsvs | ✅ ready | ROSA | 4.20.8 | AWS | us-west-2 |
```

### Example 4: Get Cluster Details

**User**: "Show me details for prod-ocp"

**Output**:
```
**Cluster Details: prod-ocp**
- ID: 762df996-acba-4a42-9fe9-edb0a8ec8bee
- Version: 4.21.0
- Status: Installing (45% complete)
- Platform: Baremetal
- Hosts: 3/3 ready
- Network: API VIP configured, Ingress VIP configured
```

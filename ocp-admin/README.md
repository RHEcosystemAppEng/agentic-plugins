# Agentic skill pack for Red Hat OpenShift administration

Administration and management tools for OpenShift Container Platform including cluster lifecycle management, multi-cluster operations, workload orchestration, and security policies

**Persona**: OpenShift Administrator
**Marketplaces**: Claude Code, Cursor

---

## Overview

The ocp-admin collection provides specialized tools for managing OpenShift clusters throughout their lifecycle:

- **Complete cluster lifecycle**: Creation, configuration, monitoring, and operations
- **Multi-cluster management**: Consolidated reporting across multiple clusters
- **Assisted Installer integration**: Automated cluster deployment with validation
- **Network security**: Zero Trust NetworkPolicy design with live cluster verification
- **Comprehensive documentation**: 17 reference documents covering all aspects of OpenShift administration

---

## Quick Start

### Prerequisites

- Claude Code CLI or IDE extension
- **For cluster creation**:
  - Red Hat account with access to cloud.redhat.com
  - Offline token from https://cloud.redhat.com/openshift/token
  - Python 3.10+ with `uv` installed
  - Assisted Service MCP server (see setup below)
- **For cluster operations**:
  - OpenShift cluster access via `KUBECONFIG`
  - For multi-cluster reports, a kubeconfig with multiple contexts
- **For security validation**:
  - `python3` + `requests` — helper scripts for API calls
  - `regctl` — remote image metadata inspection ([install guide](https://github.com/regclient/regclient))
  - `cosign` — SBOM extraction from container attestations ([install guide](https://github.com/sigstore/cosign))
  - `syft` — (optional) fallback SBOM generation when attestations are unavailable ([install guide](https://github.com/anchore/syft))
  - `oc` + `podman` — CoreOS RPM extraction (coreos-cve-validator only)
  - Registry authentication: `regctl registry login registry.redhat.io` for Red Hat image access

### Installation (Lola)

Install the pack with [Lola](https://github.com/LobsterTrap/lola):

```bash
lola market add rh-agentic-plugins https://raw.githubusercontent.com/RHEcosystemAppEng/agentic-catalog/main/marketplace/rh-agentic-collection.yml
lola install -f ocp-admin
```

Verify installation:

```bash
lola list
# Optional: lola list -a claude-code
```

---

## Environment Setup

### Important: MCP Server Configuration

**⚠️ CRITICAL**: The `mcps.json` file in this plugin is for **reference only**. MCP servers are **NOT automatically installed** by Claude Code plugins.

**You must manually configure MCP servers** in your Claude Code settings using **one of these methods**:

#### Option A: Using Claude Code `/mcp` Command (Recommended)

1. Open Claude Code
2. Type `/mcp` to open MCP Server Manager
3. Click "Add Server" for each server below
4. Copy the configuration from `mcps.json`

#### Option B: Manual Settings Configuration

Add the MCP servers to your settings file:

**Linux/macOS**: `~/.claude/settings.json`
**Windows**: `%APPDATA%\.claude\settings.json`

```json
{
  "mcpServers": {
    "openshift-self-managed": {
      // ... copy from mcps.json
    },
    "openshift-ocm-managed": {
      // ... copy from mcps.json
    }
  }
}
```

---

### 1. MCP Servers for Cluster Management

This plugin requires **TWO MCP servers** for complete functionality:

| MCP Server | Purpose | Cluster Types | Required For |
|-----------|---------|---------------|--------------|
| `openshift-self-managed` | Assisted Installer API | OCP, SNO | cluster-creator, cluster-inventory |
| `openshift-ocm-managed` | OCM API | ROSA, ARO, OSD | cluster-inventory |

Both servers use the same container image but with different configurations.

---

### 2. Get Your Red Hat Offline Token

**Required for both MCP servers**:

1. Visit https://cloud.redhat.com/openshift/token
2. Log in with your Red Hat account
3. Click **"Load token"** → **"Copy to clipboard"**
4. Set environment variable:

```bash
export OFFLINE_TOKEN="your-token-here"

# Verify
test -n "$OFFLINE_TOKEN" && echo "✓ Set" || echo "✗ Missing"

# Make persistent (add to shell profile)
echo 'export OFFLINE_TOKEN="your-token-here"' >> ~/.bashrc
source ~/.bashrc
```

**Note**: Token is long-lived (30 days), auto-refreshes on use.

---

### 3. Configure MCP Servers in Claude Code

Copy the **entire configuration** from `ocp-admin/mcps.json` to your Claude Code settings:

**From**: `ocp-admin/mcps.json` (reference)
**To**: `~/.claude/settings.json` (active configuration)

**Full Configuration** (copy this to your settings):

```json
{
  "mcpServers": {
    "openshift-self-managed": {
      "command": "bash",
      "args": [
        "-c",
        "U=(); \
         [ \"$(uname -s)\" = Linux ] && U=(--userns=keep-id:uid=1001,gid=0); \
         exec podman run \"${U[@]}\" \
           --rm \
           -i \
           --network=host \
           -e OFFLINE_TOKEN=\"${OFFLINE_TOKEN}\" \
           -e TRANSPORT=stdio \
           -e INVENTORY_URL=\"${INVENTORY_URL:-https://api.openshift.com/api/assisted-install/v2}\" \
           -e PULL_SECRET_URL=\"${PULL_SECRET_URL:-https://api.openshift.com/api/accounts_mgmt/v1/access_token}\" \
           -e OCM_URL=\"${OCM_URL:-https://api.openshift.com/api/clusters_mgmt/v1}\" \
           quay.io/ecosystem-appeng/assisted-service-mcp@sha256:e3e84602c6ef2882dc0737e7ad0fafd16d39887dce9f4fb399c470b11158f486"
      ],
      "env": {
        "OFFLINE_TOKEN": "${OFFLINE_TOKEN}",
        "INVENTORY_URL": "${INVENTORY_URL}",
        "PULL_SECRET_URL": "${PULL_SECRET_URL}",
        "OCM_URL": "${OCM_URL}"
      },
      "description": "Red Hat Assisted Installer MCP server for self-managed clusters (OCP, SNO)"
    },
    "openshift-ocm-managed": {
      "command": "bash",
      "args": [
        "-c",
        "U=(); \
         [ \"$(uname -s)\" = Linux ] && U=(--userns=keep-id:uid=1001,gid=0); \
         exec podman run \"${U[@]}\" \
           --rm \
           -i \
           --network=host \
           -e OFFLINE_TOKEN=\"${OFFLINE_TOKEN}\" \
           -e TRANSPORT=stdio \
           -e INVENTORY_URL=\"${INVENTORY_URL:-https://api.openshift.com/api/assisted-install/v2}\" \
           -e PULL_SECRET_URL=\"${PULL_SECRET_URL:-https://api.openshift.com/api/accounts_mgmt/v1/access_token}\" \
           -e OCM_URL=\"${OCM_URL:-https://api.openshift.com/api/clusters_mgmt/v1}\" \
           quay.io/ecosystem-appeng/assisted-service-mcp@sha256:e3e84602c6ef2882dc0737e7ad0fafd16d39887dce9f4fb399c470b11158f486"
      ],
      "env": {
        "OFFLINE_TOKEN": "${OFFLINE_TOKEN}",
        "OCM_URL": "${OCM_URL}"
      },
      "description": "Red Hat OCM MCP server for managed service clusters (ROSA, ARO, OSD)"
    }
  }
}
```

**Verify Podman is installed**:

```bash
# Check Podman
podman --version

# Test container pull
podman pull quay.io/ecosystem-appeng/assisted-service-mcp@sha256:e3e84602c6ef2882dc0737e7ad0fafd16d39887dce9f4fb399c470b11158f486
```

**Test the MCP servers**:

```bash
# Restart Claude Code after configuration
# Then try:
# "List all my OpenShift clusters"
```

### 2. OpenShift MCP Server (for cluster operations)

The `cluster-report` skill uses the [OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server) container image from `quay.io/redhat-user-workloads/crt-nshift-lightspeed-tenant/openshift-mcp-server`, pinned by SHA256 digest for supply chain security. No local build is required -- the image is pulled automatically on first use.

To verify the image integrity:
```bash
podman inspect --format='{{.Digest}}' quay.io/redhat-user-workloads/crt-nshift-lightspeed-tenant/openshift-mcp-server@sha256:2f52c860f91ab3c8a5129b727bdef0d620e733013f073b10355866c45eafd053
```

**Configure cluster access**:

```bash
# Set KUBECONFIG to your cluster
export KUBECONFIG="/path/to/your/kubeconfig"

# Verify access
oc get nodes
# or
kubectl get nodes
```

---

## Skills

### 1. **cluster-creator** - End-to-End Cluster Deployment

Create OpenShift clusters using the Red Hat Assisted Installer with full workflow automation.

**Use when**:
- "Create a new OpenShift cluster"
- "Install OpenShift on my servers"
- "Set up a single-node cluster for edge deployment"
- "Deploy a production HA cluster"

**MCP Server**: `openshift-installer` (Assisted Service)

**What it does**:
- Interactive cluster configuration gathering
- Support for SNO and HA deployments
- Platform-specific setup (baremetal, vsphere, oci, nutanix)
- VIP configuration for HA clusters
- Static networking with NMState
- ISO generation and host discovery
- Role assignment and validation
- Installation monitoring
- Credential retrieval and secure storage
- **18-step guided workflow** with human-in-the-loop at critical points

**Available Tools** (11 total):
- `list_versions` - List available OpenShift versions
- `create_cluster` - Create cluster definition
- `cluster_info` - Get cluster details and status
- `set_cluster_vips` - Configure API and Ingress VIPs
- `set_host_role` - Assign master/worker roles to hosts
- `cluster_iso_download_url` - Get discovery ISO URL
- `install_cluster` - Start cluster installation
- `cluster_credentials_download_url` - Download kubeconfig and credentials
- `generate_nmstate_yaml` - Generate NMState network configuration
- `validate_nmstate_yaml` - Validate network configuration
- `alter_static_network_config_nmstate_for_host` - Apply static networking to hosts

**Documentation**:
- [Input Validation Guide](skills/cluster-creator/docs/input-validation-guide.md) - Parameter requirements
- [Providers](skills/cluster-creator/docs/providers.md) - Infrastructure providers (baremetal, vsphere, oci, nutanix)
- [Platforms](skills/cluster-creator/docs/platforms.md) - OpenShift types (SNO, OCP, ROSA, ARO, OSD)
- [Networking](skills/cluster-creator/docs/networking.md) - Network configuration, VIPs, CIDR planning
- [Static Networking Guide](skills/cluster-creator/docs/static-networking-guide.md) - NMState configuration
- [Host Requirements](skills/cluster-creator/docs/host-requirements.md) - Hardware specifications
- [Examples](skills/cluster-creator/docs/examples.md) - 10 real-world configurations
- [Troubleshooting](skills/cluster-creator/docs/troubleshooting.md) - Common errors and solutions
- [INDEX.md](skills/cluster-creator/docs/INDEX.md) - Complete documentation navigation

### 2. **cluster-inventory** - Cluster Discovery and Status

List and inspect ALL OpenShift cluster types with comprehensive status information.

**Use when**:
- "List my OpenShift clusters"
- "Show cluster status"
- "Get details about cluster [name]"
- "What clusters are installing?"
- "Show all my clusters" (self-managed and managed services)

**MCP Server**: `openshift-installer` (Dual API: Assisted Service + OCM)

**What it does**:
- **Dual API Query**: Queries both Assisted Installer and OCM APIs
- Lists self-managed clusters (OCP, SNO) from Assisted Installer
- Lists managed service clusters (ROSA, ARO, OSD) from OCM
- Merges and normalizes results into unified view
- Shows cluster status and installation progress
- Provides detailed cluster events and validation errors (Assisted Installer only)
- Read-only operations (safe for continuous monitoring)

**Supported Cluster Types**:
- **Self-Managed**: OCP (OpenShift Container Platform), SNO (Single-Node OpenShift)
- **Managed Services**: ROSA (Red Hat OpenShift Service on AWS), ARO (Azure Red Hat OpenShift), OSD (OpenShift Dedicated)

### 3. **cluster-report** - Multi-Cluster Health Reporting

Generate consolidated health reports across multiple OpenShift clusters.

**Use when**:
- "Generate a health report for all my clusters"
- "Show resource usage across clusters"
- "List pods with issues in the fleet"
- "What's the GPU allocation across clusters?"

**MCP Server**: `openshift` (OpenShift MCP Server)

**What it does**:
- Aggregates metrics from multiple clusters
- Reports CPU, memory, GPU usage
- Identifies failed pods and attention items
- Provides per-cluster and fleet-wide summaries
- Supports 10–100+ clusters via service account tokens

**Helper Scripts**:
- `assemble.py` - Resolves file references and loads MCP output
- `aggregate.py` - Computes metrics and identifies issues

### 4. **container-cve-validator** - Container Image CVE Validation

Validate CVEs against Red Hat container images using official SBOM attestations, Red Hat VEX data, and CVE metadata from MITRE/OSV.dev.

**Use when**:
- "Is CVE-2024-45490 a real issue in my UBI9 image?"
- "Validate this CVE against registry.redhat.io/ubi9/ubi:latest"
- "My scanner flagged RHSA-2026:3337 on our image. Is this relevant?"
- "Batch scan these CVEs from a CSV file"

**What it does**:
- Extracts official SBOM attestations from container images
- Checks Red Hat VEX/CSAF data for product-specific vulnerability status
- Performs version comparison (RPM EVR, Go semver, PyPI, npm)
- Scans for newer patched images in the same or newer product stream
- Detects VEX data gaps and recommends reporting to secalert@redhat.com
- Supports CVE IDs, RHSA advisory IDs, and batch CSV input
- Output formats: markdown (full/summary), JSON, CSV

**Helper Scripts** (in `scripts/security-validation/`):
- `validate_input.py` - Validates CVE IDs and image references
- `inspect_image.py` - Extracts container image metadata via regctl
- `fetch_cve_metadata.py` - Queries MITRE, OSV.dev, and Go vuln DB
- `download_sbom.py` - Fetches SBOM attestations from registry
- `fetch_redhat_vex.py` - Retrieves Red Hat VEX security advisories
- `scan_newer_images.py` - Finds patched image releases

### 5. **coreos-cve-validator** - CoreOS CVE Validation

Validate CVEs against Red Hat Enterprise Linux CoreOS (RHCOS) in specific OCP releases.

**Use when**:
- "Does CVE-2025-61726 affect CoreOS in OCP 4.20.16?"
- "Check this CVE against RHCOS in our OCP cluster"
- "Validate RHSA against CoreOS"

**What it does**:
- Extracts full RPM package list from CoreOS images via `oc adm release info` + `podman`
- Classifies RPMs by source (RHEL repository, OCP repository, Fast Datapath)
- Validates against VEX data with RHEL EUS stream awareness (not latest RHEL)
- Detects RHCOS VEX discrepancies (RPM patched in RHEL but CoreOS not rebuilt)
- Handles both legacy (OCP < 4.19) and RHEL-based (OCP >= 4.19) CoreOS versioning

**Helper Scripts** (in `scripts/security-validation/`):
- `validate_input.py` - Validates CVE IDs and OCP versions
- `fetch_cve_metadata.py` - Queries CVE data sources
- `fetch_coreos_metadata.py` - Extracts CoreOS RPM list (supports `--authfile` for pull secret)
- `fetch_redhat_vex.py` - Retrieves VEX advisories

### 6. **cve-recon** - CVE Reconnaissance

Query MITRE, OSV.dev, and Go vulnerability database to produce a structured report for a given CVE.

**Use when**:
- "What packages does CVE-2024-45490 affect?"
- "Look up CVE details and version ranges"
- "Get ecosystem and severity info for this CVE"

**What it does**:
- Queries MITRE CVE API, OSV.dev, and Go vulnerability database in a single call
- Reports affected packages with ecosystem, version ranges, and CVSS scores
- Provides cross-references (GO-*, GHSA-*) and deduplicated reference URLs
- Output formats: markdown, JSON, CSV

### 7. **image-inspect** - Container Image Metadata Inspection

Fetch container image labels, validate registry ownership, resolve tag/digest via SBOM, and report the SBOM artifact reference.

**Use when**:
- "Inspect this container image"
- "What SBOM does this image have?"
- "Check metadata for registry.redhat.io/ubi9/ubi:latest"
- "Is this image from Red Hat?"

**What it does**:
- Extracts image labels (CPE, name, vendor, maintainer, build timestamp)
- Validates registry ownership (official Red Hat vs. mirrored)
- Resolves tag/digest from SBOM `pkg:oci/` PURL
- Reports SBOM artifact OCI reference and fetch command
- Output formats: markdown, JSON, CSV

### 8. **network-policy-architect** - Zero Trust NetworkPolicy Design

Design and validate Kubernetes NetworkPolicies following Zero Trust principles (NIST SP 800-207). Two-tier analysis — architecture review then live cluster verification — produces a verified implementation plan with dry-run results.

**Use when**:
- "Create NetworkPolicies for my namespace"
- "Audit network isolation for this workload"
- "Design network segmentation for a new application"
- "Verify NetworkPolicies implement Zero Trust"

**MCP Server**: `openshift-administration` (OpenShift MCP Server)

**What it does**:
- **Tier 1 (Architecture Analysis)**: Maps all pod types, services, communication flows, and special networking cases (hostNetwork, OVN-K, DNS on 5353) from source code and manifests
- **Tier 2 (Live Cluster Verification)**: Validates draft rules against a running cluster using MCP tools — verifies pod labels, services, existing policies, and performs dry-run policy application with health checks
- Produces implementation plan with default-deny, per-pod rules, exceptions, dry-run results, and NIST SP 800-207 alignment
- Requires human confirmation before applying or removing dry-run policies

---

## Multi-Cluster Authentication

For running `cluster-report` across many clusters (10–100+), use service account tokens instead of interactive `oc login`. This avoids repeated browser-based OAuth sessions and produces non-expiring tokens.

| Script / Manifest | Purpose |
|-------------------|---------|
| [`build-kubeconfig.py`](scripts/cluster-report/build-kubeconfig.py) | Builds merged kubeconfig from SA tokens (`setup` + `build` subcommands) |
| [`cluster-reporter-rbac.yaml`](scripts/cluster-report/cluster-reporter-rbac.yaml) | Read-only RBAC resources (ClusterRole, ClusterRoleBinding) |

> **Required permissions**: The RBAC setup creates cluster-scoped resources, so the user running `setup` needs `cluster-admin` privileges. This is a one-time step per cluster. If RBAC has already been applied, use `--skip-rbac`.

**Quick start**:

```bash
# 1. One-time setup (requires cluster-admin): apply RBAC and extract tokens
python3 ocp-admin/scripts/cluster-report/build-kubeconfig.py setup --all-contexts

# If RBAC is already configured, skip the apply step
python3 ocp-admin/scripts/cluster-report/build-kubeconfig.py setup --all-contexts --skip-rbac

# 2. Build merged kubeconfig from saved tokens
python3 ocp-admin/scripts/cluster-report/build-kubeconfig.py \
  build --clusters ~/.ocp-clusters/clusters.json --verify

# 3. Export and run
export KUBECONFIG=/tmp/cluster-report-kubeconfig
# In Claude Code: /cluster-report
```

See [skills/cluster-report/docs/multi-cluster-auth.md](skills/cluster-report/docs/multi-cluster-auth.md) for the full setup guide, token rotation, and troubleshooting.

---

## MCP Server Integration

The pack integrates with two MCP servers for comprehensive cluster management:

### **openshift-installer** - Assisted Service MCP Server

Provides access to Red Hat Assisted Installer API for cluster lifecycle operations.

**Repository**: https://github.com/openshift-assisted/assisted-service-mcp

**Technology**: Python with `uv` runtime

**Available Tools**: 15+ tools across categories:
- **Cluster Management**: list_clusters, cluster_info, create_cluster, install_cluster, set_cluster_vips
- **Host Management**: set_host_role
- **Networking**: generate_nmstate_yaml, validate_nmstate_yaml, alter_static_network_config_nmstate_for_host
- **Downloads**: cluster_iso_download_url, cluster_credentials_download_url
- **Events**: cluster_events, host_events
- **Versions**: list_versions, list_operator_bundles
- **Operators**: add_operator_bundle_to_cluster

**Configuration** (in `mcps.json`):
```json
{
  "mcpServers": {
    "openshift-installer": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/assisted-service-mcp",
        "run",
        "mcp",
        "run",
        "/path/to/assisted-service-mcp/assisted_service_mcp/src/main.py"
      ],
      "env": {
        "OFFLINE_TOKEN": "${OFFLINE_TOKEN}"
      },
      "description": "Red Hat Assisted Installer MCP server for cluster creation and management",
      "security": {
        "credentials": "env-only"
      }
    }
  }
}
```

**Key Configuration Notes**:
- Uses `uv` for Python environment management (faster than pip/virtualenv)
- Requires `OFFLINE_TOKEN` from https://cloud.redhat.com/openshift/token
- Communicates with Red Hat Hybrid Cloud Console APIs
- No container required (pure Python STDIO transport)

### **openshift** - OpenShift MCP Server

Provides access to Kubernetes/OpenShift cluster operations for multi-cluster management.

**Repository**: https://github.com/openshift/openshift-mcp-server

**Technology**: Go binary in container

**Enabled Toolsets**: `core` and `config` (via `--toolsets core,config`)

**Available Tools**:
- **Resources**: resources_list, resources_get, resources_create_or_update, resources_delete
- **Pods**: pods_list, pods_get, pods_log, pods_exec, pods_top
- **Nodes**: nodes_top, nodes_log, nodes_stats_summary
- **Namespaces**: namespaces_list, projects_list
- **Events**: events_list

**Configuration** (in `mcps.json`):
```json
{
  "mcpServers": {
    "openshift": {
      "command": "bash",
      "args": [
        "-c",
        "U=(); [ \"$(uname -s)\" = Linux ] && U=(--userns=keep-id:uid=65532,gid=65532); exec podman run \"${U[@]}\" --rm -i --network=host -v \"${KUBECONFIG}:/kubeconfig:ro,Z\" --entrypoint /app/kubernetes-mcp-server quay.io/ecosystem-appeng/openshift-mcp-server:latest --kubeconfig /kubeconfig --read-only --toolsets core,config"
      ],
      "env": {
        "KUBECONFIG": "${KUBECONFIG}"
      },
      "description": "Red Hat OpenShift MCP server for multi-cluster administration and reporting",
      "security": {
        "isolation": "container",
        "network": "local",
        "credentials": "env-only"
      }
    }
  }
}
```

**Key Configuration Notes**:
- Uses Podman to run container image `quay.io/ecosystem-appeng/openshift-mcp-server:latest`
- `--userns=keep-id:uid=65532,gid=65532` - Rootless container security (Linux only)
- Mounts `KUBECONFIG` as read-only with `,Z` for SELinux labeling
- `--read-only` - Enforces read-only operations (safe for reporting)
- `--toolsets core,config` - Enables Kubernetes core and config operations
- `--network=host` - Required for local/remote cluster access

> **Container UID mapping**: On Linux, the MCP server automatically adds `--userns=keep-id:uid=65532,gid=65532` to map the host user to the container's non-root UID (65532), allowing the container to read `chmod 600` files like `KUBECONFIG` without weakening file permissions. On macOS the flag is omitted automatically since Podman runs inside a VM where `--userns` can cause startup failures.

---

## Sample Workflows

### Workflow 1: Create Single-Node Cluster

```
User: "Create a single-node OpenShift cluster for edge deployment"
→ cluster-creator skill guides through:
  - Cluster name, domain, version selection
  - SSH key configuration
  - ISO generation
  - Host discovery and validation
  - Installation monitoring
  - Credential download

Result: Fully operational SNO cluster in ~45 minutes
```

### Workflow 2: Create HA Cluster with Static IPs

```
User: "Create a 3-master, 2-worker cluster on bare metal with static IPs"
→ cluster-creator skill configures:
  - HA cluster type
  - VIP addresses (API + Ingress)
  - Static networking (NMState YAML per host)
  - Host role assignment
  - Installation with validation

Result: Production HA cluster with static networking
```

### Workflow 3: Multi-Cluster Health Report

```
User: "Generate a health report for all my clusters"
→ cluster-report skill:
  - Connects to all clusters in KUBECONFIG
  - Gathers metrics (CPU, memory, GPU, pods)
  - Identifies issues (high utilization, failed pods)
  - Produces consolidated report

Result: Fleet-wide health summary with attention items
```

### Workflow 4: Container CVE Validation

```
User: "Is CVE-2024-45490 a real issue in registry.redhat.io/ubi9/ubi:latest?"
→ container-cve-validator skill:
  - Extracts SBOM from image attestations
  - Queries MITRE and OSV.dev for affected packages/versions
  - Checks Red Hat VEX for product-specific status
  - Scans for newer patched images if a fix exists

Result: True/false positive determination with remediation guidance
```

### Workflow 5: CoreOS Vulnerability Check

```
User: "Does CVE-2025-61726 affect CoreOS in OCP 4.20.16?"
→ coreos-cve-validator skill:
  - Extracts RPM list from CoreOS image
  - Matches affected package and checks version
  - Validates against VEX under OCP and RHEL EUS CPEs
  - Reports whether CoreOS has been rebuilt with the fix

Result: CoreOS-specific vulnerability assessment with RHEL EUS stream awareness
```

### Workflow 6: Network Policy Design for Zero Trust

```
User: "Create NetworkPolicies for the qtodo namespace following Zero Trust"
→ network-policy-architect skill:
  - Tier 1: Analyzes source code and Helm charts for pod types, services, flows
  - Drafts per-pod ingress/egress rules with justifications
  - Tier 2: Verifies pod labels, services, existing policies via MCP
  - Applies policies as dry-run, verifies health, cleans up
  - Produces implementation plan with NIST SP 800-207 alignment

Result: Verified NetworkPolicy set with default-deny and per-pod rules
```

### Workflow 7: Check Cluster Installation Progress

```
User: "What's the status of my cluster installation?"
→ cluster-inventory skill:
  - Lists all clusters
  - Shows installation progress
  - Displays recent events
  - Reports validation errors (if any)

Result: Real-time installation status without leaving Claude
```

---

## Documentation

The pack includes 17 comprehensive reference documents covering all aspects of OpenShift administration:

### Installation & Planning
- [Input Validation Guide](skills/cluster-creator/docs/input-validation-guide.md) - Parameter validation rules
- [Providers](skills/cluster-creator/docs/providers.md) - Infrastructure providers (baremetal, vsphere, oci, nutanix)
- [Platforms](skills/cluster-creator/docs/platforms.md) - OpenShift platform types (SNO, OCP, ROSA, ARO, OSD)
- [Host Requirements](skills/cluster-creator/docs/host-requirements.md) - Hardware specifications
- [Networking](skills/cluster-creator/docs/networking.md) - Network configuration, VIPs, CIDR planning, Egress IP, Multus, SR-IOV, Dual-Stack
- [Static Networking Guide](skills/cluster-creator/docs/static-networking-guide.md) - NMState configuration (Simple/Advanced/Manual modes)
- [Storage](skills/cluster-creator/docs/storage.md) - Storage options, CSI drivers, ODF
- [Examples](skills/cluster-creator/docs/examples.md) - 10 real-world cluster configurations

### Post-Installation
- [Credentials Management](skills/cluster-creator/docs/credentials-management.md) - Authentication, OAuth, RBAC, identity providers
- [Multi-Cluster Authentication](skills/cluster-report/docs/multi-cluster-auth.md) - Service account tokens, kubeconfig merging
- [Day-2 Operations](skills/cluster-creator/docs/day-2-operations.md) - Monitoring, logging, updates, scaling, maintenance
- [Certificate Management](skills/cluster-creator/docs/certificate-management.md) - Certificate lifecycle and rotation
- [Backup and Restore](skills/cluster-creator/docs/backup-restore.md) - etcd backup/restore procedures

### Reference & Troubleshooting
- [Quick Reference](skills/cluster-creator/docs/quick-reference.md) - Common `oc` commands and scenarios
- [Troubleshooting](skills/cluster-creator/docs/troubleshooting.md) - Common errors and resolutions
- [INDEX.md](skills/cluster-creator/docs/INDEX.md) - Complete documentation navigation

**All documentation**:
- Derived from official Red Hat sources
- Optimized for AI context usage (concise)
- Production-ready examples (no toy code)
- Comprehensive cross-references
- Validated against OpenShift 4.18

---

## Troubleshooting

### MCP Server Won't Start (openshift-installer)

**Problem**: Server fails to connect or times out

**Solutions**:
1. Verify `uv` is installed: `uv --version`
2. Check OFFLINE_TOKEN is set: `echo "OFFLINE_TOKEN is ${OFFLINE_TOKEN:+set}"`
3. Verify path in `mcps.json` points to your local `assisted-service-mcp` clone
4. Test manually:
   ```bash
   cd /path/to/assisted-service-mcp
   OFFLINE_TOKEN="your-token" uv run assisted_service_mcp.src.main
   ```
5. Check network connectivity to cloud.redhat.com

### MCP Server Won't Start (openshift)

**Problem**: Container fails to start or can't access cluster

**Solutions**:
1. Verify KUBECONFIG is set: `echo $KUBECONFIG`
2. Test cluster access: `oc get nodes` or `kubectl get nodes`
3. Check container image exists: `podman images | grep openshift-mcp-server`
4. Verify SELinux context on kubeconfig file (Linux): `ls -Z $KUBECONFIG`
5. Test container manually:
   ```bash
   podman run --rm -i --network=host \
     -v "${KUBECONFIG}:/kubeconfig:ro,Z" \
     quay.io/ecosystem-appeng/openshift-mcp-server:latest \
     --kubeconfig /kubeconfig --read-only --toolsets core,config
   ```

### Cluster Creation Fails

**Problem**: Cluster stays in "insufficient" or validation error state

**Solutions**:
1. Check host requirements match cluster type (SNO vs HA)
2. Verify VIPs are in same subnet as nodes
3. Review cluster events: Use `cluster-inventory` skill
4. Check troubleshooting guide: [skills/cluster-creator/docs/troubleshooting.md](skills/cluster-creator/docs/troubleshooting.md)
5. Verify network connectivity between hosts

### Skills Not Triggering

**Problem**: Skills don't activate on expected queries

**Solutions**:
1. Verify module is installed: `lola list`
2. Reload Claude Code to refresh plugins
3. Check skill descriptions match query intent
4. Use explicit phrasing from skill examples

---

## Architecture Reference

### Directory Structure

```
ocp-admin/
├── README.md                    # This file
├── mcps.json                    # MCP server configurations
├── docs/                        # Comprehensive reference documentation (17 files)
│   ├── INDEX.md                 # Master documentation navigation
│   ├── input-validation-guide.md
│   ├── providers.md
│   ├── platforms.md
│   ├── networking.md
│   ├── static-networking-guide.md
│   ├── host-requirements.md
│   ├── storage.md
│   ├── examples.md
│   ├── credentials-management.md
│   ├── multi-cluster-auth.md
│   ├── day-2-operations.md
│   ├── certificate-management.md
│   ├── backup-restore.md
│   ├── quick-reference.md
│   └── troubleshooting.md
├── skills/
│   ├── cluster-creator/SKILL.md      # End-to-end cluster deployment
│   ├── cluster-inventory/SKILL.md    # Cluster discovery and status
│   ├── cluster-report/SKILL.md       # Multi-cluster health reporting
│   ├── container-cve-validator/      # Container image CVE validation
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── 01-vex-validation-procedure.md
│   │       └── 02-report-template.md
│   ├── coreos-cve-validator/SKILL.md # CoreOS CVE validation
│   ├── cve-recon/SKILL.md            # CVE reconnaissance
│   ├── image-inspect/SKILL.md        # Container image metadata inspection
│   └── network-policy-architect/SKILL.md  # Zero Trust NetworkPolicy design
└── scripts/
    ├── cluster-report/
    │   ├── build-kubeconfig.py       # Multi-cluster authentication
    │   ├── cluster-reporter-rbac.yaml
    │   ├── assemble.py               # MCP output assembly
    │   └── aggregate.py              # Metrics aggregation
    └── security-validation/          # CVE validation helper scripts
        ├── validate_input.py         # Input validation
        ├── inspect_image.py          # Image metadata extraction
        ├── fetch_cve_metadata.py     # MITRE/OSV.dev/Go vuln DB queries
        ├── download_sbom.py          # SBOM attestation extraction
        ├── generate_sbom_syft.py     # Fallback SBOM generation
        ├── fetch_coreos_metadata.py  # CoreOS RPM extraction
        ├── fetch_redhat_vex.py       # Red Hat VEX data fetching
        ├── fetch_rhsa_advisory.py    # RHSA advisory resolution
        └── scan_newer_images.py      # Patched image scanning
```

*Optional:* `.claude-plugin/plugin.json` — only if publishing via Claude Code’s plugin format; not required for [Lola](https://github.com/LobsterTrap/lola) install.

### Key Patterns

- **Skills encapsulate operations** - Each skill handles one category of cluster or security tasks
- **Complete lifecycle coverage** - Create → Configure → Monitor → Operate → Validate Security
- **Dual MCP integration** - Assisted Installer (creation) + OpenShift (operations)
- **Script-based security validation** - Python helper scripts for CVE/SBOM/VEX data fetching (no MCP servers)
- **Environment-based auth** - OFFLINE_TOKEN (Assisted Installer) + KUBECONFIG (cluster ops)
- **Human-in-the-loop** - User approval required before critical operations
- **Comprehensive documentation** - 17 reference docs covering all aspects
- **Production-ready** - Real examples, validation, error handling

---

## Security Model

**Assisted Installer access**:
- Uses OFFLINE_TOKEN for Red Hat Hybrid Cloud Console authentication
- Token scoped to user's Red Hat account
- No credential storage or caching
- All operations audited in Red Hat console

**Cluster access**:
- Uses KUBECONFIG for Kubernetes authentication
- Respects Kubernetes RBAC permissions
- ServiceAccount-based authorization for multi-cluster
- Read-only operations by default (cluster-report)

**Security validation data sources**:
- Official Red Hat SBOM attestations (build-time and release-time) — extracted via cosign
- Red Hat VEX/CSAF data from https://security.access.redhat.com/data/csaf/v2/
- MITRE CVE API, OSV.dev, Go vulnerability database — public APIs, no authentication required
- No credential files accessed directly — pull secret path provided by user on auth failure only

---

## Development

See main repository [README.md](../README.md) for:
- Adding new skills
- Creating agents
- Integrating MCP servers
- Testing and validation

---

## License

[Apache 2.0](../LICENSE)

---

## References

- [Agentic skill pack for Red Hat OpenShift administration repository](https://github.com/RHEcosystemAppEng/agentic-plugins/tree/main/ocp-admin) - Documentation and details for this skill pack
- [OpenShift Container Platform documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18) - Documentation for Red Hat OpenShift Container Platform
- [Assisted Installer documentation](https://docs.redhat.com/en/documentation/assisted_installer_for_openshift_container_platform) - Documentation for Red Hat OpenShift Container Platform Assisted Installer
- [Assisted Service MCP Server](https://github.com/openshift-assisted/assisted-service-mcp) - Documentation for Assisted Service MCP Server
- [OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server) - Documentation and details for the OpenShift MCP Server
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [Red Hat Security Data](https://security.access.redhat.com/) - Official Red Hat VEX/CSAF data and security advisories
- [MITRE CVE API](https://cveawg.mitre.org/) - Authoritative CVE metadata source
- [OSV.dev](https://osv.dev/) - Open Source Vulnerability database
- [Sigstore cosign](https://github.com/sigstore/cosign) - SBOM attestation extraction tool
- [regclient](https://github.com/regclient/regclient) - Registry client for image metadata inspection
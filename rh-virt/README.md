# Agentic skill pack for Red Hat OpenShift Virtualization (Kubevirt)

  Provides automation capabilities for VM lifecycle management, provisioning, and inventory operations on OpenShift clusters using KubeVirt.

**Persona**: Virtualization Administrator, OpenShift Administrator
**Marketplaces**: Claude Code, Cursor

## Overview

The rh-virt collection provides specialized tools for managing virtual machines in OpenShift Virtualization environments:

- **5 specialized skills** for complete VM lifecycle management
- **OpenShift MCP server integration** for KubeVirt operations
- **Full VM lifecycle coverage** from creation to deletion with safety-first design

## Quick Start

### Prerequisites

- Claude Code CLI or IDE extension
- OpenShift cluster (>= 4.19) with Virtualization operator installed
- ServiceAccount with appropriate RBAC permissions for VirtualMachine resources
- KUBECONFIG environment variable configured with cluster access

### Environment Setup

Configure OpenShift cluster access:

```bash
export KUBECONFIG="/path/to/your/kubeconfig"
```

Verify access to the cluster:

```bash
oc get virtualmachines -A
# or
kubectl get vms -A
```

### MCP Server Container Image

This pack uses the [OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server) container image from `quay.io/redhat-user-workloads/crt-nshift-lightspeed-tenant/openshift-mcp-server`, pinned by SHA256 digest for supply chain security. No local build is required — the image is pulled automatically on first use.

To verify the image integrity:
```bash
podman inspect --format='{{.Digest}}' quay.io/redhat-user-workloads/crt-nshift-lightspeed-tenant/openshift-mcp-server@sha256:2f52c860f91ab3c8a5129b727bdef0d620e733013f073b10355866c45eafd053
```

### Installation (Lola)

Install the pack with [Lola](https://github.com/LobsterTrap/lola):

```bash
lola market add rh-agentic-collections https://raw.githubusercontent.com/RHEcosystemAppEng/agentic-collections/main/marketplace/rh-agentic-collection.yml
lola install -f rh-virt
```

## Skills

The pack provides 5 specialized skills for complete VM lifecycle management:

### 1. **vm-create** - Virtual Machine Provisioning

Create new virtual machines in OpenShift Virtualization with automatic error diagnosis and workarounds.

**Use when:**
- "Create a new VM"
- "Deploy a virtual machine"
- "Provision a VM with specific configuration"

**MCP Tools Used:**
- `vm_create` (kubevirt toolset) - Creates VirtualMachine resources with instance type resolution

**What it does:**
- Creates VirtualMachine resources with intelligent defaults
- Automatically resolves instance types based on size hints (small, medium, large, xlarge …)
- Configures storage, networking, and OS workloads
- **Automatically diagnoses scheduling issues** (e.g., node taints, resource constraints)
- **Proposes workarounds** for common errors
- **Applies fixes** with user confirmation (human-in-the-loop)
- Requires explicit user approval before creating VMs (resource consumption)

### 2. **vm-lifecycle-manager** - VM Power Management

Control VM lifecycle operations including start, stop, and restart.

**Use when:**
- "Start VM [name]"
- "Stop the virtual machine [name]"
- "Restart VM [name]"
- "Power on/off VM [name]"

**MCP Tools Used:**
- `vm_lifecycle` (kubevirt toolset) - Manages VM power state transitions

**What it does:**
- Starts stopped/halted VMs (changes runStrategy to Always)
- Stops running VMs gracefully (changes runStrategy to Halted)
- Restarts VMs (stop + start sequence)
- Manages VM runStrategy transitions safely
- Requires explicit user confirmation for each operation (prevents accidental service disruption)

### 3. **vm-inventory** - VM Discovery and Status

List and inspect virtual machines across namespaces with comprehensive status information.

**Use when:**
- "List all VMs"
- "Show VMs in namespace [name]"
- "Get details of VM [name]"
- "What VMs are running?"

**MCP Tools Used:**
- `resources_list` (core toolset) - Lists VirtualMachine resources across namespaces
- `resources_get` (core toolset) - Retrieves detailed VM specifications and status

**What it does:**
- Lists VMs across all namespaces or specific namespace
- Shows VM status (Running, Stopped, Provisioning, Error) and readiness
- Provides detailed VM configuration (vCPU, memory, storage, networks)
- Filters VMs by labels or field selectors
- Displays resource usage, node placement, and health conditions
- Read-only operations with fallback to `oc` CLI if MCP tools unavailable

### 4. **vm-delete** - VM Destruction and Cleanup

Permanently delete virtual machines and their associated resources with strict safety confirmations.

**Use when:**
- "Delete VM [name]"
- "Remove virtual machine [name]"
- "Destroy VM [name]"
- "Clean up VM [name]"

**MCP Tools Used:**
- `resources_delete` (core toolset) - Deletes VirtualMachine, DataVolume, and PVC resources
- `resources_get` (core toolset) - Verifies VM exists and retrieves details
- `resources_list` (core toolset) - Discovers dependent storage resources
- `vm_lifecycle` (kubevirt toolset) - Stops running VMs before deletion

**What it does:**
- **Permanent VM deletion** with typed confirmation (user must type VM name exactly)
- **Pre-deletion validation** - checks VM exists, running state, dependent resources
- **Protection enforcement** - refuses deletion of VMs with `protected: "true"` label
- **Deletion options** - VM only (preserve storage) or VM + storage (complete cleanup)
- **Graceful shutdown** - stops running VMs before deletion
- **Storage discovery** - identifies and optionally deletes DataVolumes and PVCs
- **Safety-first design** - multiple confirmation steps, clear warnings about data loss
- Requires explicit user confirmation at each critical step (human-in-the-loop)

### 5. **vm-clone** - VM Cloning and Duplication

Clone existing virtual machines for testing, scaling, or creating VM templates.

**Use when:**
- "Clone VM [source] to [target]"
- "Create a copy of VM [name]"
- "Duplicate VM [name] for testing"
- "Create 3 copies of template-vm"

**MCP Tools Used:**
- `resources_get` (core toolset) - Get source VM configuration
- `resources_create_or_update` (core toolset) - Create cloned VM and storage resources
- `resources_list` (core toolset) - List DataVolumes, PVCs, VMs

**What it does:**
- **Clone VM configuration** - copies instance type, preferences, network settings, tolerations
- **Flexible storage strategies** - clone storage (full copy), reference existing (shared), or create new empty storage
- **Batch cloning** - create multiple copies in one operation
- **Cross-namespace cloning** - clone VMs between different namespaces
- **Name conflict detection** - verifies target VM name availability
- **Resource impact preview** - shows CPU, memory, storage consumption before cloning
- **Automatic UUID generation** - generates new firmware UUIDs and MAC addresses for clones
- Requires explicit user confirmation and storage strategy selection (human-in-the-loop)

## MCP Server Integration

The pack integrates with the OpenShift MCP server (configured in `mcps.json`), which provides two toolsets for comprehensive cluster and virtualization management:

### **openshift-virtualization** - OpenShift MCP Server

Provides access to both Kubernetes core operations and KubeVirt virtual machine management through the Model Context Protocol.

**Repository**: https://github.com/openshift/openshift-mcp-server
**Image**: `quay.io/redhat-user-workloads/crt-nshift-lightspeed-tenant/openshift-mcp-server` (pinned by SHA256 digest)

**Enabled Toolsets**: `core` and `kubevirt` (via `--toolsets core,kubevirt`)

**Available Toolsets**:

The server provides two toolsets enabled via `--toolsets core,kubevirt`:

**KubeVirt Toolset** (`kubevirt`):
- `vm_create` - Create new VirtualMachines with instance type resolution and OS selection
- `vm_lifecycle` - Manage VM power state (start/stop/restart)

**Core Toolset** (`core`):
- `resources_list` - List Kubernetes resources (VMs, Pods, Deployments, etc.)
- `resources_get` - Get detailed resource information
- `resources_create_or_update` - Create or update Kubernetes resources
- `resources_delete` - Delete Kubernetes resources
- `resources_scale` - Scale deployments and statefulsets
- `pods_list`, `pods_list_in_namespace` - List pods across namespaces or in specific namespace
- `pods_get`, `pods_log`, `pods_exec`, `pods_delete`, `pods_run` - Pod operations
- `pods_top` - Resource consumption metrics for pods
- `nodes_top`, `nodes_log`, `nodes_stats_summary` - Node operations and metrics
- `events_list` - List cluster events for debugging
- `namespaces_list`, `projects_list` - Namespace and project discovery

**Configuration**:
```json
{
  "mcpServers": {
    "openshift-virtualization": {
      "command": "podman",
      "args": [
        "run",
        "--rm",
        "-i",
        "--network=host",
        "--userns=keep-id:uid=65532,gid=65532",
        "-v", "${KUBECONFIG}:/kubeconfig:ro,Z",
        "--entrypoint", "/openshift-mcp-server",
        "quay.io/redhat-user-workloads/crt-nshift-lightspeed-tenant/openshift-mcp-server@sha256:2f52c860f91ab3c8a5129b727bdef0d620e733013f073b10355866c45eafd053",
        "--kubeconfig", "/kubeconfig",
        "--toolsets", "core,kubevirt"
      ],
      "env": {
        "KUBECONFIG": "${KUBECONFIG}"
      },
      "description": "Red Hat Openshift MCP server for interacting with Openshift Container Platform clusters and its operators",
      "security": {
        "isolation": "container",
        "network": "local",
        "credentials": "env-only"
      }
    }
  }
}
```

**Configuration Details**:
- `--userns=keep-id:uid=65532,gid=65532` - Maps container user namespace for rootless Podman security
- `,Z` flag on volume mount - Applies SELinux context label for container access to kubeconfig
- `--entrypoint /openshift-mcp-server` - Specifies the MCP server binary to execute
- `--kubeconfig /kubeconfig` - Path to kubeconfig inside the container
- `--toolsets core,kubevirt` - Enables both core Kubernetes and KubeVirt-specific tool collections
- `--network=host` - Required for accessing local/remote Kubernetes clusters

## Sample Workflows

### Workflow 1: Create and Start VM

```
User: "Create a VM called web-server in namespace production"
→ vm-create skill creates the VM

User: "Start the web-server VM"
→ vm-lifecycle-manager skill starts the VM

User: "Check if it's running"
→ vm-inventory skill shows VM status
```

### Workflow 2: VM Inventory Check

```
User: "Show all VMs in production namespace"
→ vm-inventory skill lists all VMs with status

User: "What's the status of database-vm?"
→ vm-inventory skill shows detailed VM information
```

### Workflow 3: VM Lifecycle Management

```
User: "Stop all VMs in development namespace"
→ vm-lifecycle-manager skill stops each VM

User: "Restart the api-server VM"
→ vm-lifecycle-manager skill restarts the VM
```

### Workflow 4: VM Deletion and Cleanup

```
User: "Delete VM test-vm in namespace dev"
→ vm-delete skill validates VM exists
→ Discovers 30Gi DataVolume attached
→ Presents deletion options (VM only vs VM + storage)

User: "Delete VM + storage"

Agent: "Type 'test-vm' to confirm permanent deletion: _____"

User: "test-vm"

Agent: "Proceed with permanent deletion? (yes/cancel)"

User: "yes"
→ vm-delete deletes VM and storage
→ Reports 30Gi storage freed
```

### Workflow 5: VM Cloning for Test Environment

```
User: "Clone production-web to staging-web in namespace staging"
→ vm-clone skill validates source VM exists
→ Discovers 100Gi storage
→ Presents storage cloning options

Agent: "How should storage be cloned?
        1. Clone Storage (full copy) - 100Gi new allocation
        2. Reference Existing Storage (shared - dangerous)
        3. Create New Empty Storage - 100Gi new allocation
        4. Cancel"

User: "1"

→ vm-clone presents complete configuration preview

Agent: "Clone Configuration Review:
        Source: production-web (production namespace)
        Target: staging-web (staging namespace)
        Storage: Clone Storage (100Gi)

        Proceed with VM cloning? (yes/no)"

User: "yes"

→ vm-clone creates DataVolume with PVC clone source
→ Creates cloned VirtualMachine with new UUIDs
→ Monitors storage cloning progress

Agent: "⏳ Storage cloning in progress... (45%)
        ...
        ✓ VM Cloned Successfully
        Clone completed in 8m15s
        VM staging-web ready to start"
```

### Workflow 6: Automatic Error Diagnosis and Remediation

```
User: "Create a Fedora VM called test-vm in namespace demo"
→ vm-create skill creates the VM
→ Detects ErrorUnschedulable status
→ Consults docs/troubleshooting/scheduling-errors.md for domain knowledge
→ Diagnoses: Node taints prevent scheduling
→ Proposes workaround: Add tolerations to VM spec

Agent: "⚠️ VM Scheduling Issue Detected
        Root Cause: Node taints prevent VM scheduling

        I can apply a workaround to add the required tolerations.
        How would you like to proceed?"

User: "apply workaround"
→ vm-create patches VM with tolerations
→ Verifies VM can now be scheduled
→ Reports success

Agent: "✓ Workaround Applied Successfully
        VM can now be scheduled on virtualization nodes"
```

**Key Features**:
- **Automatic diagnosis**: Detects ErrorUnschedulable and other common errors
- **Documentation consultation**: Reads troubleshooting/INDEX.md and category files for domain knowledge
- **Intelligent workarounds**: Proposes fixes for MCP tool limitations
- **Human-in-the-loop**: Requires explicit user confirmation before applying patches
- **Transparent**: Explains temporary limitations and suggests filing enhancement requests

## Configuration

MCP server is configured in `mcps.json` (see [MCP Server Integration](#mcp-server-integration) for full configuration and available tools).

**Key Configuration Notes**:
- Uses the `quay.io/redhat-user-workloads/crt-nshift-lightspeed-tenant/openshift-mcp-server` image pinned by SHA256 digest
- `--userns=keep-id:uid=65532,gid=65532` - Enables rootless container security with user namespace mapping
- Mounts `KUBECONFIG` as read-only volume inside container with `,Z` for SELinux labeling
- `--entrypoint /openshift-mcp-server` - Specifies the MCP server binary
- `--toolsets core,kubevirt` - Enables both core Kubernetes and KubeVirt-specific tools
- Uses `--network=host` for cluster access (required for local/remote clusters)
- Requires OpenShift Virtualization operator installed on the cluster
- ServiceAccount needs RBAC permissions for VirtualMachine resources

## Troubleshooting

### Automatic Diagnosis (Recommended)

The **vm-create** skill includes automatic error diagnosis and workaround proposals. When VMs encounter scheduling issues:

1. **Detection**: Skill automatically detects ErrorUnschedulable and other error states
2. **Diagnosis**: Consults `docs/troubleshooting/INDEX.md` and category files to understand root cause
3. **Investigation**: Executes diagnostic commands (node taints, resource availability, events)
4. **Proposal**: Presents clear diagnosis with workaround options
5. **Remediation**: Applies fix with user confirmation (human-in-the-loop)

**Common Issues Handled**:
- **ErrorUnschedulable** - Node taints/tolerations mismatch, resource constraints, node selector issues
- **ErrorDataVolumeNotReady** - Storage provisioning delays, storage class issues, quota exceeded

**For comprehensive troubleshooting guidance**, see [docs/troubleshooting/INDEX.md](skills/vm-rebalance/docs/troubleshooting/INDEX.md).

### MCP Server Won't Start

**Problem**: Server fails to connect to cluster

**Solutions**:
1. Verify KUBECONFIG is set: `echo $KUBECONFIG`
2. Test cluster access: `oc get nodes` or `kubectl get nodes`
3. Check ServiceAccount permissions: `oc auth can-i create virtualmachines -A`

### VM Operations Fail

**Problem**: VM creation or lifecycle operations return errors

**Solutions**:
1. Verify OpenShift Virtualization operator is installed
2. Check namespace exists and ServiceAccount has access
3. Verify RBAC permissions for VirtualMachine resources
4. Check cluster resource availability (CPU, memory, storage)
5. Let vm-create skill run automatic diagnosis (see Workflow 4 above)

### Skills Not Triggering

**Problem**: Skills don't activate on expected queries

**Solutions**:
1. Verify module is installed: `lola list`
2. Reload Claude Code to refresh plugins
3. Check skill descriptions match query intent
4. Use explicit phrasing from skill examples

## Architecture Reference

### Directory Structure

```
rh-virt/
├── README.md                    # This file
├── mcps.json                    # MCP server configuration
├── docs/                        # AI-optimized knowledge base
│   └── troubleshooting/         # VM error diagnosis and workarounds (categorized by error type)
│       ├── INDEX.md             # Navigation hub for troubleshooting docs
│       ├── scheduling-errors.md # ErrorUnschedulable diagnostics
│       ├── storage-errors.md    # Storage provisioning issues
│       ├── lifecycle-errors.md  # Start/stop/terminating problems
│       ├── runtime-errors.md    # CrashLoopBackOff diagnostics
│       ├── network-errors.md    # Network attachment failures
│       └── .ai-index/           # Semantic indexing for AI discovery
│           └── semantic-index.json
└── skills/
    ├── vm-create/SKILL.md      # VM provisioning with auto-diagnosis
    ├── vm-lifecycle-manager/SKILL.md  # VM power management
    ├── vm-inventory/SKILL.md    # VM discovery and status
    ├── vm-delete/SKILL.md       # VM destruction and cleanup
    └── vm-clone/SKILL.md        # VM cloning and duplication
```

*Optional:* `.claude-plugin/plugin.json` — only if publishing via Claude Code’s plugin format; not required for [Lola](https://github.com/LobsterTrap/lola) install.

### Key Patterns

- **Skills encapsulate operations** - Each skill handles one category of VM tasks
- **Complete lifecycle coverage** - Create → Clone → Inventory → Lifecycle → Delete
- **MCP provides tools** - OpenShift MCP server exposes KubeVirt operations
- **Environment-based auth** - KUBECONFIG for secure cluster access
- **Automatic diagnosis** - Skills detect errors, consult docs, propose workarounds
- **Document consultation** - Skills read troubleshooting/ category files for domain knowledge
- **Human-in-the-loop** - User approval required before critical operations (lifecycle changes, deletion)
- **Safety-first design** - Typed confirmation for destructive operations, protection labels, multi-step validation
- **Workaround transparency** - Clear communication of MCP tool limitations and temporary solutions

## Security Model

**Cluster access**:
- Uses KUBECONFIG for authentication
- Respects Kubernetes RBAC permissions
- ServiceAccount-based authorization
- No credential storage or caching

**VM operations**:
- Namespace isolation enforced
- Resource quotas respected
- All operations audited in Kubernetes API logs

## Development

See main repository [README.md](../README.md) for:
- Adding new skills
- Creating agents
- Integrating MCP servers
- Testing and validation

## License

[Apache 2.0](../LICENSE)

## References

- [Agentic skill pack for Red Hat OpenShift administration repository](https://github.com/RHEcosystemAppEng/agentic-collections/tree/main/ocp-admin) - Documentation and details for this skill pack
- [OpenShift Virtualization Documentation](https://docs.openshift.com/container-platform/latest/virt/about_virt/about-virt.html)
- [KubeVirt User Guide](https://docs.openshift.com/container-platform/latest/virt/about_virt/about-virt.html)
- [OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server) - Documentation and details for the OpenShift MCP Server
- [MCP Protocol Specification](https://modelcontextprotocol.io)

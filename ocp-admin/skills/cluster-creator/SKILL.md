---
name: cluster-creator
description: |
  End-to-end OpenShift cluster creation using Red Hat Assisted Installer.
  Handles Single-Node OpenShift (SNO) and HA multi-node clusters on baremetal, vsphere, oci, nutanix.

  Use when:
  - "Create a new OpenShift cluster"
  - "Install OpenShift on my servers"
  - "Set up a single-node cluster for edge deployment"
  - "Deploy a production HA cluster"

  Complete workflow: cluster definition, ISO generation, host discovery/validation, role assignment,
  network configuration (VIPs, static networking), installation monitoring, credential retrieval.

  NOT for:
  - Listing existing clusters → Use `/cluster-inventory` skill
  - Modifying running clusters → Out of scope (Day-2 operations require direct cluster access)
  - Cluster upgrades (not yet supported)
license: Apache-2.0
model: inherit
color: green
allowed-tools: open_cluster_creator list_versions create_cluster cluster_info set_cluster_vips set_host_role cluster_iso_download_url install_cluster cluster_credentials_download_url cluster_logs_download_url list_static_network_config generate_nmstate_yaml validate_nmstate_yaml alter_static_network_config_nmstate_for_host
metadata:
  mcp_server: openshift-self-managed
  mcp_tools_priority: true
  environment_vars:
    - OFFLINE_TOKEN
  destructive: true
---

# cluster-creator

**MCP-First Approach**: This skill uses MCP tools from `openshift-self-managed` server. MCP tools have **absolute priority**.

**CLI Tools Policy**:
- ✅ **ALWAYS use MCP tools** when available
- ⚠️ **Last resort only**: CLI commands (`oc`, `kubectl`) may be attempted if no MCP alternative exists
- ⚠️ **Assume unavailable**: CLI tools are likely not installed in the execution environment

---

## Prerequisites

**Required MCP Servers**: `openshift-self-managed` ([setup guide](../README.md#environment-setup))

**MCP Server Architecture**:
This skill uses `openshift-self-managed` MCP server exclusively. This server connects to Red Hat Assisted Installer API to create self-managed OpenShift clusters.

| MCP Server | Used By This Skill? | Cluster Types | API Backend |
|------------|---------------------|---------------|-------------|
| `openshift-self-managed` | ✅ YES | OCP, SNO | Assisted Installer API (`/api/assisted-install/v2`) |
| `openshift-ocm-managed` | ❌ NO | ROSA, ARO, OSD | OCM API (`/api/clusters_mgmt/v1`) |

**Required MCP Tools** (all from `openshift-self-managed`):
`list_versions`, `create_cluster`, `cluster_info`, `set_cluster_vips`, `set_host_role`, `cluster_iso_download_url`, `install_cluster`, `cluster_credentials_download_url`, `cluster_logs_download_url`, `list_static_network_config`, `generate_nmstate_yaml`, `validate_nmstate_yaml`, `alter_static_network_config_nmstate_for_host`

**Environment Variables**: `OFFLINE_TOKEN` ([obtain here](https://cloud.redhat.com/openshift/token))

**Cluster Types Supported**:
- **OCP** (OpenShift Container Platform) - Self-managed HA clusters (3+ control plane nodes)
  - Platforms: baremetal, vsphere, nutanix, oci
- **SNO** (Single-Node OpenShift) - Self-managed single-node clusters
  - Platform: Always "none" (Red Hat API requirement)

**NOT Supported by This Skill** (different APIs, different workflows):
- **ROSA** (Red Hat OpenShift Service on AWS) - Use `openshift-ocm-managed` MCP server
- **ARO** (Azure Red Hat OpenShift) - Use `openshift-ocm-managed` MCP server
- **OSD** (OpenShift Dedicated) - Use `openshift-ocm-managed` MCP server

**Verification**:
1. Check `openshift-self-managed` in `mcps.json`
2. Verify `OFFLINE_TOKEN` set: `test -n "$OFFLINE_TOKEN"`
3. Test connection: Call `list_versions` to verify MCP server responsive

**On Failure**: Stop immediately, display setup instructions, ask "How to proceed? (setup/skip/abort)", wait for user input.

**Security**: Never expose credential values in output.

---

## When to Use This Skill

**Use when**:
- Creating new OpenShift cluster from scratch
- Deploying SNO for edge/development
- Setting up production HA cluster
- Have servers ready for OpenShift installation

**Do NOT use when**:
- Listing/inspecting clusters → Use `/cluster-inventory` skill
- Managing workloads → Out of scope (use `oc` CLI with credentials from this skill)
- Troubleshooting → Use `/cluster-inventory` skill
- Upgrading clusters (not supported)

---

## Workflow

End-to-end cluster creation with interactive guidance and validation.

### Step 0: Initialize Task Tracking

**Create tasks in logical order:**

```
TaskCreate(subject: "#1 Verify prerequisites", description: "Check MCP servers, OFFLINE_TOKEN")
TaskCreate(subject: "#2 Gather cluster requirements", description: "Type, platform, version, name, domain, arch, SSH, hardware")
TaskCreate(subject: "#3 Configure networking", description: "CIDRs, VIPs, static IPs")
TaskCreate(subject: "#4 Review and confirm", description: "Display summary, get approval")
TaskCreate(subject: "#5 Create cluster definition", description: "Create in Assisted Installer")
TaskCreate(subject: "#6 Apply platform config", description: "VIPs, static configs")
TaskCreate(subject: "#7 Generate cluster ISO", description: "Generate ISO URL")
TaskCreate(subject: "#8 Discover and assign hosts", description: "Check discovery, roles")
TaskCreate(subject: "#9 Validate readiness", description: "Verify cluster ready")
TaskCreate(subject: "#10 Start installation", description: "Confirm, trigger install")
TaskCreate(subject: "#11 Monitor installation", description: "Track progress")
TaskCreate(subject: "#12 Retrieve credentials", description: "Download kubeconfig")
```

**During execution**: Update task status to "in_progress" when starting, "completed" when done.

### Step 1: Environment Detection and Prerequisites

**TaskUpdate**: Mark task #1 as `in_progress`

**Check for interactive UI**: If the `open_cluster_creator` tool is available, call it immediately. The interactive Creator form handles Steps 2 through 6. Once the cluster is created via the form, resume from **Step 7** using the cluster ID returned by the form.

**Otherwise (text-only)**: Execute prerequisites verification from the Prerequisites section above, then continue to Step 2. On failure, consult [troubleshooting.md](docs/troubleshooting.md) and stop.

---

### Step 2: Gather Cluster Requirements


**Context**: This skill creates SELF-MANAGED clusters (OCP, SNO) via Assisted Installer. NOT for ROSA/ARO/OSD (use cluster-inventory for those).

Use AskUserQuestion to collect configuration:

1. **Cluster Type**: SNO (single-node) or HA (multi-node, 3+ control plane)
2. **Platform**:
   - **SNO**: Platform is automatically set to "none" (Red Hat API requirement) - DO NOT ask user
   - **HA**: Ask user to select: baremetal, vsphere, nutanix, or oci
3. **Version**: Call `list_versions`, show "Full Support" versions
4. **Cluster Name**: Ask "Cluster name? (or type your custom name directly)" - Suggest based on context (e.g., "prod-ocp", "edge-site-01", "dev-cluster") OR user types custom name. Validate: 1-54 chars, lowercase/numbers/hyphens, starts with letter ([validation](docs/input-validation-guide.md#cluster-name))
5. **Base Domain**: Ask "Base domain? (e.g., example.com)" - User types domain directly. Validate: valid DNS format ([validation](docs/input-validation-guide.md#base-domain))
6. **CPU Arch**: x86_64 (default), aarch64, ppc64le, s390x
7. **SSH Key**: Ask "How to provide?" Options: Generate new (recommended, save to cluster folder) | Existing file (path) | Paste | ⚠️ None (warn, require "PROCEED WITHOUT SSH" confirmation)
8. **Hardware**: Confirm servers meeting [host requirements](docs/host-requirements.md) are ready

**Create folder**: `/tmp/{cluster_name}.{base_domain}/` (permissions 700), display location

**Store all values** for subsequent steps.

---

### Step 3: Network Configuration

Ask: "How to configure networking?" Options: 1) Default (auto CIDRs, DHCP, HA: ask VIPs) | 2) Custom CIDRs (ask each, validate) | 3) Static IPs (Simple/Advanced/Manual modes, use `generate_nmstate_yaml`) | 4) Describe requirements (AI infers from text like "192.168.1.0/24, 100 pods")

**Reference**: [Networking Guide](docs/networking.md) has detailed examples for all 4 options

---

### Step 4: Configuration Briefing


Display summary: Cluster Name, Type (SNO/HA), Version, Platform, Architecture, Domain, VIPs (if applicable), Networking (DHCP/Static)

**Reference**: [Examples](docs/examples.md)

---

### Step 5: Confirmation Before Creation

**CRITICAL CHECKPOINT**

Ask: "Review configuration. Ready to create cluster definition?"

**Options**:
- **Yes**: Proceed to Step 6
- **No**: Allow parameter modification, re-display, re-ask
- **Abort**: Exit gracefully

---

### Step 6: Create Cluster Definition


**Tool**: `create_cluster`

**Parameters**: `{name, version, base_domain, single_node, platform, cpu_architecture, ssh_public_key}`

**Output**: Cluster UUID (`cluster_id`) - **CRITICAL for all subsequent operations**

**Save metadata** to `/tmp/{cluster_name}.{base_domain}/cluster-info.json`: cluster_id, cluster_name, base_domain, openshift_version, cluster_type, platform, cpu_architecture, created_at, api_url, console_url

**Error Handling**: Display error, allow retry/abort if duplicate name or invalid parameters.

---

### Step 7: Apply Platform Configuration


**7a. Set VIPs** (HA + baremetal/vsphere/nutanix only):
- **Tool**: `set_cluster_vips`
- **Parameters**: `{cluster_id, api_vip, ingress_vip}`

**7b. Apply Static Network** (if configured):
- For each host: **Tool**: `alter_static_network_config_nmstate_for_host`
- **Parameters**: `{cluster_id, nmstate_yaml, mac_address}`
- **Verify**: Call `list_static_network_config`

**Reference**: [Providers](docs/providers.md), [Networking](docs/networking.md)

---

### Step 8: Generate Cluster ISO

**Tool**: `cluster_iso_download_url`, **Parameters**: `{cluster_id}`

**Save URL**: `/tmp/{cluster_name}.{base_domain}/iso-download-url.txt`

**Download ISO**: Read the saved URL and download with safety flags:
```bash
iso_url="$(cat /tmp/{cluster_name}.{base_domain}/iso-download-url.txt)"
case "$iso_url" in
  https://*.openshiftapps.com/* | \
  https://api.openshift.com/* | \
  https://mirror.openshift.com/* )
    : ;;
  *)
    echo "ERROR: ISO URL domain not in allowlist: $iso_url" >&2
    exit 1
    ;;
esac
curl --fail --proto "=https" --tlsv1.2 -L -# \
  -o /tmp/{cluster_name}.{base_domain}/discovery.iso \
  -- "$iso_url"
```

**Verify download**: Check file exists and size > 0

**Display**: ISO ready at `/tmp/{cluster_name}.{base_domain}/discovery.iso`. Boot {expected_host_count} server(s) from this ISO, wait 5-10 min, say "check for hosts". Static configs applied in boot order.

---

### Step 9: Wait for User to Boot Hosts


Display: "Waiting for you to boot hosts. When ready, say 'check for hosts'."

**Wait for user trigger** - No automatic polling.

---

### Step 10: Check Host Discovery


**Tool**: `cluster_info`
**Parameters**: `{cluster_id}`

**Parse**: Extract `hosts` array, count discovered hosts

**Display**: Table with Host #, Hostname, CPU, RAM, Disk, Status

**Validation**:
- SNO: Requires exactly 1 host
- HA: Minimum 3 hosts

**If insufficient**: Ask to wait/proceed/abort.

**Reference**: [Host Requirements](docs/host-requirements.md)

---

### Step 11: Host Role Assignment


**SNO**: Single host auto-assigned "master"

**HA**:
- Suggest first 3 hosts as "master"
- Additional hosts as "worker"
- Allow user override

**Tool**: `set_host_role` (for each host)
**Parameters**: `{cluster_id, host_id, role}`

---

### Step 12: Validate Cluster Readiness


**Tool**: `cluster_info`

**Check**: Cluster `status` should be "ready"

**If validation fails**:
1. Display errors from cluster_info
2. Consult [troubleshooting.md](docs/troubleshooting.md) for cluster status meanings and validation error diagnosis
3. Offer options: fix/wait/abort

---

### Step 13: Final Confirmation Before Installation

**CRITICAL CHECKPOINT**

**Display**:
```
Ready to Start Installation

Cluster: {cluster_name}
Hosts: {count}
Expected Duration: 45-60 minutes

WARNING: Starting installation is irreversible!
Cannot pause or cancel once started.
```

Ask: "Start installation now?"

**Options**:
- **YES - Start now**: Proceed to Step 14
- **Wait - Review first**: Display config, re-ask
- **Abort**: Exit skill

---

### Step 14: Start Installation


**Tool**: `install_cluster`
**Parameters**: `{cluster_id}`

**On Success**: Display "Installation started!"

**On Error**:
1. Display error message
2. Consult [troubleshooting.md](docs/troubleshooting.md) for error diagnosis
3. If error is new/undocumented, note it for future documentation
4. Offer retry/abort

---

### Step 15: Monitor Installation


**Display**:
```
Installation Phases:
1. Preparing
2. Installing (bootstrapping)
3. Installing control plane
4. Finalizing
5. Completed

How to monitor:
- Say "check status" anytime
- Or use background monitoring

Background monitoring? (yes/no)
```

**If background**: Use Task tool with `run_in_background=true`

**If manual**: Wait for "check status", then call `cluster_info`, display progress, repeat until "installed" or "error"

**If installation fails**:
1. Consult [troubleshooting.md](docs/troubleshooting.md) for cluster lifecycle states and common installation errors
2. Download logs (`cluster_logs_download_url`) for detailed diagnosis
3. Offer options: diagnose errors, cleanup and retry, or manual intervention
4. **Cleanup**: Failed cluster remains in Assisted Installer - use cluster_info to verify state before deleting or retrying with same cluster_id

---

### Step 16: Installation Complete


Display: "Installation Completed! Cluster: {cluster_name}, Status: installed, Time: {duration}"

---

### Step 17: Retrieve Credentials

**Document Consultation** (REQUIRED):
1. **Action**: Read [credentials-management.md](docs/credentials-management.md)
2. **Output**: "I consulted credentials-management.md for credential download procedures."

**Execute**: Follow download procedure to save kubeconfig and kubeadmin-password to `/tmp/{cluster_name}.{base_domain}/` (permissions 600)

**Display**:
```
✅ Credentials downloaded to /tmp/{cluster_name}.{base_domain}/
   - kubeconfig (600)
   - kubeadmin-password (600)

To use cluster:
export KUBECONFIG=/tmp/{cluster_name}.{base_domain}/kubeconfig
```

**Security**: Credentials provide full admin access. Never expose presigned URLs.

---

### Step 18: Cluster Ready

**Display**:
```
🎉 OpenShift Cluster Ready!

Cluster: {cluster_name}.{base_domain}
API: https://api.{cluster_name}.{base_domain}:6443
Console: https://console-openshift-console.apps.{cluster_name}.{base_domain}

📁 Artifacts: /tmp/{cluster_name}.{base_domain}/
   (kubeconfig, kubeadmin-password, ssh-key, discovery.iso, iso-download-url.txt, cluster-info.json)

Next Steps:
- Verify via MCP: export KUBECONFIG=/tmp/{cluster_name}.{base_domain}/kubeconfig
  MCP Tool: resources_list (Parameters: {kind: "Node"})
- Alternative (oc CLI, unlikely available): oc --kubeconfig <path> get nodes
- SSH to nodes (if key configured): ssh -i /tmp/{cluster_name}.{base_domain}/ssh-key core@<node-ip>
- Web console: kubeadmin + password from /tmp/{cluster_name}.{base_domain}/kubeadmin-password
- Configure identity provider (idp.md), RBAC (rbac.md)
- Install operators and applications

Congratulations!
```

**Ask**: "Archive cluster folder to permanent storage? (yes/no)"

**If yes**: Ask destination (default: ~/.kube/clusters/), copy folder with `cp -r`, set permissions 700, display confirmation

**Reference**: [Credentials Management](docs/credentials-management.md)

---

## Dependencies

### Required MCP Servers
- `openshift-self-managed` - Red Hat Assisted Installer service for self-managed clusters ([setup](../README.md#environment-setup))

**Important**: This skill uses ONLY `openshift-self-managed` MCP server. Do NOT use `openshift-ocm-managed` (that server is for ROSA/ARO/OSD managed service clusters, not for OCP/SNO self-managed clusters).

### Required MCP Tools
All tools from `openshift-self-managed` MCP server:
- `list_versions`, `create_cluster`, `cluster_info`, `set_cluster_vips`, `set_host_role`
- `cluster_iso_download_url`, `install_cluster`, `cluster_credentials_download_url`, `cluster_logs_download_url`
- `list_static_network_config`, `generate_nmstate_yaml`, `validate_nmstate_yaml`, `alter_static_network_config_nmstate_for_host`

### Related Skills
- `/cluster-inventory` - List and inspect all cluster types (uses both MCP servers)

### Reference Documentation
**Configuration & Validation**:
- [Input Validation Guide](docs/input-validation-guide.md) - Parameter requirements
- [Networking](docs/networking.md) - Network configuration, VIPs, CIDR planning
- [Static Networking Guide](docs/static-networking-guide.md) - NMState configuration

**Platform & Infrastructure**:
- [Providers](docs/providers.md) - Infrastructure providers (baremetal, vsphere, oci, nutanix)
- [Platforms](docs/platforms.md) - OpenShift types (SNO, OCP, ROSA, ARO, OSD)
- [Host Requirements](docs/host-requirements.md) - Hardware specs by cluster type

**Post-Installation**:
- [Credentials Management](docs/credentials-management.md) - Kubeconfig and authentication setup
- [Identity Providers](docs/idp.md) - HTPasswd, LDAP, OIDC, GitHub authentication
- [RBAC](docs/rbac.md) - Role-Based Access Control and Security Context Constraints
- [Certificate Rotation](docs/certificate-rotation.md) - Certificate management and renewal
- [Security Checklist](docs/security-checklist.md) - Post-installation security verification
- [Storage](docs/storage.md) - Storage options by provider
- [Examples](docs/examples.md) - Configuration examples
- [Troubleshooting](docs/troubleshooting.md) - Common errors and resolutions

**Complete Documentation Guide**:
- **[Documentation Index](docs/INDEX.md)** - Navigate all ocp-admin documentation (consult for topics not explicitly referenced above)

---

## Human-in-the-Loop

This skill performs critical, irreversible operations requiring explicit user confirmation:

1. **Cluster Definition Creation** (Step 5): Display configuration, ask "Ready to create?"
2. **Starting Installation** (Step 13): Display summary, emphasize "WARNING: Irreversible!", wait for explicit "YES"
3. **After Major Steps**: Report VIP/network/role configuration results

**Never Assume Approval** - Always wait for explicit confirmation.

---

## Example Usage

**User**: "Create a single-node OpenShift cluster for my edge location."

**Result**: SNO deployed in ~45 min. All artifacts in `/tmp/edge-site-01.edge.local/`: kubeconfig, kubeadmin-password, SSH keys, discovery.iso, ISO URL, metadata

**More Examples**: See [examples.md](docs/examples.md) for HA, static networking, multi-cluster, and air-gapped configurations.

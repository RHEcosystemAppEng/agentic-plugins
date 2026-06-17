<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, AGENTS.md, marketplace/rh-agentic-collection.yml
-->

### Prerequisites

- Claude Code CLI or IDE extension (if using Claude Code)
- Podman (or Docker) for the container-based MCP servers in **`mcps.json`**
- Red Hat account with access to [cloud.redhat.com](https://cloud.redhat.com) for **cluster creation** and **inventory** flows
- **Offline token** from [OpenShift offline token](https://cloud.redhat.com/openshift/token) for Assisted Installer and OCM APIs
- For **`/cluster-report`**: valid **`KUBECONFIG`** with contexts that point at real OpenShift clusters (read-only MCP mode)

### Environment setup

Variable **names** must match **`mcps.json`** (use **`${...}`** placeholders only in git; never commit secrets).

**Assisted Installer + managed clusters** (`openshift-self-managed`, `openshift-ocm-managed`):

```bash
export OFFLINE_TOKEN="your-offline-api-token"
```

**Multi-cluster kube report** (`openshift-administration`):

```bash
export KUBECONFIG="/path/to/your/kubeconfig"
```

### Installation (Lola)

```bash
lola install -f ocp-admin
```

Module path: **`ocp-admin`** in **`marketplace/rh-agentic-collection.yml`**. See the root [README.md](../../README.md) for full prerequisites and MCP setup.

### Installation (Claude Code)

```bash
lola install -f ocp-admin -a claude-code
```

### Installation (Cursor)

```bash
lola install -f ocp-admin -a cursor
```

### MCP configuration

Servers are defined in **`mcps.json`** at the pack root: Assisted Installer / OCM (`OFFLINE_TOKEN`) and read-only OpenShift API (`KUBECONFIG`). Use **`${VAR}`** placeholders only; never print token or kubeconfig contents in chat output.

**Linux vs macOS:** OpenShift MCP `podman` args may include user-namespace flags for `KUBECONFIG` mounts; adjust per the pack **README** if Podman runs in a VM.

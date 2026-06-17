<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, AGENTS.md, marketplace/rh-agentic-collection.yml
-->

### Prerequisites

- Claude Code CLI or IDE extension (if using Claude Code)
- Podman (or Docker) for the container-based MCP server defined in **`mcps.json`**
- OpenShift cluster (**>= 4.19**) with the **OpenShift Virtualization** operator installed
- A kubeconfig with RBAC sufficient for VirtualMachine and related KubeVirt resources in target namespaces

### Environment setup

Point **`KUBECONFIG`** at a kubeconfig file the MCP container can read (names must match **`mcps.json`**):

```bash
export KUBECONFIG="/path/to/your/kubeconfig"
```

Verify the API sees KubeVirt / VM objects (optional smoke check):

```bash
oc get virtualmachines -A
# or
kubectl get vms -A
```

The pack **`mcps.json`** mounts `${KUBECONFIG}` read-only into the MCP container and passes **`${KUBECONFIG}`** in `env` — use placeholders only in git; never commit kubeconfig contents or secrets.

If you build the OpenShift MCP image locally instead of pulling a published image, follow **Building the MCP Server Container Image** in the pack **[README.md](../../README.md)**.

### Installation (Lola)

From a checkout of this repository, install the pack with [Lola](https://github.com/LobsterTrap/lola):

```bash
lola install -f rh-virt
```

The module is declared in **`marketplace/rh-agentic-collection.yml`** (`path: rh-virt`). See the root [README.md](../../README.md) for marketplace setup.

### Installation (Claude Code)

```bash
lola install -f rh-virt -a claude-code
```

### Installation (Cursor)

```bash
lola install -f rh-virt -a cursor
```

### MCP configuration

Server definitions live in **`mcps.json`** at the pack root (`openshift-virtualization` server, **`--toolsets`** includes **`kubevirt`**). Use **`${VAR}`** placeholders only; never commit secrets.

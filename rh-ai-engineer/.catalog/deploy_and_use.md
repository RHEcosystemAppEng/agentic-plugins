<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, AGENTS.md, marketplace/rh-agentic-collection.yml
-->

### Prerequisites

- Claude Code CLI or IDE extension (if using Claude Code)
- OpenShift cluster with **OpenShift AI (RHOAI)** installed and namespaces where you will work
- **`oc`** / **`kubectl`** access and a kubeconfig for the **`openshift`** and **`rhoai`** MCP flows
- Podman (recommended) for the containerized **OpenShift** MCP, or adjust per README for your OS
- Optional: **AI Observability** MCP deployed on-cluster (see **`mcps.json`** description URL) for GPU / vLLM / tracing helpers

### Environment setup

Names must match **`mcps.json`**. Do not commit secrets.

**Cluster API (OpenShift MCP + rhoai stdio transport):**

```bash
export KUBECONFIG="/path/to/your/kubeconfig"
```

The **`rhoai`** server maps **`RHOAI_MCP_KUBECONFIG_PATH`** to **`${KUBECONFIG}`** in **`mcps.json`**—set **`KUBECONFIG`** once for both.

**`RHOAI_MCP_TRANSPORT`** is set to **`stdio`** in **`mcps.json`** (fixed for this pack). You do not need to export or override it unless you maintain a forked **`mcps.json`**.

**AI Observability MCP (optional HTTP MCP):**

```bash
export AI_OBSERVABILITY_MCP_URL="https://your-ai-observability-route.openshift-ai.svc.cluster.local:8080"
```

Omit or leave unset if you rely on **`openshift`** / **`rhoai`** only; skills should degrade gracefully when observability tools are unavailable.

### Installation (Lola)

```bash
lola install -f rh-ai-engineer
```

Module path: **`rh-ai-engineer`** in **`marketplace/rh-agentic-collection.yml`**. See the root [README.md](../../README.md) for full setup.

### Installation (Claude Code)

```bash
lola install -f rh-ai-engineer -a claude-code
```

### Installation (Cursor)

```bash
lola install -f rh-ai-engineer -a cursor
```

### MCP configuration

Servers are defined in **`mcps.json`**: **`openshift`** (Podman + **`KUBECONFIG`** mount), **`rhoai`** (**`uvx`** transport using **`KUBECONFIG`**), and optional **`ai-observability`** (**`AI_OBSERVABILITY_MCP_URL`**). Use **`${...}`** placeholders only; never echo kubeconfig or token contents.

**Linux vs macOS:** the **`openshift`** entry may add user-namespace flags for `KUBECONFIG` readability on Linux; on macOS Podman-in-VM may require README adjustments.

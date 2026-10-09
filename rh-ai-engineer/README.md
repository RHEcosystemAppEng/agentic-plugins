# Red Hat AI Engineer Agent Plugin

Automation tools for AI/ML engineers working with Red Hat OpenShift AI (RHOAI). Deploy and manage models, pipelines, registries, workbenches, and serving runtimes on OpenShift AI.

## Skills

| Command | Description |
|---------|-------------|
| `/ds-project-setup` | Create and configure Data Science Projects with namespace, data connections, pipeline server, and model serving |
| `/workbench-manage` | Create and manage Jupyter notebook workbenches with image selection, resources, and lifecycle |
| `/model-deploy` | Deploy AI/ML models with vLLM, NIM, or Caikit+TGIS runtimes |
| `/model-registry` | Register, version, and promote ML models in the Model Registry across environments |
| `/pipeline-manage` | Create, run, schedule, and monitor Data Science Pipelines (Kubeflow Pipelines 2.0) |
| `/nim-setup` | Configure NVIDIA NIM platform on OpenShift AI (NGC credentials, Account CR) |
| `/serving-runtime-config` | Configure custom ServingRuntime CRs for model serving frameworks |
| `/debug-inference` | Troubleshoot failed or slow InferenceService deployments |
| `/ai-observability` | Analyze model performance, GPU utilization, cluster health, and distributed traces |
| `/model-monitor` | Configure TrustyAI bias detection (SPD, DIR) and data drift monitoring |
| `/guardrails-config` | Deploy TrustyAI Guardrails Orchestrator with input/output content safety detectors |

## Prerequisites

### Tools
- `podman` for running containerized MCP servers
- `oc` CLI (OpenShift client) for cluster access

### Environment Variables
- `KUBECONFIG` - Path to Kubernetes configuration file
- `AI_OBSERVABILITY_MCP_URL` (optional) - URL for the AI Observability MCP server
- `RHOAI_MCP_TRANSPORT` - Declared in **`mcps.json`** as **`stdio`** for the **`rhoai`** server; no export needed unless you maintain a customized **`mcps.json`**

### Cluster Requirements
- OpenShift cluster with Red Hat OpenShift AI operator installed
- KServe model serving platform configured
- NVIDIA GPU nodes available (for GPU-accelerated inference)

### For NIM Deployments
- NVIDIA GPU Operator installed
- Node Feature Discovery (NFD) Operator installed
- NGC API key

## MCP Servers

| Server | Type | Requirement | Description |
|--------|------|-------------|-------------|
| `openshift` | Container (podman) | **Required** | Kubernetes resource CRUD, pod management, logs, events. The only hard-required server — all RHOAI operations have OpenShift equivalents. |
| `rhoai` | Local process (uvx) | **Preferred** | RHOAI-specific convenience tools: model deployment, serving runtimes, data connections, project management. Automatic fallback to OpenShift when unavailable or returning errors. |
| `ai-observability` | Remote HTTP | **Optional** | vLLM metrics, GPU monitoring, distributed tracing. Skipped when unavailable. |

The `openshift` MCP server is the foundation for all skills. It provides reliable Kubernetes resource CRUD operations that serve as automatic fallbacks when RHOAI MCP tools are unavailable or return errors.

The `rhoai` MCP server provides high-level, RHOAI-domain-specific tools that simplify model deployment (no YAML construction needed), runtime management (including platform template discovery), and project validation. When these tools fail (auth errors, API inconsistencies), skills transparently fall back to equivalent OpenShift operations. See [rhoai-mcp](https://github.com/opendatahub-io/rhoai-mcp) for details. Note: the upstream project does not publish a public container image or version tags, so this plugin runs the server via `uvx` pinned to a specific commit hash for reproducibility.

The `ai-observability` MCP server is optional. When available, it enables GPU pre-flight checks before deployment and post-deployment performance validation.

### Deploying the AI Observability MCP Server

The `ai-observability` server runs inside the cluster to access Prometheus/Thanos and Tempo directly. See the [ai-observability-summarizer repo](https://github.com/rh-ai-quickstart/ai-observability-summarizer) for advanced configuration.

```bash
git clone https://github.com/rh-ai-quickstart/ai-observability-summarizer.git
cd ai-observability-summarizer
make install NAMESPACE=ai-observability
export AI_OBSERVABILITY_MCP_URL=https://$(oc get route aiobs-mcp-server-route -n ai-observability -o jsonpath='{.spec.host}')
```

## Supported Runtimes

| Runtime | Use Case | Setup Required |
|---------|----------|----------------|
| vLLM | Default for open-source LLMs (Llama, Granite, Mixtral, Mistral) | None |
| NVIDIA NIM | Optimized inference with TensorRT-LLM on NVIDIA GPUs | `/nim-setup` |
| Caikit+TGIS | Models in Caikit format with gRPC API | Model conversion |

See [supported-runtimes.md](skills/serving-runtime-config/references/supported-runtimes.md) for detailed runtime comparison.

## Supported Models

Common models with known hardware profiles:

| Model | Parameters | Min GPUs | Default Runtime |
|-------|-----------|----------|-----------------|
| Llama 3.1 8B | 8B | 1x (16GB VRAM) | vLLM |
| Llama 3.1 70B | 70B | 4x A100 80GB | vLLM / NIM |
| Granite 3.1 8B | 8B | 1x (16GB VRAM) | vLLM |
| Mixtral 8x7B | 46.7B MoE | 2x A100 80GB | vLLM |
| Mistral 7B | 7B | 1x (16GB VRAM) | vLLM |

See [known-model-profiles.md](skills/model-deploy/references/known-model-profiles.md) for full profiles. Models not listed are supported via live documentation lookup.

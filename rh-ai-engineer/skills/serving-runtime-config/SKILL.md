---
name: serving-runtime-config
description: |
  Configure custom ServingRuntime CRs on OpenShift AI for model serving frameworks not covered by built-in runtimes.

  Use when:
  - "Create a custom serving runtime"
  - "I need a runtime for ONNX / Triton / custom framework"
  - "Customize vLLM runtime parameters"
  - "What serving runtimes are available?"
  - "Add a custom container image for model serving"

  Handles listing existing runtimes, creating new ServingRuntime CRs, and validating compatibility with target models.

  NOT for deploying models (use /model-deploy after runtime is configured).
  NOT for NIM platform setup (use /nim-setup).
model: inherit
color: blue
license: Apache-2.0
allowed-tools: resources_get resources_list resources_create_or_update list_serving_runtimes create_serving_runtime list_data_science_projects list_models
---

# /serving-runtime-config Skill

Configure custom ServingRuntime custom resources on Red Hat OpenShift AI. Use when built-in runtimes (vLLM, NIM, Caikit+TGIS) do not support the target model framework, or when customizing an existing runtime's parameters (env vars, model format, container image).

## Prerequisites

**Required MCP Server**: `openshift` ([OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server))

**Required MCP Tools** (from openshift):
- `resources_get` - Inspect existing ServingRuntime CRs in detail
- `resources_list` - List ServingRuntime and ClusterServingRuntime CRs (OpenShift fallback)
- `resources_create_or_update` - Create fully custom ServingRuntime CR (when not using templates, or as fallback)

**Preferred MCP Server**: `rhoai` ([RHOAI MCP Server](https://github.com/opendatahub-io/rhoai-mcp)) — used when available, automatic OpenShift fallback on failure

**Preferred MCP Tools** (from rhoai):
- `list_serving_runtimes` - List available runtimes and platform templates with supported model formats
- `create_serving_runtime` - Instantiate a serving runtime from a platform template (no YAML needed)
- `list_data_science_projects` - Validate namespace is an RHOAI project

**Optional MCP Server**: `ai-observability` ([AI Observability MCP](https://github.com/rh-ai-quickstart/ai-observability-summarizer))

**Optional MCP Tools** (from ai-observability):
- `list_models` - Verify deployed models use the new runtime

**Common prerequisites** (KUBECONFIG, OpenShift+RHOAI cluster, KServe, verification protocol): See [skill-conventions.md](../references/skill-conventions.md).

**Fallback templates**: See [openshift-fallback-templates.md](../references/openshift-fallback-templates.md) for OpenShift YAML templates used when RHOAI tools are unavailable.

## When to Use This Skill

**Use this skill when you need to:**
- Create a custom ServingRuntime for a framework not covered by built-in runtimes
- Customize an existing runtime's parameters (env vars, container image, model format)
- Instantiate a platform template runtime into a namespace
- List and compare available serving runtimes and templates

**Do NOT use this skill when:**
- You want to deploy a model using an existing runtime (use `/model-deploy`)
- You need NIM platform setup (use `/nim-setup`)
- You need to troubleshoot a deployment (use `/debug-inference`)

## Workflow

### Step 1: Validate Target Namespace

**Ask the user for:**
- **Namespace**: Target namespace for the ServingRuntime

**MCP Tool**: `list_data_science_projects` (from rhoai)

**Parameters**: none

Verify the user-specified namespace is an RHOAI Data Science Project.

**If rhoai unavailable or returns error**: Use `resources_list` (from openshift) with `apiVersion: v1`, `kind: Namespace`, `labelSelector: opendatahub.io/dashboard=true`.

**Error Handling**:
- If namespace not found in project list -> Report: "Namespace `[namespace]` is not an RHOAI Data Science Project. Use `/ds-project-setup` to create one, or specify a different namespace." **WAIT for user decision.**

### Step 2: Gather Requirements

**Ask the user for:**
- **Use case**: What framework/model needs serving? (e.g., "ONNX model", "custom TensorRT engine", "vLLM with custom args")
- **Intent**: New runtime from scratch, or customize an existing one?

**Document Consultation** (read before listing runtimes):
1. **Action**: Read [supported-runtimes.md](../../docs/references/supported-runtimes.md) using the Read tool to understand available runtimes and their capabilities
2. **Output to user**: "I consulted [supported-runtimes.md](../../docs/references/supported-runtimes.md) to understand available runtimes."

**MCP Tool**: `list_serving_runtimes` (from rhoai)

**Parameters**:
- `namespace`: validated namespace from Step 1 - REQUIRED
- `include_templates`: `true` - REQUIRED (shows both existing runtimes and platform templates)

**If rhoai unavailable or returns error**: Use `resources_list` (from openshift) with `apiVersion: serving.kserve.io/v1alpha1`, `kind: ServingRuntime`, `namespace: [namespace]` for namespace runtimes, and `kind: ClusterServingRuntime` for platform templates. Filter by label `opendatahub.io/dashboard=true` and check `spec.supportedModelFormats` for compatibility.

**Present findings** in a table:

| Runtime Name | Model Format | Source | Requires Instantiation |
|--------------|-------------|--------|----------------------|
| [name] | [format] | namespace / template | [true/false] |

The response distinguishes between:
- **Existing runtimes** (`source: "namespace"`) - ready to use with `/model-deploy`
- **Platform templates** (`source: "template"`, `requires_instantiation: true`) - must be instantiated first

If an existing runtime fits the user's need, recommend using it directly with `/model-deploy`. If a platform template fits, offer to instantiate it (Step 5 alternative). Otherwise, proceed to Step 3 for custom runtime creation.

**WAIT for user to confirm whether to create a new runtime, instantiate a template, or customize an existing one.**

### Step 3: Determine Runtime Configuration

Based on the user's framework and model requirements, determine the ServingRuntime spec.

**If customizing an existing runtime:**

**MCP Tool**: `resources_get` (from openshift)

**Parameters**:
- `apiVersion`: `"serving.kserve.io/v1alpha1"` - REQUIRED
- `kind`: `"ServingRuntime"` - REQUIRED
- `namespace`: user-specified namespace - REQUIRED
- `name`: name of the existing runtime to customize - REQUIRED

Extract the current spec as a starting point. Present the current configuration and ask what the user wants to change.

**If the user requests a runtime for an unfamiliar framework -> Trigger live doc lookup:**
1. **Action**: Read [live-doc-lookup.md](../references/live-doc-lookup.md) using the Read tool for the lookup protocol
2. **Output to user**: "Framework [name] is not in my cached runtimes. I'll look up its serving requirements."
3. Use **WebFetch** to retrieve specs from Red Hat OpenShift AI documentation
4. Extract: container image, model format name, supported protocols, required env vars
5. **Output to user**: "I looked up [framework] on [source] to confirm its runtime requirements: [summary]"

**Collect runtime parameters:**

| Parameter | Value | Source |
|-----------|-------|--------|
| Runtime name | [name] | user input |
| Container image | [image:tag] | user input / doc lookup |
| Model format name | [format] | user input / doc lookup |
| Supported protocol versions | [v1, v2, grpc-v2] | user input / default |
| Multi-model serving | [true/false] | default: false (single-model) |
| Environment variables | [list] | user input |
| GPU resource requirements | [limits] | user input |

**WAIT for user to confirm or modify parameters.**

### Step 4: Generate ServingRuntime YAML

Generate the ServingRuntime manifest using values from Steps 2-3.

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: ServingRuntime
metadata:
  name: [runtime-name]
  namespace: [namespace]
  labels:
    opendatahub.io/dashboard: "true"
  annotations:
    openshift.io/display-name: "[Display Name]"
spec:
  supportedModelFormats:
    - name: [model-format-name]
      version: "[version]"
      autoSelect: true
  multiModel: false
  containers:
    - name: kserve-container
      image: [container-image:tag]
      ports:
        - containerPort: 8080
          protocol: TCP
      env:
        - name: [ENV_VAR_NON_SECRET]
          value: "[non-sensitive-value]"
        - name: [SECRET_ENV_VAR]
          valueFrom:
            secretKeyRef:
              name: [k8s-secret-name]
              key: [secret-key-name]
      resources:
        limits:
          nvidia.com/gpu: "[gpu-count]"
        requests:
          cpu: "[cpu]"
          memory: "[memory]"
```

Display the ServingRuntime YAML to the user, **redacting any sensitive values**.

**Ask**: "Proceed with creating this ServingRuntime? (yes/no/modify)"

**WAIT for explicit confirmation.**

- If **yes** -> Proceed to Step 5
- If **no** -> Abort
- If **modify** -> Ask what to change, regenerate YAML, return to this step

### Step 5: Create ServingRuntime

**If instantiating from a platform template** (user chose a template from Step 2):

**MCP Tool**: `create_serving_runtime` (from rhoai)

**Parameters**:
- `namespace`: target namespace - REQUIRED
- `template_name`: name of the template to instantiate (e.g., `"vllm-cuda-runtime-template"`) - REQUIRED

The response includes the created runtime name, display name, and supported model formats.

**If rhoai unavailable or returns error**: Use `resources_get` (from openshift) to fetch the ClusterServingRuntime template, copy its spec to a namespace-scoped ServingRuntime, and create via `resources_create_or_update` (from openshift). See [openshift-fallback-templates.md](../references/openshift-fallback-templates.md#servingruntime) for the pattern.

**If creating a fully custom runtime** (custom container image, non-template configuration):

**MCP Tool**: `resources_create_or_update` (from openshift)

**Parameters**:
- `manifest`: full ServingRuntime manifest as JSON string - REQUIRED
- `namespace`: user-specified namespace - REQUIRED

**Error Handling**:
- If namespace not found -> Report error, suggest creating namespace or using `/ds-project-setup`
- If runtime name already exists -> Ask user: "ServingRuntime `[name]` already exists. Update it? (yes/no)"
- If CRD not found -> Report: "ServingRuntime CRD not available. Ensure Red Hat OpenShift AI operator is installed."
- If RBAC error -> Report insufficient permissions

### Step 6: Validate Runtime

**MCP Tool**: `list_serving_runtimes` (from rhoai)

**Parameters**:
- `namespace`: user-specified namespace - REQUIRED
- `include_templates`: `false`

Verify the runtime appears in the namespace runtime list.

**If rhoai unavailable or returns error**: Use `resources_list` (from openshift) with `apiVersion: serving.kserve.io/v1alpha1`, `kind: ServingRuntime`, `namespace: [namespace]` for namespace runtimes, and `kind: ClusterServingRuntime` for platform templates. Filter by label `opendatahub.io/dashboard=true` and check `spec.supportedModelFormats` for compatibility.

For detailed inspection:

**MCP Tool**: `resources_get` (from openshift)

**Parameters**:
- `apiVersion`: `"serving.kserve.io/v1alpha1"` - REQUIRED
- `kind`: `"ServingRuntime"` - REQUIRED
- `namespace`: user-specified namespace - REQUIRED
- `name`: the created runtime name - REQUIRED

**Report results** showing: runtime name, namespace, model format, container image, and next steps (`/model-deploy` to deploy a model using this runtime).

## Common Issues

For common issues (GPU scheduling, OOMKilled, image pull errors, RBAC), see [common-issues.md](../references/common-issues.md).

### Issue 1: InferenceService Cannot Find Runtime

**Error**: InferenceService status shows "Unknown" or runtime not matched

**Cause**: The `modelFormat.name` in the InferenceService does not match any `supportedModelFormats[].name` in available ServingRuntimes.

**Solution:**
1. Verify the model format name matches exactly (case-sensitive)
2. Check the runtime is in the same namespace as the InferenceService
3. Ensure the runtime has `opendatahub.io/dashboard: "true"` label

### Issue 2: Runtime Port Mismatch

**Error**: InferenceService created but health checks fail, endpoint returns connection refused

**Cause**: The `containerPort` in the ServingRuntime does not match the port the serving framework actually listens on.

**Solution:**
1. Check the framework's documentation for its default serving port
2. Update the `containerPort` in the ServingRuntime spec
3. Or set an environment variable to configure the framework's listen port to match

## Dependencies

### MCP Tools
See [Prerequisites](#prerequisites) for the complete list of required and optional MCP tools.

### Related Skills
- `/model-deploy` - Deploy a model using the configured runtime
- `/nim-setup` - NIM platform setup (if NIM runtime is needed instead)
- `/debug-inference` - Troubleshoot InferenceService failures after deployment

### Reference Documentation
- [supported-runtimes.md](../../docs/references/supported-runtimes.md) - Runtime capabilities and model format names
- [live-doc-lookup.md](../references/live-doc-lookup.md) - Protocol for fetching specs for unknown frameworks

## Critical: Human-in-the-Loop Requirements

See [skill-conventions.md](../references/skill-conventions.md) for general HITL and security conventions.

**Skill-specific checkpoints:**
- After namespace validation (Step 1): confirm namespace or redirect to `/ds-project-setup`
- After listing existing runtimes (Step 2): confirm whether to create new or customize existing
- After collecting parameters (Step 3): confirm runtime configuration
- Before creating ServingRuntime (Step 4): display full YAML, confirm
- **NEVER** overwrite an existing ServingRuntime without user confirmation

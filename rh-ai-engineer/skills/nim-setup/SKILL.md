---
name: nim-setup
description: |
  Configure NVIDIA NIM platform on OpenShift AI for optimized model inference.

  Use when:
  - "Set up NIM on my cluster"
  - "Configure NGC credentials for NIM"
  - "I want to deploy a NIM model but haven't set up the platform"
  - "Create the NIM Account CR"

  One-time prerequisite before deploying models with NVIDIA NIM runtime via /model-deploy.

  NOT for deploying models (use /model-deploy instead).
  NOT for vLLM or Caikit deployments (NIM-specific only).
model: inherit
color: blue
license: Apache-2.0
allowed-tools: resources_get resources_list resources_create_or_update events_list list_data_science_projects list_serving_runtimes get_gpu_info
---

# /nim-setup Skill

Configure the NVIDIA NIM platform on OpenShift AI. This is a one-time setup that creates NGC credentials and the NIM Account custom resource, enabling NIM-based model deployments via `/model-deploy`.

## Prerequisites

**Required MCP Server**: `openshift` ([OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server))

**Required MCP Tools** (from openshift):
- `resources_get` - Check operator installations and existing resources
- `resources_list` - List resources in a namespace
- `resources_create_or_update` - Create secrets, Account CR, ConfigMap
- `events_list` - Check events for errors during setup

**Optional MCP Server**: `rhoai` ([RHOAI MCP Server](https://github.com/opendatahub-io/rhoai-mcp))

**Optional MCP Tools** (from rhoai):
- `list_data_science_projects` - Validate namespace is an RHOAI Data Science Project
- `list_serving_runtimes` - Verify NIM ServingRuntimes after setup

**Optional MCP Server**: `ai-observability` (for `get_gpu_info` to verify GPU availability)

**Common prerequisites** (KUBECONFIG, OpenShift+RHOAI cluster, verification protocol): See [skill-conventions.md](../references/skill-conventions.md).

**Required User Input**:
- NGC API key (from https://ngc.nvidia.com)
- Target namespace for NIM resources

**Additional cluster requirements**:
- OpenShift cluster >= 4.14
- NVIDIA GPU Operator installed
- Node Feature Discovery (NFD) Operator installed
- ServiceAccount with RBAC permissions to create Secrets, Accounts, and ConfigMaps

## When to Use This Skill

**Use this skill when you need to:**
- Set up NVIDIA NIM platform on OpenShift AI for the first time
- Create or refresh NGC credentials (image pull secret + API key secret)
- Create the NIM Account custom resource
- Verify GPU Operator and NFD Operator are installed and healthy

**Do NOT use this skill when:**
- You want to deploy a model (use `/model-deploy` after NIM setup is complete)
- You want to deploy with vLLM or Caikit+TGIS (NIM-specific only, use `/model-deploy` directly)
- You need to create a custom ServingRuntime (use `/serving-runtime-config`)

## Workflow

### Step 0: Validate Target Namespace (Optional)

If the `rhoai` MCP server is available, validate that the target namespace is an RHOAI Data Science Project:

**MCP Tool**: `list_data_science_projects` (from rhoai)

If the namespace is not in the project list, warn: "Namespace `[namespace]` is not a Data Science Project. NIM setup may not work correctly. Consider creating a Data Science Project first."

If `rhoai` MCP is not available, skip this check and proceed.

### Step 1: Verify GPU Operator and Node Feature Discovery

**Document Consultation** (read before verifying operators):
1. **Action**: Read [supported-runtimes.md](../../docs/references/supported-runtimes.md) using the Read tool to understand NIM platform requirements
2. **Output to user**: "I consulted [supported-runtimes.md](../../docs/references/supported-runtimes.md) to understand NIM platform requirements."

Check that the NVIDIA GPU Operator and NFD Operator are installed and healthy.

**MCP Tool**: `resources_get` (from openshift)

**Parameters**:
- `apiVersion`: `"operators.coreos.com/v1alpha1"` - REQUIRED
- `kind`: `"ClusterServiceVersion"` - REQUIRED
- `namespace`: `"nvidia-gpu-operator"` - REQUIRED (namespace where GPU Operator CSV is installed)
- `name`: the CSV name matching `"gpu-operator-certified"` prefix

**Expected Output**: ClusterServiceVersion object with `status.phase: "Succeeded"`

Repeat for NFD Operator:
- `namespace`: `"openshift-nfd"`
- `name`: the CSV name matching `"nfd"` prefix

**Error Handling**:
- If GPU Operator CSV not found -> Report to user: "NVIDIA GPU Operator is not installed. Install it from OperatorHub before proceeding."
- If NFD Operator CSV not found -> Report to user: "Node Feature Discovery Operator is not installed. Install it from OperatorHub before proceeding."
- If `status.phase` != `"Succeeded"` -> Report current phase and suggest troubleshooting
- Offer to skip this check if user confirms operators are installed via another method

### Step 2: Collect NGC Credentials from User

Ask the user for their NGC API key. This key is used for two purposes:
1. Pulling NIM container images from `nvcr.io` (image pull secret)
2. Authenticating NIM API calls at runtime (API key secret)

**Ask the user**:
```
To set up NIM, I need your NVIDIA NGC API key.

You can generate one at: https://ngc.nvidia.com/setup/api-key

Please provide:
1. Your NGC API key
2. The target namespace for NIM resources (e.g., "my-ai-project")
```

**WAIT for user to provide the NGC API key and namespace.**

**SECURITY**: Store the key in memory only for the duration of this skill. Never echo or display the actual key value in output.

### Step 3: Create NGC Image Pull Secret

Generate and display the docker-registry Secret YAML for pulling NIM images from `nvcr.io`.

**Show the user the Secret manifest** (with API key value redacted):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ngc-image-pull-secret
  namespace: [namespace]
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: [base64-encoded docker config for nvcr.io]
```

Note: The `.dockerconfigjson` contains:
- Registry: `nvcr.io`
- Username: `$oauthtoken`
- Password: `[NGC API key - REDACTED in display]`

**Ask**: "Should I create this image pull secret in namespace `[namespace]`? (yes/no)"

**WAIT for explicit user confirmation.**

**MCP Tool**: `resources_create_or_update` (from openshift)

**Parameters**:
- `manifest`: full Secret manifest as JSON string - REQUIRED
  - The JSON must include apiVersion, kind, metadata (name, namespace), type, and data fields
- `namespace`: user-specified namespace - REQUIRED
  - Example: `"my-ai-project"`

**Expected Output**: Created Secret object with `metadata.uid`

**Error Handling**:
- If secret already exists -> Ask user: "Secret `ngc-image-pull-secret` already exists. Should I update it? (yes/no)"
- If namespace not found -> Report error, suggest creating namespace first
- If RBAC error -> Report insufficient permissions

### Step 4: Create NGC API Key Secret

Generate and display the generic Secret YAML for the NGC API key used at runtime.

**Show the user the Secret manifest** (with API key value redacted):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ngc-api-key
  namespace: [namespace]
type: Opaque
stringData:
  NGC_API_KEY: "[REDACTED]"
```

**Ask**: "Should I create this API key secret in namespace `[namespace]`? (yes/no)"

**WAIT for explicit user confirmation.**

**MCP Tool**: `resources_create_or_update` (from openshift)

**Parameters**:
- `manifest`: full Secret manifest as JSON string - REQUIRED
- `namespace`: user-specified namespace - REQUIRED

**Expected Output**: Created Secret object with `metadata.uid`

**Error Handling**:
- If secret already exists -> Ask user if they want to update it
- If RBAC error -> Report insufficient permissions

### Step 5: Create NIM Account CR

Generate and display the NIM Account custom resource that manages the NIM platform lifecycle.

**Show the user the Account CR manifest:**

```yaml
apiVersion: nim.opendatahub.io/v1
kind: Account
metadata:
  name: nim-account
  namespace: [namespace]
spec:
  apiKeySecret:
    name: ngc-api-key
  imagePullSecret:
    name: ngc-image-pull-secret
```

**Ask**: "Should I create this NIM Account CR in namespace `[namespace]`? (yes/no)"

**WAIT for explicit user confirmation.**

**MCP Tool**: `resources_create_or_update` (from openshift)

**Parameters**:
- `manifest`: full Account CR manifest as JSON string - REQUIRED
- `namespace`: user-specified namespace - REQUIRED

**Expected Output**: Created Account object with `metadata.uid`

**Error Handling**:
- If Account CR already exists -> Report current status, ask if user wants to update
- If CRD not found (`nim.opendatahub.io/v1` Account) -> Report: "NIM CRD not available. Ensure Red Hat OpenShift AI operator is installed and includes NIM support."
- If RBAC error -> Report insufficient permissions

### Step 6: (Optional) Configure NIM Model Catalog

**Ask**: "Would you like to customize which NIM models appear in the catalog? (yes/no, default: no)"

If user says **no** -> Skip to Step 7 (default catalog is used).

If user says **yes**:

**Show the user the ConfigMap template:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nim-model-catalog
  namespace: [namespace]
data:
  model-catalog.json: |
    [
      {
        "name": "[model-name]",
        "displayName": "[display-name]",
        "shortDescription": "[description]"
      }
    ]
```

Ask user which models to include, generate the ConfigMap, and confirm before creating.

**MCP Tool**: `resources_create_or_update` (from openshift)

### Step 7: Validate NIM Platform Readiness

Check that the NIM platform is ready for model deployments.

**Step 7a: Check Account CR Status**

**MCP Tool**: `resources_get` (from openshift)

**Parameters**:
- `apiVersion`: `"nim.opendatahub.io/v1"` - REQUIRED
- `kind`: `"Account"` - REQUIRED
- `namespace`: user-specified namespace - REQUIRED
- `name`: `"nim-account"` - REQUIRED

**Expected Output**: Account object with `status.conditions` showing ready state

**Step 7b: Verify NIM ServingRuntimes**

**MCP Tool**: `list_serving_runtimes` (from rhoai) - preferred if rhoai MCP available

**Parameters**:
- `namespace`: user-specified namespace - REQUIRED
- `include_templates`: `false`

**Fallback MCP Tool**: `resources_list` (from openshift)
- `apiVersion`: `"serving.kserve.io/v1alpha1"`, `kind`: `"ServingRuntime"`, `namespace`: user-specified namespace

**Expected Output**: List of ServingRuntime objects including NIM runtimes

**Step 7c: (Optional) GPU Inventory Check**

If `ai-observability` MCP server is available, use `get_gpu_info` to report cluster GPU inventory.

**Report results** showing: Account CR status, credentials status (created/existing), available NIM ServingRuntimes, GPU inventory (if available), and next steps (`/model-deploy`).

**On failure**: Report Account CR status details and error message. Suggest troubleshooting steps: check Account CR events, verify NGC API key validity, check OpenShift AI operator logs. Ask if user wants help troubleshooting.

## Common Issues

For common issues (GPU scheduling, OOMKilled, image pull errors, RBAC), see [common-issues.md](../references/common-issues.md).

### Issue 1: Account CR Stuck in "Pending"

**Error**: Account CR `status.conditions` shows pending state indefinitely

**Cause**: NGC credentials are invalid, expired, or the RHOAI operator cannot reach NGC services.

**Solution:**
1. Verify NGC API key is valid by testing at https://ngc.nvidia.com
2. Check Account CR events: use `events_list` filtered by namespace to find events related to the Account resource
3. Regenerate NGC API key and re-run `/nim-setup` with new credentials

### Issue 2: GPU Operator Not Installed

**Error**: ClusterServiceVersion for `gpu-operator-certified` not found

**Cause**: NVIDIA GPU Operator was not installed from OperatorHub.

**Solution:**
1. Install NVIDIA GPU Operator from OperatorHub in the OpenShift console
2. Wait for the operator to reach `Succeeded` phase
3. Verify GPU nodes are detected: check for `nvidia.com/gpu` resources on nodes
4. Re-run `/nim-setup`

### Issue 3: NIM ServingRuntimes Not Appearing

**Error**: `resources_list` for ServingRuntimes returns no NIM runtimes

**Cause**: Account CR is not yet ready, or the RHOAI operator version does not include NIM support.

**Solution:**
1. Check Account CR status — runtimes are created asynchronously after the Account becomes ready
2. Wait 2-3 minutes and re-check
3. Verify RHOAI operator version supports NIM integration
4. Check operator logs for errors

## Dependencies

### MCP Tools
See [Prerequisites](#prerequisites) for the complete list of required and optional MCP tools.

### Related Skills
- `/model-deploy` - Deploy a model using NIM runtime after setup is complete
- `/serving-runtime-config` - Configure custom serving runtimes if NIM doesn't fit

### NIM Deployment Handoff to /model-deploy

When handing off to `/model-deploy` after NIM setup, note these NIM-specific considerations:

- **NIM URI scheme**: NIM models may use a `nim://` URI scheme which the `deploy_model` RHOAI tool may not recognize. If this happens, `/model-deploy` will fall back to creating the InferenceService via OpenShift direct with the NIM container image, NGC credentials, and NIM-specific env vars.
- **CUDA driver compatibility**: The `latest` NIM image tag may bundle a CUDA version incompatible with the cluster's GPU drivers. Always recommend a specific tag (e.g., `1.8.3`) matched to the GPU driver version.
- **NIM_MAX_MODEL_LEN**: NIM defaults to a very large context length that can cause KV cache OOM on smaller GPUs. Recommend setting `NIM_MAX_MODEL_LEN=16384` for T4/A10 GPUs.
- **GPU tolerations**: GPU nodes are almost always tainted in production. `/model-deploy` will automatically detect and add tolerations after deployment.

### Reference Documentation
- [supported-runtimes.md](../../docs/references/supported-runtimes.md) - NIM runtime capabilities and requirements
- [live-doc-lookup.md](../references/live-doc-lookup.md) - Protocol for fetching current RHOAI/NIM documentation

## Critical: Human-in-the-Loop Requirements

See [skill-conventions.md](../references/skill-conventions.md) for general HITL and security conventions.

**Skill-specific checkpoints:**
- Before creating each Secret: display manifest (credentials REDACTED), confirm
- Before creating Account CR: display manifest, confirm
- Before creating ConfigMap (if applicable): display manifest, confirm
- **NEVER** display actual NGC API key values in output

## Example Usage

See [nim-setup examples](../../docs/examples/nim-setup.md) for a complete first-time NIM setup walkthrough.

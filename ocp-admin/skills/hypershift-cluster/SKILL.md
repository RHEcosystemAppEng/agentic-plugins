---
name: hypershift-cluster
description: |
  Create, inspect, access, and destroy provider-neutral HyperShift hosted
  OpenShift clusters (guests) on an existing HyperShift management cluster, then
  deploy application code into the verified guest.

  Use when:
  - "Create a HyperShift hosted cluster / guest"
  - "Deploy my app into a hosted OpenShift guest"
  - "Check status of or access a hosted control plane"
  - "Tear down a HyperShift guest and verify cleanup"
  - "Install the HyperShift operator" (only when explicitly requested)

  Provider-neutral lifecycle over aws, kubevirt, agent, azure, gcp, none,
  openstack, and powervs using the installed hypershift or hcp CLI.

  NOT for:
  - ROSA service provisioning (`rosa create cluster`) → separate workflow
  - Assisted Installer cluster creation → use the cluster-creator skill
  - Creating the initial management cluster → out of scope
license: Apache-2.0
model: inherit
color: green
allowed-tools: Bash Read Write Edit Glob Grep
metadata:
  environment_vars:
    - KUBECONFIG
    - HYPERSHIFT_CONFIG
  destructive: true
---

# /hypershift-cluster Skill

Create a small development guest with an isolated Kubernetes API and worker nodes.
Use the existing HyperShift installation. Read [providers.md](references/providers.md)
for the selected provider and [operations.md](references/operations.md) for command
usage, readiness, deployment, recovery, and teardown. Research provenance and limits
are in [research.md](references/research.md).
If the user explicitly requests installing HyperShift, first read
[bootstrap.md](references/bootstrap.md). Do not bootstrap it implicitly during
ordinary guest creation.
For an explicitly requested operator installation **inside a guest**, read
[guest-operators.md](references/guest-operators.md). This is distinct from
installing HyperShift on management.
For building and iterating on local project code in the guest, read
[code-workflow.md](references/code-workflow.md). The agent and source workspace
remain local; the guest runs the deployed workload.
For mixed worker pools or accelerator workloads, read
[accelerators.md](references/accelerators.md). For requested inference measurements,
also read [inference-benchmarks.md](references/inference-benchmarks.md).

## When to Use This Skill

**Use when**:
- Creating a provider-neutral HyperShift hosted cluster (guest) on an existing management cluster
- Accessing, deploying application code into, or verifying a hosted guest
- Tearing down a guest and verifying cleanup of its provider resources
- Installing the HyperShift operator on management (only when explicitly requested)

**Do NOT use when**:
- Provisioning via ROSA (`rosa create cluster`) or the Assisted Installer → use the `/cluster-creator` skill instead
- Creating or recreating the initial management cluster → out of scope
- Listing or reporting on existing clusters → use the `/cluster-inventory` or `/cluster-report` skill instead

## Boundaries that change the workflow

- **Management** credentials manage `HostedCluster`, `NodePool`, and associated
  lifecycle resources. **Guest** credentials deploy and test code. Some providers
  also have an **infrastructure** cluster/account. Keep all three explicit.
- Hosted control planes consume management-cluster CPU, memory, storage, and
  networking. Their controllers create a control-plane namespace, usually
  `<hostedcluster-namespace>-<name>`. The management cluster cannot remain literally
  unchanged. Preserve its existing control plane, shared operators, configuration,
  unrelated namespaces, and other guests. Do not install/upgrade HyperShift or patch
  ingress, storage defaults, SCCs, or shared RBAC as a hidden workaround for missing
  prerequisites. Report the precise prerequisite for the administrator to prepare
  separately unless the user has explicitly requested that setup.
- Provider-neutral means a common lifecycle over provider-specific infrastructure.
  Never substitute `rosa create cluster`, Assisted Installer cluster creation, or a
  fake generic `HostedCluster` template for the chosen HyperShift provider workflow.
  HyperShift's **Agent provider** is infrastructure, distinct from the AI agent.
- `hypershift` is the upstream development CLI; `hcp` exposes a product CLI surface.
  Inspect the installed CLI's `create cluster <provider> --help` and matching version
  documentation. Supported providers and flags differ. Do not assume latest upstream
  documentation establishes support in the user's release.
- **`create cluster ... --render` is not a safe planning operation.** Provider
  completion can create cloud infrastructure/IAM before YAML is emitted. The helper's
  `plan` constructs a command locally without running the CLI. Rendering sensitive
  resources produces credentials and is not necessary for this workflow.
- Creating cloud resources costs money; destroying a guest deletes its data. Carry
  forward existing user authorization. If the concrete target, spend, or deletion
  exceeds that authorization, prepare the plan and ask only for the missing scope.
  Do not ask again for an operation already authorized for the same target and scope.

## Gather and prepare

Discover information from the user's files and read-only tools before asking for it.
Resolve helper paths relative to this skill directory (`$SKILL_DIR` in examples).
Requires a POSIX host (macOS/Linux), Python 3.10+, PyYAML 6, an `oc` client compatible
with the target cluster versions, and a compatible `hypershift` or `hcp` CLI.
Configured AWS cleanup verification also requires the AWS CLI.
The skill is portable without MCP tools. A connected Kubernetes tool is usable only
if it pins the same target context and keeps credential values out of output.

Collect:

- Existing management kubeconfig file, explicit context, and `kube-system` namespace
  UID obtained from that explicit context. Record version/distribution, installed
  HyperShift image/version, served CRD versions, compatible guest releases, and
  capacity/storage/network/policy constraints. Do not use ambient current-context.
- Provider; guest name and existing lifecycle namespace; pinned release image digest
  and worker architecture; pull-secret and optional SSH public-key **file paths**.
- Worker count/size, reachable API and ingress/DNS design, network CIDRs that fit
  provider routing, region/zones, and provider-specific prerequisites/credentials.
  Small does not mean zero resources: two workers are the starter example, not a
  universally supported minimum. Zero workers supports control-plane exploration,
  but does not yield an application-ready environment.
  For mixed pools, set `node_pools` expectations for every pool, including the base
  pool. `replicas` still controls the CLI's initial pool size; it is not the total
  expected topology. Additional pools need a separately reviewed creation step.
- Whether infra/IAM/DNS are new, reused, or shared; their ownership and cleanup
  plan; intended application namespace/code/image/tests and the desired lifetime.
  HyperShift does not provide ROSA's generic expiration contract: record a cleanup
  reminder or use the user's existing automation, without inventing a TTL feature.

Copy [profile.example.json](assets/profile.example.json) to a **private run directory**
(mode 0700), replace every example value, and adapt `create_args` / `destroy_args`
using provider help and [providers.md](references/providers.md). Use absolute file
paths and `--long-flag=value` tokens; do not put literal credentials into the profile.
The helper explicitly selects `SingleReplica` for both control plane and guest infra,
appropriate for a disposable development environment, without HA guarantees. If HA
is required, adapt that helper policy deliberately before creating anything.

## Workflow

**MCP Tool**: none — this skill is CLI/script-based (`hypershift`/`hcp`, `oc`, `aws`) and invokes no MCP tools. **Parameters**: every `hcp.py` subcommand takes `--profile <profile.json>` and a private `--state-dir`; subcommand flags are documented in [operations.md](references/operations.md). **Error handling**: see [operations.md](references/operations.md) for timeout and partial-failure recovery, and never label an unperformed check as passed.

### Step 1: Plan and preflight

Run `plan`, inspect `preflight`, and complete the selected provider's checks.
Preflight proves the target/CRDs/basic RBAC/CLI flags, **not** release compatibility,
capacity, cloud permissions, DNS reachability, or provider readiness. Record those
separately with evidence. Never label unperformed checks as passed.

### Step 2: Present the plan and create

Present a concise concrete plan: management identity, guest name/namespace,
   provider/region, release, worker resources, SingleReplica tradeoff, expected
   management/provider changes, reused resources, cleanup ownership, and cost scope.
   Execute `create --execute` within the user's authorized scope.

### Step 3: Observe readiness

Observe the actual command/session and cluster state. Use bounded `wait` or
   `status`; do not treat CLI success, kubeconfig publication, or `Available=True`
   alone as an application-ready cluster. Check current-generation availability,
   guest `/readyz`, Ready workers in each requested pool, advertised accelerator
   resources, guest ClusterVersion, and ClusterOperator conditions.
   Do not restart a launch merely because observation timed out.

### Step 4: Access the guest

Run `access` to retrieve the Secret referenced by `status.kubeconfig.name` into a
   private guest-only file. It checks TLS, the published guest API host/port, and a
   guest `kube-system` UID different from management; the saved HC/guest UIDs detect
   replacement. Never print kubeconfigs, passwords, Secret bodies, or credential logs.

### Step 5: Deploy application code (when requested)

When code deployment is requested, build/test the code, publish an image somewhere
   guest workers can pull **if that action is authorized**, then render manifests or
   the Helm/Kustomize output locally. Review namespaces, resources/probes, arbitrary
   UID compatibility, image references, and the guest's admission policy. Run `deploy`
   for discovery and server validation, then `deploy --execute` for the requested
   apply. It allows namespaced resources in a dedicated guest namespace. Cluster-wide
   CRDs/operators/RBAC need a separate reviewed guest plan with the same identity
   checks; follow `guest-operators.md` for an OLM installation. Do not widen the
   helper to silently admit platform changes.

### Step 6: Verify rollout

Verify rollout and an application-specific smoke test through the guest's explicit
kubeconfig and pinned context. A successful apply is not proof the application works.

### Step 7: Teardown (when requested)

If teardown was requested, record and review `inventory` before deletion; see
   [teardown.md](references/teardown.md) for ownership, storage, AWS configuration,
   verification and timeout recovery. Execute `destroy --execute` only for the
   authorized guest. `verify-cleanup` must confirm API and supported cloud cleanup;
   a successful destroy CLI exit is not sufficient. Never delete the shared lifecycle
   namespace, management cluster, operator, shared IAM/VPC/DNS, or finalizers by default.

Use `operations.md` for timeout and partial-failure recovery. After a create attempt,
reconcile existing provider resources before any retry. The local attempt receipt
intentionally blocks automatic reruns. Do not clear it to make a failing check pass.

## Report results

State the actual outcome: planned, submitted, reconciling, guest ready, application
verified, or cleanup verified. Include the provider and cluster identities, private
kubeconfig **path**, tested code/image, rollout/smoke-test results, unresolved
conditions, cleanup ownership, and next action. Distinguish offline/fake-CLI checks
from actual cluster tests. Never claim all providers work based on one provider's test.

## Dependencies

### Required MCP Servers
None — this skill is CLI/script-based and uses no MCP server.

### Required MCP Tools
None — the skill drives the `hypershift`/`hcp`, `oc`, and `aws` CLIs via Bash and local helper scripts.

### Required CLIs
- `oc` — management and guest cluster API access.
- `hypershift` or `hcp` — hosted cluster lifecycle (create/destroy). Inspect the installed `create cluster <provider> --help`; supported providers and flags vary by version.
- `aws` — read-only AWS inventory and cleanup verification (AWS provider teardown only).

### Helper Scripts
- [`hcp.py`](scripts/hcp.py) — profile-driven lifecycle: `plan`, `preflight`, `create`, `status`, `wait`, `access`, `verify-guest`, `deploy`, `inventory`, `verify-cleanup`. Previews are local; mutations require `--execute`.
- [`cleanup.py`](scripts/cleanup.py) — read-only AWS ownership/preservation inventory used by teardown verification.
- [`make_profile.py`](scripts/make_profile.py) — build a validated `profile.json`, resolving the management kubeconfig from `HYPERSHIFT_CONFIG` (or, with confirmation, `KUBECONFIG`) and deriving context + kube_system_uid from the cluster.

### Environment Variables
- `KUBECONFIG` / `HYPERSHIFT_CONFIG` — management kubeconfig resolution for `make_profile.py` (the skill itself uses the explicit path pinned in the profile, never an ambient context).

### Related Skills
- `/cluster-creator` — Assisted Installer cluster creation (distinct provisioning model).
- `/cluster-inventory` — list and inspect existing clusters.

### Reference Documentation
- [providers.md](references/providers.md) — provider selection and provider-specific create flags.
- [operations.md](references/operations.md) — command usage, readiness, deployment, recovery, teardown.
- [bootstrap.md](references/bootstrap.md) — explicit HyperShift operator installation on management.
- [guest-operators.md](references/guest-operators.md) — OLM operator installation inside a guest.
- [code-workflow.md](references/code-workflow.md) — build/test locally, render and deploy workload code to the guest.
- [accelerators.md](references/accelerators.md) — mixed/accelerator NodePools and readiness.
- [inference-benchmarks.md](references/inference-benchmarks.md) — requested inference measurements.
- [teardown.md](references/teardown.md) — destroy sequencing and cleanup verification.
- [research.md](references/research.md) — provenance and limits.

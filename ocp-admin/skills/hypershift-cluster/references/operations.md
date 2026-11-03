# Commands, validation, and recovery

`$SKILL_DIR` below is the absolute directory containing this skill's `SKILL.md`.
Use a private working directory for the profile, state, and credentials. Keep the
same `--state-dir` for every command against a guest. Python dependencies belong
in the agent's execution environment, not in the guest cluster.

## Prepare the target

Obtain the management fingerprint with a read-only command on the intended context:

```bash
oc --kubeconfig=/absolute/path/management.kubeconfig --context=management-context \
  get namespace kube-system -o jsonpath='{.metadata.uid}'
```

Place that UID into `management.kube_system_uid` in the profile. The namespace UID
is an identity fingerprint, not the OpenShift ClusterVersion clusterID. Pinning it
prevents a context name from silently selecting another cluster. A management
rebuild changes it and requires a deliberate new profile/state directory.

Use explicitly targeted read-only checks to inspect management version, operator
Deployment image/availability, CRD served versions, storage, quotas and scheduling
capacity, appropriate ingress/service exposure, and selected-provider requirements.
The operator namespace/deployment may differ under MCE; discover it rather than
assuming a fixed name. `hypershift version` can contact a cluster: if using it, pass
a private, explicitly pinned kubeconfig rather than relying on the ambient context.
Use matching release documentation and the operator's supported-versions data to
select a release image; resolve a chosen tag to a digest with `oc adm release info`
using explicit registry credentials as required. Never pick `latest` implicitly.

Check `oc version --client=true` before relying on the installed client. An old
client can perform some reads while lacking commands or behavior needed for a new
cluster. Match it to the management/guest releases using the
[OpenShift CLI compatibility guidance](https://docs.redhat.com/en/documentation/openshift_container_platform/4.20/html/cli_tools/openshift-cli-oc).
When a different client is needed, keep it in a private run tools directory,
verify its official download checksum, and prepend that directory to `PATH` for
the helper and follow-up commands. Preserve the user's existing binaries and
shell configuration. Record the selected client version in the live test report.

## Plan and launch

```bash
python3 "$SKILL_DIR/scripts/hcp.py" --profile /private/run/profile.json \
  plan
python3 "$SKILL_DIR/scripts/hcp.py" --profile /private/run/profile.json \
  --state-dir /private/run/state preflight
python3 "$SKILL_DIR/scripts/hcp.py" --profile /private/run/profile.json \
  --state-dir /private/run/state create --execute
```

`plan` runs no subprocesses, reads no cluster credentials, and creates no state.
It is a command preview, not a server dry-run or a price estimate. Creation without
`--execute` also returns a preview. In the profile, the starter's `create_args`
`["--cores=2", "--memory=6Gi"]` apply only to KubeVirt. Replace them for other
providers using their installed help. Provider arguments cannot override common
target, release, count, render, or force flags. They are passed as argv, never a shell.
Prefer credentials already defined in the management cluster. For AWS, set
`secret_creds` to the name of a Secret in the lifecycle namespace containing the
native `sts-creds`, `pull-secret`, and `base-domain` keys; the helper passes it to
the native AWS create and destroy commands with `--secret-creds=...` and never
reads the values.
Use local provider credential files only when no compatible in-cluster Secret or
pre-provisioned infrastructure/IAM configuration exists. Never put literal tokens
in argv/profile fields. Plans display provider arguments but redact no values supplied
by the user, so keep credential-bearing paths and names non-sensitive.

Creation requires an existing lifecycle namespace and installed CRDs. It does not
install the operator or alter shared management settings. The CLI creates normal
per-guest resources and, depending on provider/options, cloud infrastructure and
IAM. The helper supplies a private flattened management config for the chosen
context through `KUBECONFIG` because lifecycle CLIs do not consistently support
`--context` or `--kubeconfig`. Ambient Kubernetes configuration is not used.
Provider CLIs may still inherit cloud environment credentials/profile variables when
the provider requires them. Verify the chosen cloud account/project identity before
launch, and prefer management-cluster Secrets so workstation cloud credentials are
not required. External-provider profiles pin that identity in `cloud_identity`; the
helper checks the effective AWS, Azure, GCP, OpenStack or IBM Cloud identity before
mutation. Unsupported credential-selection flags are rejected rather than silently
using a second account or project. AWS profiles also require matching `--region`
provider arguments, and the `make_profile.py` builder requires
`--cloud-account-id` and `--cloud-region`.
For another guest on the same management cluster, use a separate profile and state
directory. Choose a new name and infra ID, verify its network CIDRs against existing
networks, and check cloud credential expiry for the expected operation duration.
Reusing shared HyperShift/OIDC/DNS setup does not make the previous guest's identity
receipt or per-guest infrastructure reusable.

Durable, non-secret lifecycle identity, create attempts, teardown inventory and
destroy receipts are stored in the management namespace as
`hypershift-lifecycle-<name>` (a ConfigMap keyed to the management UID, namespace
and guest name). Cross-host mutations use its Kubernetes `resourceVersion` as a
shared lock. The operator needs `get`, `create` and `update` permission for that
ConfigMap. A second authorized host may resume from a new private state directory
after independently passing the same management and cloud identity checks; local
files remain private diagnostics.

The helper stores sensitive CLI output in local mode-0600 files, with a mode-0700
state directory. Do not paste these logs into chat or commit them. `guest.kubeconfig`
is an admin credential; use shorter-lived/scoped guest credentials for later work
when available. Management kubeconfig exec plugins are trusted user inputs and may
require interactive authentication; guest credentials extracted by the helper must
be embedded and cannot execute auth plugins. This is checked both on extraction
and before reusing the saved guest kubeconfig.

## Observe readiness and access

```bash
python3 "$SKILL_DIR/scripts/hcp.py" --profile /private/run/profile.json \
  --state-dir /private/run/state status
python3 "$SKILL_DIR/scripts/hcp.py" --profile /private/run/profile.json \
  --state-dir /private/run/state wait --timeout 1800 --interval 20
python3 "$SKILL_DIR/scripts/hcp.py" --profile /private/run/profile.json \
  --state-dir /private/run/state access
```

Run long commands through the agent's asynchronous shell/session mechanism so it
can continue reporting progress. Poll the existing handle rather than launching a
second create. `wait` reports conditions every interval and has a finite deadline.
It requires current-generation HC availability, the published kubeconfig, reachable
guest `/readyz`, and `workers_ready=true`. Without `node_pools`, this means at least
`replicas` Ready, non-deleting nodes. With `node_pools`, every listed NodePool must
exist for this HC with the expected replica specification, and have enough Ready,
non-deleting guest nodes advertising the requested per-node extended resources.
Unexpected pools make the topology incomplete. Pool membership uses the exact
`hypershift.openshift.io/nodePool` node label; optional selectors retain that label.
These are expectations, not commands to create or resize pools. It does not
suppress network/authentication failures as ordinary waiting. Re-run `status` after
addressing such a failure; do not infer a failed launch from a failed observation.

After access, take the **saved** `guest_context` from private `state/identity.json`;
verify the guest and explicitly inspect:

```bash
python3 "$SKILL_DIR/scripts/hcp.py" --profile /private/run/profile.json \
  --state-dir /private/run/state verify-guest
oc --kubeconfig=/private/run/state/guest.kubeconfig --context=GUEST_CONTEXT \
  get clusterversion version
oc --kubeconfig=/private/run/state/guest.kubeconfig --context=GUEST_CONTEXT \
  get clusteroperators
```

Check ClusterVersion Available=True and Progressing=False, plus expected release,
and investigate Degraded/unavailable ClusterOperators. Record exceptions explicitly;
workers being Ready does not prove ingress/storage/registry is ready for the code.
Also require ClusterVersion Failing=False. The helper's `wait` ends when the guest
API and configured worker pools/resources are ready; it does **not** wait for these platform
checks. In the RHTAS live run, both workers were Ready while platform operators were
still initializing. Treat missing/Unknown operator availability as not yet verified.
Inspect bootstrap condition reasons and pending pods, then use a bounded observation
loop if the initial rollout is progressing. A bootstrap condition alone does not
justify recreating the guest. Report an actual platform exception if proceeding
with work that does not depend on the affected component.
Never run `oc config use-context` or merge guest credentials into the default file.

For a requested guest operator, continue with
[guest-operators.md](guest-operators.md) after these checks. Keep the helper's
ordinary workload scope restrictions intact.

## Deploy and test code

Build and test the user's project with its native tools. Choose a reachable image
registry and user-authorized publishing mechanism; do not rely on an enabled guest
internal registry, external ingress, or a management-cluster image build service.
Render Helm/Kustomize output locally into ordinary manifests before this helper:

```bash
python3 "$SKILL_DIR/scripts/hcp.py" --profile /private/run/profile.json \
  --state-dir /private/run/state deploy --manifest /private/run/rendered.yaml \
  --namespace app-dev
python3 "$SKILL_DIR/scripts/hcp.py" --profile /private/run/profile.json \
  --state-dir /private/run/state deploy --manifest /private/run/rendered.yaml \
  --namespace app-dev --execute
```

Preview mode requires the guest application namespace to exist for real server
validation. If absent, `--execute` creates it on the verified guest, then server
validates all workloads before their apply. A failed validation may leave an empty
application namespace. No cluster-wide resources, Kubernetes `List` wrappers,
multiple namespaces, or protected system namespaces are admitted by this helper.
Empty YAML documents and comment-only separators in rendered output are ignored;
the file must contain at least one Kubernetes object.
Use workload Deployments, Services, Routes, etc. in a dedicated namespace; the
helper queries the guest's live API discovery to determine resource scope. It does
not replace review of privileged pods, RBAC, images, or admission policy.

All direct follow-up commands must use the same guest kubeconfig and pinned context:

```bash
oc --kubeconfig=/private/run/state/guest.kubeconfig --context=GUEST_CONTEXT \
  --namespace=app-dev rollout status deployment/MY_APP --timeout=180s
```

Use the project's health check/integration tests. For a cluster without external
application routing, use a guest-targeted port-forward and test localhost. Record
image digest, deployment generation, rollout outcome and smoke-test result. Keep
port-forward process handles and stop them when done. Re-run `verify-guest` before
new mutation sequences or changing credentials. For rollback, apply the previous
reviewed guest manifests/image or use a guest-targeted rollout undo; never roll
back the management cluster to fix an application.

## Failure recovery

- **CLI failure or timeout:** a private error log may contain credentials. Inspect
  locally, redact before reporting. Check the exact HC, NodePools, control-plane
  namespace, and provider resources by recorded infra ID. A create attempt is
  recorded before invocation in the shared ConfigMap. It prevents automatic retries
  even if the HC never appeared: cloud/IAM setup may already exist. Only after
  inventory proves absence or a deliberate reuse/cleanup plan, run
  `create --resume --execute` from an authorized host. Do not assume no HC means
  no spend.
- **Pending control plane:** inspect HC condition reasons/messages privately,
  operator availability, target control-plane namespace pods/events/PVCs, DNS and
  endpoint publishing. Do not repair shared operator/configuration implicitly.
  For external endpoint DNS, check records in each intended public/private zone
  and resolution from the hosted control-plane namespace. Published records can
  coexist with cached NXDOMAIN answers; see the DNS guidance in
  [bootstrap.md](bootstrap.md). Preserve shared DNS while observing cache expiry.
- **Pending workers:** inspect only NodePools for `spec.clusterName` matching this
  HC; then provider machines/VMs or Agent inventory, image/architecture, quotas,
  ignition connectivity and node boot errors. No universal `NodePool Ready` condition
  is assumed; report actual conditions and guest node status.
- **Identity mismatch:** stop mutations. Inspect profile, kubeconfig contexts, HC
  UID and API host/port, and saved namespace UIDs. Do not auto-update fingerprints.
- **Apply failure:** inspect guest admission errors, namespace policy, image pull,
  SCC/arbitrary UID compatibility and application pods. Do not grant management or
  guest cluster-admin/SCC privileges as an automatic workaround.

## Destroy and prove cleanup

Read [teardown.md](teardown.md) for the ownership manifest, storage capture,
provider coverage, receipts and resume rules. Set the profile's `infra_id` from
the verified live HC before inventory. The inventory step is read-only.

```bash
python3 "$SKILL_DIR/scripts/hcp.py" --profile /private/run/profile.json \
  --state-dir /private/run/state inventory
python3 "$SKILL_DIR/scripts/hcp.py" --profile /private/run/profile.json \
  --state-dir /private/run/state plan --action destroy
python3 "$SKILL_DIR/scripts/hcp.py" --profile /private/run/profile.json \
  --state-dir /private/run/state destroy --cluster-grace-period 1800 --execute
python3 "$SKILL_DIR/scripts/hcp.py" --profile /private/run/profile.json \
  --state-dir /private/run/state verify-cleanup
```

Before destroy, record HC UID, `spec.infraID`, platform spec, owned resources, data
loss and reuse/preservation decisions. Set `destroy_args` from installed provider
help; creation arguments are not automatically reused for deletion. Missing
credentials or preservation choices can leak resources or remove shared infra.
The first destroy refuses an absent or deleting HC and requires the reviewed
inventory. `destroy --resume --execute` supports a failed/interrupted recorded
attempt after inspecting actual progress, with matching target, inventory digest
and provider arguments. A process lock prevents overlapping lifecycle operations,
including a native CLI surviving its parent. The configured AWS path can finish
provider cleanup after HC removal using the recorded infra ID, region and account;
other providers require the original HC or separate provider recovery. No receipt
means separate manual recovery; do not manufacture one or clear a guard. The helper
blocks `--force` and does not manually strip finalizers. A timeout may mean cleanup
is still active. A successful CLI attempt goes to `verify-cleanup`, not another destroy.

Verify HC, its NodePools, and its control-plane namespace disappear, and check the
provider's resources identified by infra ID, including IAM/OIDC, disks/snapshots,
load balancers, DNS records, machines/VMs and any externally provisioned workers.
Absence of a Kubernetes object is not proof of cloud cleanup. `verify-cleanup`
returns exit 2 for residual resources, preservation discrepancies or incomplete
coverage. Read/API/authentication failures remain errors, never absence. Repeat
read-only verification when eventual deletion is still progressing. Automatic cloud
verification currently covers a configured AWS ownership inventory; other providers
need separate provider checks and cannot receive an automated complete receipt.
Guest credentials are removed automatically only after complete verification.
Preserve non-secret ownership/identity records needed to investigate residual spend.

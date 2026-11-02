# Explicit HyperShift operator setup

Use this reference only when the user requests installing HyperShift on an
existing or currently installing management cluster. Initial management-cluster
provisioning remains a separate workflow. User authorization for operator setup
does not authorize recreating the management cluster or replacing its workloads.

## Wait for the intended management cluster

An installer directory with `metadata.json`, `.openshift_install.log`, and
`auth/kubeconfig` can describe a standalone OpenShift management-cluster install;
its kubeconfig is not automatically a hosted guest credential. Read only the
needed metadata and kubeconfig context/endpoint fields. Installer state, logs and
auth files may contain pull secrets, private keys and passwords; do not dump them.

If installation is already running, identify its actual process/session and
observe that launch. A directory, state file or old log alone does not prove the
installer is live. Poll the same handle and actual cluster state. An observation
deadline does not justify a new `create cluster` invocation. Do not change the
installer's files or restart it because a DNS/API probe timed out.

Before setup, require installation-complete evidence and healthy management API,
ClusterVersion and expected ClusterOperators/nodes. Pin the management namespace
UID through its explicit kubeconfig/context as in `operations.md`. Distinguish
local DNS caching from missing public records and from an unhealthy API backend.
Do not disable TLS verification to bypass these failures.

## Prepare a concrete install plan

Use the installed CLI's actual `install --help` and matching source/docs. Choose
an immutable operator image digest and a compatible CLI revision. The operator
determines supported guest versions; inspect its published `supported-versions`
ConfigMap after installation before selecting a guest release.
Verify that the digest is still fetchable immediately before installation. Upstream
development registry images can disappear after their mutable tag moves; a digest
in a previous run record is not evidence the image remains available. If it has
disappeared, select a published image and match its source revision again.

Render and review the **operator install** manifests locally where supported by
that CLI. This is a different code path from `create cluster --render`, which may
provision infrastructure. Confirm what the selected version's render command
does, protect any rendered Secrets in a mode-0600 private file, and report object
kinds/scope without displaying credential data.

The install can add cluster-wide CRDs, RBAC, priority classes, admission/conversion
webhooks and namespaced operator resources. Compare existing CRDs and controllers
first. Recent upstream installs coordinate ownership with OpenShift's Cluster CAPI
Operator using the `ClusterAPI` configuration and unmanaged CRD list. Preserve
that coordination; do not blindly apply conflicting CAPI schemas or force
ownership conflicts away. Make required shared API changes explicit in the plan.
Use server-side apply for CRD dry-runs and installation: large HostedCluster schemas
can exceed the client-side last-applied annotation size limit. If the bundle overlaps
management-owned APIs, compare served/stored versions and the selected provider's
requirements before changing them. In an AWS setup, existing unused IPAM APIs may
be preserved while installing only new CRDs. With a CLI that supports it, establish
the reviewed new CRDs first and use `install --install-scope=resources` for the
operator resources. Do not omit an API version required by the chosen provider or
overwrite management-owned schemas merely to make installation pass.

## AWS setup, when selected

Verify cloud identity against the actual management infrastructure and use an
explicit region; a failing default STS endpoint does not prove credentials are
invalid. Follow the [AWS quick setup](https://hypershift.pages.dev/getting-started/quick-setup/)
and [operator installation guide](https://hypershift.pages.dev/how-to/install/)
for the chosen revision rather than assuming every release exposes the same flags.

The AWS workflow needs an OIDC document bucket and appropriate operator access.
Keep the bucket owned by this setup separate from temporary installer bootstrap
assets. Allow anonymous reads of the required discovery/JWKS documents, not
credential files or arbitrary private objects. Never disable account-wide public
access controls as an incidental fix. Use provider roles where the management
identity setup and CLI support them; otherwise record the precise scope and
expiry of temporary credentials used for the test. Plan renewal before credentials
expire if the operator will remain in use.

When installing external-dns, constrain its domain filter and ownership ID to a
dedicated hosted-cluster subtree, and scope Route53 writes accordingly. Preserve
management API/ingress records and other guests. Record whether operator resources
are retained after guest teardown; destroying a test guest must not remove shared
operator infrastructure.
Verify that the configured domain filter selects an actual public hosted zone.
A dedicated subdomain beneath an existing parent zone may yield no matching zone
with the installed external-dns version. Create/tag a dedicated child zone and
delegate its NS records from the parent when needed, then scope operator writes to
the child zone. Do not broaden the domain filter or IAM writes across management
DNS as a workaround. Refresh external-dns's zone cache after creating the zone and
verify that it actually publishes the guest endpoint records.

Check guest endpoint DNS from both outside and inside the management VPC before
creating the guest. An existing private parent zone can shadow a public child zone
and return NXDOMAIN for otherwise working public endpoints. Prefer an endpoint
domain outside that private namespace when planning a new setup. For established
endpoints, one scoped solution is a dedicated private zone with the same name as
the public guest zone, associated only with the intended management VPC. Configure
the installed external-dns to maintain both guest zones, retaining the guest-only
domain filter, TXT ownership, explicit zone-ID filters and least-privilege IAM.
Verify its actual version supports this configuration; upstream install manifests
may hardcode `--aws-zone-type=public`, requiring a recorded operator-resource
adjustment. Preserve management parent-zone records and check the HostedCluster's
`ExternalDNSReachable` condition after propagation. Record this adjustment so a
future operator reinstall does not silently restore the public-only setting.
When adding a second zone after endpoints already exist, verify records in each
zone independently: aggregate desired-state comparison can overlook the empty
zone. If seeding is necessary, copy only the intended guest records and matching
TXT ownership markers using CREATE-only changes after proving the target is empty.
Verify subsequent controller synchronization and cleanup in both zones.
Allow existing negative DNS caches to expire before concluding a correct record
change failed. Inspect the relevant SOA TTL and minimum TTL; a new record does not
invalidate cached NXDOMAIN responses. Prefer creating/verifying zones before
launching endpoint consumers, and do not restart shared management DNS to clear a
single guest's cache. See [AWS's SOA and negative caching guidance](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/SOA-NSrecords.html).

## Install and verify

Carry forward the user's explicit setup authorization. After reviewing the exact
plan, validate manifests against the management API. Use the selected CLI's
supported install flow to preserve CRD establishment, CAPI coordination, certificate
generation and webhook readiness ordering. Wait for the operator rollout and
webhooks, then inspect served HC/NodePool APIs, supported guest versions and
provider-specific readiness.

Record a healthy management baseline after setup. Run the guest lifecycle from
`SKILL.md`, compare the management baseline after guest deployment, and report
installation success separately from guest creation and application success.
Record source revisions, image digests and actual validation outcomes; local
rendering is not proof that the operator works on a live cluster.

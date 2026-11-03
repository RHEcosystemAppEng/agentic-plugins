# Design evidence and validation scope

Research date: 2026-10-30. These are upstream project capabilities, not promises
that each provider is supported by a particular OpenShift/MCE product release.

## Reference format

The requested [ocp-admin pack](https://github.com/RHEcosystemAppEng/agentic-plugins/tree/main/ocp-admin)
was inspected at commit `53fa7d8ec99b613eaaf929524de7e391850d9e80`. Its useful format
is a domain pack with `AGENTS.md`, a `skills/<name>/SKILL.md` entrypoint,
progressively loaded references and executable helpers. This pack follows that
layout. The original's Assisted Installer/OCM MCP dependencies do not implement
generic HyperShift lifecycle operations, so they are not inherited. Catalog
publication and a specific marketplace owner/repository URL are not fabricated.

The [ROSA cluster-lifecycle pack](https://github.com/openshift-online/rosa-claude-plugins/tree/main/cluster-lifecycle-skills)
was inspected at commit `966fab7eec285f985841ed8e5a3a84e009e719bd`. It provides
create/monitor/access/delete workflow structure and a small Claude plugin manifest.
Its billing accounts, OCM environments, role names, automatic expiry conventions,
and ROSA-specific CLI calls are intentionally not carried into generic HyperShift.

## HyperShift facts that drive the design

Upstream repository inspected at commit `e43aa412a11af9c7b86e66d63abb1b0620d0761f`:

- [Architecture](https://hypershift.pages.dev/getting-started/onboarding/architecture/):
  the HyperShift operator watches management-side HostedClusters and NodePools,
  creates per-guest control-plane workloads, and gives each guest an independent
  Kubernetes API. Shared management capacity is still consumed; application isolation
  does not imply no management changes or no shared failure domains.
- [CLI registration](https://github.com/openshift/hypershift/blob/e43aa412a11af9c7b86e66d63abb1b0620d0761f/cmd/cluster/cluster.go)
  includes Agent, AWS, Azure, GCP, KubeVirt, None, OpenStack and PowerVS creation and
  destruction commands. Installed binaries/releases may expose a subset.
- [Core creation](https://github.com/openshift/hypershift/blob/e43aa412a11af9c7b86e66d63abb1b0620d0761f/cmd/cluster/core/create.go)
  validates and completes provider setup **before** rendering. It omits Secrets from
  render output unless `--render-sensitive` is used. Render output alone therefore
  is neither a side-effect-free preview nor always an apply-ready cluster definition.
- [AWS completion](https://github.com/openshift/hypershift/blob/e43aa412a11af9c7b86e66d63abb1b0620d0761f/cmd/cluster/aws/create.go)
  can create infra and IAM if corresponding JSON inputs are absent. This is why
  planning only constructs argv and provider readiness/ownership is reviewed separately.
- [HostedCluster API](https://github.com/openshift/hypershift/blob/e43aa412a11af9c7b86e66d63abb1b0620d0761f/api/hypershift/v1beta1/hostedcluster_types.go)
  publishes `status.kubeconfig.name` and `status.controlPlaneEndpoint`; conditions
  are generation-aware. Credentials must be extracted from the actual reference,
  rather than guessing `<name>-admin-kubeconfig`.
- [NodePool API](https://github.com/openshift/hypershift/blob/e43aa412a11af9c7b86e66d63abb1b0620d0761f/api/hypershift/v1beta1/nodepool_types.go)
  separates worker management from HC availability. The helper filters pools by
  `spec.clusterName` and verifies actual Ready guest nodes, rather than assuming a
  generic NodePool readiness condition.
- [Destroy lifecycle](https://github.com/openshift/hypershift/blob/e43aa412a11af9c7b86e66d63abb1b0620d0761f/cmd/cluster/core/destroy.go)
  coordinates finalizers and provider cleanup; a missing HC can trigger an
  infrastructure-only upstream path. The helper declines that path until an agent
  inventories the intended infra separately, and never force-clears finalizers.

See [providers.md](providers.md) for upstream provider guides. Several contain old
example versions; select commands using the installed CLI and actual served APIs.

## What must be verified on a real environment

Offline tests can prove command targeting, identity mismatch rejection, credential
file permissions, argument handling, and workload scope validation. They cannot
prove provider infrastructure, release compatibility, reconciliation, reachable DNS,
worker readiness, image pull, rollout/smoke tests, or resource cleanup.

For the first live test, the user supplies an existing HyperShift management
cluster plus provider prerequisites and private credential paths. Run the test
sequence in [operations.md](operations.md), preserve evidence in a redacted run
report, and improve the skill only from observed outcomes. After one provider
passes, other providers remain unverified until their own tests pass.

One AWS validation run completed guest creation/access, two application revisions,
identity rejection, and management-preservation comparisons against OpenShift
4.22.18. The result supports the workflow described here; it does not establish
support for every provider, release, or infrastructure configuration.

A second AWS validation installed an operator through the guest's OLM catalog.
The CSV and owned CRDs became ready, and management-preservation checks passed.
That validated operator installation only, not a configured signing service or
artifact signing. See the reusable workflow in [guest-operators.md](guest-operators.md).

An AWS teardown validation independently checked Kubernetes, compute, volumes,
networking, load balancers, guest IAM/OIDC, registry, and DNS cleanup while
preserving management and shared dependencies. This adds AWS teardown evidence;
it does not establish other providers' cleanup behavior.

## Development workflow practices

Reviewed a separate provider-lifecycle workflow with launcher/configuration helpers,
persistent task receipts, contributor/security guidance, and behavioral tests.
Transferable practices are explicit profile routing across follow-ups,
private generated state, atomic receipt replacement, pure previews, separate setup
and daily use, authentication errors distinguished from missing targets, verified
access, failure-oriented testing and review of commit candidates. Several already
exist in this helper; the local-code cycle is documented in
[code-workflow.md](code-workflow.md). The remote agent runtime, VM base-image
capture and automatic host restoration are not part of the HyperShift workflow.

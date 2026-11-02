# Install an operator inside a verified guest

Use this path when the user requests an operator on a hosted guest. HyperShift
operator setup on management uses `bootstrap.md` instead. Carry forward the user's
authorization for the requested guest operator and required dependencies; do not
invent an extra approval step for an already authorized installation.

## Target and package selection

Run helper `verify-guest` with the guest's existing profile/state directory. Use
the saved guest kubeconfig and context for every subsequent `oc` command. Check
platform health as described in `operations.md`, including ClusterVersion and
ClusterOperators. Record the management, HostedCluster and guest UIDs before any
cluster-wide guest changes.

Discover the package **in the target guest's catalog**, then inspect its source,
channels, current CSV, supported install modes and suggested namespace. For example:

```bash
oc --kubeconfig=/private/run/state/guest.kubeconfig --context=GUEST_CONTEXT \
  -n openshift-marketplace get packagemanifest PACKAGE_NAME -o json
```

Select a compatible channel and starting CSV from that actual catalog and matching
product guidance. A package found on a different guest is only a reference. Verify
that the operator/bundle images are accessible using the intended pull-secret file;
capture registry diagnostics privately. A successful public runtime image pull does
not prove access to an entitled operator repository.

## Prepare and execute OLM installation

Review the guest-only plan: install namespace, supported OperatorGroup scope,
Subscription, chosen CSV, dependencies and expected CRDs/RBAC/webhooks. The helper's
`deploy` rejects cluster-wide resources and protected namespaces. Use explicitly
guest-targeted `oc` for this reviewed operator plan; do not relax that restriction
or send the manifests to management.

An AllNamespaces-only package needs an OperatorGroup selecting all namespaces;
targeting only the install namespace is not equivalent. Respect an existing
OperatorGroup and installed package rather than creating conflicting objects.
For a fresh install, server-validate and create the namespace first, then
server-validate the namespaced OperatorGroup and Subscription.

Use a manual Subscription install plan when reviewing the resolved bundle before
installation. Pin `startingCSV` and a suitable version channel where available.
This is an OLM review mechanism, not a requirement to ask the user again. Wait for
the Subscription's actual `status.installPlanRef`; catalog readiness and bundle
unpacking can precede creation of an InstallPlan. Do not create duplicate
Subscriptions or approve a plan guessed from its name.

Inspect the resolved CSV list and resource plan, including dependencies and
cluster-wide privileges. Some OLM plans store a ConfigMap reference in each
`status.plan[].resource.manifest` instead of inline Kubernetes manifests. Resolve
the referenced bundle ConfigMap to inspect the real resources. In the tested OLM
version, `olm.contentEncoding=gzip+base64` identified compressed bundle content in
`binaryData`; honor the actual encoding rather than treating the reference as a
CSV. A bundle CSV namespace of `placeholder` is substituted by OLM with the install
namespace, not an instruction to create a namespace named `placeholder`.

Re-run guest identity verification before approval. Check the exact InstallPlan UID,
namespace and expected CSVs, server-validate the approval patch, then approve that
plan within the authorized scope. Observe its existing resources if installation
times out or fails; do not restart guest creation to recover an OLM rollout.

## Verify and report

Require InstallPlan Complete, the expected installed CSV in Succeeded phase, an
available operator Deployment with current observed generation, Ready operator pods
and Established owned CRDs. Inspect image-pull, admission, webhook and resource
failures on the guest. Do not grant broader SCC/RBAC privileges as an automatic fix.

Report the guest identity, operator version/channel, namespace, image digest and
actual outcome. Operator installation and operand deployment are separate results.
Only create operands needed for the user's request and with their required inputs;
do not create a signing service with invented identity-provider settings merely to
exercise the operator. Compare management and existing-guest health after the work.

## Observed operator-installation pattern, not universal defaults

One AWS validation used a two-worker OpenShift 4.22 guest. Its catalog supplied an
operator package and channel, suggested a dedicated namespace, and supported only
AllNamespaces mode. The reviewed OLM installation succeeded: one Ready controller
pod, owned CRDs became Established, and management-preservation checks passed.

No Securesign operand or OIDC provider was configured. A functioning signing
service therefore was not tested. Rediscover package versions and requirements on
future targets; this one AWS run does not validate other providers or all operators.

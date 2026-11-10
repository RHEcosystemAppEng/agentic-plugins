# Develop locally and deploy into a hosted guest

Use the local agent, source checkout and native build tools. The remote target is
the verified guest's Kubernetes API. Remote agent installation, agent sign-in,
workstation credential copying and VM session management are not prerequisites.

## Keep the target attached to the work

Resolve the intended management/guest from the user's private profile and existing
identity receipt. Carry the same absolute profile path, state directory, guest
kubeconfig, saved context and application namespace through every follow-up. If a
named guest is missing or authentication fails, report that actual state; do not
fall back to another guest or silently launch a replacement. Creating another guest
is a separate lifecycle action with its own profile, state and ownership plan.

Read-only inspection must not create cloud infrastructure. Reuse a healthy guest
for edit/deploy/test cycles instead of rebuilding it for each source change. Return
the target and explicit follow-up command so the next session can resume the same
work without relying on ambient shell context.

## Deliver the local revision

1. Inspect the requested source directory and its own contributor instructions.
   Preserve unrelated local changes. Use an isolated worktree when changes need
   separation; do not require one just to deploy an existing working tree.
2. Record the source revision and whether relevant files are modified/untracked.
   A Git commit alone does not identify a dirty deployment. For generated source
   bundles such as the smoke application's ConfigMap, record the content digest as
   well. Keep source, generated manifests and deployment evidence distinguishable.
3. Run the project's relevant local build/tests. Choose the image build/publish path
   based on the project and guest architecture. Publishing to a registry must be
   authorized by the task; do not infer permission to push source, create PRs or
   publish unrelated artifacts. Keep registry credentials out of source and command
   output; use scoped guest image-pull Secrets and references when needed.
4. Resolve a built/published image to an immutable digest that the guest can pull.
   Match the worker architecture. Do not rely on an enabled internal registry or
   use a build service on management as a hidden prerequisite. Record the actual
   delivered digest rather than treating a reused tag as a source identity.
5. Render the project's Helm/Kustomize or ordinary manifests locally. Review the
   namespace, image, resources, probes and OpenShift arbitrary-UID compatibility.
   Use helper `deploy` for server validation and `deploy --execute` for the requested
   apply. Namespace/bootstrap and scope behavior are in `operations.md`; a guest
   operator uses `guest-operators.md` instead.
6. Wait for the expected Deployment generation and replica rollout, then run the
   project's real application test. Keep the explicit guest kubeconfig/context on
   direct commands. For local access, bind an owned port-forward to `127.0.0.1` and
   close that process afterward. Do not open management/cloud firewall ports as a
   convenience when localhost access satisfies the task.

The ConfigMap-based smoke application validated this delivery loop without an
image publication. That does not establish a generic container build/push path for
every project. Use the requested project's own build and health checks.

## Retain a useful deployment receipt

Store deployment evidence with the private guest run state: management/HC/guest
UIDs, profile/state paths, namespace, source revision plus dirty/content identity,
image digest, manifest digest, workload UID/generation, test command/result and
timestamp. Include the previous delivered revision when rollback matters. Capture
only the evidence needed for diagnosis; credential-bearing logs remain private.

Report the deployed target, delivered revision, rollout/test result and exact access
command. On a later edit, verify the same guest again, rebuild/re-render and repeat
the delivery checks. A successful apply does not prove changed code reached running
pods. For rollback, deploy the previous reviewed guest artifact or use a targeted
rollout undo where appropriate; do not roll back management to repair application
code. Preserve the guest unless the user requests teardown.

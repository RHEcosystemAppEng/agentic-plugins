# Rapid HyperShift prototyping

Use this workflow for experimentation, application development, benchmarking,
or validating a new platform feature.

## The loop

1. Select or generate a private profile. Keep management kubeconfig, pull-secret,
   cloud credential files, and generated state outside the repository.
2. Run `plan` to inspect the exact provider command without contacting the cluster.
3. Run `preflight` and complete provider checks before creating billable resources.
4. Run `create --execute` with a unique cluster name and infrastructure ID.
5. Run bounded `wait`, then `access` and `verify-guest`. A successful CLI command
   or `Available=True` condition is not application readiness.
6. Build and test local code with its native tooling. Publish images only through
   an authorized registry, then deploy namespaced workloads with `deploy --execute`.
7. Run smoke tests, benchmarks, or revision comparisons through the pinned guest
   kubeconfig. Record release, image digests, topology, and test results.
8. Run `inventory`, review ownership and data-loss scope, then `destroy --execute`
   and `verify-cleanup` when the experiment is complete.

## Efficiency defaults

- Use two workers in one availability zone when exact worker count matters.
- Use `SingleReplica` control plane and guest infrastructure for disposable
  development environments; this is not an HA configuration.
- Reuse management, operator, OIDC, DNS, and storage setup only when ownership
  and compatibility are verified.
- Pin release digests and worker architecture. Never use `latest`.
- Choose the smallest worker type that satisfies the workload.
- Record a cleanup reminder or use existing automation; HyperShift has no universal
  expiration guarantee.

## Completion states

Reports distinguish **planned**, **submitted**, **reconciling**, **guest ready**,
**application verified**, and **cleanup verified**. Include unresolved conditions
and private kubeconfig paths, but never print kubeconfigs, passwords, tokens, or
credential-bearing logs.

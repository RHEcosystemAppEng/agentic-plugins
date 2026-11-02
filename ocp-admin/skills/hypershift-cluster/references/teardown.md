# Inventory, destroy, resume and verify

The upstream lifecycle CLI deletes the guest. The helper's cleanup module only
reads Kubernetes and AWS APIs; it does not issue cloud deletion commands.
Use the same private profile/state directory throughout. Destroy authorization
includes the selected guest's data; carry forward preservation decisions and
identify retained external data before executing. Never delete shared namespaces,
operators, networks or finalizers to make a check pass.

## Record ownership before deletion

Set `infra_id` from the live HC and run `inventory`. It records the management,
HC and guest identities, all target NodePools, guest PV/PVC identifiers and reclaim
policies, control-plane disks, load-balancer hosts and a management preservation
baseline. It captures metadata, not Secret bodies. Review the saved
`teardown-inventory.json` before destroy. Do not substitute name-prefix matching for
resource ownership. Inventory can be refreshed only before a destroy attempt.

Inventory normally verifies the guest API and reads all guest PVs/PVCs and Services.
If the guest never became reachable, `inventory --skip-guest` permits a **partial**
record for authorized deletion. It does not convert an authentication error into
empty storage. Partial coverage cannot produce an automated verified-cleanup receipt.
Use previous provider records and separate checks for that recovery case.

For data-bearing applications, record retention/export decisions while the guest
is reachable. When appropriate within the requested deletion scope, quiesce owned
workloads and let PVCs detach/delete before worker removal. Do not remove a retained
volume or snapshot simply because the guest is being destroyed. CSI detach and
provisioner backoff can continue after workers terminate; inspect PV/PVC,
VolumeAttachment, hosted CSI logs and HCP `CloudResourcesDestroyed` conditions.
Leave working controllers in place and never strip their finalizers as a shortcut.

## AWS ownership configuration

Add `aws_cleanup` to an AWS profile using the example in
[aws-cleanup.example.json](../assets/aws-cleanup.example.json). It is a profile
fragment, not a standalone profile. Use an explicit credentials file/profile,
account ID and region. The credentials file is AWS shared-credentials INI format
(access key, secret key and optional session token), not the CLI's STS JSON file.
The adapter uses that selected profile without ambient config, container, web-identity
or instance-metadata credential fallback. It checks STS caller account on capture,
destroy/resume and verification. Credential renewal at the
same file path is allowed; changing target/provider arguments or the ownership
manifest invalidates the receipt. `destroy_args` must explicitly specify the same
region; a supplied role ARN must name that account. Credential-secret and cross-account
VPC-owner deletion paths need a separate provider plan rather than this single-account
adapter. Check credential lifetime before a long deletion.

The adapter discovers instances, attached disks, tagged EBS volumes/snapshots,
NAT gateways, ENIs and elastic IPs from the exact infra tag and owned guest VPC.
Guest/control-plane EBS volume IDs are also tracked independently of tags.
Load balancers are discovered from the owned VPC and recorded Service hosts.
A VPC without the target's ownership tag is preserved; it is not swept for other
guests' instances or network resources. Resources in shared VPCs need exact recorded
IDs, target tags or Service hosts. Record additional known resources explicitly.

Supply exact `owned` and `preserve` identifiers for IAM users/roles/profiles, OIDC
providers, S3 buckets and hosted zones from the reviewed CLI/IAM/infra records.
Include shared management VPCs, DNS zones, the OIDC bucket and shared lifecycle IAM
principals in `preserve`. All supported resource-kind names are shown in the asset.
Do not put generated guest IAM into `owned` when a reviewed preservation flag keeps it.
Use bare Route53 zone IDs, without `/hostedzone/`.

`dns_records` enumerates owned name/type pairs in shared zones, including external-dns
TXT records. Other existing records in those zones are hashed and checked for
preservation. A name/type pair includes all routing-policy set identifiers at that
name. Shared zones in `preserve.hosted_zones` are also checked. `oidc_documents`
records a shared bucket plus the exact `<infra_id>/` prefix; its bucket is preserved
automatically. Versioned prefixes are checked for object versions and delete markers
as well as current objects. An empty/root/broader prefix is rejected.

Set `ownership_reviewed: true` only after the agent has reconciled these lists with
the actual provider inventory and the authorized preservation plan. This is an
ownership check, not an additional user approval step. Review the captured IDs too.
The adapter does not discover every possible external service: custom AMIs, backup
services, independent databases, other regions/accounts and non-EBS storage need
separate verification. Non-EBS PVs prevent an automated complete receipt. Do not
claim those are covered by the automated receipt.
Missing permissions, wrong account and failed reads stop verification.

## Execute and recover

```bash
python3 "$SKILL_DIR/scripts/hcp.py" --profile /private/run/profile.json \
  --state-dir /private/run/state destroy --cluster-grace-period 1800 --execute
```

The optional grace period is seconds; installed CLI help must advertise the native
flag. Planning/preview remains local and checks neither credentials nor state.
Only execute validates the receipt and installed CLI. State uses a POSIX advisory
lock inherited by the native CLI. Do not remove the lock file: closing processes
releases the lock, while deleting the file could defeat concurrency protection.
Preserve the process/session handle while observing long operations.

`destroy-operation.json` binds attempts to the inventory digest and records outcome
without credentials. On a failed CLI or lost observation, first inspect actual
HC/NodePool/HCP/cloud progress and private logs. Once no prior process owns the
lock, resume the **same** already-authorized deletion:

```bash
python3 "$SKILL_DIR/scripts/hcp.py" --profile /private/run/profile.json \
  --state-dir /private/run/state destroy --resume --cluster-grace-period 1800 --execute
```

The helper rejects replacement HCs, changed inventory/provider arguments and
unrecorded deletes. With the configured AWS adapter it can resume provider cleanup
after HC disappearance, using the pinned infra ID, region and account. Other
providers need the original HC still present or a separate provider recovery plan.
It never infers a missing target
from a cluster name. Do not manufacture receipts for old manual operations: inspect
and complete those with a separately reviewed provider recovery command.

## Verify completion

Run `verify-cleanup` after CLI success. It checks HC, NodePools, control-plane
namespace/PVs, management nodes/version/operators, other deployments/HC identities,
and the configured AWS resource inventory. Instances must be terminated and NAT
gateways deleted. Recorded/tagged disks, networking, IAM, DNS, buckets and OIDC
documents must be absent; explicitly shared resources must remain. Newly discovered
target-tagged/owned-VPC resources also prevent completion.

Exit 2 with `cleanup_verified: false` means cleanup or preservation/coverage checks
are unresolved. Inspect the named checks, wait if deletion is progressing and repeat
verification rather than blindly rerunning destroy. API failures exit 1; they are
not treated as absence. Only a complete result removes the local guest kubeconfig
and writes `cleanup-complete.json`. The provider-neutral API checks still run without
an AWS adapter, but unsupported/partial cloud coverage deliberately cannot emit that
complete receipt. Preserve the credentials until separate provider verification or
an intentional access-revocation action warrants removing them.

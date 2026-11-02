# Provider selection and prerequisites

Read only the chosen provider's linked guide and installed CLI help. These are
upstream mechanisms, not a Red Hat product support matrix. Match the operator,
CLI, management platform, guest release, worker architecture, and feature gates to
the actual environment. Do not install provider prerequisites as an incidental
part of creating a guest.

| Provider | Existing setup to verify | Provider arguments to derive from installed help | Cleanup boundary |
| --- | --- | --- | --- |
| `kubevirt` | OpenShift Virtualization/KubeVirt, VM capacity and storage, appropriate CNI, guest API/ingress exposure, wildcard DNS/routes if used | `--cores`, `--memory`; optional worker storage and external infrastructure kubeconfig/namespace | VMs/disks and hosted control plane; preserve virtualization operator, storage classes and shared routing |
| `agent` | Assisted Service/Agent resources, an agent namespace, enough discovered and approved compatible hosts, network/API reachability | `--agent-namespace`, `--base-domain`; service publishing and API address options depend on CLI | Guest and assigned machines; preserve Assisted Service and unrelated hosts/InfraEnvs |
| `aws` | AWS credentials/account/region, quotas, OIDC/IAM integration, DNS zone, routed subnets and API reachability | Installed auth flags, such as `--role-arn` with `--sts-creds`; `--region`, `--zones`, `--base-domain`; reusable `--infra-json`, `--iam-json` when supported | Distinguish generated per-guest IAM/VPC/DNS from shared resources; inspect preserve options |
| `azure` | Correct self-managed vs managed Azure path, credentials/subscription, resource groups, identity/OIDC, network and DNS | Use the matching Azure guide and `--help`; infra/IAM JSON, location, identity and resource group inputs vary | Preserve existing resource groups, networks, identities, DNS as appropriate |
| `gcp` | Supported operator/management setup (upstream guide uses GKE), project, network/PSC, WIF/IAM and service accounts, signer key, DNS and required feature gates | `--project`, `--region`, `--zone`, network/subnet and service-account/WIF inputs from the guide | Separate guest resources from shared WIF/network/projects/service accounts |
| `openstack` | Credentials/clouds.yaml, networks, quotas, image/flavor, API/ingress routing, operator provider support | `--openstack-credentials-file`, `--openstack-cloud`, `--openstack-node-flavor`, external network/floating IP inputs as needed | Owned servers/ports/volumes; preserve shared networks and pre-existing floating IPs |
| `powervs` | Supported PowerVS management/release/architecture combination, IBM Cloud credentials, region/zone/resource group, DNS and connectivity | Derive service instance/VPC/CIS and credentials flags from matching guide/help | Inventory generated vs shared service instances, VPC, DNS and connectivity resources |
| `none` | Explicitly user-provisioned workers, ignition, external networking/API/ingress and DNS plan | `--base-domain`, publishing/API options from help; manual worker provisioning is still needed | HC deletion does not prove externally provisioned machines/networks were removed |

For KubeVirt, upstream instructions include management wildcard route admission
and storage configuration. If missing, identify the needed administrator change;
do not patch shared ingress or storage as a hidden prerequisite. An external
infrastructure cluster needs its own explicit kubeconfig and existing namespace;
management identity checks do not validate that separate infrastructure target.
Have the agent verify it independently and record its UID and scope.

For Agent, allocating existing physical hosts is a real side effect; verify exactly
which hosts are eligible and authorized. Do not create an Assisted Installer
standalone control plane when the request is for a hosted control plane.

For AWS and Azure, supplying infra/IAM files changes who owns setup, but it does not
by itself guarantee destroy will preserve everything in those files. Inspect the
installed destroy implementation/help and select preservation flags explicitly.
For example, AWS has had `--preserve-iam`, and Azure has had resource-group
preservation. Do not assume those flags are available or sufficient in every version.
When the documented reuse path requires an explicit infrastructure ID, set the
profile's optional `infra_id` field to the ID from the actual infrastructure
inventory/JSON. The helper supplies `--infra-id` and checks it against a live HC
before subsequent operations; do not put a conflicting ID in provider arguments.

For AWS, the installed CLI may require a role ARN and STS credentials for cluster
creation even though `create iam cli-role` accepts `--aws-creds`. Check each
subcommand separately. Choose explicit zones for a small test: the upstream CLI
can create one NodePool per zone, with the requested replica count in each pool.
Two replicas across several zones can therefore mean more than two workers.
Use one verified available zone when the intended test is exactly two workers.

The `create_args` field permits different provider CLI options without changing
common lifecycle code. It is not an infrastructure provisioning abstraction and
cannot make an unsupported provider/release combination supported. For a provider
absent from the installed CLI, stop at planning and identify the required upstream
path instead of falling back to another cloud.

## Primary sources

- [KubeVirt](https://hypershift.pages.dev/how-to/kubevirt/create-kubevirt-cluster/)
- [Agent](https://hypershift.pages.dev/how-to/agent/create-agent-cluster/)
- [AWS infra and IAM separately](https://hypershift.pages.dev/how-to/aws/create-infra-iam-separately/)
- [Self-managed Azure](https://hypershift.pages.dev/how-to/azure/create-self-managed-azure-cluster/)
- [GCP](https://hypershift.pages.dev/how-to/gcp/create-gcp-hosted-cluster/)
- [OpenStack](https://hypershift.pages.dev/how-to/openstack/hostedcluster/)
- [PowerVS](https://hypershift.pages.dev/how-to/powervs/create-cluster-powervs/)
- [None/user-provisioned](https://hypershift.pages.dev/how-to/none/create-none-cluster/)
- [Upstream platform overview](https://hypershift.pages.dev/getting-started/onboarding/platforms/)

Some pages retain old version examples. Use the actual served CRD schema and
matching release docs for API/flag decisions, not the example's age or version floor.

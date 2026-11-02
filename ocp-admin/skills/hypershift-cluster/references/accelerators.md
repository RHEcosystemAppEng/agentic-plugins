# Mixed pools and accelerator workloads

Use this reference when the requested application needs GPUs or another accelerator.
Do not assume every hosted cluster has a device operator, driver, free accelerator,
matching CPU architecture or sufficient memory. Establish requirements from the
project before selecting workers. Operator installation belongs to the guest's
reviewed [operator workflow](guest-operators.md), not shared management bootstrap.

## Size the actual workload

Record a pool budget covering CPU requests/limits, host RAM, GPU model/count and
VRAM, root/PVC storage, image/model download space and architecture. Include runtime
overhead and KV cache/context/concurrency for inference; model weight size alone is
insufficient. Leave guest infrastructure/operator capacity on CPU workers and
management capacity for the hosted control plane. Separate application requirements
from a temporary same-model comparison control, if benchmarking was requested.

Check the cloud account/region, accelerator and ordinary-vCPU quotas, instance
offerings and current price through provider APIs. Offering/quotas do not guarantee
capacity. Fit network CIDRs to existing routing. Record the cost scope and intended
lifetime; preserve existing spend authorization rather than asking again for the
same resources. Do not provision an additional compute platform just to expand a
comparison beyond the user's intended scope.

## Create and identify pools

Use the installed provider CLI's NodePool help and matching implementation. Review
additional NodePool creation separately from the base HC plan. Do not assume any
`--render` operation is read-only: cluster rendering is explicitly unsafe for
planning, and other render paths need matching-version evidence before use.

Assign application placement labels and, when appropriate, a GPU taint. Keep CPU
inference on CPU workers and GPU inference on the accelerator pool. Give required
discovery/driver/device-plugin operands the tolerations they need; tolerating only
the model Pod does not make the GPU discoverable. Verify labels, taints, node
architecture and actual instance hardware after provisioning.

Add expectations for **all** HC NodePools to the private profile:

```json
"node_pools": [
  {"name": "example-cpu", "replicas": 2},
  {"name": "example-gpu", "replicas": 1, "resources": {"nvidia.com/gpu": 1}}
]
```

These are readiness expectations, not creation parameters. `replicas` at profile
top level continues to size the base CLI pool. Use actual NodePool names, including
any zone suffixes; do not invent pool membership from instance type. The helper
uses the exact `hypershift.openshift.io/nodePool` label on guest nodes. Confirm the
installed release supplies that label. Optional `node_selector` fields add placement
requirements and must retain that label with the exact pool name. Unlisted pools,
missing pools, wrong replica specs, deleting nodes and absent devices keep
`workers_ready` false. Ordinary single-pool profiles remain compatible.

## Verify the device stack and application

For NVIDIA on OpenShift, use the installed CSV's examples/schema and the
[NVIDIA installation guide](https://docs.nvidia.com/datacenter/cloud-native/openshift/latest/install-gpu-ocp.html).
Check the supported OpenShift/GPU/operator combination and driver toolkit/kernel
path for the actual release. Choose its supported device-plugin or DRA workflow;
do not combine incompatible policy modes. Keep privileged operator requirements
limited to their required namespaces and operands.

Require healthy discovery/driver/device-plugin operands and a ready vendor policy.
For the extended-resource path, inspect integer GPU capacity/allocatable and request
the device in the model Pod, using the resource name for that installation. This
follows [Kubernetes extended-resource scheduling](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#extended-resources).
Advertised capacity is not free capacity; account for existing allocations before
scheduling. Hardware VRAM is not host RAM, and a GPU resource count does not prove
VRAM size or absence of time-slicing. Check actual hardware/driver output and run a
device-allocated application request. DRA readiness needs its own claim/allocation
checks; the helper's integer resource check does not validate DRA claims.

Finish with verified model/application rollout and a real request. Record physical
hardware, sharing mode, runtime image digest, driver, resource allocations, operator
versions and test results. Do not infer application readiness from a Ready node or
successful operator installation alone. For a requested comparison, continue with
[inference-benchmarks.md](inference-benchmarks.md).

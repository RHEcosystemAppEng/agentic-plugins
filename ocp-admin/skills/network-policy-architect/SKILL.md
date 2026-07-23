---
name: network-policy-architect
description: |
  Design and validate Kubernetes NetworkPolicies following Zero Trust
  principles (NIST SP 800-207). Two-tier analysis — architecture review
  then live cluster verification — produces a verified implementation
  plan with dry-run results.

  Use when:
  - "Create NetworkPolicies for my namespace"
  - "Audit network isolation for this workload"
  - "Design network segmentation for a new application"
  - "Verify NetworkPolicies implement Zero Trust"
  - User mentions "network policy", "microsegmentation", "default-deny"

  NOT for Admin Network Policy (ANP) cluster-wide rules — those are
  cluster-admin infrastructure guardrails, not application-level
  microsegmentation. NOT for CNI plugin configuration or Multus
  secondary networks.
license: Apache-2.0
model: inherit
color: red
metadata:
  author: "proguski"
  version: "1.0"
---

# network-policy-architect Skill

**Audience:** Platform engineers and security architects responsible for Kubernetes network segmentation.

**Goal:** Design NetworkPolicies that enforce the principle of least privilege at the network layer — every connection must be explicitly justified and authorized.

This skill follows **NIST SP 800-207 (Zero Trust Architecture)** which states:

> *"Zero trust assumes there is no implicit trust granted to assets or user accounts based solely on their physical or network location."*

Recommendations carry the weight of a security audit. Every rule proposed must be justified. Every port opened must be documented. Every exception must be explicitly acknowledged by the user.

**MCP-First Approach**: This skill uses MCP tools from `openshift-administration` server. MCP tools have **absolute priority**.

**CLI Tools Policy**:
- **ALWAYS use MCP tools** when available
- **Last resort only**: CLI commands (`oc`, `kubectl`) may be attempted if no MCP alternative exists
- **Assume unavailable**: CLI tools are likely not installed in the execution environment

## Critical: Human-in-the-Loop Requirements

1. **Before applying NetworkPolicies (dry-run)**
   - Display the full YAML of each policy to be applied
   - Show which namespace will be affected
   - Ask: "Should I apply these policies for dry-run verification?"
   - Wait for explicit confirmation (yes/no)

2. **Before deleting dry-run policies**
   - List all policies to be removed
   - Ask: "Should I remove the dry-run policies?"
   - Wait for confirmation

3. **Default-deny exception**
   - If the user decides NOT to implement default-deny, require explicit written acknowledgment
   - Display: *"Without default-deny, any pod not matching an existing policy has UNRESTRICTED network access — full DNS, cross-namespace, and internet egress."*
   - Ask: "Do you acknowledge this deviation from NIST SP 800-207?"

**Never assume approval** — always wait for explicit confirmation before apply or delete operations.

## Prerequisites

**Required MCP Servers:** `openshift-administration` — Kubernetes/OpenShift cluster operations ([setup guide](../../README.md))

**Required MCP Tools** (all from `openshift-administration` server):
- `pods_list` — list pods in a namespace with status and labels
- `resources_list` — list resources by apiVersion/kind in a namespace
- `resources_get` — get a single resource by apiVersion/kind/name
- `resources_create_or_update` — apply NetworkPolicy YAML (for dry-run)
- `resources_delete` — remove dry-run NetworkPolicies

**Environment Variables:**
- `KUBECONFIG` — path to kubeconfig with access to the target cluster

**Verification Steps:**
1. Check `openshift-administration` MCP server is available
2. Verify `KUBECONFIG` is set: `test -n "$KUBECONFIG" && echo "✓ Set" || echo "✗ Missing"`
3. Verify cluster access by listing namespaces via `namespaces_list`
4. If any check fails → Human Notification Protocol

**Human Notification Protocol:**

When prerequisites fail:
1. **Stop immediately** — No tool calls
2. **Report error:**
   ```
   ❌ Cannot execute skill: MCP server `openshift-administration` unavailable
   📋 Setup: Configure the openshift MCP server in mcps.json with KUBECONFIG
   ```
3. **Request decision:** "How to proceed? (setup/skip/abort)"
4. **Wait for user input**

**Security:** Never display credential values. Only report whether KUBECONFIG is set.

## When to Use This Skill

Use when:
- Creating NetworkPolicies for a Kubernetes/OpenShift namespace
- Auditing existing network isolation for a workload
- Designing network segmentation for a new application deployment
- Verifying that NetworkPolicies correctly implement Zero Trust principles
- Implementing default-deny with per-pod allow rules

Do NOT use when:
- Configuring Admin Network Policies (ANPs) — those are cluster-admin infrastructure guardrails
- Configuring CNI plugins, Multus, or SR-IOV — use cluster-level networking skills
- Troubleshooting pod connectivity without existing policies — diagnose first, then design
- Managing firewall rules outside the cluster — this skill covers Kubernetes NetworkPolicy API only

## Workflow

This skill operates in **two mandatory tiers**. Both must be completed before producing the final implementation plan.

---

### Tier 1: Architecture Analysis (Offline)

**Objective:** Understand the application's communication requirements from source code, documentation, and deployment manifests — before touching a live cluster.

### Step 1: Identify All Pod Types

For each pod type in the namespace, document:
- Pod name pattern and label selectors
- Container names and exposed ports (containerPort)
- Whether it uses `hostNetwork` (critical — NetworkPolicies do NOT apply to hostNetwork pods)
- Whether it uses `hostPID` or `hostIPC`
- Service account and RBAC bindings (indicates K8s API access needs)
- Volume mounts — especially hostPath, CSI, and projected volumes

### Step 2: Identify All Services

For each service:
- Service name, type (ClusterIP/NodePort/LoadBalancer), ports
- Which pods are targeted (selector)
- Which routes expose the service externally

### Step 3: Map Communication Flows

For each pod type, determine:
- **Ingress:** Who connects TO this pod? From which namespace? On which port? Via service or direct?
- **Egress:** Where does this pod connect? DNS? K8s API? Other pods? External services? Other namespaces?
- **Protocol:** TCP or UDP? gRPC? HTTP/HTTPS? Unix socket (not network — no NP needed)?

### Step 4: Check for Operator-Managed NetworkPolicies

Some operators create and manage their own NetworkPolicies (e.g., RHBK operator creates `keycloak-network-policy`). These must NOT be duplicated or overridden — the operator will revert changes. Document them and design around them.

### Step 5: Identify Special Networking Cases

- **hostNetwork pods** — exempt from NetworkPolicies. Document as known exception.
- **Host-network source IPs** — pods connecting FROM hostNetwork (e.g., OCP router, spire-agent) use node IPs. `podSelector`/`namespaceSelector` cannot match them. Use port-only rules.
- **K8s API server** — endpoints are node IPs after DNAT. Port-only rules on 6443 (or 443 for ClusterIP service) are required.
- **OCP router** — uses `policy-group.network.openshift.io/ingress` namespace label for ingress matching.
- **DNS** — OCP uses CoreDNS on port 5353 (not 53). Target namespace: `openshift-dns`.

### Step 6: Draft Initial Rules

For each pod type, propose:
- Ingress rules with justification
- Egress rules with justification
- Ports, protocols, selectors, and namespace selectors

**Tier 1 output:** Present the communication map and draft rules to the user. Get confirmation before proceeding to Tier 2.

---

### Tier 2: Live Cluster Verification

**Objective:** Validate the draft rules against a running cluster. Confirm actual pod labels, ports, connections, and behavior.

**Prerequisites:** User must have an OCP/Kubernetes cluster with the target application deployed and healthy. The `openshift-administration` MCP server must be connected.

### Step 7: Verify Pod Inventory

**MCP Tool:** `pods_list` (from openshift-administration)

**Parameters:**
- `namespace`: "<namespace>" (string, target namespace to verify)

**Expected Output:** List of pods with name, status, and ready state.

**Error Handling:**
- If MCP server unavailable: → Human Notification Protocol
- If namespace not found: ask user to verify namespace name

### Step 8: Verify Pod Labels

**MCP Tool:** `resources_list` (from openshift-administration)

**Parameters:**
- `apiVersion`: "v1" (string)
- `kind`: "Pod" (string)
- `namespace`: "<namespace>" (string)

**Expected Output:** Full pod specs including `metadata.labels`. Confirm labels match the selectors drafted in Tier 1.

**Error Handling:**
- If labels differ from Tier 1 analysis: update draft rules to match actual labels

### Step 9: Verify Services and Endpoints

**MCP Tool:** `resources_list` (from openshift-administration)

**Parameters (Services):**
- `apiVersion`: "v1"
- `kind`: "Service"
- `namespace`: "<namespace>"

**Parameters (Endpoints):**
- `apiVersion`: "v1"
- `kind`: "Endpoints"
- `namespace`: "<namespace>"

**Expected Output:** Services with ports, selectors, and endpoint addresses.

**Error Handling:**
- If endpoints are empty: the service has no healthy backends — investigate before applying policies

### Step 10: Verify Routes

**MCP Tool:** `resources_list` (from openshift-administration)

**Parameters:**
- `apiVersion`: "route.openshift.io/v1"
- `kind`: "Route"
- `namespace`: "<namespace>"

**Expected Output:** Routes with host, TLS termination, and target service.

**Error Handling:**
- If no routes found and ingress expected: verify the application is exposed correctly

### Step 11: Verify Existing NetworkPolicies

**MCP Tool:** `resources_list` (from openshift-administration)

**Parameters:**
- `apiVersion`: "networking.k8s.io/v1"
- `kind`: "NetworkPolicy"
- `namespace`: "<namespace>"

**Expected Output:** Existing policies including operator-managed ones. Cross-reference with Tier 1 Step 4 findings.

**Error Handling:**
- If operator-managed policies found: document them, do not duplicate

### Step 12: Verify Container Ports and hostNetwork

**MCP Tool:** `resources_list` (from openshift-administration)

**Parameters (Deployments):**
- `apiVersion`: "apps/v1"
- `kind`: "Deployment"
- `namespace`: "<namespace>"

Repeat for `kind`: "StatefulSet" and `kind`: "DaemonSet".

**Expected Output:** Workload specs including `spec.template.spec.containers[].ports` and `spec.template.spec.hostNetwork`.

**Error Handling:**
- If hostNetwork=true: flag as NetworkPolicy exception — policies do not apply to these pods

### Step 13: Review Component Logs

**MCP Tool:** `pods_log` (from openshift-administration)

**Parameters:**
- `namespace`: "<namespace>"
- `name`: "<pod-name>" (string, specific pod name)
- `tail`: 100 (integer, recent lines)

For each pod type, check logs for:
- Successful connections (confirms required flows)
- Connection sources (IP addresses, namespaces)
- Error patterns (may reveal additional required flows)

**Error Handling:**
- If pod has multiple containers: check logs for each container

### Step 14: Apply Policies as Dry-Run

**Human Confirmation Required** — display all policies and wait for approval before applying.

**MCP Tool:** `resources_create_or_update` (from openshift-administration)

**Parameters:**
- `yaml`: "<full-networkpolicy-yaml>" (string, complete NetworkPolicy manifest)

Apply each proposed NetworkPolicy. Then verify:
- All pods remain Running and Ready (use `pods_list`)
- All routes respond (check via route host)
- All dependent applications in other namespaces still work
- Logs show no new connection errors (use `pods_log`)
- Force restart critical pods and verify recovery

### Step 15: Record Dry-Run Results

For each verification check, record PASS or FAIL with evidence.

### Step 16: Clean Up Dry-Run Policies

**Human Confirmation Required** — list policies and wait for approval.

**MCP Tool:** `resources_delete` (from openshift-administration)

**Parameters:**
- `apiVersion`: "networking.k8s.io/v1"
- `kind`: "NetworkPolicy"
- `name`: "<policy-name>" (string)
- `namespace`: "<namespace>" (string)

**Error Handling:**
- If delete fails: report the error and ask user for manual intervention

---

### Implementation Plan

After both tiers are complete, produce the final implementation plan.

**The plan MUST include:**

#### 1. Executive Summary
- Namespace secured
- Number of pod types covered
- Number of NetworkPolicies proposed
- Known exceptions (hostNetwork pods, operator-managed policies)

#### 2. Default-Deny Decision

**A default-deny NetworkPolicy MUST be included in every implementation plan.**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-in-namespace-<namespace>
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

If the user decides NOT to implement default-deny, this must be:
- Explicitly documented as a **security exception**
- Justified with a written reason
- Acknowledged by the user as a **deviation from NIST SP 800-207**
- Flagged as: *"Without default-deny, any pod not matching an existing policy has UNRESTRICTED network access — full DNS, cross-namespace, and internet egress."*

#### 3. Per-Pod Policy Rules

For each pod type, document:

| Field | Detail |
|---|---|
| **Pod type** | Name, labels, workload type |
| **Policy name** | Kubernetes NetworkPolicy name |
| **Ingress rules** | Each rule with: port, protocol, source (selector or port-only), **justification** |
| **Egress rules** | Each rule with: port, protocol, destination (selector or port-only), **justification** |
| **Why this rule exists** | Reference to the communication flow identified in Tier 1 |
| **What breaks if removed** | Specific failure mode |

#### 4. Known Exceptions

Document each exception:
- hostNetwork pods — which pods, why, what it means for network isolation
- Operator-managed policies — which operator, which policy, what it covers
- Port-only rules (no selector) — which rules, why selectors can't be used
- Any pod type intentionally left without a policy — justify

#### 5. Dry-Run Results

| Verification | Result | Evidence |
|---|---|---|
| All pods Running after NP applied | PASS/FAIL | `pods_list` output |
| Routes respond | PASS/FAIL | HTTP status codes |
| Dependent apps work | PASS/FAIL | Specific checks performed |
| Pod restart recovery | PASS/FAIL | Logs showing re-attestation/reconnection |
| No new errors in logs | PASS/FAIL | Log excerpts |

#### 6. Implementation Approach

Recommend the deployment method:
- **Externalized chart** — if the app uses a Helm chart, add NP templates to the chart with values-based configuration (default disabled). Users enable via `extraValueFiles` in their pattern.
- **Direct manifests** — if the app doesn't use a chart or for pattern-specific policies.
- **Operator-managed** — if an operator should own the policies (rare, for operators you control).

#### 7. NIST SP 800-207 Alignment

Map each policy to Zero Trust principles:
- **Least privilege** — only explicitly required connections are allowed
- **Assume breach** — default-deny limits blast radius of a compromised pod
- **Microsegmentation** — per-pod policies, not per-namespace
- **No implicit trust** — cross-namespace and internet access explicitly denied unless justified

### Strict Rules

1. **Never skip Tier 2.** Architecture analysis alone is insufficient — live verification catches configuration drift, operator-added resources, and undocumented connections.
2. **Never skip default-deny.** If the user doesn't want it, document it as a security exception — don't silently omit it.
3. **Justify every open port.** "It might be needed" is not a justification. Every ingress and egress rule must trace back to an observed communication flow.
4. **Document every exception.** hostNetwork, port-only rules, operator-managed policies — all must be explicitly called out with explanations.
5. **Test before recommending.** The dry-run is mandatory. Untested policies are proposals, not recommendations.
6. **OVN-Kubernetes awareness.** On OpenShift, understand OVN-K-specific behaviors: policy-group labels for router ingress, port 5353 for DNS (not 53), DNAT for K8s API, transit IPs for hostNetwork pods.
7. **Helm template conditions.** When creating NetworkPolicy templates gated by values (e.g., `enabled: true`), always use `(eq (.Values.field | toString) "true")` — not bare `.Values.field`. Helm overrides via `extraValueFiles` and pattern frameworks often pass booleans as strings (`"true"` not `true`). Bare boolean evaluation fails silently when the value is a string, causing policies to not render. Apply `| toString` consistently to ALL condition halves in `{{- if and ... }}` expressions.
8. **MCP tools first.** Always use MCP tools from `openshift-administration` for cluster operations. Do not use `oc` or `kubectl` CLI commands unless no MCP alternative exists.

## Dependencies

### Required MCP Servers
- `openshift-administration` — Kubernetes/OpenShift cluster operations for resource queries, policy application, and log inspection ([setup guide](../../README.md))

### Required MCP Tools
- `pods_list` (from openshift-administration) — list pods with status and labels
  - Parameters: namespace
- `resources_list` (from openshift-administration) — list resources by apiVersion/kind
  - Parameters: apiVersion, kind, namespace
- `resources_get` (from openshift-administration) — get single resource
  - Parameters: apiVersion, kind, name, namespace
- `resources_create_or_update` (from openshift-administration) — apply NetworkPolicy YAML
  - Parameters: yaml
- `resources_delete` (from openshift-administration) — delete NetworkPolicy
  - Parameters: apiVersion, kind, name, namespace
- `pods_log` (from openshift-administration) — read pod logs
  - Parameters: namespace, name, tail

### Related Skills
- `/cluster-report` — use for multi-cluster health overview before designing policies

### Reference Documentation
**Official:** [Kubernetes NetworkPolicy API](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
**Official:** [OpenShift Networking - NetworkPolicy](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/networking/network-policy)
**Official:** [NIST SP 800-207 - Zero Trust Architecture](https://nvlpubs.nist.gov/nistpubs/specialpublications/NIST.SP.800-207.pdf)
**Official:** [Admin Network Policy API](https://network-policy-api.sigs.k8s.io/)

## Example Usage

**User:** "Create NetworkPolicies for the qtodo namespace following Zero Trust principles"

**Skill response:**
1. Tier 1: Analyzes qtodo source code and Helm chart, identifies pods (qtodo-app, qtodo-db), services (qtodo, qtodo-db), routes, and communication flows (ingress from router, egress to DB/DNS/Keycloak/Vault).
2. Presents communication map and draft rules for user review.
3. Tier 2: Connects to the cluster via MCP, verifies pod labels, services, and existing policies. Applies draft policies as dry-run, verifies all pods healthy, routes respond, and logs show no errors.
4. Produces the final implementation plan with default-deny, per-pod rules, exceptions, dry-run results, and NIST alignment.

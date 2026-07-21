---
title: Multi-Cluster Authentication with Service Account Tokens
category: authentication
sources:
  - title: Understanding authentication
    url: https://docs.openshift.com/container-platform/latest/authentication/understanding-authentication.html
    date_accessed: 2026-03-31
  - title: Using service accounts
    url: https://docs.openshift.com/container-platform/latest/authentication/using-service-accounts-in-applications.html
    date_accessed: 2026-03-31
  - title: Advanced Cluster Management for Kubernetes
    url: https://access.redhat.com/documentation/en-us/red_hat_advanced_cluster_management_for_kubernetes
    date_accessed: 2026-03-31
tags: [multi-cluster, authentication, service-accounts, kubeconfig, cluster-report]
semantic_keywords: [multi-cluster authentication, service account tokens, long-lived tokens, non-interactive auth, merged kubeconfig, fleet authentication]
use_cases: [cluster-report, multi-cluster-management, fleet-operations]
related_docs: [credentials-management.md, rbac.md, quick-reference.md]
last_updated: 2026-03-31
---

# Multi-Cluster Authentication with Service Account Tokens

Set up non-interactive, long-lived authentication for running `cluster-report` across many OpenShift clusters without repeated `oc login` sessions.

## Overview

The `cluster-report` skill requires valid kubeconfig contexts for every cluster it reports on. Interactive `oc login --web` opens a browser for each cluster and produces tokens that expire in ~24 hours which make it difficult to do at scale.

**Solution**: Create a read-only ServiceAccount on each cluster with a non-expiring token. A builder script assembles these tokens into a single merged kubeconfig that the skill uses unchanged.

## Prerequisites

- `oc` or `kubectl` CLI
- `python3` (stdlib only, no extra packages)
- `cluster-admin` access on each target cluster (one-time setup only)

## Quick Start (Automated)

If you're currently logged into all the clusters you would like to get a report for via `oc login`:

```bash
# Step 1: Setup — applies RBAC to each cluster, extracts SA tokens
python3 scripts/build-kubeconfig.py setup --all-contexts

# Step 2: Build — assembles a merged kubeconfig from the inventory
python3 scripts/build-kubeconfig.py \
  build --clusters ~/.ocp-clusters/clusters.json --verify

# Step 3: Use — export and run the skill
export KUBECONFIG=/tmp/cluster-report-kubeconfig
# Then in Claude Code use the skill: /cluster-report
```

After the one-time setup, only Steps 2–3 are needed for future report sessions.

## Manual Setup (Per Cluster)

If you prefer to set up each cluster individually:

### 1. Apply RBAC

> **Required permissions**: The manifest creates cluster-scoped resources (ClusterRole, ClusterRoleBinding), so the user applying it needs `cluster-admin` privileges. This is a one-time setup step.

```bash
oc login <cluster-api-url>
oc apply -f ocp-admin/scripts/cluster-report/cluster-reporter-rbac.yaml
```

This creates:

- Namespace `cluster-reporter-system`
- ServiceAccount `cluster-reporter` with a read-only ClusterRole
- ClusterRoleBinding `cluster-reporter-binding` (binds the SA to the ClusterRole)
- Token Secret `cluster-reporter-token` (non-expiring)

### 2. Extract the Token

```bash
oc get secret cluster-reporter-token -n cluster-reporter-system \
  -o jsonpath='{.data.token}' | base64 -d
```

Save this token securely. It grants read-only access to nodes, pods, namespaces, projects, cluster version, and metrics.

> **AI Safety**: Never display token values in conversation output. Verify tokens are set, but never print or echo their contents.

### 3. Add to Inventory File

Create or edit `~/.ocp-clusters/clusters.json`:

```json
{
  "clusters": [
    {
      "name": "prod-us-east",
      "api_url": "https://api.prod-us-east.example.com:6443",
      "token": "sha256~your-token-here"
    }
  ]
}
```

Set permissions: `chmod 600 ~/.ocp-clusters/clusters.json`

### 4. Build Kubeconfig

```bash
python3 scripts/build-kubeconfig.py \
  build --clusters ~/.ocp-clusters/clusters.json --output ~/.kube/cluster-report-kubeconfig
```

## RBAC Permissions

The `cluster-reporter-readonly` ClusterRole grants the minimum permissions required by the `cluster-report` skill:


| Resource                | API Group            | Verbs     | Used By                                                       |
| ----------------------- | -------------------- | --------- | ------------------------------------------------------------- |
| nodes, namespaces, pods | core                 | get, list | `nodes_top`, `resources_list`, `namespaces_list`, `pods_list` |
| clusterversions         | config.openshift.io  | get       | `resources_get` (OpenShift verification)                      |
| projects                | project.openshift.io | list      | `projects_list`                                               |
| nodes, pods (metrics)   | metrics.k8s.io       | get, list | `nodes_top`                                                   |


No create, update, delete, or watch permissions are granted.

## Clusters Inventory Format

The inventory file (`clusters.json`) supports two token modes:

### Inline Tokens (Simple)

```json
{
  "clusters": [
    {
      "name": "prod-us-east",
      "api_url": "https://api.prod-us-east.example.com:6443",
      "token": "sha256~abc123..."
    }
  ]
}
```

The file itself contains secrets — keep it out of git and set `chmod 600`.

### Environment Variable References (More Secure)

```json
{
  "clusters": [
    {
      "name": "prod-us-east",
      "api_url": "https://api.prod-us-east.example.com:6443",
      "token_env": "CLUSTER_TOKEN_PROD_US_EAST"
    }
  ]
}
```

The file contains no secrets. Load tokens into environment variables from your secrets manager before running `--build`.

### Optional: CA Certificate

```json
{
  "clusters": [
    {
      "name": "prod-us-east",
      "api_url": "https://api.prod-us-east.example.com:6443",
      "token": "sha256~abc123...",
      "ca_cert": "/path/to/prod-us-east-ca.crt"
    }
  ]
}
```

If `ca_cert` is omitted, TLS verification is skipped (`--insecure-skip-tls-verify`).

## Script Reference

### `setup` Subcommand

```bash
python3 build-kubeconfig.py setup [OPTIONS]
```


| Flag                        | Description                   | Default                         |
| --------------------------- | ----------------------------- | ------------------------------- |
| `--all-contexts`            | Setup all kubeconfig contexts | Lists contexts and exits        |
| `--contexts ctx1,ctx2`      | Setup only specified contexts | —                               |
| `--output-inventory <path>` | Inventory file path           | `~/.ocp-clusters/clusters.json` |


Behavior:

- Applies `cluster-reporter-rbac.yaml` to each cluster
- Waits up to 15 seconds for the token Secret to populate
- Extracts and saves the token to the inventory file
- Skips unreachable clusters with an error message
- Appends to existing inventory (deduplicates by name)

### `build` Subcommand

```bash
python3 build-kubeconfig.py build --clusters <path> [OPTIONS]
```


| Flag                | Description                      | Default                          |
| ------------------- | -------------------------------- | -------------------------------- |
| `--clusters <path>` | Inventory file path (required)   | —                                |
| `--output <path>`   | Kubeconfig output path           | `/tmp/cluster-report-kubeconfig` |
| `--verify`          | Test each context after building | Off                              |


Behavior:

- Reads inventory, resolves tokens (inline or env var)
- Builds kubeconfig with `kubectl config set-cluster/set-credentials/set-context`
- Partial success: continues on individual failures
- `--verify` tests each context with `cluster-info`
- Outputs JSON summary with success/error counts

## Token Rotation

SA token Secrets do not expire, but you may want to rotate them periodically:

```bash
oc delete secret cluster-reporter-token -n cluster-reporter-system
oc apply -f ocp-admin/scripts/cluster-report/cluster-reporter-rbac.yaml

oc get secret cluster-reporter-token -n cluster-reporter-system \
  -o jsonpath='{.data.token}' | base64 -d

python3 build-kubeconfig.py build --clusters ~/.ocp-clusters/clusters.json --verify
```

To detect expired or invalid tokens:

```bash
python3 build-kubeconfig.py build --clusters ~/.ocp-clusters/clusters.json --verify
```

## Security Best Practices

1. **Never commit tokens to git** — add `clusters.json` to `.gitignore`
2. **File permissions** — `chmod 600` on both `clusters.json` and the generated kubeconfig
3. **Prefer `token_env`** — store actual tokens in a secrets manager, not in files
4. **Minimum RBAC** — the ClusterRole grants read-only access only
5. **Dedicated namespace** — the SA lives in `cluster-reporter-system`, not `kube-system`
6. **Generated kubeconfig is ephemeral** — `/tmp/` is fine for session use; for persistent storage use `~/.kube/` with `chmod 600`
7. **Never display tokens in AI conversations** — verify tokens are set but never print, echo, or expose their values in output

## Troubleshooting


| Problem                                  | Cause                                     | Fix                                                           |
| ---------------------------------------- | ----------------------------------------- | ------------------------------------------------------------- |
| `--setup` skips a cluster                | Not logged in or auth expired             | `oc login <api-url>` first, then re-run setup                 |
| `--verify` fails for a cluster           | Token expired or Secret deleted           | Re-run `--setup --contexts <ctx>` for that cluster            |
| `cluster-report` shows 401 for a cluster | Token invalid                             | Same as above — re-run setup for that cluster                 |
| `cluster-report` shows 403               | SA missing permissions                    | Re-apply `cluster-reporter-rbac.yaml` on that cluster         |
| Token Secret not populated               | Token controller slow or SA doesn't exist | Wait and retry; verify SA exists in `cluster-reporter-system` |
| `--build` says "env var not set"         | Using `token_env` but env not loaded      | Export the token env vars before running `--build`            |



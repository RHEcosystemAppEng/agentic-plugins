# Red Hat Developer Agent Plugin

A Claude Code plugin for building and deploying applications on Red Hat platforms.

## Skills

| Command                  | Description                                                                                |
| ------------------------ | ------------------------------------------------------------------------------------------ |
| `/detect-project`      | Analyze project to detect language, framework, and version                                 |
| `/recommend-image`     | Recommend optimal S2I builder or base image                                                |
| `/s2i-build`           | Build container images using Source-to-Image on OpenShift                                  |
| `/deploy`              | Deploy container images to OpenShift with Service and Route                                |
| `/helm-deploy`         | Deploy applications using Helm charts                                                      |
| `/rhel-deploy`         | Deploy to standalone RHEL/Fedora systems via SSH                                           |
| `/containerize-deploy` | End-to-end workflow from source to running app (use if not sure which strategy to choose)) |

### Troubleshooting

| Command              | Description                                                                                |
| -------------------- | ------------------------------------------------------------------------------------------ |
| `/debug-pod`         | Diagnose pod failures on OpenShift (CrashLoopBackOff, ImagePullBackOff, OOMKilled, pending pods) |
| `/debug-build`       | Diagnose OpenShift build failures (S2I builds, Docker/Podman builds, BuildConfig issues)   |
| `/debug-pipeline`    | Diagnose OpenShift Pipelines (Tekton) CI/CD failures (PipelineRun, TaskRun, step errors, workspaces) |
| `/debug-network`     | Diagnose OpenShift service connectivity (DNS, endpoints, routes, network policies)          |
| `/debug-container`   | Diagnose local Podman/Docker container issues (startup failures, OOM kills, image pull errors) |
| `/debug-rhel`        | Diagnose RHEL system issues (systemd failures, SELinux denials, firewall blocking)         |

### Environment

| Command                  | Description                                                                            |
| ------------------------ | -------------------------------------------------------------------------------------- |
| `/validate-environment`  | Check required tools and environment setup (oc, helm, podman, git, cluster connectivity) |

## Prerequisites

- OpenShift cluster access (for S2I and OpenShift deployments)
- Podman installed locally
- GitHub personal access token (for GitHub integration)
- Red Hat Insights service account with Client ID and Secret (optional, for vulnerability and advisor data in `/debug-rhel` and `/rhel-deploy`)

## MCP Servers

- **openshift** - OpenShift cluster management and Helm deployments
- **podman** - Container image management and local builds
- **github** - Repository browsing and code analysis
- **lightspeed** - Red Hat Insights data (vulnerability, advisor, inventory, planning) — optional

> **Container UID mapping**: The openshift MCP server uses `--userns=keep-id:uid=65532,gid=65532` to map the host user to the container's non-root UID (65532). This allows the container to read `chmod 600` files like `KUBECONFIG` without weakening file permissions. **macOS users**: Podman runs inside a VM on macOS — this flag may cause startup failures. If the MCP server fails to start, remove the `--userns` line from `mcps.json`.

## Supported Languages

Node.js, Python, Java, Go, Ruby, .NET, PHP, Perl

## Installation

Add this plugin to your Claude Code configuration.

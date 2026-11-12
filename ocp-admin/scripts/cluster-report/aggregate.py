#!/usr/bin/env python3

import json
import sys


def parse_cpu(value):
    if value is None:
        return 0.0
    s = str(value).strip()
    if s.endswith("m"):
        return float(s[:-1]) / 1000.0
    if s.endswith("n"):
        return float(s[:-1]) / 1e9
    if s.endswith("u"):
        return float(s[:-1]) / 1e6
    return float(s)


def parse_memory(value):
    if value is None:
        return 0.0
    s = str(value).strip()
    multipliers = {
        "Ki": 1024,
        "Mi": 1024 ** 2,
        "Gi": 1024 ** 3,
        "Ti": 1024 ** 4,
        "K": 1000,
        "M": 1000 ** 2,
        "G": 1000 ** 3,
        "T": 1000 ** 4,
    }
    for suffix, mult in sorted(multipliers.items(), key=lambda x: -len(x[0])):
        if s.endswith(suffix):
            num = float(s[: -len(suffix)])
            return (num * mult) / (1024 ** 3)
    return float(s) / (1024 ** 3)


def detect_node_role(labels):
    if not labels:
        return "worker"
    prefix = "node-role.kubernetes.io/"
    roles = []
    for key in labels:
        if key.startswith(prefix):
            role = key[len(prefix):]
            if role:
                roles.append(role)
    if not roles:
        return "worker"
    priority = ["control-plane", "master", "infra", "worker"]
    for p in priority:
        if p in roles:
            return p
    return roles[0]


GPU_KEYS = ["nvidia.com/gpu", "amd.com/gpu", "intel.com/gpu"]


def detect_gpus(allocatable):
    if not allocatable:
        return 0, ""
    for key in GPU_KEYS:
        val = allocatable.get(key)
        if val is not None:
            count = int(val)
            if count > 0:
                return count, key
    return 0, ""


def parse_tabular(text):
    if not text or not isinstance(text, str):
        return []

    lines = text.splitlines()
    non_blank = [line for line in lines if line.strip()]
    if len(non_blank) < 2:
        return []

    header_line = non_blank[0]
    data_lines = non_blank[1:]

    starts = [0]
    i = 0
    while i < len(header_line):
        if header_line[i] == " ":
            space_start = i
            while i < len(header_line) and header_line[i] == " ":
                i += 1
            if i < len(header_line) and (i - space_start) >= 2:
                starts.append(i)
        else:
            i += 1

    headers = []
    for idx, start in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else len(header_line)
        headers.append(header_line[start:end].strip())

    result = []
    for line in data_lines:
        row = {}
        for idx, start in enumerate(starts):
            end = starts[idx + 1] if idx + 1 < len(starts) else len(line)
            value = line[start:end].strip() if start < len(line) else ""
            row[headers[idx]] = value
        result.append(row)

    return result


def parse_labels_string(labels_str):
    if not labels_str or labels_str == "<none>":
        return {}
    result = {}
    for item in labels_str.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" in item:
            key, val = item.split("=", 1)
            result[key] = val
        else:
            result[item] = ""
    return result


def _col(row, name, default=""):
    if name in row:
        return row[name]
    name_lower = name.lower()
    for key in row:
        if key.lower() == name_lower:
            return row[key]
    return default


def parse_pods_tabular(text):
    rows = parse_tabular(text)
    result = []
    for row in rows:
        result.append({
            "namespace": _col(row, "NAMESPACE", "unknown"),
            "name": _col(row, "NAME", "unknown"),
            "status": _col(row, "STATUS", "Unknown"),
        })
    return result


def parse_nodes_list_tabular(text):
    rows = parse_tabular(text)
    result = []
    for row in rows:
        name = _col(row, "NAME", "unknown")
        roles_str = _col(row, "ROLES", "")
        labels_str = _col(row, "LABELS", "")

        labels = parse_labels_string(labels_str)
        if roles_str and roles_str != "<none>":
            for role in roles_str.split(","):
                role = role.strip()
                if role:
                    label_key = f"node-role.kubernetes.io/{role}"
                    if label_key not in labels:
                        labels[label_key] = ""

        result.append({
            "metadata": {"name": name, "labels": labels},
            "status": {},
        })
    return result


def parse_nodes_top_tabular(text):
    rows = parse_tabular(text)
    result = []
    for row in rows:
        result.append({
            "name": _col(row, "NAME", "unknown"),
            "cpu_usage": _col(row, "CPU(cores)") or None,
            "memory_usage": _col(row, "MEMORY(bytes)") or None,
        })
    return result


def parse_projects_tabular(text):
    rows = parse_tabular(text)
    return [{"name": _col(row, "NAME", "unknown")} for row in rows]


def parse_namespaces_tabular(text):
    rows = parse_tabular(text)
    return [{"name": _col(row, "NAME", "unknown")} for row in rows]


def classify_pod_status(pod):
    if isinstance(pod, dict) and "status" in pod and isinstance(pod["status"], str):
        return pod["status"]

    status_obj = pod.get("status", {})
    if isinstance(status_obj, str):
        return status_obj

    phase = status_obj.get("phase", "Unknown")

    container_statuses = status_obj.get("containerStatuses", [])
    if not container_statuses:
        container_statuses = status_obj.get("initContainerStatuses", [])

    for cs in container_statuses or []:
        state = cs.get("state", {})
        waiting = state.get("waiting", {})
        reason = waiting.get("reason", "")
        if reason in (
            "CrashLoopBackOff",
            "ImagePullBackOff",
            "ErrImagePull",
            "CreateContainerError",
            "CreateContainerConfigError",
            "RunContainerError",
        ):
            return reason

    if phase == "Completed":
        return "Succeeded"

    return phase


def aggregate_pods_by_namespace(pods, top_n=10):
    if not pods:
        return []

    ns_data = {}
    for pod in pods:
        if "metadata" in pod:
            ns = pod["metadata"].get("namespace", "unknown")
        else:
            ns = pod.get("namespace", "unknown")

        status = classify_pod_status(pod)

        if ns not in ns_data:
            ns_data[ns] = {"namespace": ns, "pods_total": 0, "running": 0,
                           "pending": 0, "failed": 0, "succeeded": 0, "other": 0}

        ns_data[ns]["pods_total"] += 1
        if status == "Running":
            ns_data[ns]["running"] += 1
        elif status == "Pending":
            ns_data[ns]["pending"] += 1
        elif status in ("Failed", "Error"):
            ns_data[ns]["failed"] += 1
        elif status in ("Succeeded", "Completed"):
            ns_data[ns]["succeeded"] += 1
        else:
            ns_data[ns]["other"] += 1

    sorted_ns = sorted(ns_data.values(), key=lambda x: x["pods_total"], reverse=True)
    return sorted_ns[:top_n]


def process_nodes(nodes_top, nodes_list):
    nodes = {}
    metrics_available = nodes_top is not None

    if nodes_list:
        for node in nodes_list:
            if isinstance(node, dict):
                meta = node.get("metadata", {})
                name = meta.get("name", node.get("name", "unknown"))
                labels = meta.get("labels", node.get("labels", {}))
                status = node.get("status", {})
                allocatable = status.get("allocatable", {})
                capacity = status.get("capacity", {})

                role = detect_node_role(labels)
                gpu_count, gpu_type = detect_gpus(allocatable)

                cpu_total = parse_cpu(allocatable.get("cpu") or capacity.get("cpu"))
                mem_total = parse_memory(allocatable.get("memory") or capacity.get("memory"))

                nodes[name] = {
                    "name": name,
                    "role": role,
                    "cpu_used": None,
                    "cpu_total": round(cpu_total, 2),
                    "memory_used": None,
                    "memory_total": round(mem_total, 2),
                    "gpus": gpu_count,
                    "gpu_type": gpu_type,
                }

    if nodes_top:
        for entry in nodes_top:
            if isinstance(entry, dict):
                name = entry.get("name", entry.get("NAME", "unknown"))
                cpu_used = entry.get("cpu_usage") or entry.get("CPU(cores)") or entry.get("cpu")
                mem_used = entry.get("memory_usage") or entry.get("MEMORY(bytes)") or entry.get("memory")

                if name in nodes:
                    if cpu_used is not None:
                        nodes[name]["cpu_used"] = round(parse_cpu(str(cpu_used)), 2)
                    if mem_used is not None:
                        nodes[name]["memory_used"] = round(parse_memory(str(mem_used)), 2)
                else:
                    nodes[name] = {
                        "name": name,
                        "role": "worker",
                        "cpu_used": round(parse_cpu(str(cpu_used)), 2) if cpu_used else None,
                        "cpu_total": None,
                        "memory_used": round(parse_memory(str(mem_used)), 2) if mem_used else None,
                        "memory_total": None,
                        "gpus": 0,
                        "gpu_type": "",
                    }

    return list(nodes.values()), metrics_available


def process_cluster(cluster_data):
    errors = cluster_data.get("errors", [])
    nodes_top = cluster_data.get("nodes_top")
    nodes_list = cluster_data.get("nodes_list")
    projects = cluster_data.get("projects")
    namespaces = cluster_data.get("namespaces")
    pods = cluster_data.get("pods")

    if isinstance(pods, str):
        pods = parse_pods_tabular(pods)
    if isinstance(nodes_top, str):
        nodes_top = parse_nodes_top_tabular(nodes_top)
    if isinstance(nodes_list, str):
        nodes_list = parse_nodes_list_tabular(nodes_list)
    if isinstance(projects, str):
        projects = parse_projects_tabular(projects)
    if isinstance(namespaces, str):
        namespaces = parse_namespaces_tabular(namespaces)

    nodes_detail, metrics_available = process_nodes(nodes_top, nodes_list)

    cpu_used = None
    cpu_total = 0.0
    mem_used = None
    mem_total = 0.0
    gpu_total = 0

    for node in nodes_detail:
        if node["cpu_total"] is not None:
            cpu_total += node["cpu_total"]
        if node["memory_total"] is not None:
            mem_total += node["memory_total"]
        if node["cpu_used"] is not None:
            cpu_used = (cpu_used or 0.0) + node["cpu_used"]
        if node["memory_used"] is not None:
            mem_used = (mem_used or 0.0) + node["memory_used"]
        gpu_total += node["gpus"]

    cpu_percent = None
    if cpu_used is not None and cpu_total > 0:
        cpu_percent = round((cpu_used / cpu_total) * 100)

    mem_percent = None
    if mem_used is not None and mem_total > 0:
        mem_percent = round((mem_used / mem_total) * 100)

    project_count = 0
    if projects is not None:
        project_count = len(projects) if isinstance(projects, list) else 0
    elif namespaces is not None:
        project_count = len(namespaces) if isinstance(namespaces, list) else 0

    pod_status = {
        "Running": 0,
        "Pending": 0,
        "Succeeded": 0,
        "Failed": 0,
        "Unknown": 0,
        "CrashLoopBackOff": 0,
        "ImagePullBackOff": 0,
        "ErrImagePull": 0,
        "Other": 0,
    }
    pods_running = 0
    pods_total = 0

    if pods and isinstance(pods, list):
        pods_total = len(pods)
        for pod in pods:
            status = classify_pod_status(pod)
            if status in pod_status:
                pod_status[status] += 1
            else:
                pod_status["Other"] += 1
            if status == "Running":
                pods_running += 1

    top_namespaces = aggregate_pods_by_namespace(pods or [])

    return {
        "overview": {
            "cluster": cluster_data.get("context", "unknown"),
            "server": cluster_data.get("server", "unknown"),
            "node_count": len(nodes_detail),
            "cpu_used_cores": round(cpu_used, 1) if cpu_used is not None else None,
            "cpu_total_cores": round(cpu_total, 1),
            "cpu_percent": cpu_percent,
            "memory_used_gib": round(mem_used, 1) if mem_used is not None else None,
            "memory_total_gib": round(mem_total, 1),
            "memory_percent": mem_percent,
            "gpu_total": gpu_total,
            "project_count": project_count,
            "pods_running": pods_running,
            "pods_total": pods_total,
            "metrics_available": metrics_available,
        },
        "nodes": nodes_detail,
        "pod_status": {k: v for k, v in pod_status.items() if v > 0},
        "top_namespaces": top_namespaces,
        "errors": errors,
    }


def compute_totals(overview_list):
    totals = {
        "node_count": 0,
        "cpu_used_cores": None,
        "cpu_total_cores": 0.0,
        "memory_used_gib": None,
        "memory_total_gib": 0.0,
        "gpu_total": 0,
        "project_count": 0,
        "pods_running": 0,
        "pods_total": 0,
    }

    for ov in overview_list:
        totals["node_count"] += ov.get("node_count", 0)
        totals["cpu_total_cores"] += ov.get("cpu_total_cores", 0)
        totals["memory_total_gib"] += ov.get("memory_total_gib", 0)
        totals["gpu_total"] += ov.get("gpu_total", 0)
        totals["project_count"] += ov.get("project_count", 0)
        totals["pods_running"] += ov.get("pods_running", 0)
        totals["pods_total"] += ov.get("pods_total", 0)

        if ov.get("cpu_used_cores") is not None:
            totals["cpu_used_cores"] = (totals["cpu_used_cores"] or 0) + ov["cpu_used_cores"]
        if ov.get("memory_used_gib") is not None:
            totals["memory_used_gib"] = (totals["memory_used_gib"] or 0) + ov["memory_used_gib"]

    totals["cpu_total_cores"] = round(totals["cpu_total_cores"], 1)
    totals["memory_total_gib"] = round(totals["memory_total_gib"], 1)

    if totals["cpu_used_cores"] is not None:
        totals["cpu_used_cores"] = round(totals["cpu_used_cores"], 1)
    if totals["memory_used_gib"] is not None:
        totals["memory_used_gib"] = round(totals["memory_used_gib"], 1)

    if totals["cpu_used_cores"] is not None and totals["cpu_total_cores"] > 0:
        totals["cpu_percent"] = round((totals["cpu_used_cores"] / totals["cpu_total_cores"]) * 100)
    else:
        totals["cpu_percent"] = None

    if totals["memory_used_gib"] is not None and totals["memory_total_gib"] > 0:
        totals["memory_percent"] = round((totals["memory_used_gib"] / totals["memory_total_gib"]) * 100)
    else:
        totals["memory_percent"] = None

    return totals


def detect_attention_items(overview_list, per_cluster):
    items = []

    for ov in overview_list:
        cluster = ov["cluster"]
        pc = per_cluster.get(cluster, {})

        if ov.get("cpu_percent") is not None and ov["cpu_percent"] > 85:
            items.append(f"{cluster}: Cluster CPU usage at {ov['cpu_percent']}% (>85% threshold)")

        if ov.get("memory_percent") is not None and ov["memory_percent"] > 85:
            items.append(f"{cluster}: Cluster memory usage at {ov['memory_percent']}% (>85% threshold)")

        for node in pc.get("nodes", []):
            if (node.get("cpu_used") is not None and node.get("cpu_total")
                    and node["cpu_total"] > 0):
                node_cpu_pct = (node["cpu_used"] / node["cpu_total"]) * 100
                if node_cpu_pct > 85:
                    items.append(
                        f"{cluster}: Node {node['name']} CPU at {round(node_cpu_pct)}% (>85%)"
                    )
            if (node.get("memory_used") is not None and node.get("memory_total")
                    and node["memory_total"] > 0):
                node_mem_pct = (node["memory_used"] / node["memory_total"]) * 100
                if node_mem_pct > 85:
                    items.append(
                        f"{cluster}: Node {node['name']} memory at {round(node_mem_pct)}% (>85%)"
                    )

        pod_status = pc.get("pod_status", {})
        failed = pod_status.get("Failed", 0) + pod_status.get("Error", 0)
        if failed > 0:
            items.append(f"{cluster}: {failed} pods in Failed/Error state")

        unknown = pod_status.get("Unknown", 0)
        if unknown > 0:
            items.append(f"{cluster}: {unknown} pods in Unknown state")

        pending = pod_status.get("Pending", 0)
        if pending > 0:
            items.append(f"{cluster}: {pending} pods in Pending state (possible resource constraints)")

        crash = pod_status.get("CrashLoopBackOff", 0)
        if crash > 0:
            items.append(f"{cluster}: {crash} pods in CrashLoopBackOff")

        img_pull = pod_status.get("ImagePullBackOff", 0) + pod_status.get("ErrImagePull", 0)
        if img_pull > 0:
            items.append(f"{cluster}: {img_pull} pods with image pull errors")

        if not ov.get("metrics_available", True):
            items.append(f"{cluster}: Metrics Server not available — no CPU/memory usage data")

        for err in pc.get("errors", []):
            items.append(f"{cluster}: {err}")

    return items


def main():
    try:
        raw = sys.stdin.read()
    except Exception as e:
        json.dump({"error": f"Failed to read stdin: {e}"}, sys.stdout, indent=2)
        sys.exit(1)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        json.dump({"error": f"Invalid JSON input: {e}"}, sys.stdout, indent=2)
        sys.exit(1)

    clusters_input = data.get("clusters", {})
    if not clusters_input:
        json.dump({"error": "No clusters found in input"}, sys.stdout, indent=2)
        sys.exit(1)

    overview_list = []
    per_cluster = {}
    failed_clusters = []

    for ctx_name, cluster_data in clusters_input.items():
        cluster_data.setdefault("context", ctx_name)
        result = process_cluster(cluster_data)
        overview_list.append(result["overview"])
        per_cluster[ctx_name] = {
            "nodes": result["nodes"],
            "pod_status": result["pod_status"],
            "top_namespaces": result["top_namespaces"],
            "errors": result["errors"],
        }
        if result["errors"]:
            for err in result["errors"]:
                failed_clusters.append({
                    "context": ctx_name,
                    "server": cluster_data.get("server", "unknown"),
                    "error": err,
                })

    clusters_reported = sum(
        1 for ov in overview_list
        if ov["node_count"] > 0 or ov["pods_total"] > 0 or ov["project_count"] > 0
    )
    clusters_failed = len(overview_list) - clusters_reported

    totals = compute_totals(overview_list)
    attention = detect_attention_items(overview_list, per_cluster)

    output = {
        "generated_at": data.get("generated_at", ""),
        "clusters_reported": clusters_reported,
        "clusters_failed": clusters_failed,
        "overview": overview_list,
        "totals": totals,
        "per_cluster": per_cluster,
        "attention": attention,
        "failed_clusters": failed_clusters,
    }

    json.dump(output, sys.stdout, indent=2)


if __name__ == "__main__":
    main()

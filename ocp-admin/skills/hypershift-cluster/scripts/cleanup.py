"""Read-only teardown inventories and verification. No cloud deletion commands.

The upstream CLI owns deletion. AWS resource names outside EC2/VPC discovery
come from the reviewed ownership manifest, never a cluster-name substring search.
"""
import datetime
import hashlib
import json
from pathlib import Path
import re


KINDS = {"vpcs", "instances", "volumes", "snapshots", "nat_gateways", "network_interfaces",
         "elastic_ips", "load_balancers_v2", "load_balancers_v1", "roles", "instance_profiles",
         "oidc_providers", "buckets", "hosted_zones", "users"}

# Recorded identifiers are interpolated into AWS CLI --filters strings. Accept
# only the provider's canonical ID shape so a stored value cannot inject an
# additional filter or alter the resource scope of a destructive safety check.
ID_PATTERNS = {
    "vpcs": r"vpc-[0-9a-f]{8,17}",
    "instances": r"i-[0-9a-f]{8,17}",
    "volumes": r"vol-[0-9a-f]{8,17}",
    "snapshots": r"snap-[0-9a-f]{8,17}",
    "nat_gateways": r"nat-[0-9a-f]{8,17}",
    "network_interfaces": r"eni-[0-9a-f]{8,17}",
    "elastic_ips": r"eipalloc-[0-9a-f]{8,17}",
    "load_balancers_v2": r"arn:aws[a-z-]*:elasticloadbalancing:[a-z0-9-]+:\d{12}:loadbalancer/[A-Za-z0-9./_-]+",
    "load_balancers_v1": r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,30}[A-Za-z0-9])?",
    "roles": r"[A-Za-z0-9+=,.@_-]{1,64}",
    "instance_profiles": r"[A-Za-z0-9+=,.@_-]{1,128}",
    "oidc_providers": r"arn:aws[a-z-]*:iam::\d{12}:oidc-provider/[A-Za-z0-9._/:=+,@-]+",
    "buckets": r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]",
    "hosted_zones": r"Z[0-9A-Z]{1,32}",
    "users": r"[A-Za-z0-9+=,.@_-]{1,64}",
}
DNS_TYPES = {"A", "AAAA", "CAA", "CNAME", "MX", "NS", "PTR", "SOA", "SRV", "TXT"}
INFRA_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")


def valid_id(kind, value):
    return isinstance(value, str) and re.fullmatch(ID_PATTERNS[kind], value) is not None


def checked_ids(kind, values, require):
    ids = sorted(set(values))
    require(all(valid_id(kind, value) for value in ids),
            f"AWS {kind} filter values are not valid resource identifiers.")
    return ids


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def record_digest(record):
    # Route 53 does not guarantee ResourceRecords ordering between reads.
    # Canonicalize list values so an unchanged shared record keeps its digest.
    canonical = dict(record)
    records = canonical.get("ResourceRecords")
    if isinstance(records, list):
        canonical["ResourceRecords"] = sorted(records,
                                              key=lambda item: json.dumps(item, sort_keys=True))
    return digest(canonical)


def record_name(value):
    # Route 53 returns wildcard labels escaped as \052; compare in the form
    # operators write in the ownership manifest.
    return value.replace("\\052", "*").rstrip(".").lower()


def conditions(obj):
    return {c["type"]: c["status"] for c in obj.get("status", {}).get("conditions", [])}


def management_snapshot(s, cp_namespace):
    # Use an explicit all-namespaces list for preservation, rather than the
    # kubeconfig's default namespace. No data-bearing workload specs are saved.
    deployments = json.loads(s.oc("get", "deployments", "--all-namespaces", "-o", "json"))["items"]
    return {
        "nodes": {n["metadata"]["name"]: {"uid": n["metadata"]["uid"],
                   "ready": conditions(n).get("Ready") == "True"} for n in s.get("nodes")["items"]},
        "version": s.get("clusterversion", "version"),
        "deployments": {d["metadata"]["namespace"] + "/" + d["metadata"]["name"]:
                        {"uid": d["metadata"]["uid"], "replicas": d["spec"].get("replicas", 1),
                         "images": [[c["name"], c["image"]] for c in d["spec"]["template"]["spec"]["containers"]]}
                        for d in deployments if d["metadata"]["namespace"] != cp_namespace},
        "hostedclusters": {h["metadata"]["namespace"] + "/" + h["metadata"]["name"]:
                           {"uid": h["metadata"]["uid"], "spec_digest": digest(h["spec"]),
                            "available": conditions(h).get("Available") == "True"}
                           for h in json.loads(s.oc("get", "hostedclusters.hypershift.openshift.io",
                                                   "--all-namespaces", "-o", "json"))["items"]
                           if (h["metadata"]["namespace"], h["metadata"]["name"]) != (s.p["namespace"], s.p["name"])},
        "lifecycle_namespace_uid": s.get("namespace", s.p["namespace"])["metadata"]["uid"],
    }


def storage(pv):
    return {"name": pv["metadata"]["name"], "uid": pv["metadata"]["uid"],
            "driver": pv["spec"].get("csi", {}).get("driver"),
            "volume_id": pv["spec"].get("csi", {}).get("volumeHandle"),
            "reclaim_policy": pv["spec"].get("persistentVolumeReclaimPolicy"),
            "claim": pv["spec"].get("claimRef", {})}


def hosts(services):
    return [i["hostname"] for v in services for i in v.get("status", {}).get("loadBalancer", {}).get("ingress", [])
            if "hostname" in i]


def capture(s, hc, skip_guest, require):
    cp = s.p["namespace"] + "-" + s.p["name"]
    data = {"schema_version": 1, "at": now(), "target": {
        "management_uid": s.binding["management_uid"], "namespace": s.p["namespace"], "name": s.p["name"],
        "hostedcluster_uid": hc["metadata"]["uid"], "infra_id": hc["spec"]["infraID"], "provider": s.p["provider"]},
        "control_plane_namespace": cp, "management": management_snapshot(s, cp),
        "provider_spec_digest": digest({"platform": hc["spec"]["platform"], "dns": hc["spec"].get("dns")}),
        "nodepools": [{"name": n["metadata"]["name"], "uid": n["metadata"]["uid"]}
                      for n in s.get("nodepools.hypershift.openshift.io", namespace=s.p["namespace"])["items"]
                      if n["spec"].get("clusterName") == s.p["name"]],
        "control_plane_volumes": [storage(pv) for pv in s.get("pv")["items"]
                                 if pv["spec"].get("claimRef", {}).get("namespace") == cp],
        "guest_storage_observed": False, "guest_volumes": [], "guest_pvcs": [], "lb_hosts": [], "cloud": None}
    if s.get("namespace", cp, optional=True):
        data["lb_hosts"] += hosts(s.get("services", namespace=cp)["items"])
    if not skip_guest:
        require((s.directory / "guest.kubeconfig").is_file(),
                "Guest credentials unavailable; use inventory --skip-guest for a partial inventory.")
        data["guest_uid"] = s.verify_guest()["guest_uid"]
        data["guest_volumes"] = [storage(pv) for pv in s.get("pv", guest=True)["items"]]
        pvcs = json.loads(s.oc("get", "pvc", "--all-namespaces", "-o", "json", guest=True))["items"]
        data["guest_pvcs"] = [{"namespace": v["metadata"]["namespace"], "name": v["metadata"]["name"],
                               "uid": v["metadata"]["uid"], "volume": v["spec"].get("volumeName")} for v in pvcs]
        data["lb_hosts"] += hosts(json.loads(s.oc("get", "services", "--all-namespaces", "-o", "json", guest=True))["items"])
        data["guest_storage_observed"] = True
    if s.p.get("aws_cleanup"):
        cfg = s.p["aws_cleanup"]
        require(hc["spec"]["platform"]["aws"]["region"] == cfg["region"], "AWS cleanup region does not match HC.")
        vpc = hc["spec"]["platform"]["aws"]["cloudProviderConfig"]["vpc"]
        data["cloud"] = aws_snapshot(s, cfg, data, vpc, require)
    return data


def verify(s, inventory, require):
    cp = inventory["control_plane_namespace"]
    hc = s.hc(optional=True)  # Detect replacements, not just presence.
    before = inventory["management"]
    after = management_snapshot(s, cp)
    cos = s.get("clusteroperators")["items"]
    checks = {
        "hostedcluster_absent": hc is None,
        "nodepools_absent": not any(n["spec"].get("clusterName") == s.p["name"]
                                    for n in s.get("nodepools.hypershift.openshift.io", namespace=s.p["namespace"])["items"]),
        "control_plane_namespace_absent": s.get("namespace", cp, optional=True) is None,
        "control_plane_pvs_absent": not any(pv["spec"].get("claimRef", {}).get("namespace") == cp
                                            for pv in s.get("pv")["items"]),
        "management_nodes_preserved": {k: v["uid"] for k, v in before["nodes"].items()} ==
                                      {k: v["uid"] for k, v in after["nodes"].items()},
        "management_nodes_ready": all(n["ready"] for n in after["nodes"].values()),
        "management_version_preserved": before["version"]["spec"] == after["version"]["spec"] and
                                        before["version"]["status"]["desired"] == after["version"]["status"]["desired"],
        "management_version_healthy": all(conditions(after["version"]).get(k) == v
                                           for k, v in {"Available": "True", "Failing": "False", "Progressing": "False"}.items()),
        "management_operators_healthy": all(conditions(o).get("Available") == "True" and
                                            conditions(o).get("Degraded") == "False" for o in cos),
        "other_deployments_preserved": all(after["deployments"].get(k) == v for k, v in before["deployments"].items()),
        "other_guests_preserved": all(k in after["hostedclusters"] and
                                      after["hostedclusters"][k]["uid"] == v["uid"] and
                                      after["hostedclusters"][k]["spec_digest"] == v["spec_digest"] and
                                      (not v["available"] or after["hostedclusters"][k]["available"])
                                      for k, v in before["hostedclusters"].items()),
        "lifecycle_namespace_preserved": before["lifecycle_namespace_uid"] == after["lifecycle_namespace_uid"],
        "guest_storage_observed": inventory["guest_storage_observed"],
    }
    if inventory["cloud"] is not None:
        cloud = aws_snapshot(s, s.p["aws_cleanup"], inventory, inventory["cloud"]["vpc"], require,
                             previous=inventory["cloud"])
        for kind, ids in inventory["cloud"]["owned"].items():
            checks["aws_" + kind + "_absent"] = not (set(ids) & set(cloud["present"][kind]))
        # Also catch resources discovered by infra tags/owned VPC after inventory.
        recorded_owned = {kind: set(ids) for kind, ids in inventory["cloud"]["owned"].items()}
        checks["aws_new_owned_resources_absent"] = not any(
            set(cloud["discovered"][kind]) - recorded_owned.get(kind, set())
            for kind in cloud["discovered"])
        checks["aws_shared_resources_preserved"] = all(set(ids) <= set(cloud["present"][kind])
                                                       for kind, ids in inventory["cloud"]["preserve"].items())
        checks["aws_dns_records_absent"] = not cloud["owned_dns_present"]
        checks["aws_other_dns_preserved"] = all(k in cloud["other_dns"] and cloud["other_dns"][k] == v
                                               for k, v in inventory["cloud"]["other_dns"].items())
        checks["aws_oidc_documents_absent"] = not any(cloud["oidc_documents"].values())
        checks["aws_ownership_reviewed"] = s.p["aws_cleanup"].get("ownership_reviewed", False)
        checks["aws_storage_supported"] = all(v.get("driver") == "ebs.csi.aws.com" and
                valid_id("volumes", v.get("volume_id"))
                for v in inventory["guest_volumes"] + inventory["control_plane_volumes"])
    else:
        checks["provider_cleanup_verified"] = False
    return {"at": now(), "target": inventory["target"], "checks": checks,
            "cleanup_verified": all(checks.values()),
            "scope": "Recorded resources and supported AWS discovery; additional providers/resources require separate verification."}


def validate_aws(cfg, require):
    require(isinstance(cfg, dict) and not cfg.keys() - {"account_id", "region", "credentials_file", "profile",
            "owned", "preserve", "dns_records", "oidc_documents", "ownership_reviewed"}, "Unknown aws_cleanup fields.")
    require(isinstance(cfg.get("account_id"), str) and re.fullmatch(r"\d{12}", cfg["account_id"]), "Set AWS cleanup account_id.")
    require(isinstance(cfg.get("region"), str) and re.fullmatch(r"[a-z0-9-]+", cfg["region"]), "Set AWS cleanup region.")
    require(isinstance(cfg.get("credentials_file"), str) and Path(cfg["credentials_file"]).is_absolute(),
            "Use an absolute AWS cleanup credentials_file path.")
    require(isinstance(cfg.get("profile", "default"), str) and bool(cfg.get("profile", "default")), "Set AWS credential profile.")
    require(type(cfg.get("ownership_reviewed", False)) is bool, "ownership_reviewed must be a boolean.")
    for field in ("owned", "preserve"):
        value = cfg.get(field, {})
        require(isinstance(value, dict) and not value.keys() - KINDS, "Unknown AWS resource inventory kinds.")
        require(all(isinstance(ids, list) for ids in value.values()),
                "AWS resource identifiers must be lists.")
        for kind, ids in value.items():
            require(all(valid_id(kind, item) for item in ids),
                    f"AWS {kind} identifiers must use the provider's canonical resource ID format.")
    for kind in KINDS:
        require(not set(cfg.get("owned", {}).get(kind, [])) & set(cfg.get("preserve", {}).get(kind, [])),
                "AWS resources cannot be both owned and preserved.")
    for field, keys in (("dns_records", {"zone_id", "name", "type"}), ("oidc_documents", {"bucket", "prefix"})):
        require(isinstance(cfg.get(field, []), list), f"{field} must be a list.")
        for item in cfg.get(field, []):
            require(isinstance(item, dict) and set(item) == keys and all(isinstance(v, str) and v for v in item.values()),
                    f"Invalid {field} entry.")
    for item in cfg.get("dns_records", []):
        require(valid_id("hosted_zones", item["zone_id"]), "Invalid Route 53 hosted zone ID.")
        require(re.fullmatch(r"(?:[A-Za-z0-9*_-]+\.)+[A-Za-z0-9_-]+\.?", item["name"]),
                "Invalid Route 53 record name.")
        require(item["type"] in DNS_TYPES, "Unsupported Route 53 record type.")
    for item in cfg.get("oidc_documents", []):
        require(valid_id("buckets", item["bucket"]), "Invalid OIDC document bucket name.")
        require(re.fullmatch(r"[A-Za-z0-9._/-]+/", item["prefix"]),
                "OIDC document prefix must be a safe object prefix ending in '/'.")


def aws_environment(cfg, require):
    require(Path(cfg["credentials_file"]).is_file(), "AWS cleanup credentials file is missing.")
    env = {k: None for k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN",
                             "AWS_SECURITY_TOKEN", "AWS_DEFAULT_PROFILE", "AWS_ROLE_ARN", "AWS_ROLE_SESSION_NAME",
                             "AWS_WEB_IDENTITY_TOKEN_FILE", "AWS_CONTAINER_CREDENTIALS_FULL_URI",
                             "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI", "AWS_CONTAINER_AUTHORIZATION_TOKEN",
                             "AWS_CONTAINER_AUTHORIZATION_TOKEN_FILE")}
    env.update(AWS_SHARED_CREDENTIALS_FILE=cfg["credentials_file"], AWS_PROFILE=cfg.get("profile", "default"),
               AWS_REGION=cfg["region"], AWS_DEFAULT_REGION=cfg["region"], AWS_CONFIG_FILE="/dev/null",
               AWS_EC2_METADATA_DISABLED="true")
    return env


def check_aws_account(s, cfg, require):
    env = aws_environment(cfg, require)
    value = json.loads(s.external(["aws", "--region", cfg["region"], "--no-cli-pager", "sts", "get-caller-identity", "--output", "json"],
                                  env_overrides=env, timeout=90))
    require(value["Account"] == cfg["account_id"], "AWS cleanup account mismatch.")
    return env


def aws_snapshot(s, cfg, inventory, vpc, require, previous=None):
    env = check_aws_account(s, cfg, require)
    def aws(*args):
        raw = s.external(["aws", "--region", cfg["region"], "--no-cli-pager", *args, "--output", "json"],
                         env_overrides=env, timeout=90)
        # Some read-only S3 calls return an empty body when no configuration
        # exists, which is not an error.
        return json.loads(raw) if raw.strip() else {}
    infra = inventory["target"]["infra_id"]
    require(isinstance(infra, str) and INFRA_ID.fullmatch(infra),
            "Invalid infrastructure ID for AWS tag filters.")
    require(valid_id("vpcs", vpc), "Invalid AWS VPC ID for cleanup discovery.")
    tag = "kubernetes.io/cluster/" + infra
    def tagged(obj):
        return any(t["Key"] == tag and t["Value"] == "owned" for t in obj.get("Tags", []))
    vpcs = aws("ec2", "describe-vpcs", "--filters", "Name=vpc-id,Values=" + vpc)["Vpcs"]
    owned_vpc = previous["vpc_owned"] if previous else any(tagged(v) for v in vpcs)
    discovered = {k: set() for k in KINDS}
    configured = {k: set(cfg.get("owned", {}).get(k, [])) for k in KINDS}
    preserve = {k: set(cfg.get("preserve", {}).get(k, [])) for k in KINDS}
    if not owned_vpc:
        preserve["vpcs"].add(vpc)
    recorded = {k: set(previous["owned"].get(k, [])) | configured[k] for k in KINDS} if previous else configured
    present = {k: set() for k in KINDS}
    # AWS CLI paginates list/describe calls automatically (no --no-paginate is
    # passed), so every page is returned; absence checks rely on that behavior.
    all_vpcs = aws("ec2", "describe-vpcs")["Vpcs"]
    present["vpcs"] = {v["VpcId"] for v in all_vpcs}
    if owned_vpc and vpcs:
        discovered["vpcs"].add(vpc)
    scope = "Name=vpc-id,Values=" + vpc if owned_vpc else "Name=tag:" + tag + ",Values=owned"
    instances = [i for rr in aws("ec2", "describe-instances", "--filters", scope)["Reservations"] for i in rr["Instances"]]
    discovered["instances"] = {i["InstanceId"] for i in instances if i["State"]["Name"] != "terminated"}
    present["instances"] = set(discovered["instances"])
    # Explicit/shared instance IDs can lie outside the guest VPC.
    ids = checked_ids("instances", set(recorded.get("instances", [])) | preserve["instances"], require)
    if ids:
        extra = aws("ec2", "describe-instances", "--filters", "Name=instance-id,Values=" + ",".join(ids))
        present["instances"] |= {i["InstanceId"] for rr in extra["Reservations"] for i in rr["Instances"] if i["State"]["Name"] != "terminated"}
    volume_ids = {b["Ebs"]["VolumeId"] for i in instances for b in i.get("BlockDeviceMappings", []) if "Ebs" in b}
    volume_ids |= {v["volume_id"] for v in inventory["guest_volumes"] + inventory["control_plane_volumes"]
                   if v.get("driver") == "ebs.csi.aws.com" and v.get("volume_id")}
    volume_ids |= set(recorded.get("volumes", [])) | preserve["volumes"]
    volume_ids = set(checked_ids("volumes", volume_ids, require))
    volumes = aws("ec2", "describe-volumes", "--filters", "Name=tag:" + tag + ",Values=owned")["Volumes"]
    discovered["volumes"] = {v["VolumeId"] for v in volumes}
    if volume_ids:
        volumes += aws("ec2", "describe-volumes", "--filters", "Name=volume-id,Values=" +
                       ",".join(sorted(volume_ids)))["Volumes"]
    present["volumes"] = {v["VolumeId"] for v in volumes}
    # All recorded guest/root/control-plane disks are in scope, even without tags.
    configured["volumes"] |= volume_ids - preserve["volumes"]
    # Populated only when the NAT gateway branch runs; keep a safe default so
    # elastic IP discovery cannot raise UnboundLocalError.
    nat_ips = set()
    for kind, operation, response, idkey, opt in [
        ("snapshots", "describe-snapshots", "Snapshots", "SnapshotId", ["--owner-ids", "self", "--filters", "Name=tag:" + tag + ",Values=owned"]),
        ("nat_gateways", "describe-nat-gateways", "NatGateways", "NatGatewayId", ["--filter", scope]),
        ("network_interfaces", "describe-network-interfaces", "NetworkInterfaces", "NetworkInterfaceId", ["--filters", scope])]:
        objects = aws("ec2", operation, *opt)[response]
        discovered[kind] = {v[idkey] for v in objects if v.get("State") != "deleted"}
        # Include explicitly recorded/preserved objects using the API's ID filter.
        more = checked_ids(kind, set(recorded.get(kind, [])) | preserve[kind], require)
        if more:
            filter_key = {"snapshots": "snapshot-id", "nat_gateways": "nat-gateway-id", "network_interfaces": "network-interface-id"}[kind]
            objects += aws("ec2", operation, *( ["--owner-ids", "self"] if kind == "snapshots" else []),
                           "--filter" if kind == "nat_gateways" else "--filters", "Name=" + filter_key + ",Values=" + ",".join(more))[response]
        present[kind] = {v[idkey] for v in objects if v.get("State") != "deleted"}
        if kind == "nat_gateways":
            nat_ips = {a["AllocationId"] for v in objects if v["NatGatewayId"] not in preserve["nat_gateways"]
                       for a in v.get("NatGatewayAddresses", []) if "AllocationId" in a}
    addresses = aws("ec2", "describe-addresses")["Addresses"]
    discovered["elastic_ips"] = {v["AllocationId"] for v in addresses if tagged(v) or v.get("AllocationId") in nat_ips}
    present["elastic_ips"] = {v["AllocationId"] for v in addresses if "AllocationId" in v}
    for kind, service, response, idkey, vpckey in [
        ("load_balancers_v2", "elbv2", "LoadBalancers", "LoadBalancerArn", "VpcId"),
        ("load_balancers_v1", "elb", "LoadBalancerDescriptions", "LoadBalancerName", "VPCId")]:
        lbs = aws(service, "describe-load-balancers")[response]
        present[kind] = {v[idkey] for v in lbs}
        discovered[kind] = {v[idkey] for v in lbs if (owned_vpc and v.get(vpckey) == vpc) or
                            v["DNSName"] in inventory["lb_hosts"]}
    for kind, service, operation, response, idkey in [
        ("roles", "iam", "list-roles", "Roles", "RoleName"),
        ("users", "iam", "list-users", "Users", "UserName"),
        ("instance_profiles", "iam", "list-instance-profiles", "InstanceProfiles", "InstanceProfileName"),
        ("oidc_providers", "iam", "list-open-id-connect-providers", "OpenIDConnectProviderList", "Arn"),
        ("buckets", "s3api", "list-buckets", "Buckets", "Name"),
        ("hosted_zones", "route53", "list-hosted-zones", "HostedZones", "Id")]:
        present[kind] = {v[idkey].removeprefix("/hostedzone/") if kind == "hosted_zones" else v[idkey]
                         for v in aws(service, operation)[response]}
    for item in cfg.get("oidc_documents", []):
        require(item["prefix"] == infra + "/", "OIDC document prefix must equal the recorded infra_id plus '/'.")
        preserve["buckets"].add(item["bucket"])
    for kind in KINDS:
        require(not (configured[kind] | discovered[kind]) & preserve[kind], "Discovered AWS ownership overlaps preserved resources.")
    owned = {k: configured[k] | discovered[k] | set(recorded.get(k, [])) for k in KINDS}
    if not previous:
        require(all(ids <= present[k] for k, ids in preserve.items()), "An expected shared AWS resource is missing before teardown.")
    other_dns, owned_dns_present = {}, []
    zones = preserve["hosted_zones"] | {v["zone_id"] for v in cfg.get("dns_records", [])}
    for zone in sorted(zones & present["hosted_zones"]):
        for rr in aws("route53", "list-resource-record-sets", "--hosted-zone-id", zone)["ResourceRecordSets"]:
            is_owned = any(v["zone_id"] == zone and record_name(v["name"]) == record_name(rr["Name"])
                           and v["type"] == rr["Type"] for v in cfg.get("dns_records", []))
            key = zone + "/" + rr["Name"] + "/" + rr["Type"] + "/" + rr.get("SetIdentifier", "")
            if is_owned:
                owned_dns_present.append(key)
            else:
                other_dns[key] = record_digest(rr)
    documents = {}
    for item in cfg.get("oidc_documents", []):
        key = item["bucket"] + "/" + item["prefix"]
        documents[key] = False
        if item["bucket"] in present["buckets"]:
            documents[key] = bool(aws("s3api", "list-objects-v2", "--bucket", item["bucket"], "--prefix", item["prefix"]).get("Contents"))
            if aws("s3api", "get-bucket-versioning", "--bucket", item["bucket"]).get("Status") in {"Enabled", "Suspended"}:
                versions = aws("s3api", "list-object-versions", "--bucket", item["bucket"], "--prefix", item["prefix"])
                documents[key] |= bool(versions.get("Versions") or versions.get("DeleteMarkers"))
    return {"account_id": cfg["account_id"], "region": cfg["region"], "vpc": vpc, "vpc_owned": owned_vpc,
            "owned": {k: sorted(v) for k, v in owned.items()}, "preserve": {k: sorted(v) for k, v in preserve.items()},
            "present": {k: sorted(v) for k, v in present.items()}, "discovered": {k: sorted(v) for k, v in discovered.items()},
            "other_dns": other_dns, "owned_dns_present": owned_dns_present, "oidc_documents": documents}

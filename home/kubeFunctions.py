from time import sleep
from typing import Never

from kubernetes import client, config

from home.stylishFunctions import human_memory,parse_cpu,parse_memory

try: config.load_incluster_config()
except Exception: config.load_kube_config()

v1 = client.CoreV1Api()
custom = client.CustomObjectsApi()

pods_cache:list[dict[str, str|int|float]] = [] 

def refreshPods(time:int=60) -> Never:
    global pods_cache

    while True:
        try:
            metrics = custom.list_cluster_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                plural="pods",
            )

            metric_map = {
                (p["metadata"]["namespace"], p["metadata"]["name"]): p
                for p in metrics["items"]
            }

            new_cache = []

            for pod in v1.list_pod_for_all_namespaces().items:
                key = (pod.metadata.namespace, pod.metadata.name)

                cpu_used = 0
                mem_used = 0

                if key in metric_map:
                    for c in metric_map[key]["containers"]:
                        cpu_used += parse_cpu(c["usage"]["cpu"])
                        mem_used += parse_memory(c["usage"]["memory"])

                cpu_limit = 0
                mem_limit = 0

                for c in pod.spec.containers:
                    if c.resources and c.resources.limits:
                        if "cpu" in c.resources.limits:
                            cpu_limit += parse_cpu(c.resources.limits["cpu"])
                        if "memory" in c.resources.limits:
                            mem_limit += parse_memory(c.resources.limits["memory"])

                # Fall back to requests
                if cpu_limit == 0 or mem_limit == 0:
                    for c in pod.spec.containers:
                        if c.resources and c.resources.requests:
                            if cpu_limit == 0 and "cpu" in c.resources.requests:
                                cpu_limit += parse_cpu(c.resources.requests["cpu"])
                            if mem_limit == 0 and "memory" in c.resources.requests:
                                mem_limit += parse_memory(c.resources.requests["memory"])

                cpu_percent = round(cpu_used / cpu_limit * 100, 1) if cpu_limit else None
                mem_percent = round(mem_used / mem_limit * 100, 1) if mem_limit else None

                new_cache.append({
                    "namespace": pod.metadata.namespace,
                    "name": pod.metadata.name,
                    "node": pod.spec.node_name,
                    "status": pod.status.phase,
                    "ip": pod.status.pod_ip,

                    "cpu": {
                        "usage": f"{cpu_used * 1000:.1f}m",
                        "percent": cpu_percent
                    },

                    "memory": {
                        "usage": human_memory(mem_used),
                        "percent": mem_percent
                    }
                })

            pods_cache = new_cache
            print(f"Updated {len(pods_cache)} pods")

        except Exception as e: print(e)

        sleep(time)

def give_pods_bridge() -> list[dict[str, str|int|float]]: return pods_cache
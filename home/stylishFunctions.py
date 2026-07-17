import graphviz
from collections import defaultdict

def parse_cpu(cpu:str) -> float:
    """Convert Kubernetes CPU string to cores."""
    if cpu.endswith("n"): return float(cpu[:-1]) / 1_000_000_000
    if cpu.endswith("u"): return float(cpu[:-1]) / 1_000_000
    if cpu.endswith("m"): return float(cpu[:-1]) / 1000
    return float(cpu)

def parse_memory(mem:str) -> float:
    """Convert Kubernetes memory string to bytes."""
    units = {
        "Ki": 1024,
        "Mi": 1024 ** 2,
        "Gi": 1024 ** 3,
        "Ti": 1024 ** 4,
    }

    for suffix, multiplier in units.items(): 
        if mem.endswith(suffix): return float(mem[:-2]) * multiplier

    return float(mem)

def parse_memory_to_mib(mem_str:str|None) -> float:
    if not mem_str: return 0.0
    if mem_str.endswith(" GiB"): return float(mem_str.replace(" GiB", "")) * 1024.0
    elif mem_str.endswith(" MiB"): return float(mem_str.replace(" MiB", ""))
    elif mem_str.endswith(" KiB"): return float(mem_str.replace(" KiB", "")) / 1024.0
    return 0.0

def human_memory(num:float|int) -> str:
    """Convert bytes to MiB/GiB."""
    if num > 1024 ** 3: return f"{num / 1024 ** 3:.1f} GiB"
    return f"{num / 1024 ** 2:.1f} MiB"

def format_memory_from_mib(mib_val:float|int) -> str:
    if mib_val >= 1024.0:return f"{mib_val / 1024.0:.2f} GiB"
    return f"{mib_val:.1f} MiB"

def namespace_label_generator(namespace:str, total_cpu_m:float, formatted_memory:str) -> str:
    return f'''<
            <TABLE BORDER="0" CELLBORDER="0" CELLPADDING="4">
            <TR><TD><FONT COLOR="#8958bb"><B>{namespace}</B></FONT></TD></TR>
            <TR><TD><FONT COLOR="red">CPU {total_cpu_m:.1f}m</FONT></TD></TR>
            <TR><TD><FONT COLOR="#DAA520">RAM {formatted_memory}</FONT></TD></TR>
            </TABLE>
        >'''

def pod_label_generator(pod:dict[str, str|int|float], pod_cpu:str, pod_mem:str) -> str:
    return f'''<
                <TABLE BORDER="0" CELLBORDER="0" CELLPADDING="4">
                <TR><TD><FONT COLOR="#00BA51"><B>{pod["name"]}</B></FONT></TD></TR>
                <TR><TD><FONT COLOR="red">CPU {pod_cpu}</FONT></TD></TR>
                <TR><TD><FONT COLOR="#DAA520">RAM {pod_mem}</FONT></TD></TR>
                <TR><TD><FONT COLOR="#666666" POINT-SIZE="10">Node: {pod.get("node","-")}</FONT></TD></TR>
                <TR><TD><FONT COLOR="#666666" POINT-SIZE="10">Status: {pod.get("status","-")}</FONT></TD></TR>
                </TABLE>
            >'''

def generate_wraped_chart(strucData:list[dict[str, str|int|float]], maxPodsPerRow:int=4) -> None:
    # Grouping Data
    namespaces = defaultdict(list)
    for pod in strucData: namespaces[pod["namespace"]].append(pod)


    dot = graphviz.Digraph("k8s", format="png")
    dot.attr(rankdir="TB", bgcolor="white", nodesep="0.4", ranksep="0.8")
    dot.attr("node", shape="box", style="rounded,filled", fillcolor="white", penwidth="2")

    for namespace, pods in namespaces.items():
        # Aggregate CPU and Memory safely
        total_cpu_m = sum(parse_cpu(p.get("cpu", {}).get("usage", "0m")) for p in pods)
        total_mem_mib = sum(parse_memory_to_mib(p.get("memory", {}).get("usage", "0 MiB")) for p in pods)
        formatted_memory = format_memory_from_mib(total_mem_mib)

        ns_label = namespace_label_generator(namespace, total_cpu_m, formatted_memory)

        dot.node(namespace, label=ns_label, fillcolor="#eeeeee")

        for i, pod in enumerate(pods):
            pod_cpu = pod.get("cpu", {}).get("usage", "0m")
            pod_mem = pod.get("memory", {}).get("usage", "0 MiB")
            
            pod_label = pod_label_generator(pod, pod_cpu, pod_mem)
            
            # create the pod node
            dot.node(pod["name"], label=pod_label, fillcolor="#ffffff")
            
            # create the visible line from the Namespace to the Pod
            dot.edge(namespace, pod["name"], penwidth="2")
            
            # The wrapping trick: 
            if i >= maxPodsPerRow:
                pod_above_name = pods[i - maxPodsPerRow]["name"]
                dot.edge(pod_above_name, pod["name"], style="invis", weight="100")

    dot.render("temp/chart_wrap", cleanup=True)
    print("Graph wraped generated successfully!")

def generate_unwraped_chart(strucData:list[dict[str, str|int|float]]) -> None:
    # grouping Data
    namespaces = defaultdict(list)
    for pod in strucData: namespaces[pod["namespace"]].append(pod)

    dot = graphviz.Digraph("k8s", format="png")
    dot.attr(rankdir="TB", bgcolor="white", nodesep="0.4", ranksep="0.8")
    dot.attr("node", shape="box", style="rounded,filled", fillcolor="white", penwidth="2")

    for namespace, pods in namespaces.items():
        # Aggregate CPU and Memory safely
        total_cpu_m = sum(parse_cpu(p.get("cpu", {}).get("usage", "0m")) for p in pods)
        total_mem_mib = sum(parse_memory_to_mib(p.get("memory", {}).get("usage", "0 MiB")) for p in pods)
        formatted_memory = format_memory_from_mib(total_mem_mib)

        ns_label = namespace_label_generator(namespace, total_cpu_m, formatted_memory)
        dot.node(namespace, label=ns_label, fillcolor="#eeeeee")

        for pod in pods:
            pod_cpu = pod.get("cpu", {}).get("usage", "0m")
            pod_mem = pod.get("memory", {}).get("usage", "0 MiB")
            
            pod_label = pod_label_generator(pod, pod_cpu, pod_mem)
            
            # Create the pod node
            dot.node(pod["name"], label=pod_label, fillcolor="#ffffff")
            
            # Create the visible line from the Namespace to the Pod
            dot.edge(namespace, pod["name"], penwidth="2")

    dot.render("temp/chart_unwrap", cleanup=True)
    print("Graph unwraped generated successfully!")
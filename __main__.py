import threading
import cachetools.func

from collections import defaultdict
from flask import Flask, Response, render_template, jsonify, send_file 

from home.kubeFunctions import refreshPods, give_pods_bridge
from home.stylishFunctions import generate_wraped_chart, generate_unwraped_chart

app = Flask(__name__)

# so cache with max 4 items and 60 s live
@cachetools.func.ttl_cache(maxsize=4, ttl=60)
@app.route("/")
def index():
    pods = give_pods_bridge()
    namespaces = defaultdict(list)

    for pod in pods: namespaces[pod["namespace"]].append(pod)

    return render_template(
        "index.html",
        namespaces=dict(sorted(namespaces.items()))
    )

@cachetools.func.ttl_cache(maxsize=4, ttl=60)
@app.route("/chart/unwraped")
def chart_unwraped() -> Response:
    generate_unwraped_chart(give_pods_bridge())
    return send_file("./temp/chart_unwrap.png")

@cachetools.func.ttl_cache(maxsize=4, ttl=60)
@app.route("/chart/wraped")
def chart_wraped() -> Response:
    generate_wraped_chart(give_pods_bridge())
    return send_file("./temp/chart_wrap.png")

@cachetools.func.ttl_cache(maxsize=4, ttl=60)
@app.route("/raw/pods")
def raw_pods() -> Response: return jsonify(give_pods_bridge())

if __name__ == "__main__":
    threading.Thread(target=refreshPods, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=True)
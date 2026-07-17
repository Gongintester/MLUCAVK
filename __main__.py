import threading

from collections import defaultdict
from flask import Flask, render_template, jsonify, send_file 

from home.kubeFunctions import refreshPods, give_pods_cache
from home.stylishFunctions import generate_wraped_chart, generate_unwraped_chart

app = Flask(__name__)

@app.route("/")
def index():
    pods = give_pods_cache()

    namespaces = defaultdict(list)

    for pod in pods: namespaces[pod["namespace"]].append(pod)

    return render_template(
        "index.html",
        namespaces=dict(sorted(namespaces.items()))
    )

@app.route("/chart/unwraped")
def chart_unwraped():
    generate_unwraped_chart(give_pods_cache())
    return send_file("./chart_unwrap.png")

@app.route("/chart/wraped")
def chart_wraped():
    generate_wraped_chart(give_pods_cache())
    return send_file("./chart_wrap.png")

@app.route("/raw/pods")
def raw_pods(): return jsonify(give_pods_cache())

if __name__ == "__main__":
    threading.Thread(target=refreshPods, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=True)
import json, os
from flask import Flask, request, jsonify

app = Flask(__name__)
TOKEN = os.environ.get("RECEIVER_TOKEN", "mysecret123")


@app.route("/report", methods=["POST"])
def report():
    if request.headers.get("X-Token") != TOKEN:
        return jsonify(error="unauthorized"), 401
    data = request.get_json(force=True)
    with open("test-report.json", "w") as f:
        json.dump(data, f, indent=2)
    print("Report saved:", data["overall_status"], data["commit_sha"])
    return jsonify(status="saved")


if __name__ == "__main__":
    app.run(port=9000)
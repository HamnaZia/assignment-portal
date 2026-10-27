import os, json, datetime, urllib.request
import xml.etree.ElementTree as ET

tests = []
if os.path.exists("report.xml"):
    for tc in ET.parse("report.xml").getroot().iter("testcase"):
        result, msg = "passed", None
        bad = tc.find("failure")
        if bad is None:
            bad = tc.find("error")
        if bad is not None:
            result, msg = "failed", bad.get("message")
        tests.append({"name": tc.get("name"), "result": result,
                      "failure_message": msg})

passed = sum(t["result"] == "passed" for t in tests)
failed = sum(t["result"] == "failed" for t in tests)

report = {
    "repository": os.environ.get("GITHUB_REPOSITORY"),
    "branch": os.environ.get("GITHUB_REF_NAME"),
    "commit_sha": os.environ.get("GITHUB_SHA"),
    "pipeline_run_id": os.environ.get("GITHUB_RUN_ID"),
    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "tests": tests,
    "total": len(tests),
    "passed": passed,
    "failed": failed,
    "overall_status": "passed" if tests and failed == 0 else "failed",
}

req = urllib.request.Request(
    os.environ["RECEIVER_URL"].rstrip("/") + "/report",
    data=json.dumps(report).encode(),
    headers={"Content-Type": "application/json",
             "X-Token": os.environ["RECEIVER_TOKEN"],
             "ngrok-skip-browser-warning": "1"},
    method="POST",
)
print("Receiver replied:", urllib.request.urlopen(req, timeout=30).read().decode())
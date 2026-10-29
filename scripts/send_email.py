import json
import os
import smtplib
import ssl
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.message import EmailMessage


def need(name):
    value = os.environ.get(name, "").strip()
    if not value:
        print(f"ERROR: environment variable {name} is missing or empty.")
        print("It is passed from GitHub secrets in ci.yml (env: section).")
        sys.exit(1)
    return value


# ---------- read test results ----------
tests = []
if os.path.exists("report.xml"):
    for tc in ET.parse("report.xml").getroot().iter("testcase"):
        bad = tc.find("failure")
        if bad is None:
            bad = tc.find("error")
        name = f'{tc.get("classname", "")}.{tc.get("name", "")}'.strip(".")
        if bad is not None:
            tests.append({"name": name, "result": "failed",
                          "failure_message": bad.get("message") or "failed"})
        else:
            tests.append({"name": name, "result": "passed",
                          "failure_message": None})

passed = sum(1 for t in tests if t["result"] == "passed")
failed = sum(1 for t in tests if t["result"] == "failed")
overall = "PASSED" if tests and failed == 0 else "FAILED"

repo = os.environ.get("GITHUB_REPOSITORY", "local")
branch = os.environ.get("GITHUB_REF_NAME", "local")
sha = os.environ.get("GITHUB_SHA", "local")
run_id = os.environ.get("GITHUB_RUN_ID", "local")
timestamp = datetime.now(timezone.utc).isoformat()

report = {
    "repository": repo,
    "branch": branch,
    "commit_sha": sha,
    "pipeline_run_id": run_id,
    "timestamp": timestamp,
    "tests": tests,
    "summary": {"total": len(tests), "passed": passed, "failed": failed},
    "overall_status": overall,
}

# Save a copy of the report next to the script's working folder
with open("email-report.json", "w") as fh:
    json.dump(report, fh, indent=2)

# ---------- build the email text ----------
lines = [
    "Repository: " + repo,
    "Branch: " + branch,
    "Commit: " + sha,
    "Pipeline run: " + run_id,
    "Time (UTC): " + timestamp,
    "Overall result: " + overall,
    "Total: %d   Passed: %d   Failed: %d" % (len(tests), passed, failed),
    "",
    "Individual results:",
]
for t in tests:
    line = "  - %s: %s" % (t["name"], t["result"].upper())
    if t["failure_message"]:
        line += "\n      Failure: " + t["failure_message"]
    lines.append(line)
lines += ["", "The full JSON report is attached (test-report.json)."]

# ---------- credentials from environment (GitHub secrets) ----------
user = need("EMAIL_USER")
password = need("EMAIL_PASSWORD").replace(" ", "")
to_addr = need("EMAIL_TO")

msg = EmailMessage()
msg["Subject"] = "[%s] %s - %s" % (overall, repo, sha[:7])
msg["From"] = user
msg["To"] = to_addr
msg.set_content("\n".join(lines))
msg.add_attachment(json.dumps(report, indent=2).encode(),
                   maintype="application", subtype="json",
                   filename="test-report.json")


def send():
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465,
                              context=ssl.create_default_context(),
                              timeout=30) as s:
            s.login(user, password)
            s.send_message(msg)
        return
    except smtplib.SMTPAuthenticationError as e:
        print("Login rejected (wrong App Password or username):", e)
        sys.exit(1)
    except Exception as e:
        print("Port 465 failed, trying 587:", repr(e))
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as s:
        s.starttls(context=ssl.create_default_context())
        s.login(user, password)
        s.send_message(msg)


send()
print("Email sent to", to_addr)
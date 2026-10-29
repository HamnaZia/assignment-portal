import os, smtplib, ssl
import xml.etree.ElementTree as ET
from email.message import EmailMessage

tests = []
if os.path.exists("report.xml"):
    for tc in ET.parse("report.xml").getroot().iter("testcase"):
        bad = tc.find("failure")
        if bad is None:
            bad = tc.find("error")
        if bad is not None:
            tests.append((tc.get("name"), "FAILED", bad.get("message") or ""))
        else:
            tests.append((tc.get("name"), "PASSED", ""))

passed = sum(1 for t in tests if t[1] == "PASSED")
failed = sum(1 for t in tests if t[1] == "FAILED")
overall = "PASSED" if tests and failed == 0 else "FAILED"

repo = os.environ.get("GITHUB_REPOSITORY", "")
branch = os.environ.get("GITHUB_REF_NAME", "")
sha = os.environ.get("GITHUB_SHA", "")
run_id = os.environ.get("GITHUB_RUN_ID", "")

lines = [
    "Repository: " + repo,
    "Branch: " + branch,
    "Commit: " + sha,
    "Pipeline run: " + run_id,
    "Overall result: " + overall,
    "Total: %d   Passed: %d   Failed: %d" % (len(tests), passed, failed),
    "",
    "Individual results:",
]
for name, result, msg_text in tests:
    line = "  - %s: %s" % (name, result)
    if msg_text:
        line += "\n      Failure: " + msg_text
    lines.append(line)
lines.append("")
lines.append("The full JSON report is attached.")

user = os.environ["EMAIL_USER"].strip()
password = os.environ["EMAIL_PASSWORD"].replace(" ", "").strip()
to_addr = os.environ["EMAIL_TO"].strip()

msg = EmailMessage()
msg["Subject"] = "[%s] %s - %s" % (overall, repo, sha[:7])
msg["From"] = user
msg["To"] = to_addr
msg.set_content("\n".join(lines))

if os.path.exists("test-report.json"):
    with open("test-report.json", "rb") as f:
        msg.add_attachment(f.read(), maintype="application",
                           subtype="json", filename="test-report.json")


def send():
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465,
                              context=ssl.create_default_context(),
                              timeout=30) as s:
            s.login(user, password)
            s.send_message(msg)
        return
    except Exception as e:
        print("Port 465 failed:", repr(e))
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as s:
        s.starttls(context=ssl.create_default_context())
        s.login(user, password)
        s.send_message(msg)


send()
print("Email sent to", to_addr)
1. What is this project?

A simple web portal where students submit an assignment by entering:

Name
Registration number
Assignment title
Submission URL (a link, no file upload)

The app checks that all fields are filled in and that the URL is valid. Valid submissions are saved to a local JSON file (submissions.json) and shown in a list on the page.

Every time code is pushed to GitHub, a CI pipeline (GitHub Actions) runs the automated tests on a self-hosted runner (running on my own computer). After the tests finish:

A script builds a JSON report and sends it to a local receiver, which saves it as test-report.json on my computer.
The report is also emailed to a configurable address.
If all tests pass on main, a static demo of the portal is deployed to GitHub Pages.

The report is sent for both passing and failing runs.

Live demo (GitHub Pages): https://hamnazia.github.io/assignment-portal/

2. Project structure
assignment-portal/
├── app.py                      # Flask web application
├── templates/index.html        # Web page used by the Flask app
├── docs/index.html             # Static demo published to GitHub Pages
├── tests/test_app.py           # Automated tests (pytest)
├── receiver/receiver.py        # Local HTTP receiver that saves test-report.json
├── scripts/make_report.py      # Builds the JSON report and sends it to the receiver
├── scripts/send_email.py       # Emails the test report
├── .github/workflows/ci.yml    # CI pipeline configuration
├── requirements.txt            # Python dependencies
└── README.md
3. Requirements
Python 3.10 or newer
Git
A GitHub account
4. How to run the application
bash
# 1. Clone the repository
git clone https://github.com/HamnaZia/assignment-portal.git
cd assignment-portal

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the app
python app.py

Open http://127.0.0.1:5000 in your browser. Fill in the form and press Submit. Valid submissions are saved in submissions.json and listed on the page. Missing fields or an invalid URL show an error message and the submission is not saved.

5. How to run the tests

With the virtual environment active:

bash
pytest -v

The three test cases are:

Test name	What it checks	Expected result
test_valid_submission_is_saved	Complete details and a valid URL	Submission is saved and appears in the list
test_missing_registration_number_rejected	Registration number is empty	Submission is rejected with a validation message
test_invalid_url_rejected_and_not_saved	URL is not valid	Submission is rejected and not saved

If any test fails, pytest exits with an error and the CI test stage fails.

6. How to start the receiver

The receiver is a small Flask server that accepts the test report over HTTP and saves it as test-report.json on my computer.

Open a new terminal in the project folder:

bash
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac / Linux

cd receiver
python receiver.py
It listens on port 9000 (http://127.0.0.1:9000).
It accepts POST /report requests and checks the X-Token header against the secret token (default mysecret123, or set the RECEIVER_TOKEN environment variable before starting).
Each report overwrites receiver/test-report.json (the file is created inside the receiver folder).
Keep this terminal open while the pipeline runs.
7. Self-hosted runner (no tunnel needed)

A GitHub-hosted runner cannot reach my computer, because its "localhost" is the runner itself. Instead of using a tunnel (ngrok / Cloudflare), this project uses a self-hosted GitHub runner installed on my own computer. The job runs on my PC, so http://127.0.0.1:9000 points directly to my receiver.

Set up the runner once:

In the GitHub repo go to Settings -> Actions -> Runners -> New self-hosted runner.
Choose Windows and run the download and configure commands that GitHub shows (they include a one-time registration token).
Start the runner:
bash
   cd C:\actions-runner
   .\run.cmd
The runner shows as Idle (green) on the Runners page. Keep it running while pushing code.
8. Secrets

Secrets are stored in the repo under Settings -> Secrets and variables -> Actions -> New repository secret. They are never written in the code.

Secret name	Value	Used for
RECEIVER_URL	http://127.0.0.1:9000	Address of the local receiver
RECEIVER_TOKEN	same token as the receiver (e.g. mysecret123)	Protects the receiver
EMAIL_USERNAME	Gmail address used to send the report	Email login
EMAIL_PASSWORD	Gmail App Password (16 characters, no spaces)	Email login
EMAIL_TO	Address that receives the report	Email recipient
9. Pipeline flow (.github/workflows/ci.yml)

On every push to the repository:

The self-hosted runner checks out the pushed code.
Python dependencies are installed from requirements.txt.
pytest --junitxml=report.xml runs the tests. If a test fails, this step fails and the pipeline is marked failed.
scripts/make_report.py runs with if: always(), so it executes for both passing and failing runs. It builds a JSON report containing:
repository name, branch, commit SHA, pipeline run ID, timestamp
each test's name, result and failure message (if any)
total, passed and failed counts and the overall status
The script sends the report to RECEIVER_URL/report, and the receiver saves it as receiver/test-report.json.
scripts/send_email.py (also if: always()) emails the commit, overall result, counts, individual results and the attached JSON report.
The deploy job runs only if the test job passed (needs: test) and the branch is main. It publishes the docs/ folder to GitHub Pages. A failing run skips deploy, so the previously published version stays unchanged.
10. GitHub Pages
The static demo lives in docs/index.html (browser-only version of the portal that saves submissions in localStorage).
Enabled in Settings -> Pages -> Source: GitHub Actions.
Published URL: https://hamnazia.github.io/assignment-portal/
11. Demonstration checklist
Start the receiver (python receiver.py).
Start the self-hosted runner (.\run.cmd) and confirm it is Idle.
Push working code -> pipeline passes -> test-report.json shows "overall_status": "passed".
Introduce a defect (comment out the registration number check in app.py) and push -> pipeline fails -> test-report.json shows "overall_status": "failed" with the failure message.
Fix the defect and push -> pipeline passes again -> test-report.json is updated to "passed".
12. Troubleshooting
Job stays "Queued": the self-hosted runner is not running. Start .\run.cmd.
Report not saved: make sure the receiver terminal is running and RECEIVER_URL is http://127.0.0.1:9000.
401 unauthorized: RECEIVER_TOKEN in GitHub secrets must match the receiver's token.
Email not sent: check that EMAIL_USERNAME, EMAIL_PASSWORD (App Password) and EMAIL_TO secrets exist and are spelled exactly.

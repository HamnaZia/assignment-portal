import json, os
from urllib.parse import urlparse
from flask import Flask, render_template, request


def is_valid_url(url):
    p = urlparse(url)
    return p.scheme in ("http", "https") and "." in p.netloc


def create_app(data_file="submissions.json"):
    app = Flask(__name__)

    def load():
        if not os.path.exists(data_file):
            return []
        with open(data_file) as f:
            return json.load(f)

    def save(items):
        with open(data_file, "w") as f:
            json.dump(items, f, indent=2)

    @app.route("/", methods=["GET", "POST"])
    def index():
        errors, message, status = [], None, 200
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            reg_no = request.form.get("reg_no", "").strip()
            title = request.form.get("title", "").strip()
            url = request.form.get("url", "").strip()

            if not name:
                errors.append("Name is required.")
          #  if not reg_no:
           #     errors.append("Registration number is required.")
            if not title:
                errors.append("Assignment title is required.")
            if not url:
                errors.append("Submission URL is required.")
            elif not is_valid_url(url):
                errors.append("Submission URL is invalid.")

            if errors:
                status = 400
            else:
                items = load()
                items.append({"name": name, "reg_no": reg_no,
                              "title": title, "url": url})
                save(items)
                message = "Submission saved."
        return render_template("index.html", submissions=load(),
                               errors=errors, message=message), status

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
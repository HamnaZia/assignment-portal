import json, os, sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(str(tmp_path / "data.json"))
    return app.test_client(), tmp_path / "data.json"


def good_form():
    return {"name": "Ali", "reg_no": "FA22-BSE-001",
            "title": "DevOps Lab 1", "url": "https://github.com/ali/lab1"}


def test_valid_submission_is_saved(client):
    c, path = client
    r = c.post("/", data=good_form())
    assert r.status_code == 200
    assert b"Submission saved." in r.data
    assert b"FA22-BSE-001" in r.data          # appears in list


def test_missing_registration_number_rejected(client):
    c, path = client
    form = good_form()
    form["reg_no"] = ""
    r = c.post("/", data=form)
    assert r.status_code == 400
    assert b"Registration number is required." in r.data
    assert not path.exists()


def test_invalid_url_rejected_and_not_saved(client):
    c, path = client
    form = good_form()
    form["url"] = "not-a-url"
    r = c.post("/", data=form)
    assert r.status_code == 400
    assert b"Submission URL is invalid." in r.data
    assert not path.exists()
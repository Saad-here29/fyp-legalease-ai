"""FastAPI's own 422s use the app's error shape, with a message and a hint
(USE-04), and keep Pydantic's "detail" list for API clients."""


def test_422_has_message_and_hint(client):
    r = client.post("/api/v1/auth/login", json={"email": "not-an-email", "password": "x"})
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "validation_error"
    assert err["message"].startswith("email: ")
    assert err["hint"]
    assert r.json()["detail"][0]["loc"] == ["body", "email"]


def test_422_counts_further_errors(client):
    r = client.post("/api/v1/auth/login", json={})
    assert r.status_code == 422
    assert "(and 1 more)" in r.json()["error"]["message"]


def test_field_names_are_readable():
    from app.main import _field_name
    assert _field_name(("body", "case_type")) == "case type"
    assert _field_name(("query", "top_k")) == "top k"
    assert _field_name(("body",)) == "request"

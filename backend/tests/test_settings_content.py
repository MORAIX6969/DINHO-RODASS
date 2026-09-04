"""Iteration 7 — settings CRUD/persistence + content CRUD (faqs/services/gallery/testimonials) + quotes with photos."""
import io
import os
import re
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")

CANONICAL = {
    "phone": "(31) 99131-0824",
    "whatsapp": "5531991310824",
    "address": "Rua João Caetano, 1013 - Ambrosina, Belo Horizonte - MG, 30421-090",
}


@pytest.fixture(scope="session")
def creds():
    p = Path("/app/memory/test_credentials.md")
    if not p.exists():
        pytest.skip("missing credentials file")
    c = p.read_text(encoding="utf-8")
    e = re.search(r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?email(?:\*\*)?\s*:\s*`?([^`\s]+)", c)
    pw = re.search(r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?password(?:\*\*)?\s*:\s*`?([^`\s]+)", c)
    if not e or not pw:
        pytest.skip("no creds parsed")
    return {"email": e.group(1), "password": pw.group(1)}


@pytest.fixture(scope="session")
def client(creds):
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json=creds, timeout=30)
    if r.status_code != 200:
        pytest.fail(f"login failed {r.status_code}: {r.text[:300]}")
    token = r.json().get("token")
    assert token
    s.headers.update({"Authorization": f"Bearer {token}"})
    return s


# ---------- Settings module ----------
class TestSettings:
    def test_canonical_settings_present(self):
        r = requests.get(f"{BASE_URL}/api/settings", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert "_id" not in d
        assert d.get("settings_version") == 2, d.get("settings_version")
        for k, v in CANONICAL.items():
            assert d[k] == v, f"{k}={d[k]!r}"
        assert "Rua+Jo" in d["maps_url"]

    def test_settings_put_requires_auth(self):
        r = requests.put(f"{BASE_URL}/api/settings", json={"meta_title": "hack"}, timeout=30)
        assert r.status_code == 401

    def test_settings_update_persists(self, client):
        original = requests.get(f"{BASE_URL}/api/settings", timeout=30).json()
        payload = dict(original)
        payload.pop("_id", None)
        payload["meta_title"] = "TEST_Title_QA7"
        payload["phone"] = "(31) 90000-0000"
        r = client.put(f"{BASE_URL}/api/settings", json=payload, timeout=30)
        assert r.status_code == 200, r.text[:300]
        assert r.json()["meta_title"] == "TEST_Title_QA7"

        # verify persistence via fresh GET
        got = requests.get(f"{BASE_URL}/api/settings", timeout=30).json()
        assert got["meta_title"] == "TEST_Title_QA7"
        assert got["phone"] == "(31) 90000-0000"
        # verify propagation to public payload
        pub = requests.get(f"{BASE_URL}/api/public", timeout=30).json()
        assert pub["settings"]["meta_title"] == "TEST_Title_QA7"

        # restore
        restore = dict(original)
        restore.pop("_id", None)
        rr = client.put(f"{BASE_URL}/api/settings", json=restore, timeout=30)
        assert rr.status_code == 200
        assert requests.get(f"{BASE_URL}/api/settings", timeout=30).json()["phone"] == CANONICAL["phone"]


# ---------- Content CRUD ----------
@pytest.mark.parametrize("collection,create_payload,update_patch,title_field", [
    ("faqs", {"question": "TEST_QA7 pergunta?", "answer": "TEST resposta", "order": 99, "active": True},
     {"answer": "TEST resposta editada"}, "question"),
    ("services", {"title": "TEST_QA7 serviço", "category": "QA", "description": "d", "image_url": "https://x/y.png", "active": True},
     {"description": "editado"}, "title"),
    ("gallery", {"title": "TEST_QA7 foto", "category": "QA", "description": "d", "image_url": "https://x/y.png", "active": True},
     {"category": "QA2"}, "title"),
    ("testimonials", {"author": "TEST_QA7 cliente", "content": "otimo", "rating": 5, "active": True},
     {"content": "muito otimo"}, "author"),
])
def test_content_crud_and_public_reflection(client, collection, create_payload, update_patch, title_field):
    r = client.post(f"{BASE_URL}/api/admin/{collection}", json=create_payload, timeout=30)
    assert r.status_code == 200, r.text[:300]
    created = r.json()
    assert "_id" not in created
    item_id = created["id"]
    assert created[title_field] == create_payload[title_field]

    try:
        listed = client.get(f"{BASE_URL}/api/admin/{collection}", timeout=30)
        assert listed.status_code == 200
        assert any(x["id"] == item_id for x in listed.json())

        pub = requests.get(f"{BASE_URL}/api/public", timeout=30).json()
        assert any(x["id"] == item_id for x in pub[collection]), f"new {collection} item missing from /api/public"

        upd = client.put(f"{BASE_URL}/api/admin/{collection}/{item_id}", json={**create_payload, **update_patch}, timeout=30)
        assert upd.status_code == 200, upd.text[:300]
        key, val = next(iter(update_patch.items()))
        assert upd.json()[key] == val
        again = [x for x in client.get(f"{BASE_URL}/api/admin/{collection}", timeout=30).json() if x["id"] == item_id][0]
        assert again[key] == val
        pub2 = requests.get(f"{BASE_URL}/api/public", timeout=30).json()
        assert [x for x in pub2[collection] if x["id"] == item_id][0][key] == val
    finally:
        d = client.delete(f"{BASE_URL}/api/admin/{collection}/{item_id}", timeout=30)
        assert d.status_code == 200
    assert not any(x["id"] == item_id for x in client.get(f"{BASE_URL}/api/admin/{collection}", timeout=30).json())
    assert not any(x["id"] == item_id for x in requests.get(f"{BASE_URL}/api/public", timeout=30).json()[collection])


def test_inactive_item_hidden_from_public(client):
    r = client.post(f"{BASE_URL}/api/admin/faqs", json={"question": "TEST_QA7 inativa?", "answer": "a", "active": False}, timeout=30)
    assert r.status_code == 200
    item_id = r.json()["id"]
    try:
        pub = requests.get(f"{BASE_URL}/api/public", timeout=30).json()
        assert not any(x["id"] == item_id for x in pub["faqs"]), "inactive FAQ leaked to public payload"
    finally:
        client.delete(f"{BASE_URL}/api/admin/faqs/{item_id}", timeout=30)


# ---------- Quotes / leads ----------
def test_quote_with_photo_visible_in_admin(client):
    png = (b"\x89PNG\r\n\x1a\n" + b"0" * 64)
    files = [("photos", ("qa7.png", io.BytesIO(png), "image/png"))]
    data = {"name": "TEST_QA7 Cliente", "phone": "31988887777", "vehicle": "Civic", "year": "2022",
            "interest": "Rodas", "message": "Quero orçamento", "origin": "Formulário de orçamento"}
    r = requests.post(f"{BASE_URL}/api/quotes", data=data, files=files, timeout=60)
    assert r.status_code == 200, r.text[:300]
    q = r.json()
    assert q["name"] == data["name"] and q["phone"] == data["phone"]
    assert len(q["photos"]) == 1 and q["photos"][0].startswith("/api/files/")
    assert q["status"] == "Novo"

    img = requests.get(f"{BASE_URL}{q['photos'][0]}", timeout=30)
    assert img.status_code == 200 and img.content == png

    quotes = client.get(f"{BASE_URL}/api/admin/quotes", timeout=30).json()
    match = [x for x in quotes if x["id"] == q["id"]]
    assert match, "quote not visible in admin listing"
    m = match[0]
    for field in ("name", "phone", "vehicle", "year", "interest", "message"):
        assert m[field] == data[field]
    assert m["photos"] == q["photos"]

    leads = client.get(f"{BASE_URL}/api/admin/leads", timeout=30).json()
    assert any(x.get("name") == data["name"] for x in leads), "lead mirror missing"

    client.delete(f"{BASE_URL}/api/admin/quotes/{q['id']}", timeout=30)
    for lead in [x for x in leads if x.get("name") == data["name"]]:
        client.delete(f"{BASE_URL}/api/admin/leads/{lead['id']}", timeout=30)


def test_quote_missing_required_field_returns_422():
    r = requests.post(f"{BASE_URL}/api/quotes", data={"phone": "31999999999"}, timeout=30)
    assert r.status_code == 422


def test_login_non_ascii_email_does_not_500():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "usuário@exemplo.com", "password": "x"}, timeout=30)
    assert r.status_code == 401, f"expected 401, got {r.status_code}: {r.text[:200]}"

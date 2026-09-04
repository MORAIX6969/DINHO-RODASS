import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://github-importer-58.preview.emergentagent.com").rstrip("/")

def test_public_and_quote_flow():
    public = requests.get(f"{BASE_URL}/api/public", timeout=20)
    assert public.status_code == 200
    data = public.json()
    assert all(k in data for k in ("services", "gallery", "faqs", "settings"))
    quote = requests.post(f"{BASE_URL}/api/quotes", data={"name":"TEST_Ana", "phone":"31999999999", "vehicle":"Civic"}, timeout=20)
    assert quote.status_code == 200
    assert quote.json()["name"] == "TEST_Ana"

def test_auth_and_services_crud():
    bad = requests.post(f"{BASE_URL}/api/auth/login", json={"email":"wrong@example.com", "password":"wrong"}, timeout=20)
    assert bad.status_code == 401
    good = requests.post(f"{BASE_URL}/api/auth/login", json={"email":"admin@dinhorodas.com", "password":"Dinho#2026"}, timeout=20)
    assert good.status_code == 200 and good.json().get("token")
    headers = {"Authorization": f"Bearer {good.json()['token']}"}
    created = requests.post(f"{BASE_URL}/api/admin/services", json={"title":"TEST Serviço", "description":"Teste"}, headers=headers, timeout=20)
    assert created.status_code == 200
    item_id = created.json()["id"]
    listed = requests.get(f"{BASE_URL}/api/admin/services", headers=headers, timeout=20)
    assert listed.status_code == 200 and any(x["id"] == item_id for x in listed.json())
    deleted = requests.delete(f"{BASE_URL}/api/admin/services/{item_id}", headers=headers, timeout=20)
    assert deleted.status_code == 200 and deleted.json()["ok"] is True

# Dashboard metrics: auth guard + payload shape (added iteration 2)
def test_dashboard_metrics_auth_and_shape():
    unauth = requests.get(f"{BASE_URL}/api/dashboard/metrics", timeout=20)
    assert unauth.status_code in (401, 403), unauth.status_code
    login = requests.post(f"{BASE_URL}/api/auth/login", json={"email":"admin@dinhorodas.com", "password":"Dinho#2026"}, timeout=20)
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['token']}"}
    metrics = requests.get(f"{BASE_URL}/api/dashboard/metrics", headers=headers, timeout=20)
    assert metrics.status_code == 200
    body = metrics.json()
    for key in ("total_leads", "total_quotes", "new_quotes", "converted"):
        assert key in body, f"missing {key} in {body}"
        assert isinstance(body[key], int)
    assert "_id" not in body

# Bad token must not be accepted (added iteration 2)
def test_admin_rejects_invalid_token():
    r = requests.get(f"{BASE_URL}/api/admin/services", headers={"Authorization": "Bearer notavalidtoken"}, timeout=20)
    assert r.status_code in (401, 403), r.status_code

# Health endpoint (added iteration 3 - deploy config bugfix verification)
def test_health_ok():
    r = requests.get(f"{BASE_URL}/api/health", timeout=20)
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    assert body.get("status") == "ok", body

# Health must report database connected (iteration 4 - requirements.txt slim-down regression)
def test_health_database_connected():
    r = requests.get(f"{BASE_URL}/api/health", timeout=20)
    assert r.status_code == 200, r.text[:300]
    assert r.json().get("database") == "connected", r.json()

# Quote with multipart image upload -> file stored and served by /api/files/{id} (python-multipart dep)
def test_quote_with_image_upload_and_file_retrieval():
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
        "890000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
    )
    r = requests.post(
        f"{BASE_URL}/api/quotes",
        data={"name": "TEST_Upload", "phone": "31988887777", "vehicle": "Gol", "year": "2020",
              "interest": "Rodas", "message": "TEST upload", "origin": "site-form"},
        files=[("photos", ("test.png", png, "image/png"))],
        timeout=30,
    )
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    assert body["name"] == "TEST_Upload"
    assert body["phone"] == "31988887777"
    assert body["status"] == "Novo"
    assert "_id" not in body
    assert len(body["photos"]) == 1, body
    file_url = body["photos"][0]
    assert file_url.startswith("/api/files/")

    img = requests.get(f"{BASE_URL}{file_url}", timeout=20)
    assert img.status_code == 200
    assert img.headers.get("content-type", "").startswith("image/")
    assert img.content == png

    # persisted in quotes listing
    login = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "admin@dinhorodas.com", "password": "Dinho#2026"}, timeout=20)
    headers = {"Authorization": f"Bearer {login.json()['token']}"}
    listed = requests.get(f"{BASE_URL}/api/admin/quotes", headers=headers, timeout=20)
    assert listed.status_code == 200
    match = [x for x in listed.json() if x["id"] == body["id"]]
    assert match and match[0]["photos"] == body["photos"]
    requests.delete(f"{BASE_URL}/api/admin/quotes/{body['id']}", headers=headers, timeout=20)

# Unknown file id -> 404
def test_unknown_file_returns_404():
    r = requests.get(f"{BASE_URL}/api/files/does-not-exist", timeout=20)
    assert r.status_code == 404, r.status_code

# Invalid collection name must 404, not 500
def test_invalid_collection_returns_404():
    login = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "admin@dinhorodas.com", "password": "Dinho#2026"}, timeout=20)
    headers = {"Authorization": f"Bearer {login.json()['token']}"}
    r = requests.get(f"{BASE_URL}/api/admin/bogus", headers=headers, timeout=20)
    assert r.status_code == 404, r.status_code

# /api/public shape: services/gallery/faqs lists, settings dict with company data
def test_public_payload_shape():
    data = requests.get(f"{BASE_URL}/api/public", timeout=20).json()
    for key in ("services", "testimonials", "gallery", "faqs"):
        assert isinstance(data[key], list), key
        for row in data[key]:
            assert "_id" not in row
    assert isinstance(data["settings"], dict)
    assert data["settings"].get("company_name") == "Dinho Rodas", data["settings"]
    assert data["settings"].get("whatsapp")

# Login error responses must be JSON with a `detail` message (frontend renders d.detail)
def test_login_error_is_json_with_detail():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email":"admin@dinhorodas.com", "password":"wrongpass"}, timeout=20)
    assert r.status_code == 401
    assert "application/json" in r.headers.get("content-type", "")
    assert isinstance(r.json().get("detail"), str) and r.json()["detail"]

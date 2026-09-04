#!/usr/bin/env python3
"""
Backend API Tests for Dinho Rodas
Tests focus on: Public testimonials array, Settings, Services CRUD, Gallery CRUD
"""
import requests
import json
import io
from pathlib import Path

# Configuration
BASE_URL = "https://2e65216d-6450-4c87-92ca-a611eeb27631.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@dinhorodas.com.br"
ADMIN_PASSWORD = "DinhoAdmin@2026"

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def log_pass(test_name):
    print(f"✅ PASS: {test_name}")
    test_results["passed"].append(test_name)

def log_fail(test_name, reason):
    print(f"❌ FAIL: {test_name}")
    print(f"   Reason: {reason}")
    test_results["failed"].append({"test": test_name, "reason": reason})

def log_warning(test_name, reason):
    print(f"⚠️  WARNING: {test_name}")
    print(f"   Reason: {reason}")
    test_results["warnings"].append({"test": test_name, "reason": reason})

def get_auth_token():
    """Login and get auth token"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10
        )
        if response.status_code == 200:
            token = response.json().get("token")
            log_pass("Admin login")
            return token
        else:
            log_fail("Admin login", f"Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        log_fail("Admin login", str(e))
        return None

def test_public_testimonials_array(token):
    """
    Test 1: Public testimonials array
    - GET /api/public must contain testimonials key (array)
    - POST testimonial with valid data
    - Verify it appears in public array
    - DELETE testimonial
    - Verify it disappears from public array
    """
    print("\n" + "="*80)
    print("TEST 1: PUBLIC TESTIMONIALS ARRAY")
    print("="*80)
    
    # Step 1a: GET /api/public - verify testimonials key exists
    try:
        response = requests.get(f"{BASE_URL}/public", timeout=10)
        if response.status_code != 200:
            log_fail("GET /api/public", f"Status {response.status_code}: {response.text}")
            return
        
        data = response.json()
        if "testimonials" not in data:
            log_fail("GET /api/public - testimonials key", "testimonials key missing from response")
            return
        
        if not isinstance(data["testimonials"], list):
            log_fail("GET /api/public - testimonials type", f"testimonials is not an array, got {type(data['testimonials'])}")
            return
        
        log_pass("GET /api/public returns testimonials array")
        initial_count = len(data["testimonials"])
        print(f"   Initial testimonials count: {initial_count}")
        
    except Exception as e:
        log_fail("GET /api/public", str(e))
        return
    
    # Step 1b: POST /api/admin/testimonials
    testimonial_data = {
        "author": "Cliente Teste",
        "content": "Atendimento excepcional na Dinho Rodas!",
        "rating": 5,
        "active": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/admin/testimonials",
            json=testimonial_data,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            log_fail("POST /api/admin/testimonials", f"Status {response.status_code}: {response.text}")
            return
        
        created = response.json()
        if "id" not in created:
            log_fail("POST /api/admin/testimonials - response", "No id in response")
            return
        
        testimonial_id = created["id"]
        log_pass("POST /api/admin/testimonials")
        print(f"   Created testimonial ID: {testimonial_id}")
        
    except Exception as e:
        log_fail("POST /api/admin/testimonials", str(e))
        return
    
    # Step 1c: GET /api/public - verify testimonial appears
    try:
        response = requests.get(f"{BASE_URL}/public", timeout=10)
        if response.status_code != 200:
            log_fail("GET /api/public (after create)", f"Status {response.status_code}")
            return
        
        data = response.json()
        testimonials = data.get("testimonials", [])
        
        # Find the created testimonial
        found = None
        for t in testimonials:
            if t.get("id") == testimonial_id:
                found = t
                break
        
        if not found:
            log_fail("GET /api/public - testimonial visibility", f"Created testimonial {testimonial_id} not found in public array")
            return
        
        # Verify fields match
        if found.get("author") != testimonial_data["author"]:
            log_fail("GET /api/public - testimonial author", f"Expected '{testimonial_data['author']}', got '{found.get('author')}'")
            return
        
        if found.get("content") != testimonial_data["content"]:
            log_fail("GET /api/public - testimonial content", f"Expected '{testimonial_data['content']}', got '{found.get('content')}'")
            return
        
        if found.get("rating") != testimonial_data["rating"]:
            log_fail("GET /api/public - testimonial rating", f"Expected {testimonial_data['rating']}, got {found.get('rating')}")
            return
        
        log_pass("GET /api/public shows created testimonial with correct data")
        
    except Exception as e:
        log_fail("GET /api/public (after create)", str(e))
        return
    
    # Step 1d: DELETE /api/admin/testimonials/{id}
    try:
        response = requests.delete(
            f"{BASE_URL}/admin/testimonials/{testimonial_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            log_fail("DELETE /api/admin/testimonials", f"Status {response.status_code}: {response.text}")
            return
        
        log_pass("DELETE /api/admin/testimonials")
        
    except Exception as e:
        log_fail("DELETE /api/admin/testimonials", str(e))
        return
    
    # Step 1e: GET /api/public - verify testimonial disappeared
    try:
        response = requests.get(f"{BASE_URL}/public", timeout=10)
        if response.status_code != 200:
            log_fail("GET /api/public (after delete)", f"Status {response.status_code}")
            return
        
        data = response.json()
        testimonials = data.get("testimonials", [])
        
        # Verify testimonial is gone
        for t in testimonials:
            if t.get("id") == testimonial_id:
                log_fail("GET /api/public - testimonial deletion", f"Deleted testimonial {testimonial_id} still appears in public array")
                return
        
        log_pass("GET /api/public - deleted testimonial removed from array")
        
    except Exception as e:
        log_fail("GET /api/public (after delete)", str(e))
        return

def test_services_crud_upload(token):
    """
    Test 2: Services CRUD + upload (regression)
    - Upload PNG
    - Create service with image_url
    - GET /api/public shows service
    - DELETE service
    """
    print("\n" + "="*80)
    print("TEST 2: SERVICES CRUD + UPLOAD (REGRESSION)")
    print("="*80)
    
    # Step 2a: Upload PNG
    try:
        # Create a minimal PNG (1x1 pixel)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        
        files = {'file': ('test.png', io.BytesIO(png_data), 'image/png')}
        response = requests.post(
            f"{BASE_URL}/admin/upload",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            log_fail("POST /api/admin/upload (services)", f"Status {response.status_code}: {response.text}")
            return
        
        upload_result = response.json()
        if "url" not in upload_result:
            log_fail("POST /api/admin/upload - response", "No url in response")
            return
        
        image_url = upload_result["url"]
        log_pass("POST /api/admin/upload (services)")
        print(f"   Uploaded image URL: {image_url}")
        
    except Exception as e:
        log_fail("POST /api/admin/upload (services)", str(e))
        return
    
    # Step 2b: Create service
    service_data = {
        "title": "Reg Test",
        "description": "desc",
        "image_url": image_url,
        "active": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/admin/services",
            json=service_data,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            log_fail("POST /api/admin/services", f"Status {response.status_code}: {response.text}")
            return
        
        created = response.json()
        if "id" not in created:
            log_fail("POST /api/admin/services - response", "No id in response")
            return
        
        service_id = created["id"]
        log_pass("POST /api/admin/services")
        print(f"   Created service ID: {service_id}")
        
    except Exception as e:
        log_fail("POST /api/admin/services", str(e))
        return
    
    # Step 2c: GET /api/public - verify service appears
    try:
        response = requests.get(f"{BASE_URL}/public", timeout=10)
        if response.status_code != 200:
            log_fail("GET /api/public (services)", f"Status {response.status_code}")
            return
        
        data = response.json()
        services = data.get("services", [])
        
        # Find the created service
        found = None
        for s in services:
            if s.get("id") == service_id:
                found = s
                break
        
        if not found:
            log_fail("GET /api/public - service visibility", f"Created service {service_id} not found in public array")
            return
        
        # Verify image_url
        if found.get("image_url") != image_url:
            log_fail("GET /api/public - service image_url", f"Expected '{image_url}', got '{found.get('image_url')}'")
            return
        
        log_pass("GET /api/public shows created service with correct image_url")
        
    except Exception as e:
        log_fail("GET /api/public (services)", str(e))
        return
    
    # Step 2d: DELETE service
    try:
        response = requests.delete(
            f"{BASE_URL}/admin/services/{service_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            log_fail("DELETE /api/admin/services", f"Status {response.status_code}: {response.text}")
            return
        
        log_pass("DELETE /api/admin/services")
        
    except Exception as e:
        log_fail("DELETE /api/admin/services", str(e))
        return

def test_gallery_crud_upload(token):
    """
    Test 3: Gallery CRUD + upload (regression)
    - Verify 2 items exist: "Fachada Dinho Rodas" and "Roda VW premium"
    - Upload PNG
    - Create gallery item
    - GET /api/public shows it
    - DELETE it
    """
    print("\n" + "="*80)
    print("TEST 3: GALLERY CRUD + UPLOAD (REGRESSION)")
    print("="*80)
    
    # Step 3a: Verify seeded items exist
    try:
        response = requests.get(
            f"{BASE_URL}/admin/gallery",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            log_fail("GET /api/admin/gallery", f"Status {response.status_code}: {response.text}")
            return
        
        gallery_items = response.json()
        
        # Look for the 2 seeded items
        titles = [item.get("title") for item in gallery_items]
        
        if "Fachada Dinho Rodas" not in titles:
            log_fail("GET /api/admin/gallery - seeded items", "Missing 'Fachada Dinho Rodas'")
            return
        
        if "Roda VW premium" not in titles:
            log_fail("GET /api/admin/gallery - seeded items", "Missing 'Roda VW premium'")
            return
        
        log_pass("GET /api/admin/gallery contains seeded items")
        print(f"   Found {len(gallery_items)} gallery items including required seeds")
        
    except Exception as e:
        log_fail("GET /api/admin/gallery", str(e))
        return
    
    # Step 3b: Upload PNG
    try:
        # Create a minimal PNG (1x1 pixel)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        
        files = {'file': ('test_gallery.png', io.BytesIO(png_data), 'image/png')}
        response = requests.post(
            f"{BASE_URL}/admin/upload",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            log_fail("POST /api/admin/upload (gallery)", f"Status {response.status_code}: {response.text}")
            return
        
        upload_result = response.json()
        if "url" not in upload_result:
            log_fail("POST /api/admin/upload - response", "No url in response")
            return
        
        image_url = upload_result["url"]
        log_pass("POST /api/admin/upload (gallery)")
        print(f"   Uploaded image URL: {image_url}")
        
    except Exception as e:
        log_fail("POST /api/admin/upload (gallery)", str(e))
        return
    
    # Step 3c: Create gallery item
    gallery_data = {
        "title": "Reg Test Photo",
        "image_url": image_url,
        "active": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/admin/gallery",
            json=gallery_data,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            log_fail("POST /api/admin/gallery", f"Status {response.status_code}: {response.text}")
            return
        
        created = response.json()
        if "id" not in created:
            log_fail("POST /api/admin/gallery - response", "No id in response")
            return
        
        gallery_id = created["id"]
        log_pass("POST /api/admin/gallery")
        print(f"   Created gallery item ID: {gallery_id}")
        
    except Exception as e:
        log_fail("POST /api/admin/gallery", str(e))
        return
    
    # Step 3d: GET /api/public - verify gallery item appears
    try:
        response = requests.get(f"{BASE_URL}/public", timeout=10)
        if response.status_code != 200:
            log_fail("GET /api/public (gallery)", f"Status {response.status_code}")
            return
        
        data = response.json()
        gallery = data.get("gallery", [])
        
        # Find the created gallery item
        found = None
        for g in gallery:
            if g.get("id") == gallery_id:
                found = g
                break
        
        if not found:
            log_fail("GET /api/public - gallery visibility", f"Created gallery item {gallery_id} not found in public array")
            return
        
        log_pass("GET /api/public shows created gallery item")
        
    except Exception as e:
        log_fail("GET /api/public (gallery)", str(e))
        return
    
    # Step 3e: DELETE gallery item
    try:
        response = requests.delete(
            f"{BASE_URL}/admin/gallery/{gallery_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            log_fail("DELETE /api/admin/gallery", f"Status {response.status_code}: {response.text}")
            return
        
        log_pass("DELETE /api/admin/gallery")
        
    except Exception as e:
        log_fail("DELETE /api/admin/gallery", str(e))
        return

def test_settings_regression(token):
    """
    Test 4: Settings endpoint (regression - MUST NOT BREAK)
    - GET /api/settings returns full object
    - PUT /api/settings with same body preserves values
    """
    print("\n" + "="*80)
    print("TEST 4: SETTINGS ENDPOINT (REGRESSION - CRITICAL)")
    print("="*80)
    
    # Step 4a: GET /api/settings
    try:
        response = requests.get(f"{BASE_URL}/settings", timeout=10)
        if response.status_code != 200:
            log_fail("GET /api/settings", f"Status {response.status_code}: {response.text}")
            return
        
        settings = response.json()
        
        # Verify required fields
        required_fields = ["company_name", "phone", "whatsapp", "address", "hours"]
        missing_fields = []
        for field in required_fields:
            if field not in settings:
                missing_fields.append(field)
        
        if missing_fields:
            log_fail("GET /api/settings - required fields", f"Missing fields: {', '.join(missing_fields)}")
            return
        
        log_pass("GET /api/settings returns all required fields")
        print(f"   company_name: {settings.get('company_name')}")
        print(f"   phone: {settings.get('phone')}")
        print(f"   whatsapp: {settings.get('whatsapp')}")
        
    except Exception as e:
        log_fail("GET /api/settings", str(e))
        return
    
    # Step 4b: PUT /api/settings with same body
    try:
        # Remove _id if present (MongoDB field)
        settings_copy = {k: v for k, v in settings.items() if k != "_id"}
        
        response = requests.put(
            f"{BASE_URL}/settings",
            json=settings_copy,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code != 200:
            log_fail("PUT /api/settings", f"Status {response.status_code}: {response.text}")
            return
        
        updated_settings = response.json()
        
        # Verify all values preserved
        mismatches = []
        for key, value in settings.items():
            if key == "_id":
                continue
            if updated_settings.get(key) != value:
                mismatches.append(f"{key}: expected '{value}', got '{updated_settings.get(key)}'")
        
        if mismatches:
            log_fail("PUT /api/settings - value preservation", f"Mismatches: {'; '.join(mismatches)}")
            return
        
        log_pass("PUT /api/settings preserves all values")
        
    except Exception as e:
        log_fail("PUT /api/settings", str(e))
        return

def print_summary():
    """Print test summary"""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    print(f"\n✅ PASSED: {len(test_results['passed'])}")
    for test in test_results["passed"]:
        print(f"   - {test}")
    
    if test_results["warnings"]:
        print(f"\n⚠️  WARNINGS: {len(test_results['warnings'])}")
        for warning in test_results["warnings"]:
            print(f"   - {warning['test']}: {warning['reason']}")
    
    if test_results["failed"]:
        print(f"\n❌ FAILED: {len(test_results['failed'])}")
        for failure in test_results["failed"]:
            print(f"   - {failure['test']}")
            print(f"     Reason: {failure['reason']}")
    
    print("\n" + "="*80)
    if test_results["failed"]:
        print("RESULT: TESTS FAILED ❌")
    else:
        print("RESULT: ALL TESTS PASSED ✅")
    print("="*80)

def main():
    print("="*80)
    print("DINHO RODAS BACKEND API TESTS")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Admin: {ADMIN_EMAIL}")
    print("="*80)
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("\n❌ Cannot proceed without auth token")
        return
    
    # Run all tests
    test_public_testimonials_array(token)
    test_services_crud_upload(token)
    test_gallery_crud_upload(token)
    test_settings_regression(token)
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    main()

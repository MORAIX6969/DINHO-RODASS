#!/usr/bin/env python3
"""
Smoke test for Dinho Rodas backend after frontend 401 handler change.
Tests all critical auth flows including deliberate bad token scenarios.
"""

import requests
import json
import sys

# Backend URL from frontend/.env
BASE_URL = "https://2e65216d-6450-4c87-92ca-a611eeb27631.preview.emergentagent.com"
API_URL = f"{BASE_URL}/api"

# Admin credentials from /app/memory/test_credentials.md
ADMIN_EMAIL = "admin@dinhorodas.com.br"
ADMIN_PASSWORD = "DinhoAdmin@2026"

def print_test(name):
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print('='*60)

def print_result(success, message):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")
    return success

def test_health():
    """Test 1: GET /api/health returns 200 with {status:"ok", database:"connected"}"""
    print_test("Health Check")
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code != 200:
            return print_result(False, f"Expected 200, got {response.status_code}")
        
        data = response.json()
        if data.get("status") != "ok":
            return print_result(False, f"Expected status='ok', got {data.get('status')}")
        
        if data.get("database") != "connected":
            return print_result(False, f"Expected database='connected', got {data.get('database')}")
        
        return print_result(True, "Health endpoint returns correct response")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_login():
    """Test 2: POST /api/auth/login with admin credentials returns 200 with token"""
    print_test("Admin Login")
    try:
        payload = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        response = requests.post(f"{API_URL}/auth/login", json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
        if response.status_code != 200:
            return print_result(False, f"Expected 200, got {response.status_code}"), None
        
        data = response.json()
        token = data.get("token")
        
        if not token:
            return print_result(False, "No token in response"), None
        
        return print_result(True, f"Login successful, token received (length: {len(token)})"), token
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}"), None

def test_authenticated_testimonials(token):
    """Test 3: With token: GET /api/admin/testimonials returns 200 (array). POST creates. DELETE removes."""
    print_test("Authenticated Testimonials CRUD")
    headers = {"Authorization": f"Bearer {token}"}
    created_id = None
    
    try:
        # GET testimonials
        print("\n--- GET /api/admin/testimonials ---")
        response = requests.get(f"{API_URL}/admin/testimonials", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
        if response.status_code != 200:
            return print_result(False, f"GET expected 200, got {response.status_code}")
        
        data = response.json()
        if not isinstance(data, list):
            return print_result(False, f"GET expected array, got {type(data)}")
        
        print(f"✓ GET returns array with {len(data)} items")
        
        # POST create testimonial
        print("\n--- POST /api/admin/testimonials ---")
        new_testimonial = {
            "name": "Test Smoke User",
            "text": "This is a smoke test testimonial for backend regression check.",
            "rating": 5
        }
        response = requests.post(f"{API_URL}/admin/testimonials", json=new_testimonial, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
        if response.status_code not in [200, 201]:
            return print_result(False, f"POST expected 200/201, got {response.status_code}")
        
        created = response.json()
        created_id = created.get("id")
        
        if not created_id:
            return print_result(False, "POST did not return id")
        
        print(f"✓ POST created testimonial with id: {created_id}")
        
        # DELETE testimonial
        print("\n--- DELETE /api/admin/testimonials/{id} ---")
        response = requests.delete(f"{API_URL}/admin/testimonials/{created_id}", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200] if response.text else '(empty)'}")
        
        if response.status_code not in [200, 204]:
            return print_result(False, f"DELETE expected 200/204, got {response.status_code}")
        
        print(f"✓ DELETE removed testimonial")
        
        return print_result(True, "Authenticated testimonials CRUD working correctly")
        
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_unauthenticated_testimonials():
    """Test 4: Without token: GET /api/admin/testimonials returns 401 with detail message"""
    print_test("Unauthenticated Testimonials Access")
    try:
        response = requests.get(f"{API_URL}/admin/testimonials", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code != 401:
            return print_result(False, f"Expected 401, got {response.status_code} (SECURITY ISSUE: endpoint should require auth)")
        
        data = response.json()
        if "detail" not in data:
            return print_result(False, "Expected 'detail' field in 401 response")
        
        return print_result(True, f"Correctly returns 401 with detail: '{data.get('detail')}'")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_bad_token_testimonials():
    """Test 5: With DELIBERATELY BAD/expired token: GET /api/admin/testimonials returns 401"""
    print_test("Bad/Expired Token Testimonials Access")
    bad_headers = {"Authorization": "Bearer fake123"}
    try:
        response = requests.get(f"{API_URL}/admin/testimonials", headers=bad_headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code != 401:
            return print_result(False, f"Expected 401, got {response.status_code} (CRITICAL: frontend 401 auto-logout depends on this)")
        
        data = response.json()
        if "detail" not in data:
            return print_result(False, "Expected 'detail' field in 401 response")
        
        return print_result(True, f"Correctly returns 401 for bad token with detail: '{data.get('detail')}'")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def test_settings():
    """Test 6: GET /api/settings returns 200 with settings"""
    print_test("Settings Endpoint")
    try:
        response = requests.get(f"{API_URL}/settings", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:300]}")
        
        if response.status_code != 200:
            return print_result(False, f"Expected 200, got {response.status_code}")
        
        data = response.json()
        required_fields = ["company_name", "phone", "whatsapp", "address"]
        missing = [f for f in required_fields if f not in data]
        
        if missing:
            return print_result(False, f"Missing required fields: {missing}")
        
        return print_result(True, f"Settings endpoint returns correct data with company_name='{data.get('company_name')}'")
    except Exception as e:
        return print_result(False, f"Exception: {str(e)}")

def main():
    print("\n" + "="*60)
    print("DINHO RODAS BACKEND SMOKE TEST")
    print("After frontend 401 handler change - Regression check")
    print("="*60)
    print(f"Backend URL: {BASE_URL}")
    print(f"Admin Email: {ADMIN_EMAIL}")
    
    results = []
    
    # Test 1: Health
    results.append(test_health())
    
    # Test 2: Login
    login_result, token = test_login()
    results.append(login_result)
    
    if not token:
        print("\n❌ CRITICAL: Cannot proceed with authenticated tests - login failed")
        print_summary(results)
        sys.exit(1)
    
    # Test 3: Authenticated testimonials CRUD
    results.append(test_authenticated_testimonials(token))
    
    # Test 4: Unauthenticated access
    results.append(test_unauthenticated_testimonials())
    
    # Test 5: Bad token access (CRITICAL for frontend 401 handler)
    results.append(test_bad_token_testimonials())
    
    # Test 6: Settings
    results.append(test_settings())
    
    print_summary(results)
    
    if not all(results):
        sys.exit(1)

def print_summary(results):
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"Tests Passed: {passed}/{total}")
    
    if all(results):
        print("\n✅ ALL SMOKE TESTS PASSED - Backend regression check successful")
        print("Frontend 401 handler will work correctly (backend returns 401 for bad tokens)")
    else:
        print("\n❌ SOME TESTS FAILED - See details above")

if __name__ == "__main__":
    main()

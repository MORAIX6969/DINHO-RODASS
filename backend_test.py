#!/usr/bin/env python3
"""
Surgical fix verification for Dinho Rodas backend.
Tests Services/Gallery separation and new upload endpoint.
"""
import requests
import io
from PIL import Image

# Configuration
BASE_URL = "https://2e65216d-6450-4c87-92ca-a611eeb27631.preview.emergentagent.com"
ADMIN_EMAIL = "admin@dinhorodas.com.br"
ADMIN_PASSWORD = "DinhoAdmin@2026"

# Global token storage
AUTH_TOKEN = None

def log_test(name, passed, details=""):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"\n{status}: {name}")
    if details:
        print(f"  Details: {details}")
    return passed

def test_health():
    """Test 1: Health endpoint"""
    try:
        resp = requests.get(f"{BASE_URL}/api/health", timeout=10)
        data = resp.json()
        
        passed = (
            resp.status_code == 200 and
            data.get('status') == 'ok' and
            data.get('database') == 'connected'
        )
        
        return log_test(
            "Health Check",
            passed,
            f"Status: {resp.status_code}, Response: {data}"
        )
    except Exception as e:
        return log_test("Health Check", False, f"Exception: {str(e)}")

def test_login():
    """Test 2: Admin login"""
    global AUTH_TOKEN
    try:
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10
        )
        data = resp.json()
        
        if resp.status_code == 200 and 'token' in data:
            AUTH_TOKEN = data['token']
            return log_test(
                "Admin Login",
                True,
                f"Token received: {AUTH_TOKEN[:20]}..."
            )
        else:
            return log_test(
                "Admin Login",
                False,
                f"Status: {resp.status_code}, Response: {data}"
            )
    except Exception as e:
        return log_test("Admin Login", False, f"Exception: {str(e)}")

def test_services_crud():
    """Test 3: Services CRUD (independent from gallery)"""
    if not AUTH_TOKEN:
        return log_test("Services CRUD", False, "No auth token available")
    
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    service_id = None
    all_passed = True
    
    # 3a: Create service
    try:
        resp = requests.post(
            f"{BASE_URL}/api/admin/services",
            json={
                "title": "Rodas",
                "description": "Pintando suas rodas.",
                "active": True
            },
            headers=headers,
            timeout=10
        )
        data = resp.json()
        
        if resp.status_code == 200 and 'id' in data:
            service_id = data['id']
            log_test(
                "Create Service",
                True,
                f"Service created with ID: {service_id}"
            )
        else:
            all_passed = False
            log_test(
                "Create Service",
                False,
                f"Status: {resp.status_code}, Response: {data}"
            )
            return False
    except Exception as e:
        log_test("Create Service", False, f"Exception: {str(e)}")
        return False
    
    # 3b: Verify service in services collection
    try:
        resp = requests.get(
            f"{BASE_URL}/api/admin/services",
            headers=headers,
            timeout=10
        )
        services = resp.json()
        
        found = any(
            s.get('title') == 'Rodas' and 
            s.get('description') == 'Pintando suas rodas.' and
            s.get('id') == service_id
            for s in services
        )
        
        if not log_test(
            "Service in Services Collection",
            found,
            f"Found {len(services)} services, target service {'found' if found else 'NOT FOUND'}"
        ):
            all_passed = False
    except Exception as e:
        log_test("Service in Services Collection", False, f"Exception: {str(e)}")
        all_passed = False
    
    # 3c: Verify service NOT in gallery collection
    try:
        resp = requests.get(
            f"{BASE_URL}/api/admin/gallery",
            headers=headers,
            timeout=10
        )
        gallery = resp.json()
        
        # Check if our specific service appears in gallery
        contaminated = any(
            g.get('title') == 'Rodas' and 
            g.get('description') == 'Pintando suas rodas.'
            for g in gallery
        )
        
        if not log_test(
            "Service NOT in Gallery Collection",
            not contaminated,
            f"Gallery has {len(gallery)} items, contamination: {contaminated}"
        ):
            all_passed = False
    except Exception as e:
        log_test("Service NOT in Gallery Collection", False, f"Exception: {str(e)}")
        all_passed = False
    
    # 3d: Verify in public endpoint
    try:
        resp = requests.get(f"{BASE_URL}/api/public", timeout=10)
        public_data = resp.json()
        
        # Service should be in services array
        in_services = any(
            s.get('title') == 'Rodas' and 
            s.get('description') == 'Pintando suas rodas.'
            for s in public_data.get('services', [])
        )
        
        # Service should NOT be in gallery array
        in_gallery = any(
            g.get('title') == 'Rodas' and 
            g.get('description') == 'Pintando suas rodas.'
            for g in public_data.get('gallery', [])
        )
        
        passed = in_services and not in_gallery
        if not log_test(
            "Public Endpoint Separation",
            passed,
            f"In services: {in_services}, In gallery: {in_gallery}"
        ):
            all_passed = False
    except Exception as e:
        log_test("Public Endpoint Separation", False, f"Exception: {str(e)}")
        all_passed = False
    
    # 3e: Update service
    try:
        resp = requests.put(
            f"{BASE_URL}/api/admin/services/{service_id}",
            json={
                "title": "Rodas Personalizadas",
                "description": "Pintando suas rodas.",
                "active": True
            },
            headers=headers,
            timeout=10
        )
        data = resp.json()
        
        passed = (
            resp.status_code == 200 and
            data.get('title') == 'Rodas Personalizadas'
        )
        
        if not log_test(
            "Update Service",
            passed,
            f"Status: {resp.status_code}, Updated title: {data.get('title')}"
        ):
            all_passed = False
    except Exception as e:
        log_test("Update Service", False, f"Exception: {str(e)}")
        all_passed = False
    
    # 3f: Delete service
    try:
        resp = requests.delete(
            f"{BASE_URL}/api/admin/services/{service_id}",
            headers=headers,
            timeout=10
        )
        
        passed = resp.status_code == 200
        if not log_test(
            "Delete Service",
            passed,
            f"Status: {resp.status_code}"
        ):
            all_passed = False
    except Exception as e:
        log_test("Delete Service", False, f"Exception: {str(e)}")
        all_passed = False
    
    return all_passed

def test_gallery_upload():
    """Test 4: Gallery upload endpoint"""
    if not AUTH_TOKEN:
        return log_test("Gallery Upload", False, "No auth token available")
    
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    all_passed = True
    file_id = None
    file_url = None
    gallery_id = None
    
    # 4a: Upload valid PNG
    try:
        # Create a small test PNG
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        files = {'file': ('test.png', img_bytes, 'image/png')}
        resp = requests.post(
            f"{BASE_URL}/api/admin/upload",
            files=files,
            headers=headers,
            timeout=10
        )
        data = resp.json()
        
        if resp.status_code == 200 and 'id' in data and 'url' in data:
            file_id = data['id']
            file_url = data['url']
            log_test(
                "Upload PNG",
                True,
                f"File uploaded: {file_id}, URL: {file_url}"
            )
        else:
            all_passed = False
            log_test(
                "Upload PNG",
                False,
                f"Status: {resp.status_code}, Response: {data}"
            )
            return False
    except Exception as e:
        log_test("Upload PNG", False, f"Exception: {str(e)}")
        return False
    
    # 4b: Verify file retrieval
    try:
        resp = requests.get(f"{BASE_URL}{file_url}", timeout=10)
        
        passed = (
            resp.status_code == 200 and
            resp.headers.get('content-type', '').startswith('image/')
        )
        
        if not log_test(
            "Retrieve Uploaded File",
            passed,
            f"Status: {resp.status_code}, Content-Type: {resp.headers.get('content-type')}"
        ):
            all_passed = False
    except Exception as e:
        log_test("Retrieve Uploaded File", False, f"Exception: {str(e)}")
        all_passed = False
    
    # 4c: Try uploading invalid file type (txt)
    try:
        files = {'file': ('test.txt', io.BytesIO(b'test content'), 'text/plain')}
        resp = requests.post(
            f"{BASE_URL}/api/admin/upload",
            files=files,
            headers=headers,
            timeout=10
        )
        
        passed = resp.status_code == 400
        if not log_test(
            "Reject Invalid File Type",
            passed,
            f"Status: {resp.status_code} (expected 400)"
        ):
            all_passed = False
    except Exception as e:
        log_test("Reject Invalid File Type", False, f"Exception: {str(e)}")
        all_passed = False
    
    # 4d: Try upload without auth
    try:
        img = Image.new('RGB', (100, 100), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        files = {'file': ('test2.png', img_bytes, 'image/png')}
        resp = requests.post(
            f"{BASE_URL}/api/admin/upload",
            files=files,
            timeout=10
        )
        
        passed = resp.status_code == 401
        if not log_test(
            "Upload Without Auth",
            passed,
            f"Status: {resp.status_code} (expected 401)"
        ):
            all_passed = False
    except Exception as e:
        log_test("Upload Without Auth", False, f"Exception: {str(e)}")
        all_passed = False
    
    # 4e: Create gallery item with uploaded image
    try:
        resp = requests.post(
            f"{BASE_URL}/api/admin/gallery",
            json={
                "title": "Test Photo",
                "image_url": file_url,
                "active": True
            },
            headers=headers,
            timeout=10
        )
        data = resp.json()
        
        if resp.status_code == 200 and 'id' in data:
            gallery_id = data['id']
            log_test(
                "Create Gallery Item",
                True,
                f"Gallery item created: {gallery_id}"
            )
        else:
            all_passed = False
            log_test(
                "Create Gallery Item",
                False,
                f"Status: {resp.status_code}, Response: {data}"
            )
    except Exception as e:
        log_test("Create Gallery Item", False, f"Exception: {str(e)}")
        all_passed = False
    
    # 4f: Verify gallery item NOT in services
    try:
        resp = requests.get(
            f"{BASE_URL}/api/admin/services",
            headers=headers,
            timeout=10
        )
        services = resp.json()
        
        contaminated = any(
            s.get('title') == 'Test Photo'
            for s in services
        )
        
        if not log_test(
            "Gallery NOT in Services",
            not contaminated,
            f"Services has {len(services)} items, contamination: {contaminated}"
        ):
            all_passed = False
    except Exception as e:
        log_test("Gallery NOT in Services", False, f"Exception: {str(e)}")
        all_passed = False
    
    # 4g: Verify in public endpoint
    try:
        resp = requests.get(f"{BASE_URL}/api/public", timeout=10)
        public_data = resp.json()
        
        in_gallery = any(
            g.get('title') == 'Test Photo'
            for g in public_data.get('gallery', [])
        )
        
        if not log_test(
            "Gallery in Public Endpoint",
            in_gallery,
            f"Gallery item found in public: {in_gallery}"
        ):
            all_passed = False
    except Exception as e:
        log_test("Gallery in Public Endpoint", False, f"Exception: {str(e)}")
        all_passed = False
    
    # 4h: Cleanup - delete gallery item
    if gallery_id:
        try:
            resp = requests.delete(
                f"{BASE_URL}/api/admin/gallery/{gallery_id}",
                headers=headers,
                timeout=10
            )
            log_test(
                "Delete Gallery Item",
                resp.status_code == 200,
                f"Status: {resp.status_code}"
            )
        except Exception as e:
            log_test("Delete Gallery Item", False, f"Exception: {str(e)}")
    
    return all_passed

def test_settings():
    """Test 5: Settings endpoint (verify not broken)"""
    if not AUTH_TOKEN:
        return log_test("Settings", False, "No auth token available")
    
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    all_passed = True
    
    # 5a: Get settings
    try:
        resp = requests.get(f"{BASE_URL}/api/settings", timeout=10)
        settings = resp.json()
        
        required_fields = [
            'company_name', 'phone', 'whatsapp', 'address',
            'hours', 'maps_url', 'instagram'
        ]
        
        has_all_fields = all(field in settings for field in required_fields)
        
        if not log_test(
            "Get Settings",
            resp.status_code == 200 and has_all_fields,
            f"Status: {resp.status_code}, Has all fields: {has_all_fields}"
        ):
            all_passed = False
            return False
        
        # 5b: Update settings (round-trip test)
        resp = requests.put(
            f"{BASE_URL}/api/settings",
            json=settings,
            headers=headers,
            timeout=10
        )
        updated = resp.json()
        
        # Verify key fields preserved
        preserved = all(
            settings.get(field) == updated.get(field)
            for field in required_fields
        )
        
        if not log_test(
            "Update Settings (Round-trip)",
            resp.status_code == 200 and preserved,
            f"Status: {resp.status_code}, Values preserved: {preserved}"
        ):
            all_passed = False
    except Exception as e:
        log_test("Settings", False, f"Exception: {str(e)}")
        all_passed = False
    
    return all_passed

def test_quote_form():
    """Test 6: Quote form submission"""
    try:
        data = {
            'name': 'João Silva',
            'phone': '31999887766',
            'vehicle': 'Honda Civic',
            'year': '2020',
            'interest': 'Pintura de rodas',
            'message': 'Gostaria de um orçamento para pintura das rodas do meu carro.'
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/quotes",
            data=data,
            timeout=10
        )
        result = resp.json()
        
        passed = (
            resp.status_code == 200 and
            'id' in result and
            result.get('name') == 'João Silva'
        )
        
        return log_test(
            "Quote Form Submission",
            passed,
            f"Status: {resp.status_code}, Lead created: {result.get('id', 'N/A')}"
        )
    except Exception as e:
        return log_test("Quote Form Submission", False, f"Exception: {str(e)}")

def main():
    """Run all tests"""
    print("=" * 70)
    print("DINHO RODAS BACKEND - SURGICAL FIX VERIFICATION")
    print("=" * 70)
    
    results = []
    
    # Test sequence
    results.append(("Health", test_health()))
    results.append(("Login", test_login()))
    results.append(("Services CRUD", test_services_crud()))
    results.append(("Gallery Upload", test_gallery_upload()))
    results.append(("Settings", test_settings()))
    results.append(("Quote Form", test_quote_form()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - No regressions detected!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - Review required")
        return 1

if __name__ == "__main__":
    exit(main())

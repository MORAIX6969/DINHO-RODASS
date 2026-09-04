#!/usr/bin/env python3
"""
Dinho Rodas Backend Upload Feature Testing
Tests upload functionality for BOTH Services and Gallery tabs
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
        print(f"  {details}")
    return passed

def create_test_image(color='red'):
    """Create a small test PNG image"""
    img = Image.new('RGB', (100, 100), color=color)
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

# ============================================================================
# TEST A - UPLOAD ENDPOINT
# ============================================================================

def test_a_upload_endpoint():
    """TEST A: Verify upload endpoint works exactly like before"""
    global AUTH_TOKEN
    print("\n" + "="*70)
    print("TEST A - UPLOAD ENDPOINT")
    print("="*70)
    
    all_passed = True
    
    # Step 1: Login
    try:
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10
        )
        data = resp.json()
        
        if resp.status_code == 200 and 'token' in data:
            AUTH_TOKEN = data['token']
            log_test("Step 1: Login", True, f"Token: {AUTH_TOKEN[:20]}...")
        else:
            log_test("Step 1: Login", False, f"Status: {resp.status_code}, Response: {data}")
            return False
    except Exception as e:
        log_test("Step 1: Login", False, f"Exception: {str(e)}")
        return False
    
    # Step 2: Upload PNG file
    file_url = None
    try:
        img_bytes = create_test_image('red')
        files = {'file': ('test_upload.png', img_bytes, 'image/png')}
        headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
        
        resp = requests.post(
            f"{BASE_URL}/api/admin/upload",
            files=files,
            headers=headers,
            timeout=10
        )
        data = resp.json()
        
        # Must return {id, url, content_type, size}
        has_required_fields = all(k in data for k in ['id', 'url', 'content_type', 'size'])
        url_format_correct = data.get('url', '').startswith('/api/files/')
        
        if resp.status_code == 200 and has_required_fields and url_format_correct:
            file_url = data['url']
            log_test(
                "Step 2: Upload PNG", 
                True, 
                f"ID: {data['id']}, URL: {file_url}, Type: {data['content_type']}, Size: {data['size']} bytes"
            )
        else:
            all_passed = False
            log_test(
                "Step 2: Upload PNG", 
                False, 
                f"Status: {resp.status_code}, Has fields: {has_required_fields}, URL format: {url_format_correct}"
            )
            return False
    except Exception as e:
        log_test("Step 2: Upload PNG", False, f"Exception: {str(e)}")
        return False
    
    # Step 3: Retrieve uploaded image
    try:
        resp = requests.get(f"{BASE_URL}{file_url}", timeout=10)
        
        is_200 = resp.status_code == 200
        is_image = resp.headers.get('content-type', '').startswith('image/')
        has_content = len(resp.content) > 0
        
        passed = is_200 and is_image and has_content
        
        if not log_test(
            "Step 3: Retrieve Image", 
            passed,
            f"Status: {resp.status_code}, Content-Type: {resp.headers.get('content-type')}, Size: {len(resp.content)} bytes"
        ):
            all_passed = False
    except Exception as e:
        log_test("Step 3: Retrieve Image", False, f"Exception: {str(e)}")
        all_passed = False
    
    return all_passed

# ============================================================================
# TEST B - SERVICES USES UPLOADED IMAGE URL
# ============================================================================

def test_b_services_with_upload():
    """TEST B: Verify Services tab can use uploaded image URLs"""
    if not AUTH_TOKEN:
        print("\n❌ TEST B SKIPPED: No auth token")
        return False
    
    print("\n" + "="*70)
    print("TEST B - SERVICES USES UPLOADED IMAGE URL")
    print("="*70)
    
    all_passed = True
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    service_id = None
    uploaded_url = None
    
    # Step 4: Create service with uploaded image
    try:
        # First upload an image for the service
        img_bytes = create_test_image('blue')
        files = {'file': ('service_image.png', img_bytes, 'image/png')}
        
        resp = requests.post(
            f"{BASE_URL}/api/admin/upload",
            files=files,
            headers=headers,
            timeout=10
        )
        upload_data = resp.json()
        uploaded_url = upload_data.get('url')
        
        if not uploaded_url:
            log_test("Step 4a: Upload image for service", False, "No URL returned")
            return False
        
        # Now create service with this image_url
        resp = requests.post(
            f"{BASE_URL}/api/admin/services",
            json={
                "title": "Rodas",
                "description": "Pintando suas rodas.",
                "image_url": uploaded_url,
                "active": True
            },
            headers=headers,
            timeout=10
        )
        data = resp.json()
        
        if resp.status_code == 200 and data.get('image_url') == uploaded_url:
            service_id = data['id']
            log_test(
                "Step 4: Create Service with image_url", 
                True,
                f"Service ID: {service_id}, image_url: {uploaded_url}"
            )
        else:
            all_passed = False
            log_test(
                "Step 4: Create Service with image_url", 
                False,
                f"Status: {resp.status_code}, image_url match: {data.get('image_url') == uploaded_url}"
            )
            return False
    except Exception as e:
        log_test("Step 4: Create Service with image_url", False, f"Exception: {str(e)}")
        return False
    
    # Step 5: Verify service in public endpoint
    try:
        resp = requests.get(f"{BASE_URL}/api/public", timeout=10)
        public_data = resp.json()
        
        service_found = None
        for s in public_data.get('services', []):
            if s.get('title') == 'Rodas' and s.get('description') == 'Pintando suas rodas.':
                service_found = s
                break
        
        if service_found and service_found.get('image_url') == uploaded_url:
            log_test(
                "Step 5: Service in public endpoint", 
                True,
                f"Found service with correct image_url"
            )
        else:
            all_passed = False
            log_test(
                "Step 5: Service in public endpoint", 
                False,
                f"Service found: {service_found is not None}, URL match: {service_found.get('image_url') == uploaded_url if service_found else False}"
            )
    except Exception as e:
        log_test("Step 5: Service in public endpoint", False, f"Exception: {str(e)}")
        all_passed = False
    
    # Step 6: Verify NO cross-contamination with gallery
    try:
        resp = requests.get(
            f"{BASE_URL}/api/admin/gallery",
            headers=headers,
            timeout=10
        )
        gallery = resp.json()
        
        # Check if our service appears in gallery
        contaminated = any(
            g.get('title') == 'Rodas' and 
            g.get('description') == 'Pintando suas rodas.'
            for g in gallery
        )
        
        if not contaminated:
            log_test(
                "Step 6: No cross-contamination in gallery", 
                True,
                f"Gallery has {len(gallery)} items, service NOT found (correct)"
            )
        else:
            all_passed = False
            log_test(
                "Step 6: No cross-contamination in gallery", 
                False,
                f"Service found in gallery collection (WRONG!)"
            )
    except Exception as e:
        log_test("Step 6: No cross-contamination in gallery", False, f"Exception: {str(e)}")
        all_passed = False
    
    # Step 7: Delete service
    if service_id:
        try:
            resp = requests.delete(
                f"{BASE_URL}/api/admin/services/{service_id}",
                headers=headers,
                timeout=10
            )
            
            if resp.status_code == 200:
                log_test("Step 7: Delete service", True, f"Service deleted successfully")
            else:
                all_passed = False
                log_test("Step 7: Delete service", False, f"Status: {resp.status_code}")
        except Exception as e:
            log_test("Step 7: Delete service", False, f"Exception: {str(e)}")
            all_passed = False
    
    return all_passed

# ============================================================================
# TEST C - GALLERY UPLOAD REGRESSION CHECK
# ============================================================================

def test_c_gallery_upload_regression():
    """TEST C: Verify Gallery upload still works (regression check)"""
    if not AUTH_TOKEN:
        print("\n❌ TEST C SKIPPED: No auth token")
        return False
    
    print("\n" + "="*70)
    print("TEST C - GALLERY UPLOAD REGRESSION CHECK")
    print("="*70)
    
    all_passed = True
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    gallery_id = None
    uploaded_url = None
    
    # Step 8: Upload image for gallery
    try:
        img_bytes = create_test_image('green')
        files = {'file': ('gallery_image.png', img_bytes, 'image/png')}
        
        resp = requests.post(
            f"{BASE_URL}/api/admin/upload",
            files=files,
            headers=headers,
            timeout=10
        )
        data = resp.json()
        uploaded_url = data.get('url')
        
        if resp.status_code == 200 and uploaded_url:
            log_test(
                "Step 8: Upload image for gallery", 
                True,
                f"URL: {uploaded_url}"
            )
        else:
            log_test("Step 8: Upload image for gallery", False, f"Status: {resp.status_code}")
            return False
    except Exception as e:
        log_test("Step 8: Upload image for gallery", False, f"Exception: {str(e)}")
        return False
    
    # Step 9: Create gallery item
    try:
        resp = requests.post(
            f"{BASE_URL}/api/admin/gallery",
            json={
                "title": "Teste",
                "image_url": uploaded_url,
                "active": True
            },
            headers=headers,
            timeout=10
        )
        data = resp.json()
        
        if resp.status_code == 200 and data.get('image_url') == uploaded_url:
            gallery_id = data['id']
            log_test(
                "Step 9: Create gallery item", 
                True,
                f"Gallery ID: {gallery_id}, image_url: {uploaded_url}"
            )
        else:
            all_passed = False
            log_test(
                "Step 9: Create gallery item", 
                False,
                f"Status: {resp.status_code}, image_url match: {data.get('image_url') == uploaded_url}"
            )
            return False
    except Exception as e:
        log_test("Step 9: Create gallery item", False, f"Exception: {str(e)}")
        return False
    
    # Step 10: Verify in public endpoint
    try:
        resp = requests.get(f"{BASE_URL}/api/public", timeout=10)
        public_data = resp.json()
        
        gallery_found = None
        for g in public_data.get('gallery', []):
            if g.get('title') == 'Teste' and g.get('image_url') == uploaded_url:
                gallery_found = g
                break
        
        if gallery_found:
            log_test(
                "Step 10: Gallery item in public endpoint", 
                True,
                f"Found gallery item with correct image_url"
            )
        else:
            all_passed = False
            log_test(
                "Step 10: Gallery item in public endpoint", 
                False,
                f"Gallery item not found in public endpoint"
            )
    except Exception as e:
        log_test("Step 10: Gallery item in public endpoint", False, f"Exception: {str(e)}")
        all_passed = False
    
    # Step 11: Delete gallery item
    if gallery_id:
        try:
            resp = requests.delete(
                f"{BASE_URL}/api/admin/gallery/{gallery_id}",
                headers=headers,
                timeout=10
            )
            
            if resp.status_code == 200:
                log_test("Step 11: Delete gallery item", True, f"Gallery item deleted successfully")
            else:
                all_passed = False
                log_test("Step 11: Delete gallery item", False, f"Status: {resp.status_code}")
        except Exception as e:
            log_test("Step 11: Delete gallery item", False, f"Exception: {str(e)}")
            all_passed = False
    
    return all_passed

# ============================================================================
# TEST D - SETTINGS REGRESSION CHECK
# ============================================================================

def test_d_settings_regression():
    """TEST D: Verify Settings endpoint not broken"""
    if not AUTH_TOKEN:
        print("\n❌ TEST D SKIPPED: No auth token")
        return False
    
    print("\n" + "="*70)
    print("TEST D - SETTINGS REGRESSION CHECK")
    print("="*70)
    
    all_passed = True
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    
    # Step 12: GET settings
    try:
        resp = requests.get(f"{BASE_URL}/api/settings", timeout=10)
        settings = resp.json()
        
        required_fields = ['company_name', 'phone', 'whatsapp']
        has_fields = all(field in settings for field in required_fields)
        
        if resp.status_code == 200 and has_fields:
            log_test(
                "Step 12: GET /api/settings", 
                True,
                f"Status: 200, Fields present: {', '.join(required_fields)}"
            )
        else:
            all_passed = False
            log_test(
                "Step 12: GET /api/settings", 
                False,
                f"Status: {resp.status_code}, Has required fields: {has_fields}"
            )
            return False
        
        # Step 13: PUT settings (round-trip)
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
        
        if resp.status_code == 200 and preserved:
            log_test(
                "Step 13: PUT /api/settings (round-trip)", 
                True,
                f"Status: 200, Values preserved correctly"
            )
        else:
            all_passed = False
            log_test(
                "Step 13: PUT /api/settings (round-trip)", 
                False,
                f"Status: {resp.status_code}, Values preserved: {preserved}"
            )
    except Exception as e:
        log_test("Settings regression check", False, f"Exception: {str(e)}")
        all_passed = False
    
    return all_passed

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    """Run all tests"""
    print("="*70)
    print("DINHO RODAS BACKEND - UPLOAD FEATURE TESTING")
    print("Testing upload functionality for Services AND Gallery tabs")
    print("="*70)
    
    results = []
    
    # Run all test suites
    results.append(("TEST A - Upload Endpoint", test_a_upload_endpoint()))
    results.append(("TEST B - Services with Upload", test_b_services_with_upload()))
    results.append(("TEST C - Gallery Upload Regression", test_c_gallery_upload_regression()))
    results.append(("TEST D - Settings Regression", test_d_settings_regression()))
    
    # Summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    print(f"\nTotal: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✓ Upload endpoint works correctly")
        print("✓ Services can use uploaded images")
        print("✓ Gallery upload still works")
        print("✓ Settings endpoint not broken")
        print("✓ No cross-contamination between Services and Gallery")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed")
        return 1

if __name__ == "__main__":
    exit(main())

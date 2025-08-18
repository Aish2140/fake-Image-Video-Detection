import requests
import sys
import json
from datetime import datetime

class BackendAPITester:
    def __init__(self, base_url="https://deepfake-finder-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details
        })

    def test_root_endpoint(self):
        """Test GET /api/ endpoint"""
        try:
            response = requests.get(f"{self.api_base}/", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("message") == "Hello World":
                    self.log_test("GET /api/ endpoint", True)
                    return True
                else:
                    self.log_test("GET /api/ endpoint", False, f"Unexpected response: {data}")
            else:
                self.log_test("GET /api/ endpoint", False, f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test("GET /api/ endpoint", False, f"Exception: {str(e)}")
        
        return False

    def test_get_status_endpoint(self):
        """Test GET /api/status endpoint"""
        try:
            response = requests.get(f"{self.api_base}/status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("GET /api/status endpoint", True, f"Returned {len(data)} status checks")
                    return True, data
                else:
                    self.log_test("GET /api/status endpoint", False, f"Expected list, got: {type(data)}")
            else:
                self.log_test("GET /api/status endpoint", False, f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test("GET /api/status endpoint", False, f"Exception: {str(e)}")
        
        return False, []

    def test_post_status_endpoint(self):
        """Test POST /api/status endpoint"""
        test_client_name = f"test_client_{datetime.now().strftime('%H%M%S')}"
        
        try:
            payload = {"client_name": test_client_name}
            response = requests.post(
                f"{self.api_base}/status", 
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "client_name", "timestamp"]
                
                if all(field in data for field in required_fields):
                    if data["client_name"] == test_client_name:
                        self.log_test("POST /api/status endpoint", True, f"Created status check with ID: {data['id']}")
                        return True, data
                    else:
                        self.log_test("POST /api/status endpoint", False, f"Client name mismatch: expected {test_client_name}, got {data['client_name']}")
                else:
                    missing_fields = [field for field in required_fields if field not in data]
                    self.log_test("POST /api/status endpoint", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("POST /api/status endpoint", False, f"Status code: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("POST /api/status endpoint", False, f"Exception: {str(e)}")
        
        return False, {}

    def test_database_integration(self):
        """Test that data persists in database by creating and retrieving"""
        print("\n🔍 Testing Database Integration...")
        
        # Get initial count
        success, initial_data = self.test_get_status_endpoint()
        if not success:
            return False
        
        initial_count = len(initial_data)
        
        # Create new status check
        success, created_data = self.test_post_status_endpoint()
        if not success:
            return False
        
        # Get updated count
        success, updated_data = self.test_get_status_endpoint()
        if not success:
            return False
        
        updated_count = len(updated_data)
        
        if updated_count == initial_count + 1:
            # Verify the created item exists in the list
            created_id = created_data.get("id")
            found_item = next((item for item in updated_data if item.get("id") == created_id), None)
            
            if found_item:
                self.log_test("Database Integration", True, f"Successfully created and retrieved status check")
                return True
            else:
                self.log_test("Database Integration", False, "Created item not found in GET response")
        else:
            self.log_test("Database Integration", False, f"Count mismatch: expected {initial_count + 1}, got {updated_count}")
        
        return False

    def test_cors_configuration(self):
        """Test CORS headers"""
        try:
            response = requests.options(f"{self.api_base}/", timeout=10)
            
            cors_headers = {
                'access-control-allow-origin': response.headers.get('access-control-allow-origin'),
                'access-control-allow-methods': response.headers.get('access-control-allow-methods'),
                'access-control-allow-headers': response.headers.get('access-control-allow-headers')
            }
            
            if cors_headers['access-control-allow-origin']:
                self.log_test("CORS Configuration", True, f"CORS headers present: {cors_headers}")
                return True
            else:
                self.log_test("CORS Configuration", False, "No CORS headers found")
                
        except Exception as e:
            self.log_test("CORS Configuration", False, f"Exception: {str(e)}")
        
        return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Backend API Tests...")
        print(f"Testing against: {self.base_url}")
        print("=" * 50)
        
        # Test individual endpoints
        self.test_root_endpoint()
        self.test_get_status_endpoint()
        self.test_post_status_endpoint()
        
        # Test database integration
        self.test_database_integration()
        
        # Test CORS
        self.test_cors_configuration()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All backend tests passed!")
            return True
        else:
            print("⚠️  Some backend tests failed. Check details above.")
            return False

def main():
    tester = BackendAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
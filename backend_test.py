
import requests
import sys
import json
from datetime import datetime

class LinkedInResumeBuilderTester:
    def __init__(self, base_url="https://58c73fca-2907-4260-95ea-d22d46be3dd6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, expected_content=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

            status_success = response.status_code == expected_status
            
            if status_success:
                print(f"✅ Status check passed - Expected: {expected_status}, Got: {response.status_code}")
            else:
                print(f"❌ Status check failed - Expected: {expected_status}, Got: {response.status_code}")
                print(f"Response: {response.text}")
                return False, None
            
            # Try to parse JSON response
            try:
                response_data = response.json()
                print(f"📄 Response: {json.dumps(response_data, indent=2)}")
                
                # Check expected content if provided
                content_success = True
                if expected_content:
                    for key, value in expected_content.items():
                        if key not in response_data or response_data[key] != value:
                            content_success = False
                            print(f"❌ Content check failed - Expected '{key}': '{value}', Got: '{response_data.get(key, 'missing')}'")
                
                if status_success and content_success:
                    self.tests_passed += 1
                    print(f"✅ Test passed")
                    return True, response_data
                else:
                    return False, response_data
                
            except json.JSONDecodeError:
                print(f"⚠️ Response is not JSON: {response.text[:100]}...")
                # For non-JSON responses like redirects, consider it a success if status is correct
                if status_success:
                    self.tests_passed += 1
                    print(f"✅ Test passed (non-JSON response)")
                    return True, response.text
                return False, response.text

        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            return False, None

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200,
            expected_content={"message": "Resume Builder API with LinkedIn Integration"}
        )

    def test_linkedin_auth_url(self):
        """Test the LinkedIn auth URL endpoint"""
        success, response = self.run_test(
            "LinkedIn Auth URL",
            "GET",
            "auth/linkedin",
            200
        )
        
        if success and response and 'auth_url' in response:
            auth_url = response['auth_url']
            print(f"✅ LinkedIn auth URL generated: {auth_url}")
            
            # Check if auth URL contains required parameters
            required_params = [
                "response_type=code",
                "client_id=",
                "redirect_uri=",
                "scope="
            ]
            
            all_params_present = all(param in auth_url for param in required_params)
            if all_params_present:
                print("✅ Auth URL contains all required parameters")
                return True, auth_url
            else:
                print("❌ Auth URL missing some required parameters")
                return False, auth_url
        
        return False, None

    def test_templates_endpoint(self):
        """Test the templates endpoint"""
        success, response = self.run_test(
            "Resume Templates",
            "GET",
            "templates",
            200
        )
        
        if success and response:
            # Check if we have exactly 3 templates
            if len(response) == 3:
                print(f"✅ Found exactly 3 templates as expected")
            else:
                print(f"❌ Expected 3 templates, got {len(response)}")
                return False, response
            
            # Check if each template has the required fields
            required_fields = ["id", "name", "description", "preview_image", "style"]
            template_ids = ["modern", "classic", "elegant"]
            
            all_fields_present = True
            all_ids_present = True
            
            for template in response:
                for field in required_fields:
                    if field not in template:
                        all_fields_present = False
                        print(f"❌ Template missing required field: {field}")
                
                if template["id"] not in template_ids:
                    all_ids_present = False
                    print(f"❌ Unexpected template ID: {template['id']}")
            
            if all_fields_present:
                print("✅ All templates have required fields")
            
            if all_ids_present:
                print("✅ All expected template IDs are present")
                
            return all_fields_present and all_ids_present, response
        
        return False, None

    def test_status_endpoint(self):
        """Test the status endpoint"""
        # First create a status check
        client_name = f"test_client_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        create_success, create_response = self.run_test(
            "Create Status Check",
            "POST",
            "status",
            200,
            data={"client_name": client_name}
        )
        
        if not create_success:
            return False, None
        
        # Then get all status checks
        get_success, get_response = self.run_test(
            "Get Status Checks",
            "GET",
            "status",
            200
        )
        
        if get_success and get_response:
            # Check if our created status check is in the list
            found = False
            for status in get_response:
                if status.get("client_name") == client_name:
                    found = True
                    break
            
            if found:
                print(f"✅ Found our created status check in the list")
                return True, get_response
            else:
                print(f"❌ Could not find our created status check in the list")
                return False, get_response
        
        return False, None

def main():
    print("=" * 80)
    print("LinkedIn Resume Builder API Test Suite")
    print("=" * 80)
    
    tester = LinkedInResumeBuilderTester()
    
    # Test root endpoint
    root_success, _ = tester.test_root_endpoint()
    
    # Test LinkedIn auth URL endpoint
    auth_success, _ = tester.test_linkedin_auth_url()
    
    # Test templates endpoint
    templates_success, _ = tester.test_templates_endpoint()
    
    # Test status endpoint
    status_success, _ = tester.test_status_endpoint()
    
    # Print summary
    print("\n" + "=" * 80)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed / tester.tests_run) * 100:.2f}%")
    print("=" * 80)
    
    # Print individual test results
    print("\nTest Results Summary:")
    print(f"Root API Endpoint: {'✅ PASSED' if root_success else '❌ FAILED'}")
    print(f"LinkedIn Auth URL: {'✅ PASSED' if auth_success else '❌ FAILED'}")
    print(f"Resume Templates: {'✅ PASSED' if templates_success else '❌ FAILED'}")
    print(f"Status Endpoint: {'✅ PASSED' if status_success else '❌ FAILED'}")
    
    # Return success if all tests passed
    return 0 if root_success and auth_success and templates_success and status_success else 1

if __name__ == "__main__":
    sys.exit(main())

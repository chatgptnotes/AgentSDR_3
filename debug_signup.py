#!/usr/bin/env python3
"""
Debug signup issues
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_signup_form():
    """Test signup form validation"""
    try:
        from agentsdr import create_app
        from agentsdr.auth.forms import SignupForm
        
        app = create_app()
        
        with app.test_client() as client:
            with app.app_context():
                print("Testing signup form validation...")
                
                # Test 1: Get signup page
                response = client.get('/auth/signup')
                print(f"Signup page status: {response.status_code}")
                
                if response.status_code != 200:
                    print("❌ Signup page not accessible")
                    return False
                
                # Extract CSRF token
                csrf_token = None
                if b'csrf_token' in response.data:
                    import re
                    match = re.search(rb'name="csrf_token"[^>]*value="([^"]*)"', response.data)
                    if match:
                        csrf_token = match.group(1).decode()
                        print(f"✅ CSRF token extracted: {csrf_token[:20]}...")
                
                if not csrf_token:
                    print("❌ No CSRF token found")
                    return False
                
                # Test 2: Try signup with valid data
                signup_data = {
                    'email': 'test_debug@example.com',
                    'display_name': 'Test Debug User',
                    'password': 'testpassword123',
                    'confirm_password': 'testpassword123',
                    'csrf_token': csrf_token
                }
                
                print("Attempting signup with valid data...")
                response = client.post('/auth/signup', data=signup_data, follow_redirects=False)
                print(f"Signup response status: {response.status_code}")
                
                if response.status_code == 400:
                    print("❌ 400 Bad Request - Form validation failed")
                    
                    # Check response content for error details
                    response_text = response.data.decode('utf-8')
                    if 'error' in response_text.lower():
                        print("Response contains error information")
                    
                    # Try to create form manually to check validation
                    form = SignupForm(data=signup_data)
                    if form.validate():
                        print("✅ Form validation passed manually")
                    else:
                        print("❌ Form validation failed:")
                        for field, errors in form.errors.items():
                            print(f"  {field}: {errors}")
                
                elif response.status_code == 302:
                    print("✅ Signup successful (redirected)")
                    
                elif response.status_code == 200:
                    print("⚠️ Signup returned 200 - check for error messages")
                    
                return True
                
    except Exception as e:
        print(f"❌ Error testing signup: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_supabase_signup():
    """Test direct Supabase signup"""
    try:
        from agentsdr import create_app
        from agentsdr.core.supabase_client import get_supabase
        
        app = create_app()
        
        with app.app_context():
            print("\nTesting direct Supabase signup...")
            
            supabase_client = get_supabase()
            
            # Try to sign up directly
            response = supabase_client.auth.sign_up({
                'email': 'test_direct_debug@example.com',
                'password': 'testpassword123'
            })
            
            if response.user:
                print(f"✅ Supabase Auth signup successful: {response.user.id}")
                return True
            else:
                print("❌ Supabase Auth signup failed")
                return False
                
    except Exception as e:
        print(f"❌ Direct Supabase signup error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Debugging Signup Issues")
    print("=" * 40)
    
    # Test form validation
    test_signup_form()
    
    # Test direct Supabase
    test_direct_supabase_signup()

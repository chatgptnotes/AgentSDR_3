#!/usr/bin/env python3
"""
Test authentication functionality
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_auth():
    """Test authentication functionality"""
    try:
        print("Testing authentication functionality...")
        
        from agentsdr import create_app
        app = create_app()
        
        with app.test_client() as client:
            # Test 1: Try to login with existing user
            print("\n1. Testing login with existing user...")
            
            # Get CSRF token first
            response = client.get('/auth/login')
            print(f"Login page loaded: {response.status_code}")
            
            # Extract CSRF token from the response
            csrf_token = None
            if b'csrf_token' in response.data:
                # Simple extraction - in real scenario you'd parse HTML properly
                import re
                match = re.search(rb'name="csrf_token"[^>]*value="([^"]*)"', response.data)
                if match:
                    csrf_token = match.group(1).decode()
                    print(f"✅ CSRF token extracted: {csrf_token[:20]}...")
            
            if csrf_token:
                # Try login with existing user
                login_data = {
                    'email': 'banduwaghmare1221@gmail.com',  # Existing user from database
                    'password': 'testpassword123',  # We don't know the actual password
                    'csrf_token': csrf_token,
                    'remember_me': False
                }
                
                response = client.post('/auth/login', data=login_data, follow_redirects=False)
                print(f"Login attempt status: {response.status_code}")
                
                if response.status_code == 302:
                    print("✅ Login redirected (likely successful or to error page)")
                elif response.status_code == 200:
                    if b'Invalid email or password' in response.data:
                        print("⚠️ Login failed: Invalid credentials (expected - we don't know the password)")
                    elif b'Login failed' in response.data:
                        print("⚠️ Login failed: General error")
                    else:
                        print("⚠️ Login returned 200 but unclear result")
            
            # Test 2: Try signup with new user
            print("\n2. Testing signup with new user...")
            
            response = client.get('/auth/signup')
            print(f"Signup page loaded: {response.status_code}")
            
            # Extract CSRF token
            csrf_token = None
            if b'csrf_token' in response.data:
                import re
                match = re.search(rb'name="csrf_token"[^>]*value="([^"]*)"', response.data)
                if match:
                    csrf_token = match.group(1).decode()
                    print(f"✅ CSRF token extracted: {csrf_token[:20]}...")
            
            if csrf_token:
                # Try signup with new user
                signup_data = {
                    'email': 'test_new_user@example.com',
                    'display_name': 'Test User',
                    'password': 'testpassword123',
                    'confirm_password': 'testpassword123',
                    'csrf_token': csrf_token
                }
                
                response = client.post('/auth/signup', data=signup_data, follow_redirects=False)
                print(f"Signup attempt status: {response.status_code}")
                
                if response.status_code == 302:
                    print("✅ Signup redirected (likely successful)")
                elif response.status_code == 200:
                    if b'Account created successfully' in response.data:
                        print("✅ Signup successful")
                    elif b'Account creation failed' in response.data:
                        print("⚠️ Signup failed: Account creation error")
                    elif b'already exists' in response.data:
                        print("⚠️ Signup failed: Account already exists")
                    else:
                        print("⚠️ Signup returned 200 but unclear result")
        
        print("\n3. Testing Supabase Auth directly...")
        
        # Test Supabase auth directly
        from agentsdr.core.supabase_client import get_supabase
        with app.app_context():
            supabase_client = get_supabase()
            
            # Try to sign up a test user directly with Supabase
            try:
                response = supabase_client.auth.sign_up({
                    'email': 'direct_test@example.com',
                    'password': 'testpassword123'
                })
                
                if response.user:
                    print("✅ Supabase direct signup successful")
                    print(f"User ID: {response.user.id}")
                    print(f"Email: {response.user.email}")
                else:
                    print("⚠️ Supabase direct signup failed: No user returned")
                    
            except Exception as e:
                print(f"⚠️ Supabase direct signup error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during auth test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_auth()

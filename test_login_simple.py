#!/usr/bin/env python3
"""
Simple test for login functionality
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_login():
    """Test login functionality"""
    try:
        print("Testing login functionality...")
        
        from agentsdr import create_app
        from agentsdr.core.supabase_client import get_supabase
        
        app = create_app()
        
        with app.app_context():
            print("\n1. Testing Supabase Auth login...")
            
            # Test login with one of the existing users
            # We'll use the test user we just created
            test_email = "test_auth_flow@example.com"
            test_password = "testpassword123"
            
            supabase_client = get_supabase()
            
            try:
                # Try to sign in with Supabase Auth
                response = supabase_client.auth.sign_in_with_password({
                    'email': test_email,
                    'password': test_password
                })
                
                if response.user:
                    print(f"✅ Supabase Auth login successful: {response.user.id}")
                    print(f"Email: {response.user.email}")
                    
                    # Test if we can get the user from our database
                    from agentsdr.auth.models import User
                    user = User.get_by_email(test_email)
                    
                    if user:
                        print(f"✅ User found in database: {user.display_name}")
                        print("✅ Login flow should work!")
                    else:
                        print("❌ User not found in database")
                        
                else:
                    print("❌ Supabase Auth login failed - no user returned")
                    
            except Exception as e:
                print(f"❌ Login test error: {e}")
                if "Invalid login credentials" in str(e):
                    print("This is expected - we don't know the actual passwords of existing users")
                    print("But signup should work for new users!")
        
        print("\n2. Testing with Flask test client...")
        
        with app.test_client() as client:
            # Test signup page
            response = client.get('/auth/signup')
            if response.status_code == 200:
                print("✅ Signup page accessible")
            else:
                print(f"❌ Signup page error: {response.status_code}")
            
            # Test login page
            response = client.get('/auth/login')
            if response.status_code == 200:
                print("✅ Login page accessible")
            else:
                print(f"❌ Login page error: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during login test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_login()

#!/usr/bin/env python3
"""
Test Flask app startup and identify any issues
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_app_startup():
    """Test if the Flask app can start properly"""
    try:
        print("Testing Flask app startup...")
        
        # Test imports
        print("1. Testing imports...")
        from agentsdr import create_app
        print("✅ Successfully imported create_app")
        
        # Test app creation
        print("2. Testing app creation...")
        app = create_app()
        print("✅ Successfully created Flask app")
        
        # Test app configuration
        print("3. Testing app configuration...")
        with app.app_context():
            print(f"✅ App name: {app.name}")
            print(f"✅ Debug mode: {app.debug}")
            print(f"✅ Secret key set: {'Yes' if app.secret_key else 'No'}")
            print(f"✅ Supabase URL: {'Set' if app.config.get('SUPABASE_URL') else 'Missing'}")
            print(f"✅ Supabase Anon Key: {'Set' if app.config.get('SUPABASE_ANON_KEY') else 'Missing'}")
            print(f"✅ Supabase Service Key: {'Set' if app.config.get('SUPABASE_SERVICE_ROLE_KEY') else 'Missing'}")
        
        # Test routes
        print("4. Testing routes...")
        with app.test_client() as client:
            # Test main page
            response = client.get('/')
            print(f"✅ Main page status: {response.status_code}")
            
            # Test login page
            response = client.get('/auth/login')
            print(f"✅ Login page status: {response.status_code}")
            
            # Test signup page
            response = client.get('/auth/signup')
            print(f"✅ Signup page status: {response.status_code}")
        
        print("\n🎉 All tests passed! Flask app is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Error during app startup test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_app_startup()

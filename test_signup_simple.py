#!/usr/bin/env python3
"""
Simple test for signup functionality
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_signup():
    """Test signup functionality"""
    try:
        print("Testing signup functionality...")
        
        from agentsdr import create_app
        from agentsdr.auth.models import User
        
        app = create_app()
        
        with app.app_context():
            print("\n1. Testing User.create_user method...")
            
            # Test creating a user directly
            test_email = "test_direct_create@example.com"
            
            # First, clean up if user exists
            existing_user = User.get_by_email(test_email)
            if existing_user:
                print(f"User {test_email} already exists, skipping creation test")
            else:
                # Try to create user
                user = User.create_user(
                    email=test_email,
                    display_name="Test Direct User"
                )
                
                if user:
                    print("✅ User.create_user works!")
                    print(f"Created user: {user.email} with ID: {user.id}")
                else:
                    print("❌ User.create_user failed")
            
            print("\n2. Testing Supabase Auth + User creation...")
            
            # Test the full signup flow
            from agentsdr.core.supabase_client import get_supabase
            
            supabase_client = get_supabase()
            test_auth_email = "test_auth_flow@example.com"
            
            try:
                # Try to sign up with Supabase Auth
                response = supabase_client.auth.sign_up({
                    'email': test_auth_email,
                    'password': 'testpassword123'
                })
                
                if response.user:
                    print(f"✅ Supabase Auth signup successful: {response.user.id}")
                    
                    # Now try to create user in our database
                    user = User.create_user(
                        email=test_auth_email,
                        display_name="Test Auth Flow User",
                        user_id=response.user.id
                    )
                    
                    if user:
                        print("✅ Full signup flow works!")
                        print(f"Created user: {user.email} with ID: {user.id}")
                    else:
                        print("❌ Database user creation failed (RLS issue)")
                        
                else:
                    print("❌ Supabase Auth signup failed")
                    
            except Exception as e:
                print(f"❌ Signup test error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during signup test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_signup()

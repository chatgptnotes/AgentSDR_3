#!/usr/bin/env python3
"""
Simple test to verify database connection with updated .env file
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_env_variables():
    """Test if environment variables are loaded correctly"""
    print("=== Environment Variables Test ===")
    
    # Check Supabase credentials
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_anon = os.environ.get('SUPABASE_ANON_KEY')
    supabase_service = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    
    print(f"SUPABASE_URL: {'✅ Set' if supabase_url else '❌ Missing'}")
    print(f"SUPABASE_ANON_KEY: {'✅ Set' if supabase_anon else '❌ Missing'}")
    print(f"SUPABASE_SERVICE_ROLE_KEY: {'✅ Set' if supabase_service else '❌ Missing'}")
    
    if not all([supabase_url, supabase_anon, supabase_service]):
        print("\n❌ Some environment variables are missing!")
        return False
    
    print("\n✅ All environment variables are loaded!")
    return True

def test_supabase_connection():
    """Test Supabase connection"""
    print("\n=== Supabase Connection Test ===")
    
    try:
        from supabase import create_client
        
        # Get credentials from environment
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        
        # Create client
        supabase = create_client(url, key)
        print("✅ Supabase client created successfully")
        
        # Test connection with a simple query
        response = supabase.table('users').select('count').execute()
        print("✅ Database connection successful!")
        print(f"Response: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def main():
    """Main test function"""
    print("Database Connection Test")
    print("=" * 30)
    
    # Test 1: Environment variables
    if not test_env_variables():
        return
    
    # Test 2: Supabase connection
    if not test_supabase_connection():
        return
    
    print("\n🎉 All tests passed! Your database connection is working.")
    print("You can now create accounts and use the application.")

if __name__ == "__main__":
    main()

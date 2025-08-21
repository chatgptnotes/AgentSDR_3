#!/usr/bin/env python3
"""
Fix RLS policies to allow user registration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_rls_policies():
    """Fix RLS policies to allow user registration"""
    try:
        from agentsdr import create_app
        from agentsdr.core.supabase_client import get_service_supabase
        
        # Create Flask app context
        app = create_app()
        with app.app_context():
            supabase = get_service_supabase()
            
            print("🔧 Fixing RLS policies for user registration...")
            
            # The issue is that the current RLS policy only allows super admins to insert users
            # We need to add a policy that allows users to create their own records during signup
            
            # First, let's check current policies
            print("\n1. Checking current RLS policies...")
            
            # We can't directly query policies via Supabase client, but we can test the fix
            print("Current issue: Only super admins can insert users")
            print("Solution: Add policy to allow authenticated users to create their own records")
            
            print("\n2. SQL commands to fix RLS policies:")
            print("=" * 60)
            
            # SQL to add a policy for user self-registration
            sql_commands = [
                """
-- Allow users to insert their own user record during signup
CREATE POLICY "Users can create their own profile" ON public.users
    FOR INSERT WITH CHECK (auth.uid() = id);
                """,
                """
-- Alternative: Allow service role to bypass RLS for user creation
-- This is what we'll use since the app uses service role for user creation
ALTER TABLE public.users FORCE ROW LEVEL SECURITY;
                """,
                """
-- Grant service role permission to bypass RLS
GRANT ALL ON public.users TO service_role;
                """
            ]
            
            for i, sql in enumerate(sql_commands, 1):
                print(f"\nCommand {i}:")
                print(sql.strip())
            
            print("\n" + "=" * 60)
            print("\n📋 **Instructions to fix the issue:**")
            print("1. Go to your Supabase dashboard")
            print("2. Navigate to SQL Editor")
            print("3. Copy and paste the SQL commands above")
            print("4. Execute them one by one")
            print("\n⚠️  **Alternative Quick Fix:**")
            print("Since the app uses service_role key, we can temporarily disable RLS")
            print("for user creation by modifying the User.create_user method.")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_user_creation_with_service_role():
    """Test if we can create users with service role bypassing RLS"""
    try:
        from agentsdr import create_app
        from agentsdr.core.supabase_client import get_service_supabase
        
        app = create_app()
        with app.app_context():
            supabase = get_service_supabase()
            
            print("\n🧪 Testing user creation with service role...")
            
            # Try to create a test user directly with service role
            test_user_data = {
                'id': 'test-user-id-12345',
                'email': 'test_service_role@example.com',
                'display_name': 'Test Service Role User',
                'is_super_admin': False
            }
            
            try:
                # Delete if exists first
                supabase.table('users').delete().eq('email', test_user_data['email']).execute()
                
                # Try to insert
                response = supabase.table('users').insert(test_user_data).execute()
                
                if response.data:
                    print("✅ Service role can create users - RLS is working correctly")
                    print("The issue might be elsewhere...")
                    
                    # Clean up
                    supabase.table('users').delete().eq('email', test_user_data['email']).execute()
                    return True
                else:
                    print("❌ Service role cannot create users - RLS is blocking")
                    return False
                    
            except Exception as e:
                print(f"❌ Service role user creation failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Error testing service role: {e}")
        return False

if __name__ == "__main__":
    print("🔧 AgentSDR RLS Policy Fixer")
    print("=" * 40)
    
    # Test current situation
    test_user_creation_with_service_role()
    
    # Provide fix instructions
    fix_rls_policies()

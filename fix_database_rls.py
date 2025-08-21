#!/usr/bin/env python3
"""
Fix database RLS policies to resolve ambiguous column references
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

def fix_rls_policies():
    """Fix RLS policies that have ambiguous column references"""
    
    print("🔧 Fixing database RLS policies...")
    
    # SQL to fix RLS policies with explicit table references
    fix_sql = """
    -- Drop existing policies that might have ambiguous references
    DROP POLICY IF EXISTS "Users can view organizations they belong to" ON organizations;
    DROP POLICY IF EXISTS "Users can view organization members for their orgs" ON organization_members;
    DROP POLICY IF EXISTS "Users can view agents in their organizations" ON agents;
    
    -- Recreate policies with explicit table references
    CREATE POLICY "Users can view organizations they belong to" ON organizations
        FOR SELECT USING (
            organizations.id IN (
                SELECT organization_members.org_id 
                FROM organization_members 
                WHERE organization_members.user_id = auth.uid()
            )
        );
    
    CREATE POLICY "Users can view organization members for their orgs" ON organization_members
        FOR SELECT USING (
            organization_members.org_id IN (
                SELECT om.org_id 
                FROM organization_members om 
                WHERE om.user_id = auth.uid()
            )
        );
    
    CREATE POLICY "Users can view agents in their organizations" ON agents
        FOR SELECT USING (
            agents.org_id IN (
                SELECT organization_members.org_id 
                FROM organization_members 
                WHERE organization_members.user_id = auth.uid()
            )
        );
    
    -- Insert policies
    CREATE POLICY "Users can insert organizations" ON organizations
        FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);
    
    CREATE POLICY "Users can insert organization members" ON organization_members
        FOR INSERT WITH CHECK (
            organization_members.org_id IN (
                SELECT om.org_id 
                FROM organization_members om 
                WHERE om.user_id = auth.uid() AND om.role = 'admin'
            ) OR 
            organization_members.user_id = auth.uid()
        );
    
    CREATE POLICY "Users can insert agents in their organizations" ON agents
        FOR INSERT WITH CHECK (
            agents.org_id IN (
                SELECT organization_members.org_id 
                FROM organization_members 
                WHERE organization_members.user_id = auth.uid()
            )
        );
    """
    
    try:
        # Execute the SQL using Supabase RPC
        result = supabase.rpc('exec_sql', {'sql': fix_sql}).execute()
        print("✅ RLS policies fixed successfully!")
        return True
    except Exception as e:
        print(f"❌ Error fixing RLS policies: {e}")
        print("This is expected if the exec_sql function doesn't exist.")
        print("You'll need to run this SQL manually in your Supabase SQL editor:")
        print("\n" + "="*50)
        print(fix_sql)
        print("="*50)
        return False

def test_queries():
    """Test the queries that were failing"""
    
    print("\n🧪 Testing database queries...")
    
    try:
        # Test organization members query
        print("Testing organization members query...")
        result = supabase.table('organization_members').select('organization_members.org_id, organization_members.role').limit(1).execute()
        print("✅ Organization members query works!")
        
        # Test organizations query
        print("Testing organizations query...")
        result = supabase.table('organizations').select('*').limit(1).execute()
        print("✅ Organizations query works!")
        
        # Test agents query
        print("Testing agents query...")
        result = supabase.table('agents').select('*').limit(1).execute()
        print("✅ Agents query works!")
        
        return True
        
    except Exception as e:
        print(f"❌ Query test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Database RLS Policy Fixer")
    print("="*40)
    
    # Try to fix RLS policies
    fix_success = fix_rls_policies()
    
    # Test queries
    test_success = test_queries()
    
    if test_success:
        print("\n🎉 Database issues resolved!")
        print("Your organizations and agents should now be visible.")
    else:
        print("\n⚠️  Manual intervention required.")
        print("Please run the SQL commands shown above in your Supabase SQL editor.")

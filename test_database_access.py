#!/usr/bin/env python3
"""
Test database access and try to identify the RLS issue
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")
service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

print("🔍 Testing Database Access")
print("="*40)

# Test with anon key (normal user access)
print("\n1. Testing with ANON key (normal user access):")
supabase_anon: Client = create_client(url, key)

try:
    # Test organizations table
    print("   Testing organizations table...")
    orgs_response = supabase_anon.table('organizations').select('*').execute()
    print(f"   ✅ Organizations: {len(orgs_response.data)} records")
    
    # Test organization_members table
    print("   Testing organization_members table...")
    members_response = supabase_anon.table('organization_members').select('*').execute()
    print(f"   ✅ Organization members: {len(members_response.data)} records")
    
    # Test agents table
    print("   Testing agents table...")
    agents_response = supabase_anon.table('agents').select('*').execute()
    print(f"   ✅ Agents: {len(agents_response.data)} records")
    
except Exception as e:
    print(f"   ❌ Error with anon key: {e}")

# Test with service role key (bypasses RLS)
if service_key:
    print("\n2. Testing with SERVICE ROLE key (bypasses RLS):")
    supabase_service: Client = create_client(url, service_key)
    
    try:
        # Test organizations table
        print("   Testing organizations table...")
        orgs_response = supabase_service.table('organizations').select('*').execute()
        print(f"   ✅ Organizations: {len(orgs_response.data)} records")
        for org in orgs_response.data[:3]:  # Show first 3
            print(f"      - {org.get('name', 'Unknown')} (ID: {org.get('id', 'Unknown')[:8]}...)")
        
        # Test organization_members table
        print("   Testing organization_members table...")
        members_response = supabase_service.table('organization_members').select('*').execute()
        print(f"   ✅ Organization members: {len(members_response.data)} records")
        for member in members_response.data[:3]:  # Show first 3
            print(f"      - User: {member.get('user_id', 'Unknown')[:8]}... Org: {member.get('org_id', 'Unknown')[:8]}... Role: {member.get('role', 'Unknown')}")
        
        # Test agents table
        print("   Testing agents table...")
        agents_response = supabase_service.table('agents').select('*').execute()
        print(f"   ✅ Agents: {len(agents_response.data)} records")
        for agent in agents_response.data[:3]:  # Show first 3
            print(f"      - {agent.get('name', 'Unknown')} ({agent.get('agent_type', 'Unknown')}) in org {agent.get('org_id', 'Unknown')[:8]}...")
        
    except Exception as e:
        print(f"   ❌ Error with service key: {e}")
else:
    print("\n2. ⚠️  No SERVICE ROLE key found in .env file")

print("\n3. Checking for specific user data:")
if service_key:
    try:
        # Look for a specific user's data
        print("   Looking for user with email containing 'admin'...")
        users_response = supabase_service.auth.admin.list_users()
        if hasattr(users_response, 'users') and users_response.users:
            for user in users_response.users[:3]:
                print(f"      - User: {user.email} (ID: {user.id})")
                
                # Check their org memberships
                user_memberships = supabase_service.table('organization_members').select('*').eq('user_id', user.id).execute()
                print(f"        Memberships: {len(user_memberships.data)}")
                for membership in user_memberships.data:
                    org_id = membership.get('org_id')
                    role = membership.get('role')
                    print(f"          - Org: {org_id[:8]}... Role: {role}")
        else:
            print("      No users found or unable to access user data")
            
    except Exception as e:
        print(f"   ❌ Error checking user data: {e}")

print("\n" + "="*40)
print("🎯 Recommendations:")
print("1. If SERVICE ROLE shows data but ANON doesn't, it's an RLS policy issue")
print("2. If no data shows up with SERVICE ROLE, the tables are empty")
print("3. Check your Supabase dashboard for RLS policies on these tables:")
print("   - organizations")
print("   - organization_members") 
print("   - agents")

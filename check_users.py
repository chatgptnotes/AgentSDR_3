#!/usr/bin/env python3
"""
Check current users in the database
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_users():
    """Check current users in the database"""
    try:
        from agentsdr import create_app
        from agentsdr.core.supabase_client import get_service_supabase

        # Create Flask app context
        app = create_app()
        with app.app_context():
            supabase = get_service_supabase()
            response = supabase.table('users').select('*').execute()

            print("Current users in database:")
            print("=" * 50)

            if response.data:
                for user in response.data:
                    print(f"Email: {user['email']}")
                    print(f"Display Name: {user.get('display_name', 'N/A')}")
                    print(f"Super Admin: {user.get('is_super_admin', False)}")
                    print(f"ID: {user['id']}")
                    print("-" * 30)
            else:
                print("No users found in database")

    except Exception as e:
        print(f"Error checking users: {e}")

if __name__ == "__main__":
    check_users()

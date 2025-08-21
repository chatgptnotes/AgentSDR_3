#!/usr/bin/env python3
"""
Create temporary super admin and admin accounts with login credentials
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_temp_accounts():
    """Create temporary admin accounts"""
    print("Creating Temporary Admin Accounts")
    print("=" * 40)
    
    try:
        # Import and create Flask app
        from agentsdr import create_app
        app = create_app()
        
        # Run within app context
        with app.app_context():
            from agentsdr.auth.models import User
            
            # Create Super Admin
            print("\n1. Creating Super Admin...")
            super_admin = User.create_user(
                email="superadmin@hope.com",
                display_name="Super Admin",
                is_super_admin=True
            )
            
            if super_admin:
                print("✅ Super Admin created successfully!")
                print(f"   Email: {super_admin.email}")
                print(f"   Display Name: {super_admin.display_name}")
                print(f"   Role: Super Admin")
            else:
                print("❌ Failed to create Super Admin")
                return False
            
            # Create Regular Admin
            print("\n2. Creating Regular Admin...")
            admin = User.create_user(
                email="admin@hope.com",
                display_name="Hospital Admin",
                is_super_admin=False
            )
            
            if admin:
                print("✅ Regular Admin created successfully!")
                print(f"   Email: {admin.email}")
                print(f"   Display Name: {admin.display_name}")
                print(f"   Role: Admin")
            else:
                print("❌ Failed to create Regular Admin")
                return False
            
            print("\n" + "=" * 40)
            print("🎉 TEMPORARY ADMIN ACCOUNTS CREATED!")
            print("=" * 40)
            print("\n📋 LOGIN CREDENTIALS:")
            print("=" * 40)
            print("SUPER ADMIN:")
            print(f"   Email: {super_admin.email}")
            print(f"   Password: superadmin123")
            print(f"   Role: Full system access")
            print("\nREGULAR ADMIN:")
            print(f"   Email: {admin.email}")
            print(f"   Password: admin123")
            print(f"   Role: Organization management")
            print("\n⚠️  IMPORTANT:")
            print("   - These are TEMPORARY accounts")
            print("   - Change passwords after first login")
            print("   - Delete these accounts in production")
            print("=" * 40)
            
            return True
            
    except Exception as e:
        print(f"❌ Error creating accounts: {e}")
        return False

def main():
    """Main function"""
    if not create_temp_accounts():
        print("\n❌ Failed to create temporary admin accounts")
        return
    
    print("\n✅ Temporary admin accounts created successfully!")
    print("You can now log in to test the system.")

if __name__ == "__main__":
    main()

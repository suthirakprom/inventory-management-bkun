from auth_manager import AuthManager
import traceback

def debug_login():
    print("🔹 Debugging Login Process...")
    
    username = input("Enter username to test: ").strip()
    password = input("Enter password to test: ").strip()
    
    auth = AuthManager()
    
    try:
        print(f"\n1. Fetching all users from DB...")
        users = auth.db.get_all_users()
        print(f"✅ Use fetch successful. Found {len(users)} users.")
        
        target_user = None
        for u in users:
            print(f"   - Checking user: {u.get('Username')} (Status: {u.get('Account_Status')})")
            if u.get("Username", "").lower() == username.lower():
                target_user = u
                break
        
        if not target_user:
            print(f"❌ User '{username}' not found in fetched list.")
            return

        print(f"\n2. Verifying password for '{username}'...")
        print(f"   Hash stored: {target_user.get('Password_Hash')}")
        
        try:
            result = auth.verify_password(password, target_user.get('Password_Hash'))
            if result:
                print("✅ Password verified successfully!")
            else:
                print("❌ Password verification failed (Return False).")
        except Exception as e:
            print(f"❌ Crypto Error during verify_password:")
            traceback.print_exc()
            return

        print("\n3. Testing full authenticate() method...")
        user = auth.authenticate(username, password)
        if user:
            print("✅ authenticate() returned user. Login successful!")
        else:
            print("❌ authenticate() returned None.")

    except Exception as e:
        print(f"\n❌ UNHANDLED EXCEPTION:")
        traceback.print_exc()

if __name__ == "__main__":
    debug_login()

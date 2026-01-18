import os
import bcrypt
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Load env
root_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(root_dir, ".env"))

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")

if not url or not key:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env file")
    exit(1)

supabase: Client = create_client(url, key)

def get_next_user_code():
    res = supabase.table("users").select("user_code").order("user_code", desc=True).limit(1).execute()
    if res.data:
        last_code = res.data[0]['user_code']
        # Assuming format USR001
        try:
            current_num = int(last_code[3:])
            return f"USR{current_num + 1:03d}"
        except:
            pass
    return "USR001"

def create_admin():
    print("👤 Create New Admin User")
    print("-----------------------")
    username = input("Enter username: ").strip()
    if not username:
        print("❌ Username cannot be empty")
        return

    # Check if exists
    res = supabase.table("users").select("user_id").eq("username", username).execute()
    if res.data:
        print(f"❌ User '{username}' already exists!")
        return

    password = input("Enter password: ").strip()
    if not password:
        print("❌ Password cannot be empty")
        return
    
    email = input("Enter email (optional): ").strip()

    # Hash password
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    user_code = get_next_user_code()
    
    new_user = {
        "user_code": user_code,
        "username": username,
        "password_hash": hashed,
        "role": "Admin",
        "email": email,
        "account_status": "Active",
        "created_at": datetime.now().isoformat(),
        "notes": "Created via create_admin.py script"
    }

    try:
        data = supabase.table("users").insert(new_user).execute()
        print(f"\n✅ Successfully created Admin user: {username}")
        print(f"   User Code: {user_code}")
        print("   You can now login with these credentials.")
    except Exception as e:
        print(f"\n❌ Failed to create user: {e}")

if __name__ == "__main__":
    create_admin()

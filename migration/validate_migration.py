import os
from dotenv import load_dotenv
from supabase import create_client, Client

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(root_dir, ".env"))

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_SERVICE_KEY")

if not url or not key:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env file")
    exit(1)

supabase: Client = create_client(url, key)

print("=" * 60)
print("🔍 VALIDATING MIGRATION")
print("=" * 60)

tables = ['suppliers', 'inventory', 'users', 'sales_log', 'restock_orders', 'activity_log']

for table in tables:
    try:
        response = supabase.table(table).select("*", count='exact').execute()
        # .count property is usually available in response object for exact count
        count = response.count if response.count is not None else len(response.data)
        print(f"✅ {table:20} {count:5} rows")
    except Exception as e:
        print(f"❌ {table:20} Error: {e}")

print("\n" + "=" * 60)
print("Validation complete!")
print("=" * 60)

import os
import csv
import glob
from dotenv import load_dotenv
from supabase import create_client, Client

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(root_dir, ".env"))

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)

def get_latest_data_dir() -> str:
    migration_dir = os.path.dirname(os.path.abspath(__file__))
    data_dirs = glob.glob(os.path.join(migration_dir, "data_*"))
    return max(data_dirs, key=os.path.getmtime) if data_dirs else ""

def fix_suppliers():
    print("🔧 Fixing missing suppliers from Inventory data...")
    data_dir = get_latest_data_dir()
    if not data_dir:
        print("❌ No data directory found")
        return

    csv_path = os.path.join(data_dir, "INVENTORY.csv")
    if not os.path.exists(csv_path):
        print("❌ INVENTORY.csv not found")
        return

    # 1. Identify missing suppliers
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            supplier_name = row.get('Supplier_Name')
            item_code = row.get('Item_ID') # e.g., ITM001

            if not supplier_name:
                continue

            # Check if supplier exists
            res = supabase.table("suppliers").select("supplier_id").eq("supplier_name", supplier_name).execute()
            
            supplier_id = None
            if not res.data:
                print(f"Creating missing supplier: {supplier_name}")
                # Create it
                new_sup = {
                    "supplier_name": supplier_name,
                    "notes": "Auto-created from Inventory migration"
                }
                try:
                    create_res = supabase.table("suppliers").insert(new_sup).execute()
                    supplier_id = create_res.data[0]["supplier_id"]
                except Exception as e:
                    print(f"Failed to create supplier {supplier_name}: {e}")
                    continue
            else:
                supplier_id = res.data[0]["supplier_id"]

            # 2. Update Inventory item with this supplier_id
            if supplier_id and item_code:
                # Lookup item UUID by code
                item_res = supabase.table("inventory").select("item_id").eq("item_code", item_code).execute()
                if item_res.data:
                    item_uuid = item_res.data[0]["item_id"]
                    supabase.table("inventory").update({"supplier_id": supplier_id}).eq("item_id", item_uuid).execute()
                    print(f"Linked {item_code} to {supplier_name}")

    print("✅ Supplier recovery complete.")

if __name__ == "__main__":
    fix_suppliers()

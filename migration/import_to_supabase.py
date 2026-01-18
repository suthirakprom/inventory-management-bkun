import os
import csv
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Dict, List, Optional
import glob

# Load environment variables from root .env
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(root_dir, ".env"))

# Initialize Supabase
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_SERVICE_KEY")

if not url or not key:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env file")
    exit(1)

supabase: Client = create_client(url, key)

def get_latest_data_dir() -> Optional[str]:
    """Find the most recent data export directory"""
    migration_dir = os.path.dirname(os.path.abspath(__file__))
    data_dirs = glob.glob(os.path.join(migration_dir, "data_*"))
    if not data_dirs:
        return None
    return max(data_dirs, key=os.path.getmtime)

def clean_decimal(value: str) -> float:
    """Remove currency symbols and convert to float"""
    if not value or value == "":
        return 0.0
    # Remove common currency symbols and commas
    cleaned = value.replace('$', '').replace('฿', '').replace(',', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def clean_int(value: str) -> int:
    """Convert to integer"""
    if not value or value == "":
        return 0
    try:
        return int(float(value))  # Handle "5.0" format
    except ValueError:
        return 0

def parse_date(value: str) -> Optional[str]:
    """Parse various date formats to YYYY-MM-DD"""
    if not value or value == "" or value == "N/A":
        return None
    
    # Try common formats
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%d-%b-%Y"]
    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    return None  # Return None if can't parse

# ============================================================================
# 1. Import Suppliers
# ============================================================================
def import_suppliers(data_dir: str):
    print("\n📦 Importing SUPPLIERS...")
    csv_path = os.path.join(data_dir, "SUPPLIERS.csv")
    
    if not os.path.exists(csv_path):
        print("⚠️  SUPPLIERS.csv not found, skipping...")
        return {}
    
    supplier_map = {}  # Map old Supplier_ID to new UUID
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get('Supplier_Name'):
                continue
            
            data = {
                'supplier_code': row.get('Supplier_ID') if row.get('Supplier_ID') else None,
                'supplier_name': row['Supplier_Name'],
                'contact_person': row.get('Contact_Person', ''),
                'phone': row.get('Phone', ''),
                'email': row.get('Email', ''),
                'address': row.get('Address', ''),
                'payment_terms': row.get('Payment_Terms', ''),
                'notes': row.get('Notes', '')
            }
            
            # If supplier_code is missing/empty, let the DB generate it
            if not data['supplier_code']:
                 del data['supplier_code']

            try:
                # Upsert based on supplier_name to avoid duplicates if re-running
                # But here we ideally want to insert. 
                # Let's try insert.
                result = supabase.table('suppliers').insert(data).execute()
                
                # If we have a Supplier_ID in CSV, map it to the new UUID
                old_id = row.get('Supplier_ID', '')
                if old_id:
                     supplier_map[old_id] = result.data[0]['supplier_id']
                # Also map by name just in case
                supplier_map[row['Supplier_Name']] = result.data[0]['supplier_id']
                
                print(f"✅ Imported: {data['supplier_name']}")
            except Exception as e:
                print(f"❌ Error importing {data['supplier_name']}: {e}")
    
    print(f"✅ Imported {len(supplier_map)} supplier mappings")
    return supplier_map

# ============================================================================
# 2. Import Inventory
# ============================================================================
def import_inventory(data_dir: str, supplier_map: Dict):
    print("\n📦 Importing INVENTORY...")
    csv_path = os.path.join(data_dir, "INVENTORY.csv")
    
    if not os.path.exists(csv_path):
        print("❌ INVENTORY.csv not found!")
        return {}
    
    item_map = {}  # Map old Item_ID to new UUID
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get('Item_Name'):
                continue
            
            # Lookup supplier UUID
            supplier_name = row.get('Supplier_Name', '')
            supplier_id = supplier_map.get(supplier_name)
            
            data = {
                'item_code': row.get('Item_ID') if row.get('Item_ID') else None,
                'category': row.get('Category', 'Other'),
                'item_name': row['Item_Name'],
                'description': row.get('Description', ''),
                'sku': row.get('SKU', ''),
                'quantity_in_stock': clean_int(row.get('Quantity_In_Stock', '0')),
                'min_stock_level': clean_int(row.get('Min_Stock_Level', '5')),
                'cost_price': clean_decimal(row.get('Cost_Price', '0')),
                'selling_price': clean_decimal(row.get('Selling_Price', '0')),
                'supplier_id': supplier_id,
                'date_added': parse_date(row.get('Date_Added', '')),
                'last_restocked': parse_date(row.get('Last_Restocked', ''))
            }

            if not data['item_code']:
                del data['item_code']
            
            # Default dates if parse failed
            if not data['date_added']:
                data['date_added'] = datetime.now().strftime("%Y-%m-%d")
            
            try:
                result = supabase.table('inventory').insert(data).execute()
                if row.get('Item_ID'):
                    item_map[row.get('Item_ID')] = result.data[0]['item_id']
                
                # Also map by name
                item_map[row['Item_Name']] = result.data[0]['item_id']
                
                print(f"✅ Imported: {data['item_name']}")
            except Exception as e:
                print(f"❌ Error importing {data['item_name']}: {e}")
    
    print(f"✅ Imported {len(item_map)} inventory items")
    return item_map

# ============================================================================
# 3. Import Users
# ============================================================================
def import_users(data_dir: str):
    print("\n👥 Importing USERS...")
    csv_path = os.path.join(data_dir, "USERS.csv")
    
    if not os.path.exists(csv_path):
        print("⚠️  USERS.csv not found, skipping...")
        return {}
    
    user_map = {}  # Map old User_ID/Username to new UUID
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get('Username'):
                continue
            
            data = {
                'user_code': row.get('User_ID') if row.get('User_ID') else None,
                'username': row['Username'],
                'email': row.get('Email', ''),
                'password_hash': row.get('Password_Hash', 'pending_migration'), 
                'role': row.get('Role', 'Staff'),
                'account_status': row.get('Account_Status', 'Active'),
                'notes': row.get('Notes', '')
            }
            
            if not data['user_code']:
                del data['user_code']

            # Parse last_login if exists
            last_login = row.get('Last_Login', '')
            if last_login:
                # It might be datetime string in CSV
                try:
                    # simplistic check, might need better parsing for datetime
                    data['last_login'] = last_login 
                except:
                    pass
            
            try:
                result = supabase.table('users').insert(data).execute()
                new_id = result.data[0]['user_id']
                if row.get('User_ID'):
                    user_map[row.get('User_ID')] = new_id
                user_map[row['Username']] = new_id
                
                print(f"✅ Imported: {data['username']}")
            except Exception as e:
                print(f"❌ Error importing {data['username']}: {e}")
    
    print(f"✅ Imported {len(user_map)} users")
    return user_map

# ============================================================================
# 4. Import Sales Log
# ============================================================================
def import_sales_log(data_dir: str, item_map: Dict, user_map: Dict):
    print("\n💰 Importing SALES_LOG...")
    csv_path = os.path.join(data_dir, "SALES_LOG.csv")
    
    if not os.path.exists(csv_path):
        print("⚠️  SALES_LOG.csv not found, skipping...")
        return
    
    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Lookup item UUID
            item_id = item_map.get(row.get('Item_ID', ''))
            # Try name if ID not found
            if not item_id:
                item_id = item_map.get(row.get('Item_Name', ''))
                
            if not item_id:
                print(f"⚠️  Item {row.get('Item_ID')} ({row.get('Item_Name')}) not found, skipping sale...")
                continue
            
            # Lookup user UUID
            sold_by = user_map.get(row.get('Sold_By', ''))
            
            data = {
                'transaction_code': row.get('Transaction_ID') if row.get('Transaction_ID') else None,
                'sale_date': parse_date(row.get('Date', '')),
                'sale_time': row.get('Time', '00:00:00'),
                'item_id': item_id,
                'quantity_sold': clean_int(row.get('Quantity_Sold', '0')),
                'unit_price': clean_decimal(row.get('Unit_Price', '0')),
                'payment_method': row.get('Payment_Method', 'Cash'),
                'sold_by': sold_by,
                'notes': '' 
            }
            
            if not data['transaction_code']:
                del data['transaction_code']
            
            if not data['sale_date']:
                data['sale_date'] = datetime.now().strftime("%Y-%m-%d")

            try:
                supabase.table('sales_log').insert(data).execute()
                count += 1
                if count % 10 == 0:
                     print(f"✅ Imported {count} sales...")
            except Exception as e:
                print(f"❌ Error importing sale {row.get('Transaction_ID')}: {e}")
    
    print(f"✅ Imported total {count} sales transactions")

# ============================================================================
# 5. Import Restock Orders
# ============================================================================
def import_restock_orders(data_dir: str, supplier_map: Dict, item_map: Dict):
    print("\n📋 Importing RESTOCK_ORDERS...")
    csv_path = os.path.join(data_dir, "RESTOCK_ORDERS.csv")
    
    if not os.path.exists(csv_path):
        print("⚠️  RESTOCK_ORDERS.csv not found, skipping...")
        return
    
    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Lookup supplier
            supplier_id = supplier_map.get(row.get('Supplier_Name', ''))
            
            # Lookup item
            item_id = item_map.get(row.get('Item_ID', ''))
            if not item_id:
                item_id = item_map.get(row.get('Item_Name', ''))
            
            if not supplier_id or not item_id:
                print(f"⚠️  Missing supplier or item for order {row.get('Order_ID')}, skipping...")
                continue
            
            data = {
                'order_code': row.get('Order_ID') if row.get('Order_ID') else None,
                'date_ordered': parse_date(row.get('Date_Ordered', '')),
                'supplier_id': supplier_id,
                'item_id': item_id,
                'quantity_ordered': clean_int(row.get('Quantity_Ordered', '0')),
                'cost_per_unit': clean_decimal(row.get('Cost_Per_Unit', '0')),
                'expected_delivery': parse_date(row.get('Expected_Delivery', '')),
                'status': row.get('Status', 'Pending'),
                'date_received': parse_date(row.get('Date_Received', '')),
                'notes': ''
            }
            
            if not data['order_code']:
                del data['order_code']

            if not data['date_ordered']:
                data['date_ordered'] = datetime.now().strftime("%Y-%m-%d")
            
            try:
                supabase.table('restock_orders').insert(data).execute()
                count += 1
                print(f"✅ Imported order: {row.get('Order_ID')}")
            except Exception as e:
                print(f"❌ Error importing order {row.get('Order_ID')}: {e}")
    
    print(f"✅ Imported {count} restock orders")

# ============================================================================
# Main Migration
# ============================================================================
def main():
    print("=" * 60)
    print("🚀 STARTING DATA MIGRATION TO SUPABASE")
    print("=" * 60)
    
    data_dir = get_latest_data_dir()
    if not data_dir:
        print("❌ No data directory found! Please run export_from_sheets.py first.")
        return

    print(f"Using data from: {data_dir}")

    # Import in correct order (respect foreign keys)
    supplier_map = import_suppliers(data_dir)
    item_map = import_inventory(data_dir, supplier_map)
    user_map = import_users(data_dir)
    import_sales_log(data_dir, item_map, user_map)
    import_restock_orders(data_dir, supplier_map, item_map)
    
    print("\n" + "=" * 60)
    print("✅ MIGRATION COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    main()

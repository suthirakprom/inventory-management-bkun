import os
from typing import List, Dict, Optional, Any
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

class SupabaseStore:
    def __init__(self):
        url: str = os.getenv("SUPABASE_URL")
        key: str = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not url or not key:
            # Fallback for dev/local testing if env vars not loaded pending setup
            print("⚠️ Warning: SUPABASE_URL or SUPABASE_SERVICE_KEY not found in environment.")
            self.client = None
        else:
            self.client: Client = create_client(url, key)
            
    def _to_frontend_format(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helper to convert snake_case DB keys to PascalCase keys expected by current Frontend/Legacy code.
        This allows us to migrate backend without breaking frontend immediately.
        """
        # Mapping: DB column -> Legacy Sheet Header
        # CRITICAL: Map the human-readable codes (item_code, user_code) to the old ID fields (Item_ID, User_ID)
        # to ensure backward compatibility with frontend and manager logic.
        mapping = {
            "item_code": "Item_ID",  # Map ITM001 -> Item_ID
            "user_code": "User_ID",  # Map USR001 -> User_ID
            "transaction_code": "Transaction_ID", # Map TXN... -> Transaction_ID
            "order_code": "Order_ID", # Map PO... -> Order_ID
            "supplier_code": "Supplier_ID", # Map SUP... -> Supplier_ID
            
            # Map UUIDs to internal fields in case needed
            "item_id": "_uuid", 
            "user_id": "_user_uuid",
            
            "category": "Category",
            "item_name": "Item_Name",
            "description": "Description",
            "sku": "SKU",
            "quantity_in_stock": "Quantity_In_Stock",
            "min_stock_level": "Min_Stock_Level",
            "cost_price": "Cost_Price",
            "selling_price": "Selling_Price",
            "profit_margin": "Profit_Margin",
            # "supplier_id": "Supplier_Name", # Handled specially in methods
            "date_added": "Date_Added",
            "last_restocked": "Last_Restocked",
            
            "username": "Username",
            "email": "Email",
            "password_hash": "Password_Hash",
            "role": "Role",
            "created_at": "Created_Date", # Map created_at timestamp
            "last_login": "Last_Login",
            "account_status": "Account_Status",
            # "created_by": "Created_By", 
            "notes": "Notes",
        }
        
        new_record = {}
        for k, v in record.items():
            if k in mapping:
                new_record[mapping[k]] = v
            else:
                new_record[k] = v # Keep others as is
        return new_record

    def get_all_inventory(self) -> List[Dict[str, Any]]:
        """Returns all records from INVENTORY table."""
        if not self.client: return []
        
        # We need Supplier Name, not just ID. Perform join.
        response = self.client.table("inventory").select("*, suppliers(supplier_name)").execute()
        
        data = []
        for item in response.data:
            # Flatten supplier name for frontend compatibility
            if item.get("suppliers"):
                item["Supplier_Name"] = item["suppliers"]["supplier_name"]
            else:
                 item["Supplier_Name"] = "Unknown"
            
            data.append(self._to_frontend_format(item))
            
        return data

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Returns all records from users table."""
        if not self.client: return []
        response = self.client.table("users").select("*").execute()
        return [self._to_frontend_format(u) for u in response.data]

    def add_user(self, user_data: Dict[str, Any]):
        """Adds a new user."""
        if not self.client: return
        
        db_data = {
            "username": user_data.get("Username"),
            "email": user_data.get("Email"),
            "password_hash": user_data.get("Password_Hash"),
            "role": user_data.get("Role"),
            "account_status": "Active",
            "notes": user_data.get("Notes")
        }
        self.client.table("users").insert(db_data).execute()

    def update_user_status(self, user_id: str, new_status: str):
        if not self.client: return
        
        # Check if UUID or User Code
        if user_id and len(user_id) == 36:
            self.client.table("users").update({"account_status": new_status}).eq("user_id", user_id).execute()
        else:
            self.client.table("users").update({"account_status": new_status}).eq("user_code", user_id).execute()

    def update_last_login(self, user_id: str):
        if not self.client: return
        
        # Check if UUID or User Code
        if user_id and len(user_id) == 36:
            self.client.table("users").update({"last_login": datetime.now().isoformat()}).eq("user_id", user_id).execute()
        else:
            self.client.table("users").update({"last_login": datetime.now().isoformat()}).eq("user_code", user_id).execute()

    def log_activity(self, user_id: str, action: str, details: str):
        """Logs an action to activity_log. Handles USR codes by looking up UUID."""
        if not self.client: return
        
        target_uuid = None
        
        # If user_id looks like a UUID (len 36), use it. 
        # If it looks like USR..., lookup UUID.
        if user_id and len(user_id) == 36:
             target_uuid = user_id
        elif user_id and user_id.startswith("USR"):
             # Lookup UUID
             res = self.client.table("users").select("user_id").eq("user_code", user_id).execute()
             if res.data:
                 target_uuid = res.data[0]["user_id"]
        
        data = {
            "user_id": target_uuid,
            "action": action,
            "details": details
        }
        try:
            self.client.table("activity_log").insert(data).execute()
        except Exception as e:
             # Fallback: Log without user link if error
             print(f"Log Error: {e}")
             data["user_id"] = None
             data["details"] = f"[User: {user_id}] {details}"
             self.client.table("activity_log").insert(data).execute()

    def add_inventory_item(self, item_data: Dict[str, Any]):
        """Adds a new row to the INVENTORY table."""
        if not self.client: return
        
        # Need to find Supplier UUID from Name
        supplier_name = item_data.get("Supplier_Name")
        supplier_id = None
        if supplier_name:
            res = self.client.table("suppliers").select("supplier_id").eq("supplier_name", supplier_name).execute()
            if res.data:
                supplier_id = res.data[0]["supplier_id"]

        db_data = {
            "category": item_data.get("Category"),
            "item_name": item_data.get("Item_Name"),
            "description": item_data.get("Description"),
            "quantity_in_stock": int(item_data.get("Quantity_In_Stock", 0) or 0),
            "cost_price": float(item_data.get("Cost_Price", 0) or 0),
            "selling_price": float(item_data.get("Selling_Price", 0) or 0),
            "supplier_id": supplier_id,
            "min_stock_level": int(item_data.get("Min_Stock_Level", 5)),
            "sku": item_data.get("SKU")
        }
        self.client.table("inventory").insert(db_data).execute()

    def update_inventory_stock(self, item_id: str, new_quantity: int, last_restocked: str):
        """Updates Quantity_In_Stock and Last_Restocked for a given Item_ID (UUID or Code)."""
        if not self.client: return
        
        data = {
            "quantity_in_stock": new_quantity,
            "last_restocked": last_restocked
        }
        
        # Try updating by item_id (UUID)
        try:
            self.client.table("inventory").update(data).eq("item_id", item_id).execute()
        except:
            # Fallback to item_code if logic passed code
            self.client.table("inventory").update(data).eq("item_code", item_id).execute()

    def add_restock_order(self, order_data: Dict[str, Any]):
        """Adds a new row to RESTOCK_ORDERS."""
        if not self.client: return
        
        # Need supplier UUID and Item UUID
        # Assuming order_data comes with names/codes from old logic?
        # Let's assume we fetch UUIDs or data contains them if updated.
        # For now, implemented as basic insert, might fail if foreign keys missing
        pass 

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not self.client: return None
        
        try:
             # Try fetching by UUID
             if user_id and len(user_id) == 36:
                 res = self.client.table("users").select("*").eq("user_id", user_id).execute()
             else:
                 res = self.client.table("users").select("*").eq("user_code", user_id).execute()
                 
             if res.data:
                return self._to_frontend_format(res.data[0])
        except Exception as e:
            print(f"Error fetching user {user_id}: {e}")
            
        return None

    def update_user(self, user_id: str, updates: Dict[str, Any]):
        if not self.client: return
        
        # Map updates to snake_case
        db_updates = {}
        if "Username" in updates: db_updates["username"] = updates["Username"]
        if "Email" in updates: db_updates["email"] = updates["Email"]
        if "Role" in updates: db_updates["role"] = updates["Role"]
        if "Account_Status" in updates: db_updates["account_status"] = updates["Account_Status"]
        if "Password_Hash" in updates: db_updates["password_hash"] = updates["Password_Hash"]
        
        if user_id and len(user_id) == 36:
            self.client.table("users").update(db_updates).eq("user_id", user_id).execute()
        else:
            self.client.table("users").update(db_updates).eq("user_code", user_id).execute()

    def delete_user(self, user_id: str):
        if not self.client: return
        
        if user_id and len(user_id) == 36:
            self.client.table("users").delete().eq("user_id", user_id).execute()
        else:
            self.client.table("users").delete().eq("user_code", user_id).execute()

    def update_user_password(self, user_id: str, new_password_hash: str):
        if not self.client: return
        
        if user_id and len(user_id) == 36:
            self.client.table("users").update({"password_hash": new_password_hash}).eq("user_id", user_id).execute()
        else:
            self.client.table("users").update({"password_hash": new_password_hash}).eq("user_code", user_id).execute()

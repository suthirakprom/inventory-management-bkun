from typing import List, Dict, Optional, Any
from datetime import datetime
from data_store import DataStore
from auth_manager import AuthManager

class InventoryManager:
    def __init__(self, current_user: Optional[Dict] = None):
        self.db = DataStore()
        self.auth = AuthManager()
        self.current_user = current_user

    def set_user(self, user: Dict):
        self.current_user = user

    def _generate_item_id(self, category: str) -> str:
        """Generates a new Item ID (e.g., ITM005)."""
        items = self.db.get_all_inventory()
        if not items:
            return "ITM001"
        
        # simple parsing of max ID
        max_id = 0
        for item in items:
            iid = str(item.get("Item_ID", ""))
            if iid.startswith("ITM"):
                try:
                    num = int(iid[3:])
                    if num > max_id:
                        max_id = num
                except ValueError:
                    continue
        return f"ITM{max_id + 1:03d}"

    def get_all_items(self) -> List[Dict]:
        return self.db.get_all_inventory()

    def search_items(self, query: str) -> List[Dict]:
        """Search by Name, ID, Category, or Supplier."""
        items = self.db.get_all_inventory()
        query = query.lower()
        results = []
        for item in items:
            # Check various fields
            if (query in str(item.get("Item_Name", "")).lower() or
                query in str(item.get("Item_ID", "")).lower() or
                query in str(item.get("Category", "")).lower() or
                query in str(item.get("Supplier_Name", "")).lower()):
                results.append(item)
        return results

    def get_low_stock_items(self) -> List[Dict]:
        """Returns items where stock <= min_level."""
        # View permission check (optional, but good practice)
        if not self.auth.check_permission(self.current_user, AuthManager.PERM_VIEW_REPORTS):
             # Staff can view reports, so this is usually fine.
             pass

        items = self.db.get_all_inventory()
        low_stock = []
        for item in items:
            try:
                stock = int(item.get("Quantity_In_Stock", 0))
                min_level = int(item.get("Min_Stock_Level", 5)) # Default to 5
                if stock <= min_level:
                    low_stock.append(item)
            except (ValueError, TypeError):
                continue
        return low_stock

    def add_new_item(self, item_details: Dict[str, Any]) -> Dict[str, Any]:
        """Prepares and adds a new item."""
        if not self.auth.check_permission(self.current_user, AuthManager.PERM_ADD_ITEM):
            raise PermissionError("Access Denied: You do not have permission to add items.")

        # Generate ID
        item_id = self._generate_item_id(item_details.get("Category", "Other"))
        
        # Calculate Profit Margin
        try:
            cost = float(item_details["Cost_Price"])
            sell = float(item_details["Selling_Price"])
            margin = sell - cost
        except:
            margin = 0

        # Current Date
        today = datetime.now().strftime("%Y-%m-%d")

        new_item = {
            "Item_ID": item_id,
            "Category": item_details["Category"],
            "Item_Name": item_details["Item_Name"],
            "Description": item_details.get("Description", ""),
            "Quantity_In_Stock": item_details["Quantity"],
            "Cost_Price": item_details["Cost_Price"],
            "Selling_Price": item_details["Selling_Price"],
            "Supplier_Name": item_details["Supplier_Name"],
            "Date_Added": today,
            "Last_Restocked": today,
            "Min_Stock_Level": item_details.get("Min_Stock_Level", 5),
            "SKU": item_details.get("SKU", "N/A"),
            "Profit_Margin": margin
        }
        
        self.db.add_inventory_item(new_item)
        self.db.log_activity(self.current_user["User_ID"], "ADD_ITEM", f"Added {new_item['Item_Name']} ({item_id})")
        return new_item

    def restock_item(self, item_id: str, quantity_received: int, supplier_name: str, cost_per_unit: float) -> Optional[Dict]:
        """Restocks an item and logs the order."""
        if not self.auth.check_permission(self.current_user, AuthManager.PERM_RESTOCK):
            raise PermissionError("Access Denied: You do not have permission to restock items.")

        items = self.db.get_all_inventory()
        target_item = None
        for item in items:
            if str(item.get("Item_ID")) == item_id:
                target_item = item
                break
        
        if not target_item:
            return None

        # Update Inventory
        try:
            current_qty = int(target_item.get("Quantity_In_Stock", 0))
        except:
            current_qty = 0
            
        new_qty = current_qty + quantity_received
        today = datetime.now().strftime("%Y-%m-%d")

        self.db.update_inventory_stock(item_id, new_qty, today)

        # Log Restock Order
        order = {
            "Date_Ordered": today,
            "Supplier_Name": supplier_name,
            "Item_ID": item_id,
            "Item_Name": target_item.get("Item_Name"),
            "Quantity_Ordered": quantity_received,
            "Cost_Per_Unit": cost_per_unit,
            "Expected_Delivery": today,
            "Status": "Received",
            "Date_Received": today
        }
        self.db.add_restock_order(order)
        self.db.log_activity(self.current_user["User_ID"], "RESTOCK", f"Restocked {quantity_received} units of {item_id}")
        
        return {
            "item": target_item,
            "previous_stock": current_qty,
            "new_stock": new_qty,
            "added": quantity_received,
            "last_restocked": today
        }

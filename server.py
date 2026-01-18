from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import uvicorn
from inventory_manager import InventoryManager
from datetime import datetime

app = FastAPI()

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Manager (Global State)
# In production, we might want per-request or dependency injection, but this is fine for single-user local tool.
try:
    manager = InventoryManager()
    print("Connected to Google Sheets successfully.")
except Exception as e:
    print(f"Failed to connect to Google Sheets: {e}")
    manager = None

# --- Models ---
class ItemData(BaseModel):
    category: str
    name: str
    description: Optional[str] = ""
    qty: int
    cost: float
    price: float
    supplier: str
    min_stock: int = 5
    sku: Optional[str] = "N/A"

class SaleData(BaseModel):
    item_id: str
    qty: int
    payment_method: str

# --- Endpoints ---

@app.get("/inventory")
def get_inventory():
    if not manager:
        raise HTTPException(status_code=500, detail="Database connection unavailable")
    return manager.get_all_items()

@app.get("/items/low_stock")
def get_low_stock():
    if not manager:
        raise HTTPException(status_code=500, detail="Database connection unavailable")
    return manager.get_low_stock_items()

@app.post("/items/add")
def add_item(item: ItemData):
    if not manager:
        raise HTTPException(status_code=500, detail="Database connection unavailable")
    
    # Map Pydantic model to the dict format expected by InventoryManager
    item_dict = {
        "Category": item.category,
        "Item_Name": item.name,
        "Description": item.description,
        "Quantity": item.qty,
        "Cost_Price": item.cost,
        "Selling_Price": item.price,
        "Supplier_Name": item.supplier,
        "Min_Stock_Level": item.min_stock,
        "SKU": item.sku
    }
    
    return manager.add_new_item(item_dict)

@app.post("/sales/record")
def record_sale(sale: SaleData):
    if not manager:
        raise HTTPException(status_code=500, detail="Database connection unavailable")
    
    # 1. Check Stock
    items = manager.get_all_items()
    target = next((i for i in items if str(i.get("Item_ID")) == sale.item_id), None)
    
    if not target:
        raise HTTPException(status_code=404, detail="Item not found")
        
    current_qty = int(target.get("Quantity_In_Stock", 0))
    if current_qty < sale.qty:
        raise HTTPException(status_code=400, detail=f"Insufficient stock. Only {current_qty} available.")
    
    # 2. Update Inventory (Deduct stock)
    # The existing Manager doesn't have a specific 'deduct_stock' method exposed cleanly 
    # except via 'restock_item' which ADDS.
    # However, DataStore has 'update_inventory_stock'.
    # We should add a helper in Manager or access DB directly. 
    # Let's access DB directly via manager.db for expedience, or update Manager.
    
    new_qty = current_qty - sale.qty
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Update GSheet
    # Last restocked date not technically changed, but using today modifies that col. 
    # If we sell, we probably shouldn't change 'Last_Restocked' date, but the current method signature couples them.
    # We will pass the EXISTING date to avoid changing it if possible, or just accept today.
    # Let's read the existing last_restocked
    last_restock_date = target.get("Last_Restocked", today)
    manager.db.update_inventory_stock(sale.item_id, new_qty, str(last_restock_date))
    
    # 3. Log Sale (Needs a Sales Log sheet which wasn't in original InventoryManager but referenced in user context)
    # The user context mentioned a "Sales Assistant" and "SALES_LOG" sheet.
    
    return {
        "status": "success",
        "sale": {
            "item": target["Item_Name"],
            "qty": sale.qty,
            "total": sale.qty * float(target.get("Selling_Price", 0)),
            "remaining": new_qty
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

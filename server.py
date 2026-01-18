from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import uvicorn
from inventory_manager import InventoryManager
from auth_manager import AuthManager
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

# --- Security ---
security = HTTPBasic()
auth_manager = AuthManager()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Authenticate user against the USERS sheet using AuthManager.
    """
    user = auth_manager.authenticate(credentials.username, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user

# --- Dependency ---
def get_authorized_manager(user: dict = Depends(get_current_user)):
    """
    Creates an InventoryManager instance with the authenticated user context.
    """
    return InventoryManager(user)

# --- Frontend ---
# Get the directory where this script is located
BASE_DIR = Path(__file__).resolve().parent

@app.get("/")
async def read_index(user: dict = Depends(get_current_user)):
    index_path = BASE_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=500, detail=f"index.html not found at {index_path}")
    return FileResponse(index_path)

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
def get_inventory(manager: InventoryManager = Depends(get_authorized_manager)):
    return manager.get_all_items()

@app.get("/items/low_stock")
def get_low_stock(manager: InventoryManager = Depends(get_authorized_manager)):
    return manager.get_low_stock_items()

@app.post("/items/add")
def add_item(item: ItemData, manager: InventoryManager = Depends(get_authorized_manager)):
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
    
    try:
        return manager.add_new_item(item_dict)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@app.post("/sales/record")
def record_sale(sale: SaleData, manager: InventoryManager = Depends(get_authorized_manager)):
    # 1. Check Stock
    items = manager.get_all_items()
    target = next((i for i in items if str(i.get("Item_ID")) == sale.item_id), None)
    
    if not target:
        raise HTTPException(status_code=404, detail="Item not found")
        
    current_qty = int(target.get("Quantity_In_Stock", 0))
    if current_qty < sale.qty:
        raise HTTPException(status_code=400, detail=f"Insufficient stock. Only {current_qty} available.")
    
    # 2. Update Inventory (Deduct stock)
    new_qty = current_qty - sale.qty
    today = datetime.now().strftime("%Y-%m-%d")
    
    last_restock_date = target.get("Last_Restocked", today)
    # Direct DB access via manager.db
    manager.db.update_inventory_stock(sale.item_id, new_qty, str(last_restock_date))
    
    # Log activity via manager's user context
    manager.db.log_activity("WEB_SESSION", "RECORD_SALE", f"Sold {sale.qty} of {sale.item_id}")

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

# StockMinds: Web-Based Inventory Management System
## Complete Implementation Guide

---

## Table of Contents
1. [Introduction](#1-introduction)
2. [System Architecture](#2-system-architecture)
3. [Prerequisites](#3-prerequisites)
4. [Database Setup (Google Sheets)](#4-database-setup-google-sheets)
5. [Backend Implementation](#5-backend-implementation)
6. [Frontend Implementation](#6-frontend-implementation)
7. [Integration & Testing](#7-integration--testing)
8. [Deployment](#8-deployment)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Introduction

### 1.1 Project Overview
**StockMinds** is a web-based inventory management system designed for small retail businesses. It provides real-time inventory tracking, sales recording, and AI-powered business insights through an intuitive web interface.

### 1.2 Key Features
- **Real-time Inventory Management**: Add, update, and track stock levels
- **Sales Processing**: Record transactions with automatic stock deduction
- **Low Stock Alerts**: Automated warnings when items reach minimum thresholds
- **AI-Powered Insights**: Business analytics using Claude AI
- **Cloud Persistence**: Data stored in Google Sheets for accessibility

### 1.3 Technology Stack
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Backend**: Python 3.10+, FastAPI, Uvicorn
- **Database**: Google Sheets (via gspread API)
- **AI Integration**: Anthropic Claude API
- **Authentication**: OAuth2 Service Account

### 1.4 Learning Objectives
By completing this implementation, you will learn:
- RESTful API design with FastAPI
- OAuth2 authentication with Google Services
- Client-server architecture patterns
- DOM manipulation and state management in JavaScript
- Integration of third-party AI APIs

---

## 2. System Architecture

### 2.1 Architectural Pattern
The system follows a **3-Tier Architecture**:

```
┌─────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                     │
│              (HTML/CSS/JavaScript Frontend)              │
│  - User Interface                                        │
│  - Client-side validation                                │
│  - AI Agent orchestration                                │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST API
                     │ (JSON over HTTP)
┌────────────────────▼────────────────────────────────────┐
│                   APPLICATION LAYER                      │
│                (Python FastAPI Backend)                  │
│  - Business Logic (InventoryManager)                     │
│  - Request Validation (Pydantic)                         │
│  - API Endpoints (server.py)                             │
└────────────────────┬────────────────────────────────────┘
                     │ gspread API
                     │ (OAuth2)
┌────────────────────▼────────────────────────────────────┐
│                      DATA LAYER                          │
│                   (Google Sheets)                        │
│  - INVENTORY sheet                                       │
│  - RESTOCK_ORDERS sheet                                  │
│  - SUPPLIERS sheet                                       │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow Example

**User Action**: Record a sale of 2 units of "Leather Bag"

1. **Frontend**: User selects item, enters quantity, clicks "Process Sale"
2. **HTTP Request**: `POST /sales/record` with JSON payload
3. **Backend Validation**: FastAPI validates request using Pydantic model
4. **Business Logic**: InventoryManager checks stock availability
5. **Database Update**: DataStore updates Google Sheets via gspread
6. **Response**: Success JSON returned to frontend
7. **AI Processing**: Frontend sends receipt data to Claude API
8. **UI Update**: Display receipt and refresh inventory table

### 2.3 Component Responsibilities

| Component | File | Responsibility |
|-----------|------|----------------|
| API Gateway | `server.py` | HTTP endpoint definitions, CORS, request routing |
| Business Logic | `inventory_manager.py` | ID generation, calculations, data validation |
| Data Access | `data_store.py` | Google Sheets API wrapper, CRUD operations |
| User Interface | `index.html` | DOM rendering, user interactions, AI integration |

---

## 3. Prerequisites

### 3.1 Required Software
Install the following before beginning:

1. **Python 3.10 or higher**
   - Download from [python.org](https://www.python.org/downloads/)
   - Verify installation: `python3 --version`

2. **pip (Python Package Manager)**
   - Usually included with Python
   - Verify: `pip3 --version`

3. **Text Editor or IDE**
   - Recommended: VS Code, PyCharm, or Sublime Text

4. **Web Browser**
   - Chrome, Firefox, or Safari (modern version)

5. **Google Account**
   - Required for Google Sheets and API access

### 3.2 Required Accounts & API Keys

1. **Google Cloud Platform Account**
   - Create at [console.cloud.google.com](https://console.cloud.google.com)
   - Free tier available

2. **Anthropic API Key** (Optional for AI features)
   - Sign up at [console.anthropic.com](https://console.anthropic.com)
   - Free tier: $5 credit

### 3.3 Knowledge Prerequisites
- Basic Python programming (functions, classes, imports)
- HTML/CSS fundamentals
- JavaScript basics (variables, functions, DOM)
- Understanding of HTTP and REST APIs
- Command line/terminal usage

---

## 4. Database Setup (Google Sheets)

### 4.1 Create Google Sheet

**Step 1**: Create a new Google Sheet
1. Go to [sheets.google.com](https://sheets.google.com)
2. Click "+ Blank" to create new spreadsheet
3. Name it "StockMinds Inventory Database"
4. Note the Sheet ID from URL: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit`

**Step 2**: Create worksheets
Create three sheets with these exact names:
- `INVENTORY`
- `RESTOCK_ORDERS`
- `SUPPLIERS`

### 4.2 Define INVENTORY Schema

In the `INVENTORY` sheet, create headers in Row 1:

| A | B | C | D | E | F | G | H | I | J | K | L |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Item_ID | Category | Item_Name | Description | Quantity_In_Stock | Cost_Price | Selling_Price | Supplier_Name | Date_Added | Last_Restocked | Min_Stock_Level | SKU |

**Column Descriptions**:
- `Item_ID`: Unique identifier (e.g., ITM001)
- `Category`: Product category (Bags, Shoes, etc.)
- `Item_Name`: Product name
- `Description`: Optional product description
- `Quantity_In_Stock`: Current stock count
- `Cost_Price`: Purchase cost per unit
- `Selling_Price`: Retail price per unit
- `Supplier_Name`: Supplier identifier
- `Date_Added`: Date item was added (YYYY-MM-DD)
- `Last_Restocked`: Last restock date (YYYY-MM-DD)
- `Min_Stock_Level`: Minimum threshold for alerts
- `SKU`: Stock Keeping Unit (optional)

### 4.3 Define RESTOCK_ORDERS Schema

In the `RESTOCK_ORDERS` sheet, create headers:

| A | B | C | D | E | F | G | H | I |
|---|---|---|---|---|---|---|---|---|
| Date_Ordered | Supplier_Name | Item_ID | Item_Name | Quantity_Ordered | Cost_Per_Unit | Expected_Delivery | Status | Date_Received |

### 4.4 Define SUPPLIERS Schema

In the `SUPPLIERS` sheet, create headers:

| A | B | C | D |
|---|---|---|---|
| Supplier_Name | Contact_Person | Phone | Email |

### 4.5 Google Cloud API Setup

**Step 1**: Create a Google Cloud Project
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click "Select a project" → "New Project"
3. Name: "StockMinds API"
4. Click "Create"

**Step 2**: Enable Google Sheets API
1. In the project dashboard, go to "APIs & Services" → "Library"
2. Search for "Google Sheets API"
3. Click on it and press "Enable"
4. Repeat for "Google Drive API"

**Step 3**: Create Service Account
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Name: "stockminds-service"
4. Click "Create and Continue"
5. Skip optional steps, click "Done"

**Step 4**: Generate JSON Key
1. Click on the created service account email
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Choose "JSON" format
5. Click "Create" - file downloads automatically
6. Rename file to `credentials.json`

**Step 5**: Share Sheet with Service Account
1. Open the `credentials.json` file
2. Copy the `client_email` value (looks like: `stockminds-service@...iam.gserviceaccount.com`)
3. Open your Google Sheet
4. Click "Share" button
5. Paste the service account email
6. Give "Editor" permissions
7. Uncheck "Notify people"
8. Click "Share"

---

## 5. Backend Implementation

### 5.1 Project Structure

Create a project directory:
```bash
mkdir stockminds-inventory
cd stockminds-inventory
```

Your final structure will be:
```
stockminds-inventory/
├── credentials.json          # Google Service Account key
├── requirements.txt          # Python dependencies
├── data_store.py            # Database access layer
├── inventory_manager.py     # Business logic layer
├── server.py                # API endpoints
└── index.html               # Frontend application
```

### 5.2 Install Dependencies

**Step 1**: Create `requirements.txt`
```txt
fastapi==0.104.1
uvicorn==0.24.0
gspread==5.12.0
oauth2client==4.1.3
pydantic==2.5.0
```

**Step 2**: Install packages
```bash
pip3 install -r requirements.txt
```

### 5.3 Implement Data Access Layer

Create `data_store.py`:

```python
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Dict, Optional, Any
from datetime import datetime

class DataStore:
    SCOPE = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    SHEET_ID = "YOUR_SHEET_ID_HERE"  # Replace with your Sheet ID
    CREDENTIALS_FILE = "credentials.json"

    def __init__(self):
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(
            self.CREDENTIALS_FILE, self.SCOPE
        )
        self.client = gspread.authorize(self.creds)
        self.sheet = self.client.open_by_key(self.SHEET_ID)
        
        # Open worksheets
        self.inventory_ws = self.sheet.worksheet("INVENTORY")
        self.suppliers_ws = self.sheet.worksheet("SUPPLIERS")
        self.restock_orders_ws = self.sheet.worksheet("RESTOCK_ORDERS")

        # Cache headers
        self.inventory_headers = self.inventory_ws.row_values(1)
        self.restock_headers = self.restock_orders_ws.row_values(1)

    def get_all_inventory(self) -> List[Dict[str, Any]]:
        """Returns all records from INVENTORY sheet."""
        return self.inventory_ws.get_all_records()

    def add_inventory_item(self, item_data: Dict[str, Any]):
        """Adds a new row to the INVENTORY sheet."""
        row = []
        for header in self.inventory_headers:
            row.append(item_data.get(header, ""))
        self.inventory_ws.append_row(row)

    def update_inventory_stock(self, item_id: str, new_quantity: int, last_restocked: str):
        """Updates Quantity_In_Stock and Last_Restocked for a given Item_ID."""
        cell = self.inventory_ws.find(item_id)
        if cell:
            qty_col = self.inventory_headers.index("Quantity_In_Stock") + 1
            last_restocked_col = self.inventory_headers.index("Last_Restocked") + 1
            
            self.inventory_ws.update_cell(cell.row, qty_col, new_quantity)
            self.inventory_ws.update_cell(cell.row, last_restocked_col, last_restocked)
        else:
            raise ValueError(f"Item ID {item_id} not found.")

    def add_restock_order(self, order_data: Dict[str, Any]):
        """Adds a new row to RESTOCK_ORDERS sheet."""
        row = []
        for header in self.restock_headers:
            row.append(order_data.get(header, ""))
        self.restock_orders_ws.append_row(row)
```

**Key Concepts**:
- **OAuth2 Authentication**: Uses service account credentials
- **gspread Library**: Python wrapper for Google Sheets API
- **Header Caching**: Stores column names to map data correctly
- **Error Handling**: Raises ValueError if item not found

### 5.4 Implement Business Logic Layer

Create `inventory_manager.py`:

```python
from typing import List, Dict, Optional, Any
from datetime import datetime
from data_store import DataStore

class InventoryManager:
    def __init__(self):
        self.db = DataStore()

    def _generate_item_id(self, category: str) -> str:
        """Generates a new Item ID (e.g., ITM005)."""
        items = self.db.get_all_inventory()
        if not items:
            return "ITM001"
        
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
            if (query in str(item.get("Item_Name", "")).lower() or
                query in str(item.get("Item_ID", "")).lower() or
                query in str(item.get("Category", "")).lower() or
                query in str(item.get("Supplier_Name", "")).lower()):
                results.append(item)
        return results

    def get_low_stock_items(self) -> List[Dict]:
        """Returns items where stock <= min_level."""
        items = self.db.get_all_inventory()
        low_stock = []
        for item in items:
            try:
                stock = int(item.get("Quantity_In_Stock", 0))
                min_level = int(item.get("Min_Stock_Level", 5))
                if stock <= min_level:
                    low_stock.append(item)
            except (ValueError, TypeError):
                continue
        return low_stock

    def add_new_item(self, item_details: Dict[str, Any]) -> Dict[str, Any]:
        """Prepares and adds a new item."""
        item_id = self._generate_item_id(item_details.get("Category", "Other"))
        
        try:
            cost = float(item_details["Cost_Price"])
            sell = float(item_details["Selling_Price"])
            margin = sell - cost
        except:
            margin = 0

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
            "SKU": item_details.get("SKU", "N/A")
        }
        
        self.db.add_inventory_item(new_item)
        return new_item

    def restock_item(self, item_id: str, quantity_received: int, 
                     supplier_name: str, cost_per_unit: float) -> Optional[Dict]:
        """Restocks an item and logs the order."""
        items = self.db.get_all_inventory()
        target_item = None
        for item in items:
            if str(item.get("Item_ID")) == item_id:
                target_item = item
                break
        
        if not target_item:
            return None

        try:
            current_qty = int(target_item.get("Quantity_In_Stock", 0))
        except:
            current_qty = 0
            
        new_qty = current_qty + quantity_received
        today = datetime.now().strftime("%Y-%m-%d")

        self.db.update_inventory_stock(item_id, new_qty, today)

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
        
        return {
            "item": target_item,
            "previous_stock": current_qty,
            "new_stock": new_qty,
            "added": quantity_received,
            "last_restocked": today
        }
```

**Key Concepts**:
- **ID Generation**: Auto-increments ITM001, ITM002, etc.
- **Profit Calculation**: Selling Price - Cost Price
- **Date Handling**: Uses ISO format (YYYY-MM-DD)
- **Separation of Concerns**: Business logic separate from data access

### 5.5 Implement API Layer

Create `server.py`:

```python
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

# Initialize Manager
try:
    manager = InventoryManager()
    print("Connected to Google Sheets successfully.")
except Exception as e:
    print(f"Failed to connect to Google Sheets: {e}")
    manager = None

# --- Pydantic Models ---
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

# --- API Endpoints ---

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
    
    # Check Stock
    items = manager.get_all_items()
    target = next((i for i in items if str(i.get("Item_ID")) == sale.item_id), None)
    
    if not target:
        raise HTTPException(status_code=404, detail="Item not found")
        
    current_qty = int(target.get("Quantity_In_Stock", 0))
    if current_qty < sale.qty:
        raise HTTPException(status_code=400, 
                          detail=f"Insufficient stock. Only {current_qty} available.")
    
    # Update Inventory
    new_qty = current_qty - sale.qty
    today = datetime.now().strftime("%Y-%m-%d")
    last_restock_date = target.get("Last_Restocked", today)
    manager.db.update_inventory_stock(sale.item_id, new_qty, str(last_restock_date))
    
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
```

**Key Concepts**:
- **FastAPI**: Modern Python web framework
- **Pydantic Models**: Automatic request validation
- **CORS Middleware**: Allows frontend to call API
- **Error Handling**: HTTP status codes (404, 400, 500)
- **RESTful Design**: GET for reads, POST for writes

### 5.6 Test Backend

**Step 1**: Update Sheet ID in `data_store.py`
Replace `YOUR_SHEET_ID_HERE` with your actual Google Sheet ID

**Step 2**: Place `credentials.json` in project directory

**Step 3**: Start the server
```bash
python3 server.py
```

You should see:
```
Connected to Google Sheets successfully.
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Step 4**: Test API endpoints
Open browser and visit:
- `http://localhost:8000/inventory` - Should return empty array `[]`
- `http://localhost:8000/docs` - FastAPI auto-generated documentation

---

## 6. Frontend Implementation

### 6.1 Create index.html

Due to length constraints, I'll provide the complete HTML file structure with key sections explained.

Create `index.html` in your project directory. The file contains:

1. **HTML Structure**: Sidebar navigation + main content area
2. **CSS Styling**: Dark theme with modern aesthetics
3. **JavaScript Logic**: API calls, DOM manipulation, AI integration

**Key JavaScript Functions**:

```javascript
// State Management
let inventory = [];
const API_URL = 'http://localhost:8000';

// Fetch data from backend
async function fetchData() {
    const res = await fetch(`${API_URL}/inventory`);
    inventory = await res.json();
    // Transform to frontend format
    inventory = inventory.map(i => ({
        id: i.Item_ID,
        name: i.Item_Name,
        category: i.Category,
        qty: parseInt(i.Quantity_In_Stock),
        min: parseInt(i.Min_Stock_Level),
        cost: parseFloat(i.Cost_Price),
        price: parseFloat(i.Selling_Price),
        supplier: i.Supplier_Name
    }));
    updateDashboard();
}

// Add new item
async function submitAddItem() {
    const itemPayload = {
        category: document.getElementById('new-category').value,
        name: document.getElementById('new-name').value,
        cost: parseFloat(document.getElementById('new-cost').value),
        price: parseFloat(document.getElementById('new-price').value),
        qty: parseInt(document.getElementById('new-qty').value),
        min_stock: parseInt(document.getElementById('new-min').value),
        supplier: document.getElementById('new-supplier').value
    };

    const res = await fetch(`${API_URL}/items/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(itemPayload)
    });

    if (!res.ok) throw new Error("Failed to save");
    await fetchData();
    alert("Item Added Successfully!");
}

// Record sale
async function submitSale() {
    const res = await fetch(`${API_URL}/sales/record`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            item_id: selectedItemId,
            qty: qty,
            payment_method: paymentMethod
        })
    });

    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail);
    }

    await fetchData();
}
```

**Copy the complete `index.html` from your existing project** as it's too large to include here in full.

### 6.2 Frontend Architecture

**Component Structure**:
1. **Settings Modal**: API key configuration
2. **Sidebar Navigation**: Route switching
3. **Dashboard**: Statistics and insights
4. **Add Item Form**: New product entry
5. **Record Sale Form**: Transaction processing
6. **Check Stock Table**: Inventory viewing
7. **Reports Section**: AI-powered analytics

**State Management Pattern**:
- Global `inventory` array holds current data
- `fetchData()` syncs with backend
- Each action triggers re-fetch and UI update

---

## 7. Integration & Testing

### 7.1 End-to-End Testing

**Test 1: Add New Item**
1. Start backend: `python3 server.py`
2. Open `index.html` in browser (file:// or local server)
3. Navigate to "Add New Item"
4. Fill form:
   - Category: Bags
   - Name: Leather Tote
   - Cost: 25.00
   - Price: 49.99
   - Quantity: 10
   - Min Stock: 3
   - Supplier: ABC Supplies
5. Click "Submit"
6. Verify in Google Sheet: New row appears with ITM001

**Test 2: Record Sale**
1. Navigate to "Record Sale"
2. Search for "Leather Tote"
3. Quantity: 2
4. Payment: Cash
5. Click "Process Sale"
6. Verify in Google Sheet: Quantity changes from 10 to 8

**Test 3: Low Stock Alert**
1. Sell 6 more units (total 8 sold, 2 remaining)
2. Check Dashboard: "Low Stock Alert" shows 1
3. Navigate to "Check Stock"
4. Filter: "Low Stock Only"
5. Verify: Leather Tote appears with orange badge

### 7.2 Common Issues & Solutions

**Issue**: "Database connection unavailable"
- **Cause**: `credentials.json` not found or invalid
- **Solution**: Verify file exists and service account has Sheet access

**Issue**: "Item ID not found"
- **Cause**: Sheet ID mismatch or wrong worksheet name
- **Solution**: Check `SHEET_ID` in `data_store.py` and worksheet names

**Issue**: CORS error in browser console
- **Cause**: Frontend not allowed to call API
- **Solution**: Verify CORS middleware in `server.py`

**Issue**: "Module not found" errors
- **Cause**: Dependencies not installed
- **Solution**: Run `pip3 install -r requirements.txt`

---

## 8. Deployment

### 8.1 Local Deployment (Development)

**Current Setup**: Already configured for local use
- Backend: `http://localhost:8000`
- Frontend: Open `index.html` directly

### 8.2 Production Deployment Options

**Option 1: Cloud Hosting (Heroku/Railway)**
1. Add `Procfile`:
   ```
   web: uvicorn server:app --host 0.0.0.0 --port $PORT
   ```
2. Set environment variables for credentials
3. Deploy via Git push

**Option 2: VPS (DigitalOcean/AWS)**
1. Install Python on server
2. Use systemd to run server as service
3. Configure nginx as reverse proxy
4. Enable HTTPS with Let's Encrypt

**Security Considerations**:
- Never commit `credentials.json` to Git
- Use environment variables for sensitive data
- Implement authentication for production
- Rate limit API endpoints
- Enable HTTPS only

---

## 9. Troubleshooting

### 9.1 Backend Issues

**Problem**: Server won't start
```bash
# Check Python version
python3 --version  # Should be 3.10+

# Reinstall dependencies
pip3 install --upgrade -r requirements.txt

# Check for port conflicts
lsof -i :8000  # Kill process if needed
```

**Problem**: Google Sheets API errors
- Verify service account email is shared with Sheet
- Check API is enabled in Google Cloud Console
- Ensure `credentials.json` is valid JSON

### 9.2 Frontend Issues

**Problem**: Data not loading
- Open browser DevTools (F12)
- Check Console for errors
- Verify API URL matches backend
- Check Network tab for failed requests

**Problem**: AI features not working
- Verify Anthropic API key in Settings
- Check browser console for API errors
- Ensure API key has credits

### 9.3 Data Issues

**Problem**: Duplicate Item IDs
- Manually check Google Sheet for duplicates
- Delete duplicates keeping newest entry
- Restart backend to refresh cache

**Problem**: Stock count incorrect
- Check `INVENTORY` sheet manually
- Verify no manual edits were made
- Re-sync by restarting backend

---

## Appendix A: Complete File Listing

Your final project should contain:

```
stockminds-inventory/
├── credentials.json          # Google Service Account (DO NOT COMMIT)
├── requirements.txt          # Python dependencies
├── data_store.py            # 64 lines - Database layer
├── inventory_manager.py     # 142 lines - Business logic
├── server.py                # 129 lines - API endpoints
├── index.html               # 807 lines - Frontend
└── README.md                # Project documentation
```

## Appendix B: API Reference

### GET /inventory
Returns all inventory items
- **Response**: Array of item objects

### GET /items/low_stock
Returns items below minimum stock
- **Response**: Array of low stock items

### POST /items/add
Adds new inventory item
- **Request Body**: ItemData model
- **Response**: Created item object

### POST /sales/record
Records a sale transaction
- **Request Body**: SaleData model
- **Response**: Sale confirmation object

---

## Conclusion

You have now built a complete full-stack inventory management system with:
- Cloud-based database (Google Sheets)
- RESTful API backend (Python/FastAPI)
- Modern web interface (HTML/CSS/JS)
- AI integration (Claude API)

**Next Steps**:
1. Add sales transaction logging to SALES_LOG sheet
2. Implement user authentication
3. Add data visualization (charts/graphs)
4. Create mobile-responsive design
5. Add export functionality (PDF reports)

**Learning Resources**:
- FastAPI Documentation: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- gspread Documentation: [docs.gspread.org](https://docs.gspread.org)
- JavaScript MDN: [developer.mozilla.org](https://developer.mozilla.org)

---

*Document Version: 1.0*  
*Last Updated: January 2026*  
*Author: StockMinds Development Team*

from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import uvicorn
from inventory_manager import InventoryManager
from auth_manager import AuthManager
from datetime import datetime, timedelta
import uuid

app = FastAPI()

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Session Storage ---
# In-memory session storage: {token: {user, expires_at, failed_attempts}}
sessions = {}
failed_login_attempts = {}  # {username: {count, locked_until}}

# --- Security ---
security = HTTPBasic()
bearer_scheme = HTTPBearer(auto_error=False)
auth_manager = AuthManager()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Authenticate user against the USERS sheet using AuthManager.
    (Legacy - used for backward compatibility)
    """
    user = auth_manager.authenticate(credentials.username, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user

def get_current_user_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """
    Authenticate user using Bearer token from session storage.
    Used for the new login system.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    session = sessions.get(token)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if session is expired
    if datetime.now() > session["expires_at"]:
        # Remove expired session
        sessions.pop(token, None)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return session["user"]

# --- Dependency ---
def get_authorized_manager(user: dict = Depends(get_current_user_token)):
    """
    Creates an InventoryManager instance with the authenticated user context.
    """
    return InventoryManager(user)

# --- Frontend ---
# Get the directory where this script is located
BASE_DIR = Path(__file__).resolve().parent

@app.get("/")
async def read_index():
    """Serve the main application page. Authentication check happens in JavaScript."""
    index_path = BASE_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=500, detail=f"index.html not found at {index_path}")
    return FileResponse(index_path)

@app.get("/login.html")
async def read_login():
    """Serve the login page"""
    login_path = BASE_DIR / "login.html"
    if not login_path.exists():
        raise HTTPException(status_code=500, detail=f"login.html not found at {login_path}")
    return FileResponse(login_path)

@app.get("/session.js")
async def read_session_js():
    """Serve the session management JavaScript"""
    session_js_path = BASE_DIR / "session.js"
    if not session_js_path.exists():
        raise HTTPException(status_code=500, detail=f"session.js not found at {session_js_path}")
    return FileResponse(session_js_path, media_type="application/javascript")

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

class UserCreateData(BaseModel):
    username: str
    password: str
    role: str
    email: Optional[str] = ""

class UserUpdateData(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None

class PasswordResetData(BaseModel):
    new_password: str

class PasswordChangeData(BaseModel):
    current_password: str
    new_password: str

# Authentication Models
class LoginRequest(BaseModel):
    username: str
    password: str

class InitialSetupRequest(BaseModel):
    username: str
    email: Optional[str] = ""
    password: str





# --- Endpoints ---

# --- Authentication Endpoints ---

@app.get("/auth/check-initial-setup")
async def check_initial_setup():
    """Check if initial admin setup is needed (no users exist)"""
    try:
        users = auth_manager.db.get_all_users()
        return {"needs_setup": len(users) == 0}
    except Exception as e:
        return {"needs_setup": False, "error": str(e)}

@app.post("/auth/initial-setup")
async def initial_setup(setup_data: InitialSetupRequest):
    """Create the first admin account"""
    try:
        # Check if users already exist
        users = auth_manager.db.get_all_users()
        if users:
            raise HTTPException(status_code=400, detail="Setup already completed. Users exist.")
        
        # Create admin user
        new_user = auth_manager.create_user(
            creator_admin=None,  # No admin exists yet
            username=setup_data.username,
            password=setup_data.password,
            role="Admin",
            email=setup_data.email
        )
        
        return {
            "status": "success",
            "message": "Admin account created successfully",
            "user": {
                "user_id": new_user.get("User_ID"),
                "username": new_user.get("Username"),
                "role": new_user.get("Role")
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Setup failed: {str(e)}")

@app.post("/auth/login")
async def login(login_data: LoginRequest):
    """Authenticate user and create session"""
    username = login_data.username.lower()
    
    # Check if account is locked
    if username in failed_login_attempts:
        attempt_data = failed_login_attempts[username]
        if attempt_data.get("locked_until") and datetime.now() < attempt_data["locked_until"]:
            remaining = (attempt_data["locked_until"] - datetime.now()).seconds // 60
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account locked due to too many failed attempts. Try again in {remaining} minutes."
            )
        elif attempt_data.get("locked_until") and datetime.now() >= attempt_data["locked_until"]:
            # Unlock account
            failed_login_attempts.pop(username, None)
    
    # Authenticate user
    try:
        user = auth_manager.authenticate(login_data.username, login_data.password)
        
        if not user:
            # Track failed attempt
            if username not in failed_login_attempts:
                failed_login_attempts[username] = {"count": 0, "locked_until": None}
            
            failed_login_attempts[username]["count"] += 1
            
            # Lock account after 5 failed attempts
            if failed_login_attempts[username]["count"] >= 5:
                failed_login_attempts[username]["locked_until"] = datetime.now() + timedelta(minutes=10)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Too many failed login attempts. Account locked for 10 minutes."
                )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Clear failed attempts on successful login
        failed_login_attempts.pop(username, None)
        
        # Check account status
        if user.get("Account_Status") != "Active":
            status_msg = user.get("Account_Status", "inactive")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {status_msg.lower()}. Please contact administrator."
            )
        
        # Generate session token
        session_token = str(uuid.uuid4())
        
        # Store session (expires in 8 hours)
        sessions[session_token] = {
            "user": user,
            "expires_at": datetime.now() + timedelta(hours=8),
            "created_at": datetime.now()
        }
        
        # Return user info and token
        return {
            "status": "success",
            "user": {
                "user_id": user.get("User_ID"),
                "username": user.get("Username"),
                "role": user.get("Role"),
                "email": user.get("Email", "")
            },
            "session_token": session_token,
            "expires_at": (datetime.now() + timedelta(hours=8)).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.post("/auth/logout")
async def logout(user: dict = Depends(get_current_user_token)):
    """Logout user and invalidate session"""
    # Find and remove the session token
    token_to_remove = None
    for token, session in sessions.items():
        if session["user"].get("User_ID") == user.get("User_ID"):
            token_to_remove = token
            break
    
    if token_to_remove:
        sessions.pop(token_to_remove, None)
    
    return {"status": "success", "message": "Logged out successfully"}

@app.get("/auth/validate")
async def validate_session(user: dict = Depends(get_current_user_token)):
    """Validate if current session is still valid"""
    return {
        "valid": True,
        "user": {
            "user_id": user.get("User_ID"),
            "username": user.get("Username"),
            "role": user.get("Role"),
            "email": user.get("Email", "")
        }
    }

@app.post("/auth/unlock-account")
async def unlock_account(username: str, admin_user: dict = Depends(get_current_user_token)):
    """Admin unlocks a user account that was locked due to failed login attempts"""
    if admin_user.get("Role") != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Clear failed login attempts for this user
    username_lower = username.lower()
    if username_lower in failed_login_attempts:
        failed_login_attempts.pop(username_lower)
        return {"status": "success", "message": f"Account {username} unlocked successfully"}
    else:
        return {"status": "success", "message": f"Account {username} was not locked"}

# --- Inventory Endpoints ---


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

# --- User Management Endpoints ---

@app.get("/users")
def get_all_users(user: dict = Depends(get_current_user_token)):
    """Get all users (Admin only)"""
    if user.get("Role") != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = auth_manager.db.get_all_users()
    # Remove password hashes from response
    for u in users:
        u.pop("Password_Hash", None)
    return users

@app.get("/users/current")
def get_current_user_info(user: dict = Depends(get_current_user_token)):
    """Get current authenticated user's information"""
    user_copy = user.copy()
    user_copy.pop("Password_Hash", None)
    return user_copy

@app.post("/users/create")
def create_user(user_data: UserCreateData, admin_user: dict = Depends(get_current_user_token)):
    """Create a new user (Admin only)"""
    try:
        new_user = auth_manager.create_user(
            admin_user,
            user_data.username,
            user_data.password,
            user_data.role,
            user_data.email
        )
        new_user.pop("Password_Hash", None)
        return new_user
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/users/{user_id}")
def update_user(user_id: str, user_data: UserUpdateData, admin_user: dict = Depends(get_current_user_token)):
    """Update user details (Admin only)"""
    try:
        updated_user = auth_manager.update_user(
            admin_user,
            user_id,
            username=user_data.username,
            email=user_data.email,
            role=user_data.role,
            status=user_data.status
        )
        updated_user.pop("Password_Hash", None)
        return updated_user
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/users/{user_id}")
def delete_user(user_id: str, admin_user: dict = Depends(get_current_user_token)):
    """Delete a user (Admin only)"""
    try:
        result = auth_manager.delete_user(admin_user, user_id)
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/users/{user_id}/reset-password")
def reset_user_password(user_id: str, password_data: PasswordResetData, admin_user: dict = Depends(get_current_user_token)):
    """Admin resets a user's password"""
    try:
        result = auth_manager.reset_user_password(admin_user, user_id, password_data.new_password)
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/users/change-password")
def change_password(password_data: PasswordChangeData, user: dict = Depends(get_current_user_token)):
    """User changes their own password"""
    try:
        result = auth_manager.change_password(user, password_data.current_password, password_data.new_password)
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


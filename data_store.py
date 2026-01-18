import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Dict, Optional, Any
from datetime import datetime
import os
import json

class DataStore:
    SCOPE = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    SHEET_ID = "158NqkQ0k_K-eCFPbecbHhT8j0BlpvrXfBJN8EGNljVQ"
    CREDENTIALS_FILE = "credentials.json"

    def __init__(self):
        json_creds = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if json_creds:
            creds_dict = json.loads(json_creds)
            self.creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, self.SCOPE)
        else:
            self.creds = ServiceAccountCredentials.from_json_keyfile_name(self.CREDENTIALS_FILE, self.SCOPE)
        self.client = gspread.authorize(self.creds)
        self.sheet = self.client.open_by_key(self.SHEET_ID)
        
        # Open worksheets
        self.inventory_ws = self.sheet.worksheet("INVENTORY")
        self.suppliers_ws = self.sheet.worksheet("SUPPLIERS")
        self.restock_orders_ws = self.sheet.worksheet("RESTOCK_ORDERS")
        
        # Initialize or Load USERS sheet
        try:
            self.users_ws = self.sheet.worksheet("USERS")
        except gspread.WorksheetNotFound:
            self.users_ws = self.sheet.add_worksheet(title="USERS", rows=100, cols=10)
            self.users_ws.append_row([
                "User_ID", "Username", "Email", "Password_Hash", "Role", 
                "Created_Date", "Last_Login", "Account_Status", "Created_By", "Notes"
            ])

        # Initialize or Load ACTIVITY_LOG sheet
        try:
            self.logs_ws = self.sheet.worksheet("ACTIVITY_LOG")
        except gspread.WorksheetNotFound:
            self.logs_ws = self.sheet.add_worksheet(title="ACTIVITY_LOG", rows=1000, cols=5)
            self.logs_ws.append_row(["Log_ID", "User_ID", "Action", "Timestamp", "Details"])

        # Cache headers to ensure we write to correct columns
        self.inventory_headers = self.inventory_ws.row_values(1)
        self.restock_headers = self.restock_orders_ws.row_values(1)
        self.users_headers = self.users_ws.row_values(1)

    def get_all_inventory(self) -> List[Dict[str, Any]]:
        """Returns all records from INVENTORY sheet."""
        return self.inventory_ws.get_all_records()

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Returns all records from USERS sheet."""
        return self.users_ws.get_all_records()

    def add_user(self, user_data: Dict[str, Any]):
        """Adds a new user to USERS sheet."""
        row = []
        for header in self.users_headers:
            row.append(user_data.get(header, ""))
        self.users_ws.append_row(row)

    def update_user_status(self, user_id: str, new_status: str):
        cell = self.users_ws.find(user_id)
        if cell:
            col = self.users_headers.index("Account_Status") + 1
            self.users_ws.update_cell(cell.row, col, new_status)

    def update_last_login(self, user_id: str):
        cell = self.users_ws.find(user_id)
        if cell:
            col = self.users_headers.index("Last_Login") + 1
            self.users_ws.update_cell(cell.row, col, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def log_activity(self, user_id: str, action: str, details: str):
        """Logs an action to ACTIVITY_LOG."""
        log_id = f"LOG{int(datetime.now().timestamp())}"
        self.logs_ws.append_row([
            log_id, user_id, action, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), details
        ])


    def add_inventory_item(self, item_data: Dict[str, Any]):
        """Adds a new row to the INVENTORY sheet."""
        # Map dictionary to row list based on headers
        row = []
        for header in self.inventory_headers:
            row.append(item_data.get(header, ""))
        self.inventory_ws.append_row(row)

    def update_inventory_stock(self, item_id: str, new_quantity: int, last_restocked: str):
        """Updates Quantity_In_Stock and Last_Restocked for a given Item_ID."""
        # Find the cell with the Item_ID
        # Note: This is efficient for small sheets, but find() can be slow on very large ones.
        cell = self.inventory_ws.find(item_id)
        if cell:
            # Update Quantity (Column index for Quantity_In_Stock)
            # We need to find the column index dynamically
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

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Returns a single user by User_ID."""
        users = self.get_all_users()
        for user in users:
            if user.get("User_ID") == user_id:
                return user
        return None

    def update_user(self, user_id: str, updates: Dict[str, Any]):
        """Updates user fields in USERS sheet."""
        cell = self.users_ws.find(user_id)
        if not cell:
            raise ValueError(f"User ID {user_id} not found.")
        
        # Update each field that's provided
        for field, value in updates.items():
            if field in self.users_headers:
                col = self.users_headers.index(field) + 1
                self.users_ws.update_cell(cell.row, col, value)

    def delete_user(self, user_id: str):
        """Deletes a user from USERS sheet."""
        cell = self.users_ws.find(user_id)
        if not cell:
            raise ValueError(f"User ID {user_id} not found.")
        self.users_ws.delete_rows(cell.row)

    def update_user_password(self, user_id: str, new_password_hash: str):
        """Updates a user's password hash."""
        cell = self.users_ws.find(user_id)
        if not cell:
            raise ValueError(f"User ID {user_id} not found.")
        
        col = self.users_headers.index("Password_Hash") + 1
        self.users_ws.update_cell(cell.row, col, new_password_hash)

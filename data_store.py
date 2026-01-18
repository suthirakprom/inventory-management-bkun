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
    SHEET_ID = "158NqkQ0k_K-eCFPbecbHhT8j0BlpvrXfBJN8EGNljVQ"
    CREDENTIALS_FILE = "credentials.json"

    def __init__(self):
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(self.CREDENTIALS_FILE, self.SCOPE)
        self.client = gspread.authorize(self.creds)
        self.sheet = self.client.open_by_key(self.SHEET_ID)
        
        # Open worksheets
        self.inventory_ws = self.sheet.worksheet("INVENTORY")
        self.suppliers_ws = self.sheet.worksheet("SUPPLIERS")
        self.restock_orders_ws = self.sheet.worksheet("RESTOCK_ORDERS")

        # Cache headers to ensure we write to correct columns
        self.inventory_headers = self.inventory_ws.row_values(1)
        self.restock_headers = self.restock_orders_ws.row_values(1)

    def get_all_inventory(self) -> List[Dict[str, Any]]:
        """Returns all records from INVENTORY sheet."""
        return self.inventory_ws.get_all_records()

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

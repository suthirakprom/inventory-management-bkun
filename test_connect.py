from data_store import DataStore
import gspread

def verify():
    print("Attempting to connect...")
    try:
        ds = DataStore()
        print("Successfully connected to Sheet.")
        
        # Check INVENTORY headers
        headers = ds.inventory_ws.row_values(1)
        expected_inv = ["Category", "Item_Name", "Description", "Quantity_In_Stock", 
                        "Cost_Price", "Selling_Price", "Supplier_Name", "Date_Added", 
                        "Last_Restocked", "Min_Stock_Level", "SKU", "Item_ID", "Profit_Margin"]
        
        if not headers:
            print("INVENTORY sheet is empty. Adding headers...")
            ds.inventory_ws.append_row(expected_inv)
        else:
            print(f"INVENTORY Headers found: {headers}")
            # simple check
            if "Item_Name" not in headers:
                print("WARNING: 'Item_Name' header missing in INVENTORY")

        # Check RESTOCK_ORDERS headers
        r_headers = ds.restock_orders_ws.row_values(1)
        expected_restock = ["Date_Ordered", "Supplier_Name", "Item_ID", "Item_Name", 
                            "Quantity_Ordered", "Cost_Per_Unit", "Expected_Delivery", 
                            "Status", "Date_Received"]
        
        if not r_headers:
            print("RESTOCK_ORDERS sheet is empty. Adding headers...")
            ds.restock_orders_ws.append_row(expected_restock)
        else:
            print(f"RESTOCK Headers found: {r_headers}")

        print("\nVerification Complete. System is ready.")
        
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    verify()

import inventory_manager
import os
import csv

def reset_database():
    print("Resetting database...")
    with open('INVENTORY.csv', 'w') as f:
        f.write("Item_ID,Item_Name,Quantity_In_Stock,Selling_Price,Min_Stock_Level\n")
        f.write("ITM001,Brown Leather Handbag,20,35.00,5\n")
        f.write("ITM005,Black Leather Wallet,3,25.00,5\n")
        f.write("ITM009,Running Shoes,2,120.00,10\n")
    
    with open('SALES_LOG.csv', 'w') as f:
        f.write("Date,Time,Item_ID,Item_Name,Quantity_Sold,Unit_Price,Total_Amount,Payment_Method,Sold_By\n")

def test_sales():
    reset_database()
    
    print("\nTest 1: Sell 2 Brown Leather Handbags")
    item = inventory_manager.find_item(inventory_manager.load_inventory(), "Brown Leather Handbag")
    assert item is not None
    success, stock, min_stock = inventory_manager.update_stock(item['Item_ID'], 2)
    assert success is True
    assert stock == 18
    print("PASS: Stock reduced to 18")
    
    # Verify Log
    with open('SALES_LOG.csv', 'r') as f:
        lines = f.readlines()
        # Header + 1 log (we need to log it manually in main, but here we test inventory_manager logic basically)
        # Ah, log_sale is called in main.py. I should call it here to verify it works too.
        inventory_manager.log_sale({
            'Date': '2026-01-17', 'Time': '12:00', 'Item_ID': item['Item_ID'],
            'Item_Name': item['Item_Name'], 'Quantity_Sold': 2, 'Unit_Price': 35.00,
            'Total_Amount': 70.00, 'Payment_Method': 'Cash', 'Sold_By': 'Test'
        })
    
    with open('SALES_LOG.csv', 'r') as f:
        lines = f.readlines()
        assert len(lines) == 2
    print("PASS: Sale logged")

    print("\nTest 2: Sell 1 Black Wallet (Low Stock Warning check)")
    item = inventory_manager.find_item(inventory_manager.load_inventory(), "Black Leather Wallet") # Stock 3
    success, stock, min_stock = inventory_manager.update_stock(item['Item_ID'], 1)
    assert success is True
    assert stock == 2
    assert stock <= min_stock # 2 <= 5
    print("PASS: Stock reduced to 2 (Low Stock trigger correct)")

    print("\nTest 3: Sell 10 Running Shoes (Insufficient Stock)")
    item = inventory_manager.find_item(inventory_manager.load_inventory(), "Running Shoes") # Stock 2
    success, stock, min_stock = inventory_manager.update_stock(item['Item_ID'], 10)
    assert success is False
    assert stock == 2 # Unchanged
    print("PASS: Insufficient stock rejected")

    print("\nAll tests passed!")

if __name__ == "__main__":
    test_sales()

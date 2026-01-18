from inventory_manager import InventoryManager
from rich.console import Console

console = Console()

def seed():
    manager = InventoryManager()
    
    items = [
        {
            "Category": "Bags",
            "Item_Name": "Brown Leather Handbag",
            "Description": "Premium leather handbag with gold finish",
            "Quantity": 20,
            "Cost_Price": 15.00,
            "Selling_Price": 35.00,
            "Supplier_Name": "ABC Suppliers",
            "SKU": "BAG-001",
            "Min_Stock_Level": 5
        },
        {
            "Category": "Shoes",
            "Item_Name": "Running Shoes Size 8",
            "Description": "Lightweight breathable running shoes",
            "Quantity": 2, # Low stock demo
            "Cost_Price": 25.00,
            "Selling_Price": 59.99,
            "Supplier_Name": "Sports Inc",
            "SKU": "SHOE-RUN-08",
            "Min_Stock_Level": 5
        },
        {
            "Category": "Wallets",
            "Item_Name": "Black Leather Wallet",
            "Description": "Minimalist bi-fold wallet",
            "Quantity": 3, # Low stock demo
            "Cost_Price": 8.00,
            "Selling_Price": 24.99,
            "Supplier_Name": "LeatherCo",
            "SKU": "WAL-BLK",
            "Min_Stock_Level": 5
        },
        {
            "Category": "Belts",
            "Item_Name": "Classic Leather Belt",
            "Description": "Durable genuine leather belt",
            "Quantity": 15,
            "Cost_Price": 5.00,
            "Selling_Price": 19.99,
            "Supplier_Name": "LeatherCo",
            "SKU": "BLT-TAN",
            "Min_Stock_Level": 10
        },
        {
            "Category": "Accessories",
            "Item_Name": "Silk Scarf",
            "Description": "100% Silk floral pattern scarf",
            "Quantity": 8,
            "Cost_Price": 12.00,
            "Selling_Price": 29.99,
            "Supplier_Name": "FashionWholesale",
            "SKU": "ACC-SCRF",
            "Min_Stock_Level": 5
        }
    ]

    console.print("[bold blue]Starting Demo Seed...[/bold blue]")
    
    for item in items:
        try:
            res = manager.add_new_item(item)
            console.print(f"[green]✓ Added:[/green] {res['Item_Name']} ({res['Item_ID']})")
        except Exception as e:
            console.print(f"[red]Failed to add {item['Item_Name']}: {e}[/red]")

    console.print("\n[bold green]✓ Demo Data Added Successfully![/bold green]")

if __name__ == "__main__":
    seed()

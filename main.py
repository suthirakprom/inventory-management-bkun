import sys
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, FloatPrompt, IntPrompt, Confirm
from rich.panel import Panel
from inventory_manager import InventoryManager

console = Console()
manager = None

def print_header():
    console.print(Panel.fit("[bold magenta]Shop Inventory Database Manager[/bold magenta]", border_style="cyan"))

def format_currency(val):
    try:
        return f"${float(val):.2f}"
    except:
        return str(val)

def show_add_item_flow():
    console.print("\n[bold green]Add New Item[/bold green]")
    
    category = Prompt.ask("Category", choices=["Bags", "Shoes", "Wallets", "Belts", "Accessories", "Other"])
    name = Prompt.ask("Item Name")
    desc = Prompt.ask("Description (optional)", default="")
    qty = IntPrompt.ask("Quantity In Stock")
    cost = FloatPrompt.ask("Cost Price ($)")
    sell = FloatPrompt.ask("Selling Price ($)")
    supplier = Prompt.ask("Supplier Name")
    sku = Prompt.ask("SKU (optional)", default="")
    min_stock = IntPrompt.ask("Min Stock Level", default=5)

    console.print("\n[yellow]Review Details:[/yellow]")
    console.print(f"Name: {name}")
    console.print(f"Category: {category}")
    console.print(f"Qty: {qty}")
    console.print(f"Cost: {format_currency(cost)} | Sell: {format_currency(sell)}")
    
    if Confirm.ask("Proceed with adding this item?"):
        with console.status("[bold green]Adding to database..."):
            new_item = manager.add_new_item({
                "Category": category,
                "Item_Name": name,
                "Description": desc,
                "Quantity": qty,
                "Cost_Price": cost,
                "Selling_Price": sell,
                "Supplier_Name": supplier,
                "SKU": sku,
                "Min_Stock_Level": min_stock
            })
        
        console.print(f"\n[bold green]✓ Added: {new_item['Item_Name']} ({new_item['Item_ID']})[/bold green]")
        console.print(f"Stock: {new_item['Quantity_In_Stock']} units")
        console.print(f"Cost: {format_currency(new_item['Cost_Price'])} | Sell: {format_currency(new_item['Selling_Price'])}")
    else:
        console.print("[red]Cancelled.[/red]")

def show_restock_flow():
    console.print("\n[bold blue]Restock Item[/bold blue]")
    query = Prompt.ask("Search Item (Name or ID)")
    
    with console.status("Searching..."):
        results = manager.search_items(query)
    
    if not results:
        if Confirm.ask("[yellow]Item not found. Do you want to add it as a new item?[/yellow]"):
            show_add_item_flow()
        return

    # Select Item
    selected_item = results[0]
    if len(results) > 1:
        console.print(f"[yellow]Found {len(results)} items. Using the first one:[/yellow]")
        # In a real app we'd let them choose, keeping it simple for now
    
    console.print(f"[bold]{selected_item['Item_Name']} ({selected_item['Item_ID']})[/bold]")
    console.print(f"Current Stock: {selected_item['Quantity_In_Stock']}")

    added_qty = IntPrompt.ask("Units Received")
    # Try to grab last supplier/cost as default
    default_cost = float(selected_item.get('Cost_Price', 0))
    cost = FloatPrompt.ask("Cost Per Unit ($)", default=default_cost)
    default_supplier = selected_item.get('Supplier_Name', "")
    supplier = Prompt.ask("Supplier", default=default_supplier)

    if Confirm.ask(f"Confirm adding {added_qty} units?"):
        with console.status("[bold blue]Updating Stock..."):
            res = manager.restock_item(str(selected_item['Item_ID']), added_qty, supplier, cost)
            
        if res:
            console.print(f"\n[bold green]✓ Restocked: {res['item']['Item_Name']} ({res['item']['Item_ID']})[/bold green]")
            console.print(f"Previous stock: {res['previous_stock']} units")
            console.print(f"Added: {res['added']} units")
            console.print(f"[bold]New stock: {res['new_stock']} units[/bold]")
            console.print(f"Last restocked: {res['last_restocked']}")

def show_check_stock():
    query = Prompt.ask("Enter Item Name, ID, or Category")
    with console.status("Checking..."):
        results = manager.search_items(query)
    
    if not results:
        console.print("[red]No items found.[/red]")
        return

    table = Table(title=f"Search Results: '{query}'")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Qty", justify="right")
    table.add_column("Status")

    for item in results:
        stock = int(item.get('Quantity_In_Stock', 0))
        min_lvl = int(item.get('Min_Stock_Level', 5))
        status = "[green]OK[/green]"
        if stock <= min_lvl:
            status = "[bold red]⚠️ LOW STOCK[/bold red]"
        
        table.add_row(str(item['Item_ID']), item['Item_Name'], str(stock), status)
    
    console.print(table)

def show_low_stock():
    with console.status("Scanning inventory..."):
        low_items = manager.get_low_stock_items()
    
    if not low_items:
        console.print("[green]All stock levels are healthy![/green]")
        return

    console.print(f"\n[bold red]Low Stock Items (at or below minimum):[/bold red]")
    for item in low_items:
        console.print(f"• {item['Item_Name']} ({item['Item_ID']}): [bold red]{item['Quantity_In_Stock']} units[/bold red] (min: {item['Min_Stock_Level']})")
    
    console.print(f"\n[bold]{len(low_items)} items need restocking[/bold]")

def run():
    global manager
    print_header()
    
    try:
        # Check credentials logic indirectly by initializing manager
        with console.status("Connecting to Google Sheets..."):
            manager = InventoryManager()
        console.print("[green]✓ Connected to Database[/green]\n")
    except Exception as e:
        console.print(f"[bold red]Error connecting to Google Sheets:[/bold red] {e}")
        console.print("[yellow]Please check credentials.json and internet connection.[/yellow]")
        return

    while True:
        choice = Prompt.ask(
            "\n[bold]What operation would you like to perform?[/bold]",
            choices=["Add Item", "Restock", "Check Stock", "Low Stock", "Search", "Exit"],
            default="Check Stock"
        )

        if choice == "Add Item":
            show_add_item_flow()
        elif choice == "Restock":
            show_restock_flow()
        elif choice == "Check Stock":
            show_check_stock()
        elif choice == "Low Stock":
            show_low_stock()
        elif choice == "Search":
            show_check_stock() # Re-use search flow
        elif choice == "Exit":
            console.print("Goodbye!")
            break

if __name__ == "__main__":
    run()

import sys
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, FloatPrompt, IntPrompt, Confirm
from rich.panel import Panel
from inventory_manager import InventoryManager
from auth_manager import AuthManager
from data_store import DataStore # Need to check if users exist directly sometimes

console = Console()
manager = None
auth_manager = None
current_user = None

def print_header(text="Shop Inventory Database Manager"):
    console.print(Panel.fit(f"[bold magenta]{text}[/bold magenta]", border_style="cyan"))

def format_currency(val):
    try:
        return f"${float(val):.2f}"
    except:
        return str(val)

# --- WORKFLOWS ---

def show_add_item_flow():
    console.print("\n[bold green]Add New Item[/bold green]")
    try:
        # Permission check happens in manager, but good to fail fast or show UI
        if not auth_manager.check_permission(current_user, AuthManager.PERM_ADD_ITEM):
            console.print("[red]Access Denied: Staff cannot create new items (Configured Rule).[/red]")
            return
            
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
            
    except PermissionError as e:
        console.print(f"[bold red]{e}[/bold red]")

def show_restock_flow():
    console.print("\n[bold blue]Restock Item[/bold blue]")
    query = Prompt.ask("Search Item (Name or ID)")
    
    with console.status("Searching..."):
        results = manager.search_items(query)
    
    if not results:
        # Only Admin or authorized staff can add new
        if Confirm.ask("[yellow]Item not found. Do you want to add it as a new item?[/yellow]"):
             show_add_item_flow()
        return

    # Select Item
    selected_item = results[0]
    if len(results) > 1:
        console.print(f"[yellow]Found {len(results)} items. Using the first one:[/yellow]")
    
    console.print(f"[bold]{selected_item['Item_Name']} ({selected_item['Item_ID']})[/bold]")
    console.print(f"Current Stock: {selected_item['Quantity_In_Stock']}")

    added_qty = IntPrompt.ask("Units Received")
    default_cost = float(selected_item.get('Cost_Price', 0))
    cost = FloatPrompt.ask("Cost Per Unit ($)", default=default_cost)
    default_supplier = selected_item.get('Supplier_Name', "")
    supplier = Prompt.ask("Supplier", default=default_supplier)

    if Confirm.ask(f"Confirm adding {added_qty} units?"):
        try:
            with console.status("[bold blue]Updating Stock..."):
                res = manager.restock_item(str(selected_item['Item_ID']), added_qty, supplier, cost)
                
            if res:
                console.print(f"\n[bold green]✓ Restocked: {res['item']['Item_Name']} ({res['item']['Item_ID']})[/bold green]")
                console.print(f"Previous stock: {res['previous_stock']} units")
                console.print(f"Added: {res['added']} units")
                console.print(f"[bold]New stock: {res['new_stock']} units[/bold]")
                console.print(f"Last restocked: {res['last_restocked']}")
        except PermissionError as e:
            console.print(f"[bold red]{e}[/bold red]")

def show_check_stock_search():
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

# --- USER MANAGEMENT (ADMIN ONLY) ---
def show_user_management():
    if not auth_manager.check_permission(current_user, AuthManager.PERM_MANAGE_USERS):
        console.print("[bold red]ACCESS DENIED: Admin only.[/bold red]")
        return

    while True:
        console.print("\n[bold cyan]User Management[/bold cyan]")
        choice = Prompt.ask(
            "Select Action",
            choices=["List Users", "Create User", "Back"],
            default="List Users"
        )
        
        if choice == "Back":
            break
            
        elif choice == "List Users":
            users = manager.db.get_all_users()
            table = Table(title="System Users")
            table.add_column("User ID", style="cyan")
            table.add_column("Username", style="bold")
            table.add_column("Role", style="magenta")
            table.add_column("Status")
            table.add_column("Last Login")
            
            for u in users:
                table.add_row(u["User_ID"], u["Username"], u["Role"], u["Account_Status"], u["Last_Login"])
            console.print(table)
            
        elif choice == "Create User":
            console.print("Create New User")
            u_name = Prompt.ask("Username")
            u_pass = Prompt.ask("Password", password=True)
            u_role = Prompt.ask("Role", choices=["Admin", "Staff"], default="Staff")
            u_email = Prompt.ask("Email (optional)", default="")
            
            try:
                auth_manager.create_user(current_user, u_name, u_pass, u_role, u_email)
                console.print(f"[bold green]✓ User {u_name} created successfully![/bold green]")
            except Exception as e:
                console.print(f"[red]Error creating user: {e}[/red]")

# --- SETUP & LOGIN ---

def first_time_setup():
    console.clear()
    print_header("INITIAL SETUP")
    console.print("[yellow]No users found in database.[/yellow]")
    console.print("Please create the [bold]System Administrator[/bold] account.\n")
    
    username = Prompt.ask("Admin Username", default="admin")
    password = Prompt.ask("Admin Password", password=True)
    confirm = Prompt.ask("Confirm Password", password=True)
    
    if password != confirm:
        console.print("[bold red]Passwords do not match. Restarting setup...[/bold red]")
        return first_time_setup()
        
    try:
        with console.status("Creating Admin Account..."):
            auth_manager.create_user(None, username, password, "Admin")
        console.print("\n[bold green]✓ Setup Complete! Access granted.[/bold green]")
        return True
    except Exception as e:
        console.print(f"[bold red]Setup Failed: {e}[/bold red]")
        sys.exit(1)

def login_screen():
    print_header("LOGIN")
    attempts = 0
    while attempts < 3:
        username = Prompt.ask("Username")
        password = Prompt.ask("Password", password=True)
        
        with console.status("Authenticating..."):
            user = auth_manager.authenticate(username, password)
            
        if user:
            console.print(f"[green]Welcome back, {user['Username']}![/green]")
            return user
        else:
            console.print("[red]Invalid username or password.[/red]")
            attempts += 1
            
    console.print("[bold red]Too many failed attempts. Exiting.[/bold red]")
    sys.exit(1)

def run():
    global manager, auth_manager, current_user
    console.clear()
    
    try:
        # Initialize Managers
        with console.status("Connecting to Database..."):
            auth_manager = AuthManager()
            # Check if USERS is empty to trigger setup
            users = auth_manager.db.get_all_users()
            
        if not users:
            first_time_setup()
        
        # Login Loop
        current_user = login_screen()
        
        # Initialize Inventory Manager with authenticated user
        manager = InventoryManager(current_user)
        
        # Main Menu Loop
        while True:
            console.print(f"\n[dim]Logged in as: {current_user['Username']} ({current_user['Role']})[/dim]")
            
            # Dynamic Menu Options based on Role
            options = ["Check Stock / Search", "Restock Item", "Add New Item", "Low Stock Report"]
            
            if current_user["Role"] == "Admin":
                options.append("Manage Users")
                
            options.append("Logout")
            options.append("Exit")
            
            choice = Prompt.ask(
                "\n[bold]Select Operation[/bold]",
                choices=options,
                default="Check Stock / Search"
            )

            if choice == "Add New Item":
                show_add_item_flow()
            elif choice == "Restock Item":
                show_restock_flow()
            elif choice == "Check Stock / Search":
                show_check_stock_search()
            elif choice == "Low Stock Report":
                show_low_stock()
            elif choice == "Manage Users":
                show_user_management()
            elif choice == "Logout":
                console.print("[yellow]Logging out...[/yellow]")
                current_user = login_screen()
                manager.set_user(current_user) # Update manager permission context
            elif choice == "Exit":
                console.print("Goodbye!")
                break
                
    except KeyboardInterrupt:
        console.print("\n[red]Exiting...[/red]")
    except Exception as e:
        console.print(f"[bold red]Critical Error: {e}[/bold red]")
        # import traceback
        # traceback.print_exc()

if __name__ == "__main__":
    run()

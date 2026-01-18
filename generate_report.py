import csv
import argparse
from datetime import datetime
from typing import List, Dict, Any
from collections import Counter

class ReportGenerator:
    def __init__(self, inventory_file='INVENTORY.csv', sales_file='SALES_LOG.csv'):
        self.inventory_file = inventory_file
        self.sales_file = sales_file
        self.inventory = []
        self.sales = []
        self.load_data()

    def load_data(self):
        """Loads data from CSV files."""
        # Load Inventory
        try:
            with open(self.inventory_file, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.inventory = list(reader)
        except FileNotFoundError:
            print(f"Error: {self.inventory_file} not found.")

        # Load Sales Log
        try:
            with open(self.sales_file, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.sales = list(reader)
        except FileNotFoundError:
            print(f"Error: {self.sales_file} not found.")

    def format_currency(self, amount: float) -> str:
        return f"${amount:,.2f}"

    def get_daily_sales(self, date_str: str = None) -> str:
        """Generates Daily Sales Summary."""
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Filter sales for the date
        daily_sales = [s for s in self.sales if s.get('Date') == date_str]
        
        total_revenue = sum(float(s['Total_Amount']) for s in daily_sales if s.get('Total_Amount'))
        transactions = len(daily_sales)
        items_sold = sum(int(s['Quantity_Sold']) for s in daily_sales if s.get('Quantity_Sold'))
        
        # Payment Methods
        payment_methods = Counter(s['Payment_Method'] for s in daily_sales if s.get('Payment_Method'))
        
        # Best Seller Today
        if daily_sales:
            item_sales = Counter()
            item_revenue = Counter()
            for s in daily_sales:
                name = s.get('Item_Name')
                qty = int(s.get('Quantity_Sold', 0))
                rev = float(s.get('Total_Amount', 0))
                item_sales[name] += qty
                item_revenue[name] += rev
            
            best_seller_name, best_seller_qty = item_sales.most_common(1)[0]
            best_seller_rev = item_revenue[best_seller_name]
            best_seller_info = f"{best_seller_name} ({best_seller_qty} sold, {self.format_currency(best_seller_rev)})"
        else:
            best_seller_info = "N/A"

        report = [
            f"📊 DAILY SALES SUMMARY - {date_str}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"💰 Total Revenue: {self.format_currency(total_revenue)}",
            f"📝 Transactions: {transactions}",
            f"📦 Items Sold: {items_sold}",
            f"🏆 Best Seller: {best_seller_info}",
            "💳 Payment Methods:"
        ]
        
        if payment_methods:
            for method, count in payment_methods.items():
                # Calculate amount per method if needed, simplistic for now
                total_method = sum(float(s['Total_Amount']) for s in daily_sales if s.get('Payment_Method') == method)
                report.append(f"   • {method}: {count} transactions ({self.format_currency(total_method)})")
        else:
            report.append("   • No transactions recorded.")

        return "\n".join(report)

    def get_low_stock_alert(self) -> str:
        """Generates Low Stock Alert."""
        low_stock_items = []
        for item in self.inventory:
            try:
                qty = int(item.get('Quantity_In_Stock', 0))
                min_level = int(item.get('Min_Stock_Level', 5))
                if qty <= min_level:
                    low_stock_items.append((item, qty, min_level))
            except ValueError:
                continue
        
        # Sort by lowest stock first
        low_stock_items.sort(key=lambda x: x[1])

        report = [
            "⚠️ LOW STOCK ALERT",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]

        if not low_stock_items:
            report.append("✅ All stock levels are healthy.")
        else:
            for item, qty, min_l in low_stock_items:
                marker = "🔴" if qty <= 2 else "🟡"
                report.append(f"   • {item.get('Item_Name')} - {qty} units (min: {min_l}) {marker}")
        
        return "\n".join(report)

    def get_inventory_value(self) -> str:
        """Generates Inventory Value Report."""
        total_items = 0
        potential_revenue = 0.0
        # Cost is missing in CSV, checking if it exists, else 0
        total_cost = 0.0
        
        for item in self.inventory:
            try:
                qty = int(item.get('Quantity_In_Stock', 0))
                price = float(item.get('Selling_Price', 0))
                cost = float(item.get('Cost_Price', 0)) # Likely 0 if missing
                
                total_items += qty
                potential_revenue += qty * price
                total_cost += qty * cost
            except ValueError:
                continue
        
        unique_items = len(self.inventory)
        potential_profit = potential_revenue - total_cost

        report = [
            "💎 INVENTORY VALUE REPORT",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "📦 Stock Overview:",
            f"   • Total Items: {total_items} units",
            f"   • Unique Products: {unique_items} items",
            "",
            "💵 Financial Value:",
            f"   • Potential Revenue: {self.format_currency(potential_revenue)}"
        ]
        
        if total_cost > 0:
             report.append(f"   • Total Cost: {self.format_currency(total_cost)}")
             report.append(f"   • Potential Profit: {self.format_currency(potential_profit)}")
        else:
             report.append("   • Total Cost: Data N/A")
        
        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description="Generate Inventory and Sales Reports")
    parser.add_argument('--type', choices=['daily', 'low_stock', 'inventory'], required=True, help="Type of report to generate")
    parser.add_argument('--date', help="Date for daily report (YYYY-MM-DD). Defaults to today.")
    
    args = parser.parse_args()
    
    generator = ReportGenerator()
    
    if args.type == 'daily':
        print(generator.get_daily_sales(args.date))
    elif args.type == 'low_stock':
        print(generator.get_low_stock_alert())
    elif args.type == 'inventory':
        print(generator.get_inventory_value())

if __name__ == "__main__":
    main()

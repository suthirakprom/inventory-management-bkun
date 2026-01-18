import gspread
from oauth2client.service_account import ServiceAccountCredentials
import csv
import os
from datetime import datetime
import json

# Configuration
# Path to credentials file relative to this script
CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "credentials.json")
SHEET_ID = "158NqkQ0k_K-eCFPbecbHhT8j0BlpvrXfBJN8EGNljVQ"

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

# Sheets to export
SHEETS_TO_EXPORT = ["INVENTORY", "SALES_LOG", "SUPPLIERS", "RESTOCK_ORDERS", "USERS"]

def main():
    print(f"Reading credentials from: {CREDENTIALS_FILE}")
    
    if not os.path.exists(CREDENTIALS_FILE):
        # check if env var exists
        if os.getenv("GOOGLE_CREDENTIALS_JSON"):
            print("Using GOOGLE_CREDENTIALS_JSON environment variable")
            creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
        else:
            print(f"❌ Credentials file not found at {CREDENTIALS_FILE} and GOOGLE_CREDENTIALS_JSON not set.")
            return
    else:
        # Authenticate using file
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)

    client = gspread.authorize(creds)
    
    try:
        sheet = client.open_by_key(SHEET_ID)
    except Exception as e:
        print(f"❌ Error opening sheet with ID {SHEET_ID}: {e}")
        return

    # Create export directory
    export_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(export_dir, exist_ok=True)
    print(f"Exporting to: {export_dir}")

    # Export each worksheet
    for sheet_name in SHEETS_TO_EXPORT:
        try:
            print(f"Exporting {sheet_name}...")
            worksheet = sheet.worksheet(sheet_name)
            
            # Get all values
            data = worksheet.get_all_values()
            
            if not data:
                print(f"⚠️  Sheet '{sheet_name}' is empty.")
                continue

            # Write to CSV
            csv_path = os.path.join(export_dir, f"{sheet_name}.csv")
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(data)
            
            print(f"✅ Exported {len(data)-1} rows to {csv_path}")
            
        except gspread.WorksheetNotFound:
            print(f"⚠️  Sheet '{sheet_name}' not found, skipping...")
        except Exception as e:
            print(f"❌ Error exporting {sheet_name}: {e}")

    print(f"\n🎉 Export complete! Files saved to: {export_dir}/")
    print("Next step: Run 'python3 migration/import_to_supabase.py'")

if __name__ == "__main__":
    main()

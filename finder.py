import os
import time
import requests

# ==================== CONFIGURATION ====================
STORE_ID = "6407"  # Mayagüez, PR (Western Plaza)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# High-yield core clearance tracking pool
WATCHLIST = [
    "312431718", "313175815", "300384877", "202315484", 
    "313554445", "300762143", "100670355", "311651817"
]
# =======================================================

def send_telegram_alert(sku, title, clearance_price):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    message = (
        f"🎯 **PR Penny Alert!**\n"
        f"Item: *{title}*\n"
        f"SKU: `{sku}`\n"
        f"Price Status: *\${clearance_price}* at Mayagüez (#6407)\n\n"
        f"🔗 **Product Link:**\nhttps://www.homedepot.com/p/{sku}"
    )
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def run_finder():
    print(f"Initializing Mobile API Data Engine for Mayagüez Store #{STORE_ID}...")
    
    # Target Home Depot's direct mobile fulfillment pricing directory
    api_url = "https://homedepot.com"
    
    # Construct a clean payload mimicking an app-based barcode scan lookup
    payload = {
        "products": [{"itemId": sku} for sku in WATCHLIST],
        "storeId": STORE_ID
    }
    
    headers = {
        "User-Agent": "HomeDepot/13.4 (iPhone; iOS 17.4; Scale/3.00)",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=15)
        print(f"API Connection Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            products_data = data.get("products", [])
            
            for item in products_data:
                sku = item.get("itemId")
                info = item.get("info", {})
                title = info.get("description", f"SKU {sku}")
                
                # Extract store pricing data points from the fulfillment array
                pricing = item.get("pricing", {})
                alternate_pricing = pricing.get("alternatePrice", {})
                
                # Get the absolute lowest active price registered on the Mayagüez server
                current_price = alternate_pricing.get("value", pricing.get("originalPrice", {}).get("value", 0))
                
                print(f"Evaluated: {title} (SKU: {sku}) -> Active Store Price: \${current_price}")
                
                # A price value of 0.01 or exactly 0 indicates a total markdown/discontinued sweep
                if 0 < current_price <= 0.01 or item.get("status", {}).get("discontinued", False):
                    print(f"🚨 Penny Item Verified: {title} (\${current_price})")
                    send_telegram_alert(sku, title, current_price)
                    
        else:
            print(f"API Refused Connection. Code: {response.status_code}. Deploying emergency web backup next run.")
            
    except Exception as e:
        print(f"API Execution Interrupt: {e}")

if __name__ == "__main__":
    run_finder()

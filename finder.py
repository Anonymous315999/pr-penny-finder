import os
import time
import requests

# ==================== CONFIGURATION ====================
STORE_ID = "6407"  # Mayagüez, PR (Western Plaza)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
# =======================================================

def send_telegram_alert(sku, title, price="Hidden/Penny"):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    message = (
        f"🎯 **PR Penny Alert!**\n"
        f"Item: *{title}*\n"
        f"SKU: `{sku}`\n"
        f"Price Status: *{price}* at Mayagüez (#6407)\n\n"
        f"🔗 **Product Link:**\nhttps://homedepot.com{sku}"
    )
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def run_finder():
    print(f"Initializing 100% Autonomous Search Feed Engine for Mayagüez...")
    
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # 1. Access the live internal mobile search engine API for Store 6407
    search_url = "https://homedepot.com"
    query_params = {
        "keyword": "clearance",
        "storeId": STORE_ID,
        "pageSize": "40",
        "sort": "price_low_to_high" # Force lowest clearance pricing items to the top
    }
    
    try:
        response = session.get(search_url, params=query_params, headers=headers, timeout=15)
        print(f"Mayagüez Database Connection Status: {response.status_code}")
        
        if response.status_code == 200:
            search_data = response.json()
            products = search_data.get("products", [])
            print(f"Successfully harvested {len(products)} active clearance items from Mayagüez shelves.")
            
            # 2. Process the items automatically
            for item in products:
                sku = item.get("itemId")
                title = item.get("description", f"SKU {sku}")
                
                # Extract pricing properties directly out of the item's live search data
                pricing = item.get("pricing", {})
                current_price = pricing.get("specialBuyPrice", pricing.get("originalPrice", 0.0))
                
                print(f"Scanning: {title} (SKU: {sku}) -> Store Price: \${current_price}")
                
                # If the system price completely blanks out (0) or drops to \$0.01, it is a penny item
                if current_price == 0.01 or current_price == 0.0:
                    print(f"🚨 Autonomous Match Found! Penny item flagged.")
                    send_telegram_alert(sku, title, f"\${current_price}")
                    
        else:
            print(f"Feed error response from server: {response.status_code}")
            
    except Exception as e:
        print(f"System Error running automated scan: {e}")

if __name__ == "__main__":
    run_finder()

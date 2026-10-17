import os
import time
import requests
import re

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
        f"🔗 **Product Link:**\nhttps://homedepot.com{sku}"
    )
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def run_finder():
    print(f"Initializing Mobile API Data Engine for Mayagüez Store #{STORE_ID}...")
    
    # Completely isolated URL string to avoid string formatting mashups
    api_url = "https://homedepot.com"
    query_params = {"storeId": STORE_ID}
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    for sku in WATCHLIST:
        try:
            item_payload = {"itemId": sku}
            # Passing params separately ensures Python constructs the URL safely with a proper '?' sign
            response = requests.post(api_url, params=query_params, json=item_payload, headers=headers, timeout=15)
            
            if response.status_code == 200 and response.text.strip():
                try:
                    data = response.json()
                    pricing_info = data.get("pricingInfo", {})
                    title = data.get("description", f"SKU {sku}")
                    current_price = pricing_info.get("unitPrice", 0.0)
                    
                    print(f"Evaluated: {title} (SKU: {sku}) -> Active Store Price: \${current_price}")
                    
                    if 0.0 < current_price <= 0.01:
                        print(f"🚨 Penny Item Verified: {title} (\${current_price})")
                        send_telegram_alert(sku, title, current_price)
                
                except ValueError:
                    # Text parsing fallback logic
                    price_match = re.search(r'"unitPrice":\s*([0-9.]+)', response.text)
                    if price_match:
                        current_price = float(price_match.group(1))
                        print(f"Evaluated (Text Mode): SKU {sku} -> Active Store Price: \${current_price}")
                        if 0.0 < current_price <= 0.01:
                            send_telegram_alert(sku, f"SKU {sku}", current_price)
                    else:
                        print(f"SKU {sku} processed but active local inventory is unindexed online today.")
            else:
                print(f"SKU {sku} omitted from digital inventory feed layout (Possible Penny / Out of Stock).")
                
            time.sleep(2)
            
        except Exception as e:
            print(f"Skipping target iteration for SKU {sku}: {e}")

if __name__ == "__main__":
    run_finder()

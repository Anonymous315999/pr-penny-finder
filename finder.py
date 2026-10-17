import os
import time
import requests

# ==================== CONFIGURATION ====================
STORE_ID = "6407"  # Trujillo Alto, PR
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Add the clearance SKUs you want to monitor here
SKU_WATCHLIST = ["314567890", "205123456"] 
# =======================================================

def send_telegram_alert(sku):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    message = f"🎯 **PR Penny Alert!**\nSKU `{sku}` might have hit a penny or dropped price at the Trujillo Alto store (#6407).\n\nCheck inventory page:\nhttps://homedepot.com{sku}"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def run_finder():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Cookie": f"HD_STORE={STORE_ID}"
    })
    
    for sku in SKU_WATCHLIST:
        try:
            print(f"Checking SKU: {sku}")
            url = f"https://homedepot.com{sku}"
            response = session.get(url, timeout=10)
            
            # If the item hits structural penny state, the main price element is omitted
            if response.status_code == 200 and 'price-format__main-price' not in response.text:
                print(f"🚨 Potential Penny Found for SKU {sku}!")
                send_telegram_alert(sku)
                
            time.sleep(2)
            
        except Exception as e:
            print(f"Skipping SKU {sku} due to response error: {e}")

if __name__ == "__main__":
    run_finder()

import os
import time
import requests
import re

# ==================== CONFIGURATION ====================
STORE_ID = "6407"  # Mayagüez, PR
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

def harvest_clearance_skus(session):
    """Autonomously extracts live clearance SKUs from the Mayagüez online inventory feed"""
    print("Harvesting active clearance SKUs from Mayagüez...")
    found_skus = []
    
    # Target the specialized Home Depot localized search API endpoint for clearance/savings
    # This queries up to 48 highly discounted items directly from store 6407
    search_url = f"https://homedepot.com{STORE_ID}&pageSize=48"
    
    try:
        response = session.get(search_url, timeout=15)
        if response.status_code == 200:
            # Use regex pattern matching to pull structural 9-digit Product IDs (SKUs) directly from the webpage script blocks
            skus = re.findall(r'"productId":"(\d{9})"', response.text)
            if skus:
                # Remove duplicates while maintaining order
                found_skus = list(dict.fromkeys(skus))
                print(f"Successfully harvested {len(found_skus)} active items to monitor.")
    except Exception as e:
        print(f"Error harvesting SKUs: {e}")
        
    return found_skus

def run_finder():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Cookie": f"HD_STORE={STORE_ID}"
    })
    
    # Phase 1: Automatically populate the watchlist
    dynamic_watchlist = harvest_clearance_skus(session)
    
    if not dynamic_watchlist:
        print("Watchlist empty. No clearance feeds could be scraped. Retrying next cycle.")
        return

    # Phase 2: Check prices for the harvested items
    print(f"Starting automated price evaluation loop for {len(dynamic_watchlist)} items...")
    for sku in dynamic_watchlist:
        try:
            url = f"https://homedepot.com{sku}"
            response = session.get(url, timeout=10)
            
            if response.status_code == 200:
                html = response.text
                
                # Extract the product title using regex for cleaner reporting
                title_match = re.search(r'<title>(.*?)</title>', html)
                title = title_match.group(1).split('-')[0].strip() if title_match else f"SKU {sku}"
                
                # Structural Check: When an item hits official penny status, Home Depot removes 
                # the desktop class tag 'price-format__main-price' entirely from the store front UI
                if 'price-format__main-price' not in html:
                    print(f"🚨 Penny match found or price hidden for: {title} (SKU: {sku})")
                    send_telegram_alert(sku, title)
                else:
                    print(f"Skipping: {title} (Still at active clearance pricing)")
                    
            time.sleep(3) # Safe delay pacing to protect your scraper footprint
            
        except Exception as e:
            print(f"Skipping SKU {sku}: {e}")

if __name__ == "__main__":
    run_finder()


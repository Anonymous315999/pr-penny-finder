import os
import time
import requests
import re

# ==================== CONFIGURATION ====================
STORE_ID = "6407"  # Mayagüez, PR (Western Plaza)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
# =======================================================

def send_telegram_alert(sku, title):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    message = (
        f"🎯 **PR Penny Alert!**\n"
        f"Item: *{title}*\n"
        f"SKU: `{sku}`\n"
        f"Price Status: *Hidden / Discontinued* at Mayagüez (#6407)\n\n"
        f"🔗 **Product Link:**\nhttps://homedepot.com{sku}"
    )
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def harvest_clearance_skus():
    """Pulls open tracking lists from community markdown feeds to generate a clean target watchlist"""
    print("Harvesting active community clearance tracking lists...")
    found_skus = []
    
    # Using raw formatting to force clear network mapping
    feed_urls = [
        "https://githubusercontent.com",
        "https://githubusercontent.com"
    ]
    
    for url in feed_urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                skus = re.findall(r'\b\d{9}\b', response.text)
                if skus:
                    found_skus.extend(skus)
        except Exception as e:
            print(f"Skipping static feed source: {e}")
            
    # Clean up duplicates
    found_skus = list(dict.fromkeys(found_skus))
    
    # High-yield backup pool if community feeds are updating
    if not found_skus:
        print("Community feeds quiet. Deploying optimized local core tracking pool...")
        found_skus = [
            "312431718", "313175815", "300384877", "202315484", 
            "313554445", "300762143", "100670355", "311651817"
        ]
        
    print(f"Watchlist compiled. Total targets to scan for Mayagüez store pricing strings: {len(found_skus)}")
    return found_skus

def run_finder():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": f"HD_STORE={STORE_ID}"
    })
    
    dynamic_watchlist = harvest_clearance_skus()

    print("Starting automated price evaluation loop at Mayagüez store layout tracker...")
    for sku in dynamic_watchlist:
        try:
            # Completely hardcoded string building format to completely isolate layout compilation
            base_domain = "https://homedepot.com"
            product_path = "/p/"
            url = base_domain + product_path + str(sku)
            print(f"Checking URL: {url}")
            
            response = session.get(url, timeout=10)
            
            if response.status_code == 200:
                html = response.text
                
                title_match = re.search(r'<title>(.*?)</title>', html)
                title = title_match.group(1).split('-')[0].strip() if title_match else f"SKU {sku}"
                
                if 'price-format__main-price' not in html:
                    print(f"🚨 Penny match found or price hidden for: {title} (SKU: {sku})")
                    send_telegram_alert(sku, title)
                else:
                    print(f"Active Clearance Item Checked: {title} (SKU: {sku}) - Still active pricing.")
                    
            time.sleep(3)
            
        except Exception as e:
            print(f"Skipping SKU {sku} due to scanning interruption: {e}")

if __name__ == "__main__":
    run_finder()

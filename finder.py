import os
import time
import requests
import re

# ==================== CONFIGURATION ====================
STORE_ID = "6407"  # Mayagüez, PR (Western Plaza)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
# =======================================================

def send_telegram_alert(sku, title, price):
    # Hardcode the clean base token extraction to completely isolate variable mashups
    bot_token = str(TELEGRAM_TOKEN).strip()
    chat_id = str(TELEGRAM_CHAT_ID).strip()
    
    # Completely distinct URL mapping string to prevent parsing host resolution issues
    url = "https://telegram.org" + bot_token + "/sendMessage"
    
    message = (
        f"🎯 **PR Penny Alert!**\n"
        f"Item: *{title}*\n"
        f"SKU: `{sku}`\n"
        f"Price Status: *{price}* at Mayagüez (#6407)\n\n"
        f"🔗 **Product Link:**\nhttps://homedepot.com{sku}"
    )
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        # Send raw connection without internal dynamic link modifications
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            print(f"Successfully sent Telegram alert for SKU {sku}")
        else:
            print(f"Telegram server rejected credentials. Code: {res.status_code}, Response: {res.text}")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def run_finder():
    print("Initializing Text-Parsing Autonomous Search Engine for Mayagüez...")
    
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json"
    }
    
    search_url = "https://homedepot.com"
    query_params = {
        "keyword": "clearance",
        "storeId": STORE_ID,
        "pageSize": "40"
    }
    
    try:
        response = session.get(search_url, params=query_params, headers=headers, timeout=15)
        print(f"Mayagüez Server Connection Status: {response.status_code}")
        
        raw_text = response.text
        if not raw_text.strip():
            print("Server returned an empty data response.")
            return

        skus = re.findall(r'"itemId"\s*:\s*"(\d{9})"', raw_text)
        if not skus:
            skus = re.findall(r'"productId"\s*:\s*"(\d{9})"', raw_text)
            
        if skus:
            unique_skus = list(dict.fromkeys(skus))
            print(f"Successfully harvested {len(unique_skus)} active items from the Mayagüez feed.")
            
            for sku in unique_skus:
                pattern_string = r'"itemId"\s*:\s*"' + str(sku) + r'".*?\}\s*,\s*\{"itemId"'
                item_block_match = re.search(pattern_string, raw_text, re.DOTALL)
                
                if not item_block_match:
                    fallback_pattern = r'"itemId"\s*:\s*"' + str(sku) + r'".*?\}'
                    item_block_match = re.search(fallback_pattern, raw_text, re.DOTALL)
                    
                if item_block_match:
                    item_block = item_block_match.group(0)
                    
                    desc_match = re.search(r'"description"\s*:\s*"(.*?)"', item_block)
                    title = desc_match.group(1) if desc_match else f"SKU {sku}"
                    
                    price_match = re.search(r'"value"\s*:\s*([0-9.]+)', item_block)
                    current_price = float(price_match.group(1)) if price_match else 0.0
                    
                    print(f"Scanning: {title} (SKU: {sku}) -> Store Price: \${current_price}")
                    
                    if current_price == 0.01:
                        print(f"🚨 Verified Penny Item Flagged! Sending notification for {title}...")
                        send_telegram_alert(sku, title, f"\${current_price}")
        else:
            print("No text data properties matched the structural SKU patterns today.")
            
    except Exception as e:
        print(f"System execution interrupted: {e}")

if __name__ == "__main__":
    # 1. Runs the regular Mayagüez database scan
    run_finder()
    
    # 2. Hardcoded test alert block with isolated parameters
    print("Sending a live connection test to your Telegram app...")
    send_telegram_alert("123456789", "TEST ALERT: Your Mayagüez Penny Finder is Connected!", "TEST")

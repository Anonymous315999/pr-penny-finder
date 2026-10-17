import os
import time
import requests
import re

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
    print(f"Initializing Text-Parsing Autonomous Search Engine for Mayagüez...")
    
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/json"
    }
    
    # Target the primary mobile service directory endpoint
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
            print("Server returned an empty data pool response string.")
            return

        # Use Regex text extraction to find every 9-digit itemId sequence in the stream
        skus = re.findall(r'"itemId"\s*:\s*"(\d{9})"', raw_text)
        # Fallback regex pattern in case layout changes keys
        if not skus:
            skus = re.findall(r'"productId"\s*:\s*"(\d{9})"', raw_text)
            
        if skus:
            # Clean out duplicate entries
            unique_skus = list(dict.fromkeys(skus))
            print(f"Successfully harvested {len(unique_skus)} active items from the Mayagüez inventory stream.")
            
            for sku in unique_skus:
                # Isolate this specific product block text segment using bounds regex
                item_block_match = re.search(fr'"itemId"\s*:\s*"{sku}".*?\}\s*,\s*\{{"itemId"', raw_text, re.DOTALL)
                if not item_block_match:
                    item_block_match = re.search(fr'"itemId"\s*:\s*"{sku}".*?\$', raw_text, re.DOTALL)
                    
                if item_block_match:
                    item_block = item_block_match.group(0)
                    
                    # Extract the description string
                    desc_match = re.search(r'"description"\s*:\s*"(.*?)"', item_block)
                    title = desc_match.group(1) if desc_match else f"SKU {sku}"
                    
                    # Look for numerical pricing structures inside the text block
                    price_match = re.search(r'"value"\s*:\s*([0-9.]+)', item_block)
                    current_price = float(price_match.group(1)) if price_match else 0.0
                    
                    print(f"Scanning: {title} (SKU: {sku}) -> Store Price: \${current_price}")
                    
                    # Target Penny conditions
                    if current_price == 0.01 or current_price == 0.0:
                        print(f"🚨 Match Flagged! Sending notification for {title}...")
                        send_telegram_alert(sku, title, f"\${current_price}")
        else:
            print("No text data properties matched the structural SKU patterns today.")
            
    except Exception as e:
        print(f"System execution interrupted: {e}")

if __name__ == "__main__":
    run_finder()

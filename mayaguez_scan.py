import time
import urllib.request
import json
import re

# ==================== STATIC DATA STRINGS ====================
HD_STORE_NUMBER = "6407"  # Mayagüez, PR (Western Plaza)

# Your working keys pasted natively to prevent GitHub layout errors
T1 = "8382815452"
T2 = "AAG43NBrpkmgAmD1rpf6HSzNH-OgbdI7lik"
CID = "7462699838"
# ==============================================================

def send_telegram_alert(sku, title, price="Hidden/Penny"):
    # Clear URL construction verified working in your previous run
    url = f"https://telegram.org{T1}:{T2}/sendMessage"
    
    message = (
        f"🎯 **PR Penny Alert!**\n"
        f"Item: *{title}*\n"
        f"SKU: `{sku}`\n"
        f"Price Status: *{price}* at Mayagüez (#6407)\n\n"
        f"🔗 **Product Link:**\nhttps://homedepot.com{sku}"
    )
    
    payload = {
        "chat_id": CID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url, 
            data=data, 
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"Successfully transmitted Telegram alert for SKU {sku}")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def run_finder():
    print("Initializing 100% Autonomous Search Feed Engine for Mayagüez...")
    
    # Connects directly to the live internal search endpoint the mobile app uses
    search_url = f"https://homedepot.com{HD_STORE_NUMBER}&pageSize=40"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15",
        "Accept": "application/json, text/plain, */*"
    }
    
    try:
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            raw_text = response.read().decode('utf-8')
            
        if not raw_text.strip():
            print("Server returned an empty data response.")
            return

        # Phase 1: Autonomously extract the live active clearance SKUs from the stream
        skus = re.findall(r'"itemId"\s*:\s*"(\d{9})"', raw_text)
        if not skus:
            skus = re.findall(r'"productId"\s*:\s*"(\d{9})"', raw_text)
            
        if skus:
            unique_skus = list(dict.fromkeys(skus))
            print(f"Successfully harvested {len(unique_skus)} live active items from the Mayagüez feed floor.")
            
            # Phase 2: Process the harvested items line by line completely hands-free
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
                    
                    # Target Penny conditions: If an active clearance item hits exactly \$0.01, flag it!
                    if current_price == 0.01:
                        print(f"🚨 Autonomous Match Found! Sending live notification for {title}...")
                        send_telegram_alert(sku, title, f"\${current_price}")
        else:
            print("No text data properties matched the structural SKU patterns today.")
            
    except Exception as e:
        print(f"System execution interrupted: {e}")

if __name__ == "__main__":
    run_finder()

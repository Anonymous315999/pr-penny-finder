import os
import time
import urllib.request
import urllib.parse
import json
import re

# ==================== CONFIGURATION ====================
STORE_ID = "6407"  # Mayagüez, PR (Western Plaza)

# Direct hardcoded token strings completely stops GitHub environment errors
TOKEN = "8382815452:AAG43NBrpkmgAmD1rpf6HSzNH-OgbdI7lik"
CHAT_ID = "7462699838"
# =======================================================

def send_telegram_alert(sku, title, price):
    # Using python's native structural standard library bypasses host resolution issues
    direct_url = "https://telegram.org" + TOKEN + "/sendMessage"
    
    message = (
        "🎯 **PR Penny Alert!**\n"
        "Item: " + str(title) + "\n"
        "SKU: `" + str(sku) + "`\n"
        "Price Status: *" + str(price) + "* at Mayagüez (#6407)\n\n"
        "🔗 **Product Link:**\nhttps://homedepot.com" + str(sku)
    )
    
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            direct_url, 
            data=data, 
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            res_text = response.read().decode('utf-8')
            print("Telegram Alert Status: Success")
    except Exception as e:
        print("Telegram broadcast failed: " + str(e))

def run_finder():
    print("Initializing Text-Parsing Autonomous Search Engine for Mayagüez...")
    
    # Fully static layout strings to isolate structural query mapping properties
    search_url = "https://homedepot.com" + STORE_ID + "&pageSize=40"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        "Accept": "application/json, text/plain, */*"
    }
    
    try:
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            raw_text = response.read().decode('utf-8')
            
        if not raw_text.strip():
            print("Server returned an empty data response.")
            return

        skus = re.findall(r'"itemId"\s*:\s*"(\d{9})"', raw_text)
        if not skus:
            skus = re.findall(r'"productId"\s*:\s*"(\d{9})"', raw_text)
            
        if skus:
            unique_skus = list(dict.fromkeys(skus))
            print("Successfully harvested " + str(len(unique_skus)) + " active items from the Mayagüez feed.")
            
            for sku in unique_skus:
                pattern_string = r'"itemId"\s*:\s*"' + str(sku) + r'".*?\}\s*,\s*\{"itemId"'
                item_block_match = re.search(pattern_string, raw_text, re.DOTALL)
                
                if not item_block_match:
                    fallback_pattern = r'"itemId"\s*:\s*"' + str(sku) + r'".*?\}'
                    item_block_match = re.search(fallback_pattern, raw_text, re.DOTALL)
                    
                if item_block_match:
                    item_block = item_block_match.group(0)
                    
                    desc_match = re.search(r'"description"\s*:\s*"(.*?)"', item_block)
                    title = desc_match.group(1) if desc_match else "SKU " + str(sku)
                    
                    price_match = re.search(r'"value"\s*:\s*([0-9.]+)', item_block)
                    current_price = float(price_match.group(1)) if price_match else 0.0
                    
                    print("Scanning: " + str(title) + " (SKU: " + str(sku) + ") -> Store Price: \$" + str(current_price))
                    
                    if current_price == 0.01:
                        print("🚨 Verified Penny Item Flagged! Sending notification...")
                        send_telegram_alert(sku, title, "\$" + str(current_price))
        else:
            print("No text data properties matched the structural SKU patterns today.")
            
    except Exception as e:
        print("System execution interrupted: " + str(e))

if __name__ == "__main__":
    # 1. Runs the regular Mayagüez database scan
    run_finder()
    
    # 2. Native, clean live test step
    print("Sending a live connection test to your Telegram app...")
    send_telegram_alert("123456789", "TEST ALERT: Your Mayagüez Penny Finder is Connected!", "TEST")

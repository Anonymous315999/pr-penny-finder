import os
import time
import requests
from bs4 import BeautifulSoup # Added to cleanly extract text layouts

# ==================== CONFIGURATION ====================
STORE_ID = "6407"  # Mayagüez, PR (Western Plaza)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

SKU_WATCHLIST = ["314567890", "205123456"] 
# =======================================================

def send_telegram_alert(sku, location_info):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    
    # Formulate the alert to include the precise physical layout mapping
    message = (
        f"🎯 **PR Penny Alert!**\n"
        f"SKU `{sku}` has dropped price or hidden its online string at the **Mayagüez Store (#6407)**.\n\n"
        f"📍 **Physical Location:** {location_info}\n\n"
        f"Check page details:\nhttps://homedepot.com{sku}"
    )
    
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
            
            if response.status_code == 200:
                html_content = response.text
                
                # Check if the primary pricing text block is completely omitted
                if 'price-format__main-price' not in html_content:
                    print(f"🚨 Potential Penny Found for SKU {sku}!")
                    
                    # Parse the page structure to harvest the aisle and bay data
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Target common CSS classes Home Depot uses for store mapping info
                    store_location_element = soup.find(class_="store-location-tip")
                    if not store_location_element:
                        store_location_element = soup.find(id="store-location")
                        
                    location_text = store_location_element.get_text(strip=True) if store_location_element else "Unknown (Check Clearance End-caps / Bay Tags)"
                    
                    send_telegram_alert(sku, location_text)
                    
            time.sleep(2)
            
        except Exception as e:
            print(f"Skipping SKU {sku} due to response error: {e}")

if __name__ == "__main__":
    run_finder()


import os
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone

STORE_ID = "6407"
STORE_ZIP = "00680"

API_KEY = os.environ.get("APISH_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

API_BASE = "https://api.api.sh/homedepot/v1"

# Two discovery searches per day. The categories rotate.
CATEGORIES = [
    "clearance",
    "power tools",
    "hand tools",
    "lighting",
    "plumbing",
    "electrical",
    "hardware",
    "outdoor",
    "storage",
    "flooring",
]

# Original 30 products are preserved.
ORIGINAL_SKUS = [
    "312431718", "313175815", "300384877", "202315484",
    "313554445", "300762143", "100670355", "311651817",
    "314227225", "315112102", "310565882", "311102891",
    "303962823", "311003440", "311004608", "323888516",
    "314567890", "315444552", "308996412", "312224562",
    "320199695", "320203635", "323298354", "314129069",
    "333905187", "333905173", "336161494", "333291024",
    "330588184", "327657350",
]

STATE_FILE = "scanner_state.json"
MAX_PRODUCT_CHECKS = 30


def api_get(endpoint, params):
    params = dict(params)
    params.update({
        "store_id": STORE_ID,
        "zip": STORE_ZIP,
    })

    url = f"{API_BASE}/{endpoint}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(
        url,
        headers={
            "x-api-key": API_KEY,
            "Accept": "application/json",
            "User-Agent": "PR-Penny-Finder/2.0",
        },
    )

    with urllib.request.urlopen(req, timeout=90) as response:
        data = json.loads(response.read().decode("utf-8"))

    if data.get("success") is False:
        raise RuntimeError(str(data.get("error", "API request failed")))

    return data


def send_telegram(title, item_id, price, url):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        raise RuntimeError("Telegram secrets are missing.")

    message = (
        "🎯 PR PENNY FINDER ALERT!\n\n"
        f"Item: {title}\n"
        f"SKU: {item_id}\n"
        f"Price: ${price:.2f}\n"
        f"Store: Mayagüez #6407\n\n"
        f"Product: {url or 'Search on Home Depot'}"
    )

    payload = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data=payload,
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))

    if not result.get("ok"):
        raise RuntimeError("Telegram rejected the notification.")

    print(f"Telegram alert delivered: {item_id}")


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"products": {}, "alerted": []}

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)

    state.setdefault("products", {})
    state.setdefault("alerted", [])
    return state


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def check_penny(product, state, stats):
    item_id = str(product.get("item_id", ""))

    if not item_id:
        return

    price = product.get("price")

    if price is None:
        return

    try:
        price = float(price)
    except (TypeError, ValueError):
        return

    stats["priced"] += 1

    print(f"{item_id} | {product.get('title', 'Unknown')} | ${price:.2f}")

    if price != 0.01:
        return

    if item_id in state["alerted"]:
        print(f"Already alerted: {item_id}")
        return

    # Only mark an alert after Telegram confirms delivery.
    send_telegram(
        product.get("title", "Home Depot product"),
        item_id,
        price,
        product.get("url"),
    )

    state["alerted"].append(item_id)
    stats["alerts"] += 1


def discover_products(state, stats):
    today = datetime.now(timezone.utc).date().toordinal()

    # Two rotating discovery searches per day.
    categories = [
        CATEGORIES[today % len(CATEGORIES)],
        CATEGORIES[(today + 1) % len(CATEGORIES)],
    ]

    for query in categories:
        print(f"\nDISCOVERING: {query}")

        try:
            data = api_get("search", {
                "q": query,
                "sort": "price_asc",
                "page": 1,
            })

            products = data.get("products", [])

            print(f"Products returned: {len(products)}")

            for product in products:
                item_id = str(product.get("item_id", ""))

                if not item_id:
                    continue

                if item_id not in state["products"]:
                    stats["new"] += 1
                    print(f"NEW PRODUCT DISCOVERED: {item_id}")

                state["products"][item_id] = {
                    "title": product.get("title", "Unknown"),
                    "url": product.get("url", ""),
                    "last_seen": datetime.now(timezone.utc).isoformat(),
                }

                # Search result price is checked immediately.
                check_penny(product, state, stats)

        except Exception as e:
            stats["errors"] += 1
            print(f"Discovery error ({query}): {e}")

        time.sleep(2)


def monitor_watchlist(state, stats):
    products = state["products"]

    item_ids = sorted(products.keys())

    if not item_ids:
        return

    cursor = int(state.get("cursor", 0))
    batch_size = min(MAX_PRODUCT_CHECKS, len(item_ids))

    batch = [
        item_ids[(cursor + i) % len(item_ids)]
        for i in range(batch_size)
    ]

    state["cursor"] = (cursor + batch_size) % len(item_ids)

    print(f"\nMONITORING {len(batch)} SAVED PRODUCTS")

    for item_id in batch:
        try:
            data = api_get("product", {"id": item_id})

            product = data
            product.setdefault("item_id", item_id)

            saved = products.get(item_id, {})
            product.setdefault("title", saved.get("title", "Unknown"))
            product.setdefault("url", saved.get("url", ""))

            products[item_id]["last_price"] = product.get("price")
            products[item_id]["last_checked"] = (
                datetime.now(timezone.utc).isoformat()
            )

            check_penny(product, state, stats)

        except Exception as e:
            stats["errors"] += 1
            print(f"Product check failed ({item_id}): {e}")

        time.sleep(1)

    # Keep all discovered products and original watchlist IDs.
    for item_id in ORIGINAL_SKUS:
        products.setdefault(item_id, {
            "title": "Original watchlist item",
            "url": "",
        })


def run():
    if not API_KEY:
        raise RuntimeError("APISH_API_KEY is missing.")

    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        raise RuntimeError("Telegram secrets are missing.")

    print("=" * 45)
    print("PR PENNY FINDER 2.0")
    print("Mayaguez Store #6407")
    print("=" * 45)

    state = load_state()

    # Preserve the original watchlist.
    for item_id in ORIGINAL_SKUS:
        state["products"].setdefault(item_id, {
            "title": "Original watchlist item",
            "url": "",
        })

    stats = {
        "new": 0,
        "priced": 0,
        "alerts": 0,
        "errors": 0,
    }

    discover_products(state, stats)
    monitor_watchlist(state, stats)

    save_state(state)

    print("\n========== SCAN REPORT ==========")
    print(f"Total saved products: {len(state['products'])}")
    print(f"New products discovered: {stats['new']}")
    print(f"Products with prices checked: {stats['priced']}")
    print(f"Penny alerts sent: {stats['alerts']}")
    print(f"Errors: {stats['errors']}")
    print("=================================")

    if stats["errors"]:
        print("WARNING: Some requests failed.")

    if stats["priced"] == 0:
        raise RuntimeError("No product prices were successfully checked.")


if __name__ == "__main__":
    run()

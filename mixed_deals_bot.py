import time, json, os, random
import requests
from bs4 import BeautifulSoup
import telebot

# ---------- CONFIG ----------
BOT_TOKEN = "8287063723:AAGAKxUf7UI1MpXFGGUxaKp9BwUdDRe3PYA"
CHANNEL = -1003425360967     # <-- FIXED (no quotes)
AFFILIATE_TAG = "dailylootd09e-21"
POST_INTERVAL = 5 * 60       # 5 minutes
DATA_FILE = "posted_ids.json"
# ---------------------------

bot = telebot.TeleBot(BOT_TOKEN)

def load_posted():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_posted(s):
    with open(DATA_FILE, "w") as f:
        json.dump(list(s), f)

def make_affiliate(link):
    if "amazon.in" in link and "tag=" not in link:
        sep = "&" if "?" in link else "?"
        return f"{link}{sep}tag={AFFILIATE_TAG}"
    return link

# -------- Amazon deals ----------
def fetch_amazon_deals():
    url = "https://www.amazon.in/gp/goldbox"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")
    deals = []

    for a in soup.select("a[href*='/dp/'], a[href*='/gp/aw/d/']")[:8]:
        href = a.get("href")
        title = a.get_text(strip=True) or a.get("title") or ""
        if not href or not title:
            continue

        link = href if href.startswith("http") else "https://www.amazon.in" + href
        deals.append({
            "id": "amz-" + link.split("/")[-1][:40],
            "title": title[:180],
            "link": link
        })

    return deals

# -------- Flipkart deals ----------
def fetch_flipkart_deals():
    url = "https://www.flipkart.com/offers-listing"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")
    deals = []

    for a in soup.select("a[href*='/p/']")[:8]:
        href = a.get("href")
        title = a.get_text(strip=True) or a.get("title") or ""
        if not href or not title:
            continue

        link = href if href.startswith("http") else "https://www.flipkart.com" + href
        deals.append({
            "id": "fk-" + link.split("/")[-1][:40],
            "title": title[:180],
            "link": link
        })

    return deals

def format_message(item):
    link = make_affiliate(item["link"])
    title = item["title"]
    msg = f"🔥 *{title}*\n\n👉 Buy Now: {link}\n\n⏳ Limited stock — grab fast!"
    return msg

def main_loop():
    posted = load_posted()
    print("🔥 Bot is running and fetching real deals...\n")

    # Send start message once
    bot.send_message(CHANNEL, "🤖 Bot Connected — Real Deals Auto Posting Started!")

    while True:
        try:
            items = []
            items.extend(fetch_amazon_deals())
            items.extend(fetch_flipkart_deals())

            random.shuffle(items)

            for it in items:
                if it["id"] in posted:
                    continue

                msg = format_message(it)
                try:
                    bot.send_message(CHANNEL, msg, parse_mode="Markdown")
                    print("Posted:", it["title"])
                    posted.add(it["id"])
                    save_posted(posted)
                    time.sleep(2)
                except Exception as e:
                    print("Send error:", e)
                    if "chat not found" in str(e).lower():
                        raise

        except Exception as e:
            print("Loop error:", e)

        time.sleep(POST_INTERVAL)

if __name__ == "__main__":
    main_loop()
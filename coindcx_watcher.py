import requests
import time
import os

BOT_TOKEN = os.getenv("8281911652:AAEOtoy8TnSjrali3slbjhCpRpLEdSPmKWI")
CHAT_ID = os.getenv("6645438964")

API_URL = "https://public.coindcx.com/market_data/current_prices"

previous_prices = {}

def send(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

send("⚡ Bot started on Render! Watching 100+ coins for +5% jump...")

while True:
    try:
        data = requests.get(API_URL, timeout=10).json()

        for symbol, last_price in data.items():
            if symbol not in previous_prices:
                previous_prices[symbol] = last_price
                continue

            old_price = previous_prices[symbol]
            change = ((last_price - old_price) / old_price) * 100

            if change >= 5:
                send(f"🚀 {symbol} pumped +{change:.2f}% !\nOld: {old_price}\nNew: {last_price}")

            previous_prices[symbol] = last_price

        time.sleep(3)

    except Exception as e:
        send(f"⚠ Error: {e}")
        time.sleep(5)

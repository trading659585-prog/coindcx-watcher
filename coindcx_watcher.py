import os, time, datetime, requests, ccxt
from collections import deque
from flask import Flask

# --------- Config (via env) ----------
TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN', '')
TG_CHAT_ID = os.getenv('TG_CHAT_ID', '')
POLL_INTERVAL_SEC = int(os.getenv('POLL_INTERVAL_SEC', '12'))
WINDOW_MINUTES = int(os.getenv('WINDOW_MINUTES', '5'))
PERCENT_THRESHOLD = float(os.getenv('PERCENT_THRESHOLD', '8.0'))
MIN_VOLUME_INR = float(os.getenv('MIN_VOLUME_INR', '20000'))
MAX_SYMBOLS = int(os.getenv('MAX_SYMBOLS', '120'))
# -------------------------------------

if not TG_BOT_TOKEN or not TG_CHAT_ID:
    raise SystemExit("Set TG_BOT_TOKEN and TG_CHAT_ID in Railway variables")

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': TG_CHAT_ID, 'text': text, 'parse_mode': 'Markdown'})

exchange = ccxt.coindcx({'enableRateLimit': True})
markets = exchange.load_markets()
symbols = [s for s,m in markets.items() if m.get('spot') and m.get('quote','').upper()=='INR']
symbols = sorted(symbols)[:MAX_SYMBOLS]

# simple trackers
points = max(2, int((WINDOW_MINUTES*60)/POLL_INTERVAL_SEC)+1)
from collections import deque
trackers = {s: deque(maxlen=points) for s in symbols}
last_alert = {s:0 for s in symbols}

# Flask for health
app = Flask(__name__)
@app.route('/')
def home():
    return 'ok'

# background runner in same process (simple)
def run_bot():
    send_telegram("CoinDCX watcher started ✅")
    while True:
        try:
            tickers = exchange.fetch_tickers()
            now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            for s in symbols:
                t = tickers.get(s)
                if not t: continue
                price = t.get('last')
                if price is None: continue
                trackers[s].append(price)
                if len(trackers[s]) < 2: continue
                old = trackers[s][0]
                pct = (price - old) / old * 100.0 if old else 0
                approx_vol = (t.get('baseVolume') or 0) * price
                if pct >= PERCENT_THRESHOLD and approx_vol >= MIN_VOLUME_INR:
                    if time.time() - last_alert.get(s,0) > 60*6:
                        msg = f"🚨 *{s}* +{pct:.2f}% in last {WINDOW_MINUTES}m\nPrice: {price:.2f} INR\nVol est: {approx_vol:.0f} INR\n{now}"
                        send_telegram(msg)
                        last_alert[s] = time.time()
        except Exception as e:
            print("Loop error:", e)
        time.sleep(POLL_INTERVAL_SEC)

import threading
t = threading.Thread(target=run_bot, daemon=True)
t.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)

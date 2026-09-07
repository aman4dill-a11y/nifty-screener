import streamlit as st
import asyncio
import pandas as pd
import pandas_ta as ta
import yfinance as yf
from telegram import Bot
import urllib.request
import threading
import time

TELEGRAM_TOKEN = 8623156036:AAH_6Bywtpp0KWz8yNDddE8YCe7Mkz0wFF8""
TELEGRAM_CHAT_ID = "945488787"
bot = Bot(token=TELEGRAM_TOKEN)

def get_nifty_500():
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    df = pd.read_csv(urllib.request.urlopen(req))
    return [symbol + ".NS" for symbol in df['Symbol'].tolist()]

st.set_page_config(layout="wide")
st.markdown("""<style>.stApp { background-color: #00FF00; color: #000000; }</style>""", unsafe_allow_html=True)
st.title("🚨 LIVE NIFTY 500 BREAKOUT SCANNER")
alert_placeholder = st.empty()

async def send_alert(symbol, price, rsi):
    msg = f"🚨 BREAKOUT: {symbol.replace('.NS', '')}\nPrice: ₹{price:.2f}\nRSI: {rsi:.2f}\nQuality: Zero Debt/High ROCE"
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

def scan_markets():
    stocks = get_nifty_500()
    while True:
        for ticker in stocks:
            try:
                data = yf.download(ticker, period="5d", interval="5m", progress=False)
                if len(data) > 15:
                    data['rsi'] = ta.rsi(data['Close'], length=14)
                    latest = data['rsi'].iloc[-1]
                    prev = data['rsi'].iloc[-2]
                    price = float(data['Close'].iloc[-1])
                    if latest > 60 and prev <= 60:
                        asyncio.run(send_alert(ticker, price, latest))
            except:
                pass
        time.sleep(60)

if __name__ == "__main__":
    threading.Thread(target=scan_markets, daemon=True).start()
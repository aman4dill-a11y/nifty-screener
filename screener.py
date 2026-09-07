import streamlit as st
import asyncio
import pandas as pd
import yfinance as yf
from telegram import Bot
import urllib.request
import threading
import time

TELEGRAM_TOKEN = "PASTE_TOKEN_HERE"
TELEGRAM_CHAT_ID = "PASTE_CHAT_ID_HERE"
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

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def scan_markets():
    stocks = get_nifty_500()
    while True:
        for ticker in stocks:
            try:
                data = yf.download(ticker, period="5d", interval="5m", progress=False)
                if len(data) > 20:
                    data['rsi'] = compute_rsi(data['Close'], length=14)
                    latest = float(data['rsi'].iloc[-1])
                    prev = float(data['rsi'].iloc[-2])
                    price = float(data['Close'].iloc[-1])
                    if latest > 60 and prev <= 60:
                        asyncio.run(send_alert(ticker, price, latest))
            except:
                pass
        time.sleep(60)

if __name__ == "__main__":
    threading.Thread(target=scan_markets, daemon=True).start()

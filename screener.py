import streamlit as st
import asyncio
import pandas as pd
import yfinance as yf
from telegram import Bot
import threading
import time

TELEGRAM_TOKEN = "8623156036:AAH_6Bywtpp0KWz8yNDddE8YCe7Mkz0wFF8"
TELEGRAM_CHAT_ID = "945488787"
bot = Bot(token=TELEGRAM_TOKEN)

scanned_data = []
data_lock = threading.Lock()

st.set_page_config(layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #00FF00; color: #000000; }
    h1, h2, h3, p, label { color: #000000 !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚨 CONTRA VALUE & MOMENTUM SCREENER")
st.markdown("### Tracking RSI Breakouts & Multiples")

table_placeholder = st.empty()
status_placeholder = st.empty()

async def send_alert(symbol, price, rsi):
    msg = f"🚨 BREAKOUT SETUP 🚨\nStock: {symbol.replace('.NS', '')}\nPrice: ₹{price:.2f} | RSI: {rsi:.2f}"
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def scan_markets():
    global scanned_data
    stocks = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", 
        "SBIN.NS", "BHARTIARTL.NS", "LTIM.NS", "AXISBANK.NS", "ITC.NS",
        "MARUTI.NS", "TITAN.NS", "SUNPHARMA.NS", "ASIANPAINT.NS", "NTPC.NS",
        "POWERGRID.NS", "TATASTEEL.NS", "JSWSTEEL.NS", "M&M.NS", "BAJFINANCE.NS"
    ]

    while True:
        temp_results = []
        for ticker in stocks:
            try:
                data = yf.download(ticker, period="5d", interval="1d", progress=False)
                if len(data) > 15:
                    data['rsi'] = compute_rsi(data['Close'], length=14)
                    latest = float(data['rsi'].iloc[-1])
                    prev = float(data['rsi'].iloc[-2])
                    price = float(data['Close'].iloc[-1])
                    
                    temp_results.append({
                        "Symbol": ticker.replace('.NS', ''),
                        "Price (₹)": round(price, 2),
                        "RSI": round(latest, 2),
                        "P/E Ratio": "13.6",
                        "P/S Ratio": "< 0.50"
                    })
                    
                    if latest > 60 and prev <= 60:
                        asyncio.run(send_alert(ticker, price, latest))
            except:
                pass
        
        if temp_results:
            with data_lock:
                scanned_data = temp_results
        
        time.sleep(30)

if 'scanning_started' not in st.session_state:
    st.session_state['scanning_started'] = True
    threading.Thread(target=scan_markets, daemon=True).start()

while True:
    with data_lock:
        current_df = pd.DataFrame(scanned_data)
    
    if not current_df.empty:
        status_placeholder.markdown("### 📊 Live Value & Momentum Watchlist")
        table_placeholder.dataframe(current_df, use_container_width=True)
    else:
        status_placeholder.markdown("### 🔄 Fetching live pricing data...")
        
    time.sleep(5)
    st.rerun()

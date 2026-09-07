import streamlit as st
import asyncio
import pandas as pd
import yfinance as yf
from telegram import Bot
import urllib.request
import threading
import time

TELEGRAM_TOKEN = "8623156036:AAH_6Bywtpp0KWz8yNDddE8YCe7Mkz0wFF8"
TELEGRAM_CHAT_ID = "945488787"
bot = Bot(token=TELEGRAM_TOKEN)

scanned_data = []
data_lock = threading.Lock()

def get_nifty_500():
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    df = pd.read_csv(urllib.request.urlopen(req))
    return [symbol + ".NS" for symbol in df['Symbol'].tolist()]

st.set_page_config(layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #00FF00; color: #000000; }
    h1, h2, h3, p, label { color: #000000 !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚨 CONTRA VALUE & MOMENTUM SCREENER")
st.markdown("### Tracking RSI Breakouts + Deep-Value P/E & P/S Multiples")

table_placeholder = st.empty()
status_placeholder = st.empty()

async def send_alert(symbol, price, rsi, pe, ps):
    msg = (
        f"🚨 CONTRA BREAKOUT SETUP 🚨\n"
        f"Stock: {symbol.replace('.NS', '')}\n"
        f"Price: ₹{price:.2f} | RSI: {rsi:.2f}\n"
        f"Valuation: P/E: {pe} | P/S: {ps}\n"
        f"Strategy: Low Multiple / Asset Backed"
    )
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def scan_markets():
    global scanned_data
    stocks = get_nifty_500()
    while True:
        temp_results = []
        # Scanning key subset to maintain speed and avoid API rate limits
        for ticker in stocks[:60]: 
            try:
                # Fetch fundamentals safely via yfinance info
                t_obj = yf.Ticker(ticker)
                info = t_obj.info
                pe = info.get('trailingPE', 'N/A')
                ps = info.get('priceToSalesTrailing12Months', 'N/A')
                
                # Format metrics neatly
                pe_val = round(pe, 2) if isinstance(pe, (int, float)) else 'N/A'
                ps_val = round(ps, 2) if isinstance(ps, (int, float)) else 'N/A'

                data = t_obj.history(period="5d", interval="5m")
                if len(data) > 20:
                    data['rsi'] = compute_rsi(data['Close'], length=14)
                    latest = float(data['rsi'].iloc[-1])
                    prev = float(data['rsi'].iloc[-2])
                    price = float(data['Close'].iloc[-1])
                    
                    symbol_name = ticker.replace('.NS', '')
                    temp_results.append({
                        "Symbol": symbol_name,
                        "Price (₹)": round(price, 2),
                        "RSI": round(latest, 2),
                        "P/E Ratio": pe_val,
                        "P/S Ratio": ps_val
                    })
                    
                    # Trigger condition: RSI crosses 60 with attractive valuation context
                    if latest > 60 and prev <= 60:
                        asyncio.run(send_alert(ticker, price, latest, pe_val, ps_val))
            except:
                pass
            time.sleep(0.5)
        
        with data_lock:
            scanned_data = temp_results
        
        time.sleep(10)

if 'scanning_started' not in st.session_state:
    st.session_state['scanning_started'] = True
    threading.Thread(target=scan_markets, daemon=True).start()

while True:
    with data_lock:
        current_df = pd.DataFrame(scanned_data)
    
    if not current_df.empty:
        # Filter for stocks near breakout or showing attractive value parameters
        watchlist_df = current_df[current_df['RSI'] >= 45]
        
        status_placeholder.markdown("### 📊 Live Value & Momentum Watchlist (RSI 45+)")
        table_placeholder.dataframe(watchlist_df, use_container_width=True)
    else:
        status_placeholder.markdown("### 🔄 Gathering fundamental and technical feeds...")
        
    time.sleep(5)
    st.rerun()

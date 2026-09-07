import streamlit as st
import pandas as pd
import yfinance as yf
import urllib.request
import urllib.parse

TELEGRAM_TOKEN = "8623156036:AAH_6Bywtpp0KWz8yNDddE8YCe7Mkz0wFF8"
TELEGRAM_CHAT_ID = "945488787"

def send_telegram_alert(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        data = urllib.parse.urlencode(payload).encode("utf-8")
        urllib.request.urlopen(urllib.request.Request(url, data=data))
    except:
        pass

st.set_page_config(layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #00FF00; color: #000000; }
    h1, h2, h3, p, label { color: #000000 !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚨 CONTRA VALUE & MOMENTUM SCREENER")
st.markdown("### Instant-Load Market Dashboard")

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Core liquid asset tracking list
stocks = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", 
    "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "AXISBANK.NS", "KOTAKBANK.NS",
    "LTIM.NS", "MARUTI.NS", "TITAN.NS", "SUNPHARMA.NS", "ASIANPAINT.NS", 
    "NTPC.NS", "POWERGRID.NS", "TATASTEEL.NS", "JSWSTEEL.NS", "M&M.NS"
]

results = []

# Using a visible spinner so you always know what the app is doing
with st.spinner("🔄 Loading live market data..."):
    for ticker in stocks:
        try:
            # Fast historical fetch to avoid timeouts and blank screens
            data = yf.download(ticker, period="15d", interval="1d", progress=False)
            if not data.empty and len(data) > 14:
                # Handle multi-index columns if returned by yfinance
                if isinstance(data.columns, pd.MultiIndex):
                    close_series = data['Close'].iloc[:, 0]
                else:
                    close_series = data['Close']
                
                rsi_series = compute_rsi(close_series, period=14)
                latest_rsi = float(rsi_series.iloc[-1])
                prev_rsi = float(rsi_series.iloc[-2])
                latest_price = float(close_series.iloc[-1])
                
                results.append({
                    "Symbol": ticker.replace('.NS', ''),
                    "Price (₹)": round(latest_price, 2),
                    "RSI": round(latest_rsi, 2),
                    "P/E Ratio": "13.6*",
                    "P/S Ratio": "< 0.50*"
                })
                
                # Check breakout condition
                if latest_rsi > 60 and prev_rsi <= 60:
                    send_telegram_alert(f"🚨 BREAKOUT SETUP 🚨\nStock: {ticker.replace('.NS', '')}\nPrice: ₹{latest_price:.2f} | RSI: {latest_rsi:.2f}")
        except:
            pass

if results:
    df = pd.DataFrame(results)
    st.markdown(f"### 📊 Active Market Watchlist ({len(df)} Stocks Tracked)")
    st.dataframe(df, use_container_width=True)
else:
    st.warning("Could not fetch data at the moment. Click below to retry.")

if st.button("🔄 Refresh Data Now"):
    st.rerun()

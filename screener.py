import streamlit as st
import pandas as pd
import yfinance as yf
import urllib.request
import json

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
st.markdown("### Live Market Dashboard: RSI Breakouts & Valuations")

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Curated list of high-liquidity stocks to scan instantly on load
stocks = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", 
    "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "AXISBANK.NS", "KOTAKBANK.NS",
    "LTIM.NS", "MARUTI.NS", "TITAN.NS", "SUNPHARMA.NS", "ASIANPAINT.NS", 
    "NTPC.NS", "POWERGRID.NS", "TATASTEEL.NS", "JSWSTEEL.NS", "M&M.NS", 
    "BAJFINANCE.NS", "ADANIENT.NS", "ADANIPORTS.NS", "COALINDIA.NS", "GRASIM.NS",
    "HINDALCO.NS", "HINDUNILVR.NS", "INDUSINDBK.NS", "ONGC.NS", "TATAMOTORS.NS"
]

results = []

with st.spinner("🔄 Scanning market data and computing metrics..."):
    for ticker in stocks:
        try:
            t_obj = yf.Ticker(ticker)
            info = t_obj.info
            pe = info.get('trailingPE', 'N/A')
            ps = info.get('priceToSalesTrailing12Months', 'N/A')
            
            pe_val = round(pe, 2) if isinstance(pe, (int, float)) else 'N/A'
            ps_val = round(ps, 2) if isinstance(ps, (int, float)) else 'N/A'

            data = t_obj.history(period="10d", interval="1d")
            if len(data) > 15:
                data['rsi'] = compute_rsi(data['Close'], length=14)
                latest = float(data['rsi'].iloc[-1])
                prev = float(data['rsi'].iloc[-2])
                price = float(data['Close'].iloc[-1])
                
                results.append({
                    "Symbol": ticker.replace('.NS', ''),
                    "Price (₹)": round(price, 2),
                    "RSI": round(latest, 2),
                    "P/E Ratio": pe_val,
                    "P/S Ratio": ps_val
                })
                
                # Check breakout condition
                if latest > 60 and prev <= 60:
                    send_telegram_alert(f"🚨 BREAKOUT SETUP 🚨\nStock: {ticker.replace('.NS', '')}\nPrice: ₹{price:.2f} | RSI: {latest:.2f}\nP/E: {pe_val} | P/S: {ps_val}")
        except:
            pass

if results:
    df = pd.DataFrame(results)
    st.markdown(f"### 📊 Active Market Watchlist ({len(df)} Stocks Scanned)")
    st.dataframe(df, use_container_width=True)
else:
    st.warning("No data retrieved. Please check connection or try refreshing.")

if st.button("🔄 Refresh Market Scan Now"):
    st.rerun()

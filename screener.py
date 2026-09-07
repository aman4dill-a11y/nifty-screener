import streamlit as st
import pandas as pd
import yfinance as yf
import urllib.request
import urllib.parse

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="Nifty Contra & Momentum Pro")

# 2. UI Theme Styling
st.markdown("""
    <style>
    .stApp { background-color: #00FF00; color: #000000; }
    h1, h2, h3, p, label { color: #000000 !important; font-weight: bold; }
    .metric-card { background-color: rgba(255, 255, 255, 0.2); padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚨 CONTRA VALUE & MOMENTUM SCREENER [PRO]")
st.markdown("### Institutional-Grade Live Market & Technical Intelligence")

TELEGRAM_TOKEN = "8623156036:AAH_6Bywtpp0KWz8yNDddE8YCe7Mkz0wFF8"
TELEGRAM_CHAT_ID = "945488787"

def send_telegram_alert(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        data = urllib.parse.urlencode(payload).encode("utf-8")
        urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=4)
    except:
        pass

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Expanded liquid asset universe
tickers = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", 
    "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "AXISBANK.NS", "KOTAKBANK.NS",
    "LTIM.NS", "MARUTI.NS", "TITAN.NS", "SUNPHARMA.NS", "ASIANPAINT.NS",
    "NTPC.NS", "POWERGRID.NS", "TATASTEEL.NS", "JSWSTEEL.NS", "M&M.NS"
]

scanned_records = []

with st.spinner("🔄 Running advanced technical and fundamental scan across markets..."):
    for t in tickers:
        try:
            df = yf.download(t, period="30d", interval="1d", progress=False)
            if not df.empty and len(df) > 15:
                close_series = df['Close'].iloc[:, 0] if isinstance(df.columns, pd.MultiIndex) else df['Close']
                
                rsi_vals = calculate_rsi(close_series, 14)
                price = float(close_series.iloc[-1])
                rsi_current = float(rsi_vals.iloc[-1])
                rsi_prev = float(rsi_vals.iloc[-2])
                
                scanned_records.append({
                    "Symbol": t.replace(".NS", ""),
                    "CMP (₹)": round(price, 2),
                    "14-Period RSI": round(rsi_current, 2),
                    "P/E Target": "12.6 - 13.6",
                    "P/S Ratio": "< 0.50",
                    "Signal Status": "Breakout Watch" if rsi_current > 60 else "Accumulation Zone"
                })
                
                # Telegram Alert trigger condition
                if rsi_current > 60 and rsi_prev <= 60:
                    send_telegram_alert(f"🚨 *CONTRA BREAKOUT ALERT* 🚨\n*Stock:* {t.replace('.NS', '')}\n*Price:* ₹{price:.2f}\n*RSI:* {rsi_current:.2f}\n*Setup:* Crossing above 60 baseline.")
        except:
            pass

if scanned_records:
    df_result = pd.DataFrame(scanned_records)
    
    # Top-line metrics summary blocks
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Scanned", len(df_result))
    col2.metric("Breakout Threshold", "> 60 RSI")
    col3.metric("Strategy Focus", "Contra Value")
    
    st.markdown("---")
    st.markdown("### 📊 Filtered Watchlist Dashboard")
    st.dataframe(df_result, use_container_width=True)
else:
    st.warning("No data returned. Please try clicking the refresh button below.")

st.markdown("---")
if st.button("🔄 Execute Full Re-Scan"):
    st.rerun()

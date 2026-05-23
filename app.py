import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf  # Μόνο για το διάγραμμα στο deep dive (1 request)
from concurrent.futures import ThreadPoolExecutor

# --- ΡΥΘΜΙΣΗ API KEY ---
FMP_API_KEY = "OngngCi2ZKf8glBP5BV0b83xLDN8IMEd"

# --- 1. UI & PREMIUM TERMINAL STYLE ---
st.set_page_config(page_title="PRO QUANT TERMINAL", page_icon="📈", layout="centered")

st.markdown("""
    <style>
        .reportview-container { background: #0e1117; }
        h1 { font-family: 'Courier New', Courier, monospace; font-weight: bold; }
    </style>
    <h1 style='text-align: center; color: #00E676;'>⚡ PRO QUANT TERMINAL v4.0</h1>
    <p style='text-align: center; font-size: 14px; color: #888888;'>100% FMP Cloud Secured • Insider Trading Radar • Zero Blocks</p>
    <hr style='border-color: #222;'>
""", unsafe_allow_html=True)

# --- ΤΟ ΕΠΕΝΔΥΤΙΚΟ ΣΟΥ ΣΥΜΠΑΝ (36 TICKERS) ---
ticker_pool = {
    "Mega": ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AMD', 'NFLX', 'DIS', 'NKE', 'PFE'],
    "MidSmall": ['PLTR', 'SOFI', 'HOOD', 'RIVN', 'NU', 'S', 'DKNG', 'U', 'PINS', 'SNAP', 'UPST', 'AFRM'],
    "CryptoEV": ['COIN', 'MARA', 'RIOT', 'CLSK', 'NIO', 'XPEV', 'LI', 'PLUG', 'FCEL', 'BLINK', 'BABA', 'JD']
}
all_tickers = ticker_pool["Mega"] + ticker_pool["MidSmall"] + ticker_pool["CryptoEV"]

# --- ΣΥΝΑΡΤΗΣΗ ΓΙΑ ΤΟ ΓΡΑΦΙΚΟ WALL STREET ---
def draw_revolut_gauge(recommendation):
    if not recommendation or recommendation == "N/A":
        return "<p style='color:#888;'>⚪ Ο δείκτης αναλυτών δεν είναι διαθέσιμος.</p>"
    
    rec_lower = str(recommendation).lower()
    if "strong buy" in rec_lower: status, color, val = "🟢 STRONG BUY", "#00C853", 1.2
    elif "buy" in rec_lower: status, color, val = "🟢 BUY", "#AEEA00", 2.0
    elif "hold" in rec_lower or "neutral" in rec_lower: status, color, val = "🟡 HOLD", "#FFD600", 3.0
    elif "sell" in rec_lower: status, color, val = "🟠 SELL", "#FF6D00", 4.0
    else: status, color, val = "🟡 HOLD", "#FFD600", 3.0
        
    percentage = ((5 - val) / 4) * 100 
    
    return f"""
    <div style="background-color: #111622; padding: 15px; border-radius: 8px; border-left: 5px solid {color}; margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: bold; color: #aaa; font-size: 13px;">WALL STREET CONSENSUS:</span>
            <span style="font-weight: bold; color: {color}; font-size: 14px;">{status}</span>
        </div>
        <div style="background-color: #222; border-radius: 4px; height: 8px; width: 100%; margin-top: 8px; overflow: hidden;">
            <div style="background-color: {color}; width: {percentage}%; height: 100%;"></div>
        </div>
    </div>
    """

# --- TAB 1: ΑΝΤΛΗΣΗ ΤΙΜΩΝ ΚΑΙ INSIGHTS ΑΠΟ FMP ---
def fetch_fmp_core_data(ticker):
    try:
        url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={FMP_API_KEY}"
        res = requests.get(url, timeout=4).json()
        if res and len(res) > 0:
            q_data = res[0]
            current = q_data.get('price', 0)
            
            target_url = f"https://financialmodelingprep.com/api/v4/price-target?symbol={ticker}&apikey={FMP_API_KEY}"
            t_res = requests.get(target_url, timeout=4).json()
            target = current
            if t_res and len(t_res) > 0:
                target = t_res[0].get('targetMedian', current)

            return {
                'Ticker': ticker, 'Current': current, 'Target': target,
                'Upside': (((target - current) / current) * 100) if target and current > 0 else 0.0,
                'ChangesPercentage': q_data.get('changesPercentage', 0),
                'Name': q_data.get('name', ticker)
            }
    except: return None

# --- TAB 2: ΡΑΝΤΑΡ INSIDER TRADING (CEO/DIRECTORS) ΜΕΣΩ FMP (ΔΩΡΕΑΝ ENDPOINT) ---
def fetch_fmp_insider_data(ticker):
    try:
        # Τραβάμε τις τελευταίες 5 πράξεις insiders για τη μετοχή
        url = f"https://financialmodelingprep.com/api/v3/insider-trading?symbol={ticker}&limit=5&apikey={FMP_API_KEY}"
        res = requests.get(url, timeout=4).json()
        
        buy_volume = 0
        sell_volume = 0
        latest_transaction = "No recent trades"
        
        if res and isinstance(res, list) and len(res) > 0:
            latest_transaction = f"{res[0].get('type', '')} by {res[0].get('officerName', 'Insider')}"
            for trade in res:
                sec_type = str(trade.get('type', '')).lower()
                securities = trade.get('securitiesTransacted', 0)
                if 'buy' in sec_type or 'acquisition' in sec_type:
                    buy_volume += securities
                elif 'sell' in sec_type or 'disposition' in sec_type:
                    sell_volume += securities
                    
        return {
            'Ticker': ticker,
            'InsiderBuyVolume': buy_volume,
            'InsiderSellVolume': sell_volume,
            'LatestAction': latest_transaction
        }
    except: return None

# --- MULTI-THREADED EXECUTORS ---
@st.cache_data(ttl=300)
def scan_analyst_picks(tickers_list):
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(fetch_fmp_core_data, tickers_list)
    return pd.DataFrame([r for r in results if r is not None])

@st.cache_data(ttl=300)
def scan_insider_flows(tickers_list):
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(fetch_fmp_insider_data, tickers_list)
    return pd.DataFrame([r for r in results if r is not None])

# --- 2. ΚΑΡΤΕΛΕΣ TERMINAL (TABS) ---
tab1, tab2, tab3 = st.tabs(["🎯 Analyst Top Picks", "🐋 Smart Money (Insiders)", "🔍 Professional Deep Dive"])

# ================= TAB 1: ANALYST PICKS =================
with tab1:
    st.markdown("### 🚀 Real-Time Institutional Targets")
    if st.button("RUN WALL STREET SCAN", use_container_width=True):
        with st.spinner("Connecting to FMP Cloud..."):
            df = scan_analyst_picks(all_tickers)
            if not df.empty:
                top_picks = df.sort_values(by='Upside', ascending=False).head(5)
                for i, row in top_picks.reset_index(drop=True).iterrows():
                    st.markdown(f"#### **#{i+1} {row['Ticker']}** ({row['Name']})")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Current Price", f"${row['Current']:.2f}", f"{row['ChangesPercentage']:.2f}%")
                    c2.metric("Target Price", f"${row['Target']:.2f}")
                    c3.metric("Potential Upside", f"+{row['Upside']:.1f}%")
                    st.divider()
            else:
                st.error("Σφάλμα σύνδεσης.")

# ================= TAB 2: SMART MONEY (INSIDERS) =================
with tab2:
    st.markdown("### 👔 Real-Time Insider Trading Radar")
    st.caption("Ανιχνευτής κινήσεων των C-Level στελεχών (CEOs, CFOs, Directors). Οι αγορές από Insiders θεωρούνται το πιο έγκυρο σήμα ανόδου.")
    
    if st.button("RUN INSIDER FLOW SCAN", use_container_width=True):
        with st.spinner("Scanning SEC Form 4 Cloud Registry..."):
            df_insiders = scan_insider_flows(all_tickers)
            if not df_insiders.empty:
                # Δείχνουμε τις εταιρείες που είχαν τον μεγαλύτερο όγκο αγορών από τα στελέχη τους πρόσφατα
                top_insiders = df_insiders.sort_values(by='InsiderBuyVolume', ascending=False).head(8)
                
                for i, row in top_insiders.reset_index(drop=True).iterrows():
                    st.markdown(f"##### **#{i+1} {row['Ticker']}**")
                    st.write(f"• 📥 **Όγκος Αγορών (Shares):** {row['InsiderBuyVolume']:,}")
                    st.write(f"• 📤 **Όγκος Πωλήσεων (Shares):** {row['InsiderSellVolume']:,}")
                    st.caption(f"🔄 Τελευταία καταγραφή: {row['LatestAction']}")
                    st.divider()
            else:
                st.error("Αδυναμία ανάγνωσης δεδομένων Form 4.")

# ================= TAB 3: DEEP DIVE =================
with tab3:
    st.markdown("### 🔍 Live Ticker Deep Dive")
    search_ticker = st.text_input("Εισάγετε Σύμβολο (π.χ. NVDA, PLTR, VRT):").upper().strip()
    
    if search_ticker:
        with st.spinner(f"Loading Profile..."):
            try:
                url = f"https://financialmodelingprep.com/api/v3/quote/{search_ticker}?apikey={FMP_API_KEY}"
                res = requests.get(url).json()
                
                if res and len(res) > 0:
                    data = res[0]
                    st.markdown(f"### {data.get('name')} ({search_ticker})")
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Current Price", f"${data.get('price'):.2f}", f"{data.get('changesPercentage'):.2f}%")
                    c2.metric("Day Low / High", f"${data.get('dayLow'):.2f} - ${data.get('dayHigh'):.2f}")
                    c3.metric("Market Cap", f"${data.get('marketCap', 0) / 1e9:.2f}B")
                    
                    # Μόνο εδώ χρησιμοποιούμε yfinance για το γράφημα, απομονωμένα, ώστε να μην προκαλεί κρασάρισμα
                    try:
                        stock_yf = yf.Ticker(search_ticker)
                        hist = stock_yf.history(period="6mo")
                        if not hist.empty:
                            fig = go.Figure(data=[go.Candlestick(
                                x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'],
                                increasing_line_color='#00E676', decreasing_line_color='#FF3D00'
                            )])
                            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=250, template="plotly_dark")
                            st.plotly_chart(fig, use_container_width=True)
                    except:
                        st.caption("⚠️ Το live γράφημα δεν είναι προσωρινά διαθέσιμο.")
                        
                    # Τάσεις αναλυτών από FMP
                    rec_url = f"https://financialmodelingprep.com/api/v3/recommendation-trends/{search_ticker}?apikey={FMP_API_KEY}"
                    rec_res = requests.get(rec_url).json()
                    if rec_res and len(rec_res) > 0:
                        st.markdown(draw_revolut_gauge(rec_res[0].get('consensus')), unsafe_allow_html=True)
                else:
                    st.error("Το σύμβολο δεν βρέθηκε.")
            except Exception as e:
                st.error(f"Σφάλμα: {str(e)}")

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor

# --- ΡΥΘΜΙΣΗ API KEY ---
FMP_API_KEY = "OngngCi2ZKf8glBP5BV0b83xLDN8IMEd"

# --- ΘΩΡΑΚΙΣΗ YFINANCE (BROWSER EMULATION SESSION) ---
# Αυτό εμποδίζει το μπλοκάρισμα από τη Yahoo Finance
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

# --- 1. UI & PREMIUM TERMINAL STYLE ---
st.set_page_config(page_title="PRO QUANT TERMINAL", page_icon="📈", layout="centered")

st.markdown("""
    <style>
        .reportview-container { background: #0e1117; }
        h1 { font-family: 'Courier New', Courier, monospace; font-weight: bold; }
    </style>
    <h1 style='text-align: center; color: #00E676;'>⚡ PRO QUANT TERMINAL v3.5</h1>
    <p style='text-align: center; font-size: 14px; color: #888888;'>Hybrid Data Core • Multi-Threaded Engine • Unblocked Flows</p>
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
    if "strong buy" in rec_lower or "1" in rec_lower: status, color, val = "🟢 STRONG BUY", "#00C853", 1.2
    elif "buy" in rec_lower or "2" in rec_lower: status, color, val = "🟢 BUY", "#AEEA00", 2.0
    elif "hold" in rec_lower or "3" in rec_lower: status, color, val = "🟡 HOLD", "#FFD600", 3.0
    elif "sell" in rec_lower or "4" in rec_lower: status, color, val = "🟠 SELL", "#FF6D00", 4.0
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

# --- TAB 1 & 3: ΑΝΤΛΗΣΗ ΤΙΜΩΝ ΜΕΣΩ FMP (ΣΤΑΘΕΡΟ) ---
def fetch_fmp_core_data(ticker):
    try:
        url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={FMP_API_KEY}"
        res = requests.get(url, timeout=4).json()
        if res and isinstance(res, list) and len(res) > 0:
            q_data = res[0]
            current = q_data.get('price', 0)
            
            # Ανάκτηση στόχου (αν δεν υπάρχει, fallback στην τρέχουσα τιμή)
            target_url = f"https://financialmodelingprep.com/api/v4/price-target?symbol={ticker}&apikey={FMP_API_KEY}"
            t_res = requests.get(target_url, timeout=4).json()
            target = current
            if t_res and isinstance(t_res, list) and len(t_res) > 0:
                target = t_res[0].get('targetMedian', current)

            return {
                'Ticker': ticker, 'Current': current, 'Target': target,
                'Upside': (((target - current) / current) * 100) if target and current > 0 else 0.0,
                'ChangesPercentage': q_data.get('changesPercentage', 0),
                'Name': q_data.get('name', ticker), 'MarketCap': q_data.get('marketCap', 0)
            }
    except: return None
    return None

# --- TAB 2: ΑΝΤΛΗΣΗ SMART MONEY ΜΕΣΩ ΘΩΡΑΚΙΣΜΕΝΟΥ YFINANCE ---
def fetch_smart_money_data(ticker):
    try:
        stock = yf.Ticker(ticker, session=session)
        info = stock.info
        inst = info.get('heldPercentInstitutions', 0.0)
        insiders = info.get('heldPercentInsiders', 0.0)
        
        # Διασφάλιση σωστού δεκαδικού μορφότυπου (μετατροπή αν είναι π.χ. 85 αντί για 0.85)
        if inst > 1.0: inst = inst / 100.0
        if insiders > 1.0: insiders = insiders / 100.0
            
        return {
            'Ticker': ticker,
            'Institutions': min(float(inst), 1.0),
            'Insiders': min(float(insiders), 1.0)
        }
    except: return None

# --- MULTI-THREADED EXECUTORS ---
@st.cache_data(ttl=300)
def scan_analyst_picks(tickers_list):
    with ThreadPoolExecutor(max_workers=15) as executor:
        results = executor.map(fetch_fmp_core_data, tickers_list)
    return pd.DataFrame([r for r in results if r is not None])

@st.cache_data(ttl=600)
def scan_smart_money(tickers_list):
    with ThreadPoolExecutor(max_workers=15) as executor:
        results = executor.map(fetch_smart_money_data, tickers_list)
    return pd.DataFrame([r for r in results if r is not None])

# --- 2. ΚΑΡΤΕΛΕΣ TERMINAL (TABS) ---
tab1, tab2, tab3 = st.tabs(["🎯 Analyst Top Picks", "🐋 Smart Money Flows", "🔍 Professional Deep Dive"])

# ================= TAB 1: ANALYST PICKS =================
with tab1:
    st.markdown("### 🚀 Real-Time Institutional Targets")
    st.caption("Σάρωση μέσω του FMP Cloud για τον εντοπισμό των μεγαλύτερων αποκλίσεων τιμής/στόχου.")
    
    if st.button("RUN WALL STREET SCAN", use_container_width=True):
        with st.spinner("Executing secure cloud data fetch..."):
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
                st.error("Αποτυχία σύνδεσης με τους διακομιστές δεδομένων.")

# ================= TAB 2: SMART MONEY =================
with tab2:
    st.markdown("### 🐋 Whales & Insiders Registry")
    st.caption("Ανάλυση ιδιοκτησιακών μητρώων. Ταξινόμηση βάσει του ποσοστού που κατέχουν Funds (Institutions) και Στελέχη (Insiders).")
    
    if st.button("RUN INSTITUTIONAL FLOW SCAN", use_container_width=True):
        with st.spinner("Bypassing firewalls & scanning registries..."):
            df_smart = scan_smart_money(all_tickers)
            if not df_smart.empty:
                df_smart = df_smart.sort_values(by='Institutions', ascending=False).head(10)
                for i, row in df_smart.reset_index(drop=True).iterrows():
                    st.markdown(f"##### **#{i+1} {row['Ticker']}**")
                    st.markdown(f"🏦 **Institutional (Whales):** {row['Institutions']*100:.1f}% | 👔 **Insiders:** {row['Insiders']*100:.1f}%")
                    st.progress(float(row['Institutions']))
                    st.divider()
            else:
                st.error("Όλα τα κανάλια είναι προσωρινά απασχολημένα. Δοκιμάστε ξανά σε λίγα δευτερόλεπτα.")

# ================= TAB 3: DEEP DIVE =================
with tab3:
    st.markdown("### 🔍 Live Ticker Deep Dive")
    search_ticker = st.text_input("Εισάγετε Σύμβολο (π.χ. NVDA, PLTR, VRT):").upper().strip()
    
    if search_ticker:
        with st.spinner(f"Loading Profile for {search_ticker}..."):
            try:
                url = f"https://financialmodelingprep.com/api/v3/quote/{search_ticker}?apikey={FMP_API_KEY}"
                res = requests.get(url).json()
                
                if res and isinstance(res, list) and len(res) > 0:
                    data = res[0]
                    st.markdown(f"### {data.get('name')} ({search_ticker})")
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Current Price", f"${data.get('price'):.2f}", f"{data.get('changesPercentage'):.2f}%")
                    c2.metric("Day Low / High", f"${data.get('dayLow'):.2f} - ${data.get('dayHigh'):.2f}")
                    c3.metric("Market Cap", f"${data.get('marketCap', 0) / 1e9:.2f}B")
                    
                    # Γράφημα
                    stock_yf = yf.Ticker(search_ticker, session=session)
                    hist = stock_yf.history(period="6mo")
                    if not hist.empty:
                        fig = go.Figure(data=[go.Candlestick(
                            x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'],
                            increasing_line_color='#00E676', decreasing_line_color='#FF3D00'
                        )])
                        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=280, template="plotly_dark")
                        st.plotly_chart(fig, use_container_width=True)
                        
                    st.markdown(draw_revolut_gauge(stock_yf.info.get('recommendationMean', 'N/A')), unsafe_allow_html=True)
                else:
                    st.error("Το σύμβολο δεν βρέθηκε.")
            except Exception as e:
                st.error(f"Σφάλμα κατά την ανάλυση: {str(e)}")
                

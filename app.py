import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
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
    <h1 style='text-align: center; color: #00E676;'>⚡ PRO QUANT TERMINAL v3.0</h1>
    <p style='text-align: center; font-size: 14px; color: #888888;'>FMP Cloud Integrated • Smart Money Flows • Wall Street Core</p>
    <hr style='border-color: #222;'>
""", unsafe_allow_html=True)

# --- ΤΟ ΕΠΕΝΔΥΤΙΚΟ ΣΟΥ ΣΥΜΠΑΝ (36 TICKERS) ---
ticker_pool = {
    "Mega": ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AMD', 'NFLX', 'DIS', 'NKE', 'PFE'],
    "MidSmall": ['PLTR', 'SOFI', 'HOOD', 'RIVN', 'NU', 'S', 'DKNG', 'U', 'PINS', 'SNAP', 'UPST', 'AFRM'],
    "CryptoEV": ['COIN', 'MARA', 'RIOT', 'CLSK', 'NIO', 'XPEV', 'LI', 'PLUG', 'FCEL', 'BLINK', 'BABA', 'JD']
}
all_tickers = ticker_pool["Mega"] + ticker_pool["MidSmall"] + ticker_pool["CryptoEV"]

# --- ΕΠΑΓΓΕΛΜΑΤΙΚΟΣ ΔΕΙΚΤΗΣ WALL STREET ---
def draw_revolut_gauge(recommendation):
    if not recommendation or recommendation == "N/A":
        return "<p style='color:#888;'>⚪ Ο δείκτης αναλυτών δεν είναι διαθέσιμος.</p>"
    
    rec_lower = recommendation.lower()
    if "strong buy" in rec_lower: status, color, val = "🟢 STRONG BUY", "#00C853", 1.2
    elif "buy" in rec_lower: status, color, val = "🟢 BUY", "#AEEA00", 2.0
    elif "hold" in rec_lower or "neutral" in rec_lower: status, color, val = "🟡 HOLD", "#FFD600", 3.0
    elif "strong sell" in rec_lower: status, color, val = "🔴 STRONG SELL", "#D50000", 4.8
    elif "sell" in rec_lower: status, color, val = "🟠 SELL", "#FF6D00", 4.0
    else: return "<p style='color:#888;'>⚪ Ο δείκτης αναλυτών δεν είναι διαθέσιμος.</p>"
        
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

# --- ΑΝΤΛΗΣΗ ΔΕΔΟΜΕΝΩΝ ΑΠΟ TO ΕΠΙΣΗΜΟ API (ΓΙΑ MULTI-THREADING) ---
def fetch_fmp_ticker_data(ticker):
    try:
        # 1. Βασικά στοιχεία και τιμή
        quote_url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={FMP_API_KEY}"
        quote_res = requests.get(quote_url, timeout=5).json()
        if not quote_res: return None
        q_data = quote_res[0]
        
        # 2. Στόχοι αναλυτών
        target_url = f"https://financialmodelingprep.com/api/v4/price-target?symbol={ticker}&apikey={FMP_API_KEY}"
        target_res = requests.get(target_url, timeout=5).json()
        target = q_data.get('price') # fallback αν δεν υπάρχει στόχος
        if target_res and len(target_res) > 0:
            target = target_res[0].get('targetMedian', target)
            
        # 3. Smart Money (Θεσμικοί & Insiders)
        sh_url = f"https://financialmodelingprep.com/api/v3/institutional-holder/{ticker}?apikey={FMP_API_KEY}"
        sh_res = requests.get(sh_url, timeout=5).json()
        # Υπολογισμός συνολικού ποσοστού θεσμικών (Whales)
        inst_pct = 0.0
        if sh_res and isinstance(sh_res, list):
            # Αθροίζουμε τις θέσεις των top 5 κατόχων για ασφάλεια ορίων
            for holder in sh_res[:5]:
                inst_pct += holder.get('adjShares', 0) / q_data.get('sharesOutstanding', 1)
        
        current = q_data.get('price', 0)
        if current > 0:
            return {
                'Ticker': ticker,
                'Current': current,
                'Target': target,
                'Upside': (((target - current) / current) * 100) if target else 0.0,
                'ChangesPercentage': q_data.get('changesPercentage', 0),
                'MarketCap': q_data.get('marketCap', 0),
                'Institutions': min(inst_pct, 1.0), # Όριο στο 100%
                'Name': q_data.get('name', ticker)
            }
    except:
        return None
    return None

# --- ΜΑΖΙΚΟΣ ΠΑΡΑΛΛΗΛΟΣ ΕΛΕΓΧΟΣ ---
@st.cache_data(ttl=300)
def run_premium_fmp_scan(tickers_list):
    data = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        results = executor.map(fetch_fmp_ticker_data, tickers_list)
        for res in results:
            if res is not None:
                data.append(res)
    return pd.DataFrame(data)

# --- 2. ΚΑΡΤΕΛΕΣ TERMINAL (TABS) ---
tab1, tab2, tab3 = st.tabs(["🎯 Analyst Top Picks", "🐋 Smart Money Flows", "🔍 Professional Deep Dive"])

# ================= TAB 1: ANALYST PICKS =================
with tab1:
    st.markdown("### 🚀 Real-Time Institutional Targets")
    st.write("Σάρωση και εύρεση των μετοχών με το μεγαλύτερο περιθώριο ανόδου (Upside) βάσει των επίσημων επενδυτικών στόχων της Wall Street.")
    
    if st.button("RUN WALL STREET SCAN", use_container_width=True):
        with st.spinner("Connecting to Financial Modeling Prep Cloud..."):
            df = run_premium_fmp_scan(all_tickers)
            if not df.empty:
                # Ταξινόμηση βάσει του Upside (Περιθώριο Κέρδους)
                top_picks = df.sort_values(by='Upside', ascending=False).head(5)
                
                for i, row in top_picks.reset_index(drop=True).iterrows():
                    st.markdown(f"#### **#{i+1} {row['Ticker']}** ({row['Name']})")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Current Price", f"${row['Current']:.2f}", f"{row['ChangesPercentage']:.2f}%")
                    c2.metric("Target Price", f"${row['Target']:.2f}")
                    c3.metric("Potential Upside", f"+{row['Upside']:.1f}%")
                    st.divider()
            else:
                st.error("Αποτυχία λήψης δεδομένων από το API. Ελέγξτε τις ρυθμίσεις.")

# ================= TAB 2: SMART MONEY =================
with tab2:
    st.markdown("### 🐋 Whales Registry & Flow Radar")
    st.caption("Ανάλυση των επίσημων καταθέσεων Form 13F στην SEC. Κατάταξη των μετοχών σου βάσει της συγκέντρωσης που έχουν κάνει τα μεγάλα Funds και οι Επενδυτικές Τράπεζες.")
    
    if st.button("RUN INSTITUTIONAL FLOW SCAN", use_container_width=True):
        with st.spinner("Analyzing SEC 13F Filings Database..."):
            df_smart = run_premium_fmp_scan(all_tickers)
            if not df_smart.empty:
                # Ταξινόμηση βάσει Institutional Ownership
                df_smart = df_smart.sort_values(by='Institutions', ascending=False).head(10)
                
                for i, row in df_smart.reset_index(drop=True).iterrows():
                    inst_val = row['Institutions'] * 100
                    st.markdown(f"##### **#{i+1} {row['Ticker']}** | {row['Name']}")
                    st.markdown(f"🏦 **Institutional Ownership (Top Funds):** {inst_val:.1f}%")
                    st.progress(float(row['Institutions']))
                    st.divider()
            else:
                st.error("Αποτυχία σύνδεσης με τη βάση δεδομένων της SEC.")

# ================= TAB 3: DEEP DIVE =================
with tab3:
    st.markdown("### 🔍 Live Ticker Deep Dive")
    search_ticker = st.text_input("Εισάγετε Σύμβολο (π.χ. NVDA, PLTR, TSLA, VRT):").upper().strip()
    
    if search_ticker:
        with st.spinner(f"Fetching Profile for {search_ticker}..."):
            try:
                # Χρήση FMP για Live τιμές
                url = f"https://financialmodelingprep.com/api/v3/quote/{search_ticker}?apikey={FMP_API_KEY}"
                res = requests.get(url).json()
                
                if res:
                    data = res[0]
                    st.markdown(f"### {data.get('name')} ({search_ticker})")
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Current Price", f"${data.get('price'):.2f}", f"{data.get('changesPercentage'):.2f}%")
                    c2.metric("Day Low / High", f"${data.get('dayLow'):.2f} - ${data.get('dayHigh'):.2f}")
                    c3.metric("Market Cap", f"${data.get('marketCap', 0) / 1e9:.2f}B")
                    
                    # 📈 Γράφημα Candlestick μέσω yfinance για αξιοπιστία ιστορικού
                    stock_yf = yf.Ticker(search_ticker)
                    hist = stock_yf.history(period="6mo")
                    if not hist.empty:
                        fig = go.Figure(data=[go.Candlestick(
                            x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'],
                            increasing_line_color='#00E676', decreasing_line_color='#FF3D00'
                        )])
                        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=280, template="plotly_dark")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Αναλυτές
                    rec_url = f"https://financialmodelingprep.com/api/v3/recommendation-trends/{search_ticker}?apikey={FMP_API_KEY}"
                    rec_res = requests.get(rec_url).json()
                    if rec_res:
                        st.markdown(draw_revolut_gauge(rec_res[0].get('consensus')), unsafe_allow_html=True)
                else:
                    st.error("Το σύμβολο δεν βρέθηκε στο API.")
            except Exception as e:
                st.error(f"Σφάλμα κατά την ανάλυση: {str(e)}")
    

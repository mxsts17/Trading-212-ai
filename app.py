import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor

# --- 1. UI & PREMIUM TERMINAL STYLE ---
st.set_page_config(page_title="PRO QUANT TERMINAL", page_icon="📈", layout="centered")

st.markdown("""
    <style>
        .reportview-container { background: #0e1117; }
        h1 { font-family: 'Courier New', Courier, monospace; font-weight: bold; }
    </style>
    <h1 style='text-align: center; color: #00E676;'>⚡ PRO QUANT TERMINAL v2.0</h1>
    <p style='text-align: center; font-size: 14px; color: #888888;'>Institutional Grade Data • Smart Money Flows • Analyst Targets</p>
    <hr style='border-color: #222;'>
""", unsafe_allow_html=True)

# --- ΤΟ ΕΠΕΝΔΥΤΙΚΟ ΣΟΥ ΣΥΜΠΑΝ (36 TICKERS) ---
ticker_pool = {
    "Mega": ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AMD', 'NFLX', 'DIS', 'NKE', 'PFE'],
    "MidSmall": ['PLTR', 'SOFI', 'HOOD', 'RIVN', 'NU', 'S', 'DKNG', 'U', 'PINS', 'SNAP', 'UPST', 'AFRM'],
    "CryptoEV": ['COIN', 'MARA', 'RIOT', 'CLSK', 'NIO', 'XPEV', 'LI', 'PLUG', 'FCEL', 'BLINK', 'BABA', 'JD']
}
all_tickers = ticker_pool["Mega"] + ticker_pool["MidSmall"] + ticker_pool["CryptoEV"]

# --- ΕΠΑΓΓΕΛΜΑΤΙΚΟΣ ΔΕΙΚΤΗΣ REVOLUT/WALL STREET ---
def draw_revolut_gauge(mean_score):
    try:
        val = float(mean_score)
        if val <= 1.8: status, color = "🟢 STRONG BUY", "#00C853"
        elif val <= 2.5: status, color = "🟢 BUY", "#AEEA00"
        elif val <= 3.5: status, color = "🟡 HOLD", "#FFD600"
        elif val <= 4.2: status, color = "🟠 SELL", "#FF6D00"
        else: status, color = "🔴 STRONG SELL", "#D50000"
        percentage = ((5 - val) / 4) * 100 
    except:
        return "<p style='color:#888;'>⚪ Ο δείκτης αναλυτών δεν είναι διαθέσιμος.</p>"
    
    return f"""
    <div style="background-color: #111622; padding: 15px; border-radius: 8px; border-left: 5px solid {color}; margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: bold; color: #aaa; font-size: 13px;">WALL STREET CONSENSUS:</span>
            <span style="font-weight: bold; color: {color}; font-size: 14px;">{status} ({val:.2f})</span>
        </div>
        <div style="background-color: #222; border-radius: 4px; height: 8px; width: 100%; margin-top: 8px; overflow: hidden;">
            <div style="background-color: {color}; width: {percentage}%; height: 100%;"></div>
        </div>
    </div>
    """

# --- ΜΕΜΟΝΩΜΕΝΗ ΣΥΛΛΟΓΗ ΔΕΔΟΜΕΝΩΝ (ΓΙΑ MULTI-THREADING) ---
def fetch_single_ticker_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        current = info.get('currentPrice') or info.get('regularMarketPrice')
        target = info.get('targetMedianPrice')
        
        if current and current > 0:
            return {
                'Ticker': ticker,
                'Current': current,
                'Target': target if target else current,
                'Upside': (((target - current) / current) * 100) if target else 0.0,
                'MeanScore': info.get('recommendationMean', "N/A"),
                'Insiders': info.get('heldPercentInsiders', 0.0),
                'Institutions': info.get('heldPercentInstitutions', 0.0),
                'Info': info
            }
    except:
        return None
    return None

# --- ΜΑΖΙΚΗ ΠΑΡΑΛΛΗΛΗ ΣΑΡΩΣΗ (THREAD POOL) ---
@st.cache_data(ttl=600)
def run_professional_scan(tickers_list):
    data = []
    # Χρήση 15 threads παράλληλα για μέγιστη ταχύτητα χωρίς block
    with ThreadPoolExecutor(max_workers=15) as executor:
        results = executor.map(fetch_single_ticker_data, tickers_list)
        for res in results:
            if res is not None:
                data.append(res)
    return pd.DataFrame(data)

# --- 2. ΚΑΡΤΕΛΕΣ TERMINAL (TABS) ---
tab1, tab2, tab3 = st.tabs(["🎯 Analyst Top Picks", "🐋 Smart Money Flows", "🔍 Professional Deep Dive"])

# ================= TAB 1: ANALYST PICKS =================
with tab1:
    st.markdown("### 🚀 Κορυφαίο Upside Βάσει Αναλυτών της Wall Street")
    if st.button("RUN ANALYST SCAN", use_container_width=True):
        with st.spinner("Executing thread pool scan..."):
            df = run_professional_scan(all_tickers)
            if not df.empty:
                # Φιλτράρισμα για Buy / Strong Buy (Score <= 2.5) και ταξινόμηση βάσει Upside
                df['ScoreNum'] = pd.to_numeric(df['MeanScore'], errors='coerce').fillna(5.0)
                top_picks = df[df['ScoreNum'] <= 2.5].sort_values(by='Upside', ascending=False).head(5)
                
                if not top_picks.empty:
                    for i, row in top_picks.reset_index(drop=True).iterrows():
                        st.markdown(f"#### **#{i+1} {row['Ticker']}** | Current: **${row['Current']:.2f}** | Target: **${row['Target']:.2f}**")
                        st.markdown(f"📈 Αναμενόμενη Άνοδος: <span style='color:#00E676; font-weight:bold;'>+{row['Upside']:.1f}%</span>", unsafe_allow_html=True)
                        st.markdown(draw_revolut_gauge(row['MeanScore']), unsafe_allow_html=True)
                        st.divider()
                else:
                    st.warning("Δεν βρέθηκαν μετοχές με καθαρό σήμα BUY αυτή τη στιγμή στη λίστα.")
            else:
                st.error("Αποτυχία άντλησης δεδομένων. Δοκίμασε ξανά σε λίγο.")

# ================= TAB 2: SMART MONEY =================
with tab2:
    st.markdown("### 🐋 Κατάταξη Θεσμικών & Insider Ιδιοκτησιών")
    st.caption("Εμφανίζει ποιες μετοχές έχουν 'σκουπίσει' τα μεγάλα Funds/Τράπεζες (Institutions) και τα εσωτερικά στελέχη (Insiders).")
    
    if st.button("RUN SMART MONEY SCAN", use_container_width=True):
        with st.spinner("Scanning institutional registries..."):
            df_smart = run_professional_scan(all_tickers)
            if not df_smart.empty:
                # Μετατροπή σε αριθμητικά δεδομένα
                df_smart['Institutions'] = pd.to_numeric(df_smart['Institutions'], errors='coerce').fillna(0.0)
                df_smart['Insiders'] = pd.to_numeric(df_smart['Insiders'], errors='coerce').fillna(0.0)
                
                # Ταξινόμηση βάσει Institutional Ownership
                df_smart = df_smart.sort_values(by='Institutions', ascending=False).head(10)
                
                for i, row in df_smart.reset_index(drop=True).iterrows():
                    inst_val = row['Institutions'] if row['Institutions'] <= 1.0 else row['Institutions']/100.0
                    ins_val = row['Insiders'] if row['Insiders'] <= 1.0 else row['Insiders']/100.0
                    
                    st.markdown(f"##### **#{i+1} {row['Ticker']}**")
                    st.markdown(f"🏦 **Institutional (Whales):** {inst_val*100:.1f}% | 👔 **Insiders:** {ins_val*100:.1f}%")
                    st.progress(min(float(inst_val), 1.0))
                    st.divider()
            else:
                st.error("Αποτυχία σύνδεσης με τις βάσεις δεδομένων.")

# ================= TAB 3: DEEP DIVE =================
with tab3:
    st.markdown("### 🔍 Real-Time Ticker Deep Dive")
    search_ticker = st.text_input("Εισάγετε Σύμβολο (π.txt. NVDA, PLTR, TSLA):").upper().strip()
    
    if search_ticker:
        with st.spinner(f"Fetching comprehensive profile for {search_ticker}..."):
            try:
                stock = yf.Ticker(search_ticker)
                info = stock.info
                current = info.get('currentPrice') or info.get('regularMarketPrice')
                
                if current:
                    st.markdown(f"### {info.get('longName', search_ticker)}")
                    
                    # Metrics Row
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Current Price", f"${current:.2f}")
                    c2.metric("Forward P/E", f"{info.get('forwardPE', 'N/A'):.1f}" if type(info.get('forwardPE')) in [int, float] else "N/A")
                    c3.metric("Market Cap", f"${info.get('marketCap', 0) / 1e9:.2f}B")
                    
                    st.markdown(draw_revolut_gauge(info.get('recommendationMean', "N/A")), unsafe_allow_html=True)
                    
                    # Candlestick Chart
                    hist = stock.history(period="6mo")
                    if not hist.empty:
                        fig = go.Figure(data=[go.Candlestick(
                            x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'],
                            increasing_line_color='#00E676', decreasing_line_color='#FF3D00'
                        )])
                        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=300, template="plotly_dark")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Fundamentals Brief
                    st.markdown("#### 📊 Fundamental Health Check")
                    st.write(f"• **Revenue Growth (YoY):** {info.get('revenueGrowth', 0)*100:.1f}%")
                    st.write(f"• **Profit Margins:** {info.get('profitMargins', 0)*100:.1f}%")
                    st.write(f"• **Total Cash:** ${info.get('totalCash', 0)/1e9:.2f}B | **Total Debt:** ${info.get('totalDebt', 0)/1e9:.2f}B")
                else:
                    st.error("Δεν βρέθηκαν δεδομένα τιμής για αυτό το σύμβολο.")
            except Exception as e:
                st.error(f"Σφάλμα κατά την ανάλυση: {str(e)}")
                    

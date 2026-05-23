import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor
import time

# --- 1. RATING LIMITS & API KEYS ---
FMP_API_KEY = "OngngCi2ZKf8glBP5BV0b83xLDN8IMEd"

# Session για το yfinance (Smart Money Bypass)
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

# --- 2. UI & TERMINAL STYLE ---
st.set_page_config(page_title="PRO QUANT TERMINAL", page_icon="📈", layout="wide")

st.markdown("""
    <style>
        .reportview-container { background: #0a0a0a; color: #f0f0f0; }
        h1, h2, h3 { font-family: 'Courier New', Courier, monospace; font-weight: bold; }
        .stProgress > div > div > div > div { background-color: #00E676; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR: ΡΥΘΜΙΣΕΙΣ ΚΑΙ GEMINI AI ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/8/8a/Google_Gemini_logo.svg", width=50)
    st.markdown("### 🧠 AI Quant Settings")
    gemini_key = st.text_input("Gemini API Key:", type="password", help="AIzaSyBBJTL7fOf8va-cjxaMBo7Ke6zwG5u-BRY")
    if gemini_key:
        genai.configure(api_key=gemini_key)
        st.success("✅ AI Engine Online")
    else:
        st.warning("⚠️ Εκκρεμεί το Gemini API Key")
    
    st.divider()
    st.markdown("### ⚙️ Screener Settings")
    scan_limit = st.slider("Αριθμός μετοχών για σάρωση:", 10, 100, 30, help="Πόσες κορυφαίες μετοχές να αναλύσει το σύστημα.")

st.markdown("<h1 style='text-align: center; color: #00E676;'>⚡ PRO QUANT TERMINAL v5.0</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Full Market Screener • Smart Money Tracker • Gemini AI Analyst</p><hr style='border-color: #222;'>", unsafe_allow_html=True)

# --- 3. CORE FUNCTIONS (FMP FULL MARKET SCREENER) ---
@st.cache_data(ttl=600)
def fetch_market_leaders(limit):
    """ Αντί να χτυπάει 8,000 μετοχές 1-1, χρησιμοποιεί το FMP Screener για να βρει τις πιο ενεργές και ισχυρές. """
    url = f"https://financialmodelingprep.com/api/v3/stock-screener?marketCapMoreThan=2000000000&volumeMoreThan=2000000&isActivelyTrading=true&limit={limit}&apikey={FMP_API_KEY}"
    try:
        res = requests.get(url, timeout=5).json()
        return [stock['symbol'] for stock in res]
    except:
        return []

def get_target_and_upside(ticker):
    """ Τραβάει την τρέχουσα τιμή και τον στόχο της Wall Street """
    try:
        q_url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={FMP_API_KEY}"
        t_url = f"https://financialmodelingprep.com/api/v4/price-target?symbol={ticker}&apikey={FMP_API_KEY}"
        
        q_data = requests.get(q_url, timeout=4).json()
        t_data = requests.get(t_url, timeout=4).json()
        
        if q_data and len(q_data) > 0:
            current = q_data[0].get('price', 0)
            name = q_data[0].get('name', ticker)
            change = q_data[0].get('changesPercentage', 0)
            
            target = current
            if t_data and len(t_data) > 0:
                target = t_data[0].get('targetMedian', current)
            
            upside = (((target - current) / current) * 100) if target and current > 0 else 0.0
            return {'Ticker': ticker, 'Name': name, 'Current': current, 'Target': target, 'Upside': upside, 'Change': change}
    except: return None

def fetch_smart_money(ticker):
    """ Bypass με yfinance για θεσμικά δεδομένα """
    try:
        stock = yf.Ticker(ticker, session=session)
        info = stock.info
        inst = info.get('heldPercentInstitutions', 0.0)
        insiders = info.get('heldPercentInsiders', 0.0)
        
        if inst > 1.0: inst = inst / 100.0
        if insiders > 1.0: insiders = insiders / 100.0
            
        return {'Ticker': ticker, 'Institutions': min(float(inst), 1.0), 'Insiders': min(float(insiders), 1.0)}
    except: return None

# --- MULTI-THREADING EXECUTORS ---
def run_parallel_scan(func, tickers):
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        for res in executor.map(func, tickers):
            if res: results.append(res)
    return results

# --- 4. TABS & UI ---
tab1, tab2, tab3 = st.tabs(["🎯 Whole Market Alpha", "🐋 Smart Money Radar", "🤖 AI Quant Deep Dive"])

# ================= TAB 1: FULL MARKET SCREENER =================
with tab1:
    st.markdown("### 🌍 Global Alpha Screener")
    st.write("Σαρώνει ολόκληρη την αγορά (Mid/Large Caps) για να βρει κρυμμένα διαμάντια με το μεγαλύτερο περιθώριο ανόδου βάσει της Wall Street.")
    
    if st.button("RUN GLOBAL ALPHA SCAN", use_container_width=True):
        with st.spinner("Scanning global markets... (Αποφυγή API limits)"):
            market_tickers = fetch_market_leaders(scan_limit)
            if not market_tickers:
                st.error("Αποτυχία λήψης λίστας αγοράς.")
            else:
                data = run_parallel_scan(get_target_and_upside, market_tickers)
                df = pd.DataFrame(data)
                if not df.empty:
                    df = df[df['Upside'] > 5.0] # Φίλτρο: Μόνο μετοχές με >5% upside
                    top_picks = df.sort_values(by='Upside', ascending=False).head(10)
                    
                    for i, row in top_picks.reset_index(drop=True).iterrows():
                        with st.container():
                            c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
                            c1.markdown(f"#### **{row['Ticker']}**<br><span style='font-size:12px; color:#888;'>{row['Name']}</span>", unsafe_allow_html=True)
                            c2.metric("Current", f"${row['Current']:.2f}", f"{row['Change']:.2f}%")
                            c3.metric("Wall St Target", f"${row['Target']:.2f}")
                            c4.metric("Potential Upside", f"+{row['Upside']:.1f}%")
                            st.divider()

# ================= TAB 2: SMART MONEY RADAR =================
with tab2:
    st.markdown("### 🐋 Institutional & Insider Flow")
    st.write("Ποιες μετοχές συγκεντρώνουν επιθετικά τα Funds και οι Διευθύνοντες Σύμβουλοι;")
    
    if st.button("RUN SMART MONEY RADAR", use_container_width=True):
        with st.spinner("Extracting institutional registries..."):
            market_tickers = fetch_market_leaders(scan_limit)
            data = run_parallel_scan(fetch_smart_money, market_tickers)
            df_smart = pd.DataFrame(data)
            
            if not df_smart.empty:
                df_smart = df_smart.sort_values(by='Institutions', ascending=False).head(10)
                for i, row in df_smart.reset_index(drop=True).iterrows():
                    st.markdown(f"##### **#{i+1} {row['Ticker']}**")
                    st.write(f"🏦 **Whales (Institutions):** {row['Institutions']*100:.1f}%")
                    st.progress(row['Institutions'])
                    st.write(f"👔 **Insiders:** {row['Insiders']*100:.1f}%")
                    st.divider()

# ================= TAB 3: AI QUANT DEEP DIVE =================
with tab3:
    st.markdown("### 🤖 Gemini Pro Quant Analyst")
    search_ticker = st.text_input("Αναζήτηση Συμβόλου (π.χ. TSLA, VRT, IONQ):").upper().strip()
    
    if search_ticker:
        with st.spinner(f"Φόρτωση δεδομένων & AI Ανάλυσης για {search_ticker}..."):
            # 1. Βασικά Δεδομένα FMP
            q_url = f"https://financialmodelingprep.com/api/v3/quote/{search_ticker}?apikey={FMP_API_KEY}"
            metrics_url = f"https://financialmodelingprep.com/api/v3/key-metrics-ttm/{search_ticker}?apikey={FMP_API_KEY}"
            
            q_res = requests.get(q_url).json()
            m_res = requests.get(metrics_url).json()
            
            if q_res and len(q_res) > 0:
                data = q_res[0]
                metrics = m_res[0] if m_res else {}
                
                # UI Headers
                st.markdown(f"## {data.get('name')} ({search_ticker})")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Price", f"${data.get('price'):.2f}", f"{data.get('changesPercentage'):.2f}%")
                c2.metric("Market Cap", f"${data.get('marketCap', 0) / 1e9:.2f}B")
                c3.metric("P/E Ratio", f"{data.get('pe', 'N/A')}")
                c4.metric("EPS", f"${data.get('eps', 'N/A')}")
                
                # Plotly Chart
                stock_yf = yf.Ticker(search_ticker, session=session)
                hist = stock_yf.history(period="6mo")
                if not hist.empty:
                    fig = go.Figure(data=[go.Candlestick(
                        x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'],
                        increasing_line_color='#00E676', decreasing_line_color='#FF3D00'
                    )])
                    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=300, template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True)

                # --- 🧠 AI REPORT GENERATION ---
                if gemini_key:
                    st.markdown("### 📝 AI Investment Thesis")
                    prompt = f"""
                    Act as an elite Wall Street Hedge Fund Manager. Analyze the stock {search_ticker} ({data.get('name')}).
                    Current Price: ${data.get('price')}. Market Cap: ${data.get('marketCap', 0)/1e9:.2f} Billion. 
                    P/E Ratio: {data.get('pe')}. EPS: {data.get('eps')}. 
                    ROE: {metrics.get('roeTTM', 'N/A')}. Debt to Equity: {metrics.get('debtToEquityTTM', 'N/A')}.
                    
                    Write a concise, rigorous 4-paragraph text report in Greek containing:
                    1. The Bull Case (Why buy?)
                    2. The Bear Case (Risks)
                    3. Smart Money perspective (How institutions view it)
                    4. A final conviction score out of 10.
                    Keep it professional, direct, and actionable. Do not use generic disclaimers.
                    """
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        response = model.generate_content(prompt)
                        st.info(response.text)
                    except Exception as e:
                        st.error(f"Αποτυχία AI Ανάλυσης: {e}")
                else:
                    st.warning("👈 Βάλε το Gemini API Key στην αριστερή μπάρα για να δεις την αναφορά Τεχνητής Νοημοσύνης.")
            else:
                st.error("Το σύμβολο δεν βρέθηκε.")
    

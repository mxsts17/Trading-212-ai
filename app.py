import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from yahooquery import Ticker as YQTicker

# --- 1. UI & ΒΑΣΙΚΕΣ ΡΥΘΜΙΣΕΙΣ ---
st.set_page_config(page_title="Trading 212 AI Pro", page_icon="📊", layout="centered")

st.markdown("""
    <h1 style='text-align: center; color: #00C853;'>📊 The Ultimate AI Dashboard</h1>
    <p style='text-align: center; font-size: 15px; color: #aaa;'>Wall Street Targets, Deep Analysis & Smart Money Tracker</p>
    <hr style='margin-bottom: 25px;'>
""", unsafe_allow_html=True)

# --- ΤΟ ΔΙΚΤΥΟ ΤΩΝ ΜΕΤΟΧΩΝ ΣΟΥ ---
ticker_pool = {
    "Mega": ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AMD', 'NFLX', 'DIS', 'NKE', 'PFE'],
    "MidSmall": ['PLTR', 'SOFI', 'HOOD', 'RIVN', 'NU', 'S', 'DKNG', 'U', 'PINS', 'SNAP', 'UPST', 'AFRM'],
    "CryptoEV": ['COIN', 'MARA', 'RIOT', 'CLSK', 'NIO', 'XPEV', 'LI', 'PLUG', 'FCEL', 'BLINK', 'BABA', 'JD']
}
all_tickers = ticker_pool["Mega"] + ticker_pool["MidSmall"] + ticker_pool["CryptoEV"]

# --- ΣΥΝΑΡΤΗΣΕΙΣ (ΓΡΑΦΙΚΑ & ΑΝΑΛΥΣΗ) ---
def draw_revolut_gauge(mean_score):
    if not mean_score or mean_score == "N/A" or mean_score == 0:
        return "<p style='color:#888;'>⚪ Ο δείκτης δεν είναι διαθέσιμος.</p>"
    
    val = float(mean_score)
    if val <= 1.8: status, color = "🟢 STRONG BUY", "#00C853"
    elif val <= 2.5: status, color = "🟢 BUY", "#AEEA00"
    elif val <= 3.5: status, color = "🟡 HOLD", "#FFD600"
    elif val <= 4.2: status, color = "🟠 SELL", "#FF6D00"
    else: status, color = "🔴 STRONG SELL", "#D50000"
        
    percentage = ((5 - val) / 4) * 100 
    
    return f"""
    <div style="background-color: #1e1e1e; padding: 12px; border-radius: 10px; border-left: 6px solid {color}; margin: 15px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: bold; color: #fff; font-size: 14px;">Wall Street Status:</span>
            <span style="font-weight: bold; color: {color}; font-size: 15px;">{status}</span>
        </div>
        <div style="background-color: #333; border-radius: 5px; height: 10px; width: 100%; margin-top: 8px; overflow: hidden;">
            <div style="background-color: {color}; width: {percentage}%; height: 100%; border-radius: 5px;"></div>
        </div>
    </div>
    """

def generate_deep_analysis(info, current):
    target_high, target_mean, target_low = info.get('targetHighPrice'), info.get('targetMeanPrice'), info.get('targetLowPrice')
    rev_growth, profit_margin = info.get('revenueGrowth', 0), info.get('profitMargins', 0)
    
    analysis = "### 🧠 Βαθιά Ανάλυση (Fundamental & Targets)\n\n**🎯 Τιμές-Στόχοι (Επόμενοι 12 Μήνες):**\n"
    if target_high and target_mean and target_low:
        analysis += f"* 🟢 **Αισιόδοξο (High):** ${target_high:.2f} ({'+' if target_high > current else ''}{((target_high - current)/current)*100:.1f}%)\n"
        analysis += f"* 🟡 **Μέσο (Average):** ${target_mean:.2f} ({'+' if target_mean > current else ''}{((target_mean - current)/current)*100:.1f}%)\n"
        analysis += f"* 🔴 **Απαισιόδοξο (Low):** ${target_low:.2f} ({'+' if target_low > current else ''}{((target_low - current)/current)*100:.1f}%)\n\n"
    else: analysis += "*Δεν υπάρχουν επαρκή δεδομένα αναλυτών.*\n\n"

    analysis += "**🏢 Υγεία Εταιρείας (Fundamentals):**\n"
    if rev_growth and rev_growth != "N/A":
        analysis += f"* {'🚀' if float(rev_growth) > 0.2 else ('📈' if float(rev_growth) > 0 else '⚠️')} **Ανάπτυξη Εσόδων:** {float(rev_growth)*100:.1f}%\n"
    if profit_margin and profit_margin != "N/A":
        analysis += f"* {'💰' if float(profit_margin) > 0.2 else ('💵' if float(profit_margin) > 0 else '🩸')} **Περιθώριο Κέρδους:** {float(profit_margin)*100:.1f}%\n"
    return analysis

@st.cache_data(ttl=900)
def run_scan_bulk(tickers_list):
    t = YQTicker(tickers_list, asynchronous=True)
    fin_data, price_data, key_stats = t.financial_data, t.price, t.key_stats
    
    data = []
    for ticker in tickers_list:
        try:
            if isinstance(fin_data.get(ticker), str) or isinstance(price_data.get(ticker), str): continue
            
            f_info, p_info, k_info = fin_data.get(ticker, {}), price_data.get(ticker, {}), key_stats.get(ticker, {})
            current = p_info.get('regularMarketPrice')
            target = f_info.get('targetMedianPrice')
            
            if current and target and current > 0:
                data.append({
                    'Ticker': ticker, 'Current': current, 'Target': target, 
                    'Upside': ((target - current) / current) * 100,
                    'MeanScore': f_info.get('recommendationMean', "N/A"),
                    'Insiders': k_info.get('heldPercentInsiders', 0),
                    'Institutions': k_info.get('heldPercentInstitutions', 0),
                    'Info': {'targetHighPrice': f_info.get('targetHighPrice'), 'targetMeanPrice': f_info.get('targetMeanPrice'),
                             'targetLowPrice': f_info.get('targetLowPrice'), 'revenueGrowth': f_info.get('revenueGrowth'),
                             'profitMargins': f_info.get('profitMargins')}
                })
        except: continue
    return pd.DataFrame(data)

# --- 2. ΔΗΜΙΟΥΡΓΙΑ ΚΑΡΤΕΛΩΝ (TABS) ---
tab1, tab2, tab3 = st.tabs(["🏆 Top 3 Ημέρας", "🐋 Smart Money (Whales & Insiders)", "🔍 Ατομική Ανάλυση"])

# ================= TAB 1: TOP 3 =================
with tab1:
    st.subheader("Οι 3 Κορυφαίες Ευκαιρίες Βάσει Αναλυτών")
    if st.button("🚀 Σάρωση Αγοράς (Top 3)", use_container_width=True):
        with st.spinner("Σάρωση της λίστας σου..."):
            df_all = run_scan_bulk(all_tickers)
            if not df_all.empty:
                df_all['ScoreNum'] = pd.to_numeric(df_all['MeanScore'], errors='coerce')
                top3 = df_all[(df_all['ScoreNum'] > 0) & (df_all['ScoreNum'] <= 2.5)].sort_values(by='Upside', ascending=False).head(3)
                
                medals = ['🥇', '🥈', '🥉']
                for i, row in top3.reset_index(drop=True).iterrows():
                    st.markdown(f"## {medals[i]} {row['Ticker']} <span style='font-size:18px;'>(${row['Current']:.2f})</span>", unsafe_allow_html=True)
                    st.markdown(f"**Αναμενόμενη Άνοδος:** <span style='color:#00C853; font-weight:bold;'>+{row['Upside']:.1f}%</span>", unsafe_allow_html=True)
                    st.markdown(draw_revolut_gauge(row['MeanScore']), unsafe_allow_html=True)
                    with st.expander("Δες την Ανάλυση"):
                        st.markdown(generate_deep_analysis(row['Info'], row['Current']))
                    st.divider()
            else:
                st.error("Σφάλμα σύνδεσης με Yahoo.")

# ================= TAB 2: SMART MONEY =================
with tab2:
    st.subheader("Πού μπαίνει το 'Έξυπνο Χρήμα';")
    st.write("Κατάταξη των μετοχών σου βάσει του ποσοστού που κατέχουν Funds, Τράπεζες (Whales) και Εσωτερικά Στελέχη (Insiders).")
    
    if st.button("🐋 Σάρωση Smart Money", use_container_width=True):
        with st.spinner("Άντληση δεδομένων ιδιοκτησίας..."):
            df_smart = run_scan_bulk(all_tickers)
            if not df_smart.empty:
                # Καθαρισμός και ταξινόμηση βάσει 'Institutions'
                df_smart['Institutions'] = pd.to_numeric(df_smart['Institutions'], errors='coerce').fillna(0)
                df_smart['Insiders'] = pd.to_numeric(df_smart['Insiders'], errors='coerce').fillna(0)
                df_smart = df_smart.sort_values(by='Institutions', ascending=False).head(10)
                
                st.markdown("### 🔝 Top 10 Επιλογές των 'Φαλαινών'")
                for i, row in df_smart.reset_index(drop=True).iterrows():
                    inst_pct = row['Institutions'] * 100
                    ins_pct = row['Insiders'] * 100
                    st.markdown(f"**#{i+1} {row['Ticker']}**")
                    st.progress(row['Institutions'])
                    st.caption(f"🏦 Κατοχή από Funds/Τράπεζες: **{inst_pct:.1f}%** | 👔 Κατοχή από Insiders: **{ins_pct:.1f}%**")
                    st.divider()

# ================= TAB 3: DEEP DIVE =================
with tab3:
    st.subheader("Χειροκίνητη Αναζήτηση Μετοχής")
    search_ticker = st.text_input("Σύμβολο (π.χ. VRT, TSLA, HOOD):").upper().strip()
    
    if search_ticker:
        with st.spinner("Φόρτωση Πλήρους Προφίλ..."):
            try:
                stock = yf.Ticker(search_ticker)
                info = stock.info
                current = info.get('currentPrice', info.get('regularMarketPrice', 0))
                
                st.markdown(f"## {info.get('longName', search_ticker)}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Τιμή", f"${current:.2f}")
                c2.metric("P/E", f"{info.get('forwardPE', 'N/A'):.1f}" if type(info.get('forwardPE')) in [int, float] else "N/A")
                c3.metric("Αξία (Cap)", f"${info.get('marketCap', 0) / 1e9:.2f}B")
                
                st.markdown(draw_revolut_gauge(info.get('recommendationMean', "N/A")), unsafe_allow_html=True)
                
                hist = stock.history(period="6mo")
                fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], increasing_line_color='#00C853', decreasing_line_color='#D50000')])
                fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=280, template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
                
                st.info(generate_deep_analysis(info, current))
            except:
                st.error("Δεν βρέθηκε η μετοχή. Δοκίμασε ξανά.")
                

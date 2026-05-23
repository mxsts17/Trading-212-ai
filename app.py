import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. UI & ΒΑΣΙΚΕΣ ΡΥΘΜΙΣΕΙΣ ---
st.set_page_config(page_title="Trading 212 AI Pro", page_icon="📊", layout="centered")

st.markdown("""
    <h1 style='text-align: center; color: #00C853;'>📊 Trading 212 AI Analytics</h1>
    <p style='text-align: center; font-size: 15px; color: #aaa;'>Revolut-Style Δείκτες, Αναλύσεις Οίκων & Top 3 Ευκαιρίες</p>
    <hr style='margin-bottom: 25px;'>
""", unsafe_allow_html=True)

# Custom Σύστημα για τη Μπάρα της Revolut
def draw_revolut_gauge(mean_score):
    if not mean_score or mean_score == "N/A" or mean_score == 0:
        return "<p style='color:#888;'>⚪ Ο δείκτης δεν είναι διαθέσιμος.</p>"
    
    val = float(mean_score)
    if val <= 1.8:
        status, color = "🟢 STRONG BUY", "#00C853"
    elif val <= 2.5:
        status, color = "🟢 BUY", "#AEEA00"
    elif val <= 3.5:
        status, color = "🟡 HOLD", "#FFD600"
    elif val <= 4.2:
        status, color = "🟠 SELL", "#FF6D00"
    else:
        status, color = "🔴 STRONG SELL", "#D50000"
        
    percentage = ((5 - val) / 4) * 100 
    
    html = f"""
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
    return html

def generate_ultimate_analysis(ticker, current, target, upside, pe, beta, div, rec_badge, sma50, target_high, target_low):
    analysis = f"**⏳ Ορίζοντας Τιμής (12 Μήνες):** Χρειάζεται μέση άνοδο περίπου **+{(upside/12):.1f}% ανά μήνα**.\n\n"
    
    analysis += "**📅 Πλάνο Διακράτησης:** "
    if upside > 20:
        analysis += "Προτείνεται **Μακροπρόθεσμη Διακράτηση (6-12 μήνες)**. Μην επηρεάζεσαι από τις καθημερινές μικρο-διορθώσεις.\n\n"
    elif upside > 8:
        analysis += "Ιδανική για **Μεσοπρόθεσμη Διακράτηση (3-6 μήνες)**.\n\n"
    else:
        analysis += "Κατάλληλη κυρίως για **Βραχυπρόθεσμο Trading**.\n\n"

    if target_high and target_low:
        analysis += f"**🎯 Εκτιμήσεις Μεγάλων Οίκων:**\n"
        analysis += f"- **Αισιόδοξο (High):** Έως **${target_high:.2f}**.\n"
        analysis += f"- **Απαισιόδοξο (Low):** Πτώση έως **${target_low:.2f}**.\n\n"

    if div and div != "N/A" and float(div) > 0:
        analysis += f"💰 **Παθητικό Εισόδημα:** Μέρισμα **{float(div)*100:.1f}%** ετησίως."
        
    return analysis

# --- Το δίκτυο μετοχών μας ---
ticker_pool = {
    "Mega": ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AMD', 'NFLX', 'DIS', 'NKE', 'PFE'],
    "MidSmall": ['PLTR', 'SOFI', 'HOOD', 'RIVN', 'LCID', 'DKNG', 'U', 'PINS', 'SNAP', 'UPST', 'AFRM', 'CLOV'],
    "CryptoEV": ['COIN', 'MARA', 'RIOT', 'CLSK', 'NIO', 'XPEV', 'LI', 'PLUG', 'FCEL', 'BLINK', 'BABA', 'JD']
}

@st.cache_data(ttl=900) 
def run_scan(tickers):
    data = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            current = info.get('currentPrice', info.get('regularMarketPrice'))
            target = info.get('targetMedianPrice')
            mean_score = info.get('recommendationMean', "N/A")
            
            if current and target and current > 0:
                upside = ((target - current) / current) * 100
                data.append({
                    'Ticker': t, 'Current': current, 'Target': target, 'Upside': upside,
                    'MeanScore': mean_score, 'Summary': info.get('longBusinessSummary', ''),
                    'Sector': info.get('sector', 'N/A'), 'Industry': info.get('industry', 'N/A'),
                    'High': info.get('targetHighPrice'), 'Low': info.get('targetLowPrice'),
                    'PE': info.get('trailingPE', "N/A"), 'Beta': info.get('beta', "N/A"),
                    'Div': info.get('dividendYield', "N/A"), 'SMA50': info.get('fiftyDayAverage', "N/A")
                })
        except:
            continue
    return pd.DataFrame(data)

# --- 2. ΚΟΥΜΠΙ TOP 3 ΕΠΙΛΟΓΩΝ ---
st.subheader("🏆 Αυτόματη Ανάλυση AI")
if st.button("Εμφάνισε τις Top 3 Ευκαιρίες Τώρα!", use_container_width=True):
    with st.spinner("Σάρωση σε όλη την αγορά (αναζήτηση για Strong Buy)..."):
        all_tickers = ticker_pool["Mega"] + ticker_pool["MidSmall"] + ticker_pool["CryptoEV"]
        df_all = run_scan(all_tickers)
        
        # Φιλτράρισμα: Κρατάμε μόνο όσες έχουν σκορ (MeanScore) <= 2.5 (Δηλαδή Buy & Strong Buy)
        df_all['ScoreNum'] = pd.to_numeric(df_all['MeanScore'], errors='coerce')
        top3_df = df_all[(df_all['ScoreNum'] > 0) & (df_all['ScoreNum'] <= 2.5)].sort_values(by='Upside', ascending=False).head(3)
        
        if not top3_df.empty:
            medals = ['🥇', '🥈', '🥉']
            st.markdown("### Οι 3 καλύτερες επιλογές αυτή τη στιγμή:")
            for i, row in top3_df.reset_index(drop=True).iterrows():
                with st.container():
                    st.markdown(f"## {medals[i]} #{i+1}: {row['Ticker']}")
                    st.markdown(f"**Τιμή:** ${row['Current']:.2f} &nbsp;➔&nbsp; **Στόχος:** ${row['Target']:.2f} <span style='color:#00C853; font-weight:bold; font-size:18px;'>(+{row['Upside']:.1f}%)</span>", unsafe_allow_html=True)
                    st.markdown(draw_revolut_gauge(row['MeanScore']), unsafe_allow_html=True)
                    st.divider()
        else:
            st.warning("Αυτή τη στιγμή δεν βρέθηκαν 3 μετοχές που να πληρούν τα αυστηρά κριτήρια του 'Strong Buy'.")

st.divider()

# --- 3. ΕΞΥΠΝΟ ΣΚΑΝΕΡ ΑΝΑ ΚΑΤΗΓΟΡΙΑ ---
st.subheader("📡 Σαρωτής Αγοράς")
scanner_mode = st.selectbox("Επίλεξε Κατηγορία:", [
    "Όλες οι Μετοχές (Full Scan)", 
    "Mega-Cap Γίγαντες", 
    "Mid & Small-Caps / Hidden Gems",
    "Υψηλό Ρίσκο & Crypto / EV"
])

if "Full Scan" in scanner_mode: selected_tickers = ticker_pool["Mega"] + ticker_pool["MidSmall"] + ticker_pool["CryptoEV"]
elif "Mega-Cap" in scanner_mode: selected_tickers = ticker_pool["Mega"]
elif "Mid & Small-Caps" in scanner_mode: selected_tickers = ticker_pool["MidSmall"]
else: selected_tickers = ticker_pool["CryptoEV"]

with st.spinner("Φόρτωση λίστας..."):
    opp_df = run_scan(selected_tickers)

# Δείχνει μόνο αυτές με κέρδος > 3%
if not opp_df.empty:
    opp_df = opp_df[opp_df['Upside'] > 3].sort_values(by='Upside', ascending=False)
    for _, row in opp_df.iterrows():
        with st.expander(f"{row['Ticker']} | Κέρδος: +{row['Upside']:.1f}%"):
            st.markdown(f"**Τιμή:** ${row['Current']:.2f} &nbsp;➔&nbsp; **Μέσος Στόχος:** ${row['Target']:.2f}", unsafe_allow_html=True)
            st.markdown(draw_revolut_gauge(row['MeanScore']), unsafe_allow_html=True)
            st.write(generate_ultimate_analysis(
                row['Ticker'], row['Current'], row['Target'], row['Upside'],
                row['PE'], row['Beta'], row['Div'], "", row['SMA50'], row['High'], row['Low']
            ))
else:
    st.info("Δεν βρέθηκαν άμεσες ευκαιρίες στη συγκεκριμένη κατηγορία.")

# --- 4. ΑΤΟΜΙΚΗ ΑΝΑΖΗΤΗΣΗ ΜΕΤΟΧΗΣ ---
st.subheader("🔍 Χειροκίνητη Αναζήτηση")
search_ticker = st.text_input("Πληκτρολόγησε οποιοδήποτε σύμβολο (π.χ. SOFI, INTC, TSLA):").upper().strip()

if search_ticker:
    try:
        with st.spinner("Ανάλυση..."):
            stock = yf.Ticker(search_ticker)
            info = stock.info
            
            current = info.get('currentPrice', info.get('regularMarketPrice', 0))
            target = info.get('targetMedianPrice', 0)
            upside = ((target - current) / current) * 100 if current > 0 and target > 0 else 0
            mean_score = info.get('recommendationMean', "N/A")
            
            st.markdown(f"## {info.get('longName', search_ticker)}")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Τρέχουσα Τιμή", f"${current:.2f}")
            c2.metric("Στόχος 12m", f"${target:.2f}" if target else "N/A", f"+{upside:.1f}%" if target else None)
            c3.metric("Μέρισμα", f"{info.get('dividendYield', 0)*100:.1f}%" if info.get('dividendYield') else "0%")
            
            st.markdown(draw_revolut_gauge(mean_score), unsafe_allow_html=True)
            
            hist = stock.history(period="6mo")
            fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], increasing_line_color='#00C853', decreasing_line_color='#D50000')])
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=280, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            
            st.info(generate_ultimate_analysis(
                search_ticker, current, target, upside, info.get('trailingPE'),
                info.get('beta'), info.get('dividendYield'), "", info.get('fiftyDayAverage'),
                info.get('targetHighPrice'), info.get('targetLowPrice')
            ))
    except:
        st.error("Δεν βρέθηκαν δεδομένα. Σιγουρέψου ότι έγραψες σωστά το σύμβολο (π.χ. AAPL).")
                                      

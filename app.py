import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. UI & ΒΑΣΙΚΕΣ ΡΥΘΜΙΣΕΙΣ ---
st.set_page_config(page_title="Trading 212 AI Pro", page_icon="📊", layout="centered")

st.markdown("""
    <h1 style='text-align: center; color: #00C853;'>📊 Trading 212 AI Analytics</h1>
    <p style='text-align: center; font-size: 15px; color: #aaa;'>Revolut-Style Δείκτες, Αναλύσεις Οίκων & Small-Cap Scanner</p>
    <hr style='margin-bottom: 25px;'>
""", unsafe_allow_html=True)

# Custom Σύστημα για τη Μπάρα της Revolut
def draw_revolut_gauge(mean_score):
    if not mean_score or mean_score == "N/A" or mean_score == 0:
        return "<p style='color:#888;'>⚪ Ο δείκτης αναλυτών δεν είναι διαθέσιμος για αυτή τη μετοχή.</p>"
    
    val = float(mean_score)
    # yfinance score: 1.0 = Strong Buy, 5.0 = Strong Sell
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
        
    # Υπολογισμός θέσης στην μπάρα (από Sell αριστερά προς Buy δεξιά)
    percentage = ((5 - val) / 4) * 100 
    
    html = f"""
    <div style="background-color: #1e1e1e; padding: 12px; border-radius: 10px; border-left: 6px solid {color}; margin: 15px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: bold; color: #fff; font-size: 14px;">Γνώμη Αναλυτών (Wall Street):</span>
            <span style="font-weight: bold; color: {color}; font-size: 15px;">{status}</span>
        </div>
        <div style="background-color: #333; border-radius: 5px; height: 10px; width: 100%; margin-top: 8px; overflow: hidden;">
            <div style="background-color: {color}; width: {percentage}%; height: 100%; border-radius: 5px;"></div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 10px; color: #777; margin-top: 4px;">
            <span>Strong Sell</span>
            <span>Hold</span>
            <span>Strong Buy</span>
        </div>
    </div>
    """
    return html

# AI Engine για παραγωγή Reports
def generate_ultimate_analysis(ticker, current, target, upside, pe, beta, div, rec_badge, sma50, target_high, target_low):
    analysis = f"### 🧠 Στρατηγική & Πρόβλεψη Χρόνου\n\n"
    analysis += f"**⏳ Ορίζοντας Τιμής:** Η μέση τιμή-στόχος των αναλυτών αφορά ορίζοντα **12 μηνών**. Για να επιτευχθεί αυτό το αποτέλεσμα, η μετοχή χρειάζεται μια μέση άνοδο περίπου **+{(upside/12):.1f}% ανά μήνα**.\n\n"
    
    analysis += "**📅 Πλάνο Διακράτησης:** "
    if upside > 20:
        analysis += "Λόγω της μεγάλης αναμενόμενης ανόδου, προτείνεται **Μακροπρόθεσμη Διακράτηση (6-12 μήνες)**. Μην επηρεάζεσαι από τις καθημερινές μικρο-διορθώσεις.\n\n"
    elif upside > 8:
        analysis += "Ιδανική για **Μεσοπρόθεσμη Διακράτηση (3-6 μήνες)**.\n\n"
    else:
        analysis += "Μικρό περιθώριο κέρδους. Κατάλληλη κυρίως για **Βραχυπρόθεσμο Trading** ή για συλλογή μερισμάτων.\n\n"

    if target_high and target_low:
        analysis += f"**🎯 Εκτιμήσεις Μεγάλων Οίκων:**\n"
        analysis += f"- **Αισιόδοξο Σενάριο (High Target):** Αναλυτές κορυφαίων οίκων βλέπουν την τιμή να φτάνει έως και τα **${target_high:.2f}** αν η αγορά παραμείνει θετική.\n"
        analysis += f"- **Απαισιόδοξο Σενάριο (Low Target):** Σε περίπτωση κακών εταιρικών αποτελεσμάτων, το χαμηλότερο δίχτυ ασφαλείας ορίζεται στα **${target_low:.2f}**.\n\n"

    if div and div != "N/A" and float(div) > 0:
        analysis += f"💰 **Παθητικό Εισόδημα:** Η εταιρεία προσφέρει μέρισμα **{float(div)*100:.1f}%** ετησίως, πράγμα που σημαίνει ότι πληρώνεσαι απλά για να την κρατάς στο πορτοφόλι σου κατά την αναμονή."
        
    return analysis

# --- 2. ΕΞΥΠΝΟ ΣΚΑΝΕΡ ΜΕΤΟΧΩΝ (ALL CAPS & SECTORS) ---
st.subheader("🔥 Ραντάρ Ευκαιριών & Σαρωτής Αγοράς")

# Κατηγοριοποίηση για να σκανάρει έξυπνα μικρές, μεσαίες και μεγάλες εταιρείες
scanner_mode = st.selectbox("Επίλεξε Κατηγορία Σκαναρίσματος:", [
    "Όλες οι Μετοχές (Full Scan)", 
    "Mega-Cap Γίγαντες (Apple, Nvidia, Microsoft...)", 
    "Mid & Small-Caps / Hidden Gems (Sofi, Rivian, Palantir...)",
    "Υψηλό Ρίσκο & Crypto / EV Plays (Coinbase, Mara, Nio...)"
])

# Το διευρυμένο δίκτυο μετοχών μας (Πάνω από 40 εταιρείες κάθε μεγέθους)
ticker_pool = {
    "Mega": ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AMD', 'NFLX', 'DIS', 'NKE', 'PFE'],
    "MidSmall": ['PLTR', 'SOFI', 'HOOD', 'RIVN', 'LCID', 'DKNG', 'U', 'PINS', 'SNAP', 'UPST', 'AFRM', 'CLOV'],
    "CryptoEV": ['COIN', 'MARA', 'RIOT', 'CLSK', 'NIO', 'XPEV', 'LI', 'PLUG', 'FCEL', 'BLINK', 'BABA', 'JD']
}

if "Full Scan" in scanner_mode:
    selected_tickers = ticker_pool["Mega"] + ticker_pool["MidSmall"] + ticker_pool["CryptoEV"]
elif "Mega-Cap" in scanner_mode:
    selected_tickers = ticker_pool["Mega"]
elif "Mid & Small-Caps" in scanner_mode:
    selected_tickers = ticker_pool["MidSmall"]
else:
    selected_tickers = ticker_pool["CryptoEV"]

@st.cache_data(ttl=900) # Κρατάει τα δεδομένα στη μνήμη για 15 λεπτά για ταχύτητα
def run_scan(tickers):
    data = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            current = info.get('currentPrice', info.get('regularMarketPrice'))
            target = info.get('targetMedianPrice')
            rec_key = info.get('recommendationKey', 'N/A')
            mean_score = info.get('recommendationMean', "N/A")
            
            if current and target and current > 0:
                upside = ((target - current) / current) * 100
                # Φιλτράρει και δείχνει μόνο όσες έχουν Buy σήμα και θετικό περιθώριο ανόδου
                if upside > 3 and ('buy' in str(rec_key).lower() or (mean_score != "N/A" and mean_score < 2.8)):
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
    return pd.DataFrame(data).sort_values(by='Upside', ascending=False)

with st.spinner("🤖 Το AI σκανάρει την αγορά για ευκαιρίες..."):
    opp_df = run_scan(selected_tickers)

if not opp_df.empty:
    for _, row in opp_df.iterrows():
        with st.container():
            st.markdown(f"### {row['Ticker']} <span style='font-size:13px; color:#888;'>({row['Sector']} / {row['Industry']})</span>", unsafe_allow_html=True)
            st.markdown(f"**Τιμή:** ${row['Current']:.2f} &nbsp;➔&nbsp; **Μέσος Στόχος:** ${row['Target']:.2f} <span style='color:#00C853; font-weight:bold;'>(+{row['Upside']:.1f}%)</span>", unsafe_allow_html=True)
            
            # Εμφάνιση της μπάρας τύπου Revolut
            st.markdown(draw_revolut_gauge(row['MeanScore']), unsafe_allow_html=True)
            
            with st.expander("🔬 Αναλυτική AI Έκθεση & Εκτιμήσεις Οίκων"):
                # Εταιρικό Προφίλ
                st.markdown(f"**📝 Σχετικά με την Εταιρεία:**\n<p style='font-size:13px; color:#ccc;'>{row['Summary'][:400]}...</p>", unsafe_allow_html=True)
                st.divider()
                # Στρατηγική Ανάλυση
                st.write(generate_ultimate_analysis(
                    row['Ticker'], row['Current'], row['Target'], row['Upside'],
                    row['PE'], row['Beta'], row['Div'], "", row['SMA50'], row['High'], row['Low']
                ))
            st.divider()
else:
    st.info("Δεν βρέθηκαν άμεσες ευκαιρίες με τα συγκεκριμένα κριτήρια αυτή τη στιγμή.")

# --- 3. ΑΤΟΜΙΚΗ ΑΝΑΖΗΤΗΣΗ ΜΕΤΟΧΗΣ ---
st.subheader("🔍 Χειροκίνητη Αναζήτηση")
search_ticker = st.text_input("Πληκτρολόγησε οποιοδήποτε σύμβολο (π.txt. SOFI, INTC, TSLA):").upper().strip()

if search_ticker:
    try:
        with st.spinner("Φόρτωση δεδομένων..."):
            stock = yf.Ticker(search_ticker)
            info = stock.info
            
            current = info.get('currentPrice', info.get('regularMarketPrice', 0))
            target = info.get('targetMedianPrice', 0)
            upside = ((target - current) / current) * 100 if current > 0 and target > 0 else 0
            mean_score = info.get('recommendationMean', "N/A")
            
            st.markdown(f"## {info.get('longName', search_ticker)}")
            st.markdown(f"**Κλάδος:** {info.get('sector', 'N/A')} | {info.get('industry', 'N/A')}")
            
            # Μετρικές στην κορυφή
            c1, c2, c3 = st.columns(3)
            c1.metric("Τρέχουσα Τιμή", f"${current:.2f}")
            c2.metric("Στόχος Wall Street", f"${target:.2f}" if target else "N/A", f"+{upside:.1f}%" if target else None)
            c3.metric("Μέρισμα", f"{info.get('dividendYield', 0)*100:.1f}%" if info.get('dividendYield') else "0%")
            
            # Revolut Gauge
            st.markdown(draw_revolut_gauge(mean_score), unsafe_allow_html=True)
            
            # Διάγραμμα Κηροπηγίων
            hist = stock.history(period="6mo")
            fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], increasing_line_color='#00C853', decreasing_line_color='#D50000')])
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=280, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            
            # Εταιρικό Προφίλ
            with st.expander("📝 Επιχειρηματικό Προφίλ της Εταιρείας"):
                st.write(info.get('longBusinessSummary', 'Δεν υπάρχει διαθέσιμη περιγραφή.'))
                
            # AI Report
            st.info(generate_ultimate_analysis(
                search_ticker, current, target, upside, info.get('trailingPE'),
                info.get('beta'), info.get('dividendYield'), "", info.get('fiftyDayAverage'),
                info.get('targetHighPrice'), info.get('targetLowPrice')
            ))
    except:
        st.error("Δεν βρέθηκαν δεδομένα. Σιγουρέψου ότι έγραψες σωστά το σύμβολο (π.χ. AAPL).")
        

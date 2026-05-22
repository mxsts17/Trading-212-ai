import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. ΒΑΣΙΚΕΣ ΡΥΘΜΙΣΕΙΣ & UI ---
st.set_page_config(page_title="AI Stock Assistant", page_icon="💎", layout="centered")

st.markdown("""
    <h1 style='text-align: center; color: #4CAF50;'>💎 AI Trading Pro</h1>
    <p style='text-align: center; font-size: 18px; color: #888;'>Premium Σαρωτής Ευκαιριών & Αναλύσεων</p>
    <hr>
""", unsafe_allow_html=True)

# Συνάρτηση μετατροπής των recommendations της Wall Street σε UI
def get_recommendation_badge(rec_key):
    mapping = {
        'strong_buy': ('🟢 STRONG BUY', 'Ισχυρή σύσταση αγοράς από τους αναλυτές. Μεγάλη εμπιστοσύνη στα θεμελιώδη.'),
        'buy': ('🟢 BUY', 'Σύσταση αγοράς. Θετική προοπτική για τη μετοχή.'),
        'hold': ('🟡 HOLD', 'Διακράτηση. Η μετοχή ίσως παραμείνει στάσιμη, αναμονή για νέα δεδομένα.'),
        'sell': ('🔴 SELL', 'Σύσταση πώλησης. Πιθανή πτώση ή υπερτιμημένη μετοχή.'),
        'strong_sell': ('🔴 STRONG SELL', 'Ισχυρή σύσταση πώλησης. Υψηλός κίνδυνος υποχώρησης.')
    }
    return mapping.get(str(rec_key).lower(), ('⚪ N/A', 'Δεν υπάρχει διαθέσιμη σύσταση.'))

# Συνάρτηση παραγωγής ανάλυσης (AI Reasoning)
def generate_analysis(ticker, current, target, upside, pe, rec_badge, rec_desc):
    analysis = f"**Γιατί αναμένεται αυτή η κίνηση;**\n\n"
    analysis += f"Η πλειοψηφία των αναλυτών της Wall Street κατατάσσει τη μετοχή της **{ticker}** ως **{rec_badge}**. {rec_desc}\n\n"
    
    if upside > 0:
        analysis += f"📈 **Προοπτική Ανόδου:** Με την τρέχουσα τιμή στα **${current:.2f}** και τη μέση τιμή-στόχο των αναλυτών στα **${target:.2f}**, η μετοχή έχει περιθώριο ανόδου (Upside) **+{upside:.1f}%**. Αυτό υποδεικνύει ότι η αγορά θεωρεί τη μετοχή υποτιμημένη σε σχέση με τη μελλοντική της κερδοφορία.\n"
    else:
        analysis += f"📉 **Προσοχή:** Η τιμή-στόχος των αναλυτών (${target:.2f}) είναι χαμηλότερη από την τρέχουσα (${current:.2f}). Η αγορά ίσως θεωρεί τη μετοχή υπερτιμημένη (Overvalued) αυτή τη στιγμή.\n"
        
    if pe and pe != "N/A":
        if float(pe) < 15:
            analysis += f"⚖️ **Αποτίμηση (P/E Ratio - {pe}):** Ο δείκτης P/E είναι χαμηλός. Αυτό συχνά σημαίνει ότι η μετοχή είναι \"φθηνή\" και αποτελεί ευκαιρία αξίας (Value Play)."
        elif float(pe) > 35:
            analysis += f"⚖️ **Αποτίμηση (P/E Ratio - {pe}):** Ο δείκτης P/E είναι αρκετά υψηλός. Οι επενδυτές πληρώνουν premium περιμένοντας ραγδαία ανάπτυξη. Αν η εταιρεία δεν πιάσει τους στόχους της, υπάρχει ρίσκο διόρθωσης."
        else:
            analysis += f"⚖️ **Αποτίμηση (P/E Ratio - {pe}):** Ο δείκτης P/E βρίσκεται σε υγιή και ισορροπημένα επίπεδα για την αγορά."
            
    return analysis

# --- 2. ΣΑΡΩΤΗΣ ΕΥΚΑΙΡΙΩΝ (TOP PICKS) ---
st.subheader("🔥 Top Ευκαιρίες της Ημέρας")
popular_tickers = ['AAPL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'PLTR', 'META', 'GOOGL', 'AMD', 'UBER']

@st.cache_data(ttl=1800) # Ανανέωση κάθε 30 λεπτά
def fetch_opportunities(tickers):
    data = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            current = info.get('currentPrice', info.get('regularMarketPrice'))
            target = info.get('targetMedianPrice')
            rec_key = info.get('recommendationKey', 'N/A')
            pe = round(info.get('trailingPE', 0), 2) if info.get('trailingPE') else "N/A"
            
            if current and target and current > 0:
                upside = ((target - current) / current) * 100
                if upside > 5 and ('buy' in str(rec_key).lower()): # Δείχνει μόνο όσες έχουν >5% άνοδο και είναι Buy
                    data.append({
                        'Ticker': t,
                        'Current': current,
                        'Target': target,
                        'Upside': upside,
                        'PE': pe,
                        'Rec': rec_key
                    })
        except:
            continue
    return pd.DataFrame(data).sort_values(by='Upside', ascending=False)

opp_df = fetch_opportunities(popular_tickers)

if not opp_df.empty:
    for _, row in opp_df.iterrows():
        rec_badge, rec_desc = get_recommendation_badge(row['Rec'])
        
        # UI Card για κάθε μετοχή
        with st.container():
            st.markdown(f"### {row['Ticker']}  |  {rec_badge}")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Τρέχουσα Τιμή", f"${row['Current']:.2f}")
            col2.metric("Τιμή Στόχος", f"${row['Target']:.2f}", f"+{row['Upside']:.1f}%")
            col3.metric("P/E Ratio", row['PE'])
            
            with st.expander("🧠 Διάβασε την AI Ανάλυση της μετοχής"):
                st.write(generate_analysis(row['Ticker'], row['Current'], row['Target'], row['Upside'], row['PE'], rec_badge, rec_desc))
            st.divider()
else:
    st.info("Αυτή τη στιγμή το σύστημα δεν βρίσκει ισχυρά Buy signals (άνω του 5% κέρδους) στη βασική λίστα.")

# --- 3. ΑΤΟΜΙΚΗ ΑΝΑΖΗΤΗΣΗ & ΔΙΑΓΡΑΜΜΑ ---
st.subheader("🔍 Βαθιά Ανάλυση Συγκεκριμένης Μετοχής")
search_ticker = st.text_input("Πληκτρολόγησε σύμβολο (π.χ. RIVN, INTC, COIN):").upper().strip()

if search_ticker:
    try:
        stock = yf.Ticker(search_ticker)
        info = stock.info
        
        current = info.get('currentPrice', info.get('regularMarketPrice', 0))
        target = info.get('targetMedianPrice', 0)
        upside = ((target - current) / current) * 100 if current > 0 and target > 0 else 0
        pe = round(info.get('trailingPE', 0), 2) if info.get('trailingPE') else "N/A"
        rec_key = info.get('recommendationKey', 'N/A')
        rec_badge, rec_desc = get_recommendation_badge(rec_key)
        
        st.markdown(f"## {info.get('longName', search_ticker)}")
        st.markdown(f"**Σύσταση Αναλυτών:** {rec_badge}")
        
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Τρέχουσα Τιμή", f"${current:.2f}")
        col_b.metric("Τιμή Στόχος", f"${target:.2f}" if target else "N/A", f"{upside:.1f}%" if target else None)
        col_c.metric("Υψηλό 52 Εβδομάδων", f"${info.get('fiftyTwoWeekHigh', 0):.2f}")

        # Διαδραστικό Διάγραμμα
        hist = stock.history(period="3mo") # Δεδομένα 3 μηνών
        fig = go.Figure(data=[go.Candlestick(x=hist.index,
                        open=hist['Open'], high=hist['High'],
                        low=hist['Low'], close=hist['Close'],
                        increasing_line_color='#00C853', decreasing_line_color='#D50000')])
        
        fig.update_layout(title="Πορεία Τιμής (Τελευταίοι 3 μήνες)",
                          margin=dict(l=0, r=0, t=40, b=0),
                          height=350, template="plotly_dark") # Σκοτεινό θέμα διαγράμματος
        st.plotly_chart(fig, use_container_width=True)
        
        # AI Report
        st.info(generate_analysis(search_ticker, current, target, upside, pe, rec_badge, rec_desc))

    except Exception as e:
        st.error("Δεν βρέθηκαν δεδομένα. Σιγουρέψου ότι το σύμβολο είναι σωστό (π.χ. MSFT).")
        

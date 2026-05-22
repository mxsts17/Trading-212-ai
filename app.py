import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. UI & ΡΥΘΜΙΣΕΙΣ ---
st.set_page_config(page_title="Trading Ultimate", page_icon="📈", layout="centered")

st.markdown("""
    <h1 style='text-align: center; color: #00C853;'>📈 Trading 212 Ultimate</h1>
    <p style='text-align: center; font-size: 16px; color: #aaa;'>Προβλέψεις Χρόνου, Τάση & Αξιολόγηση Ρίσκου</p>
    <hr>
""", unsafe_allow_html=True)

def get_recommendation_badge(rec_key):
    mapping = {
        'strong_buy': ('🟢 STRONG BUY', 'Ισχυρή σύσταση αγοράς.'),
        'buy': ('🟢 BUY', 'Σύσταση αγοράς.'),
        'hold': ('🟡 HOLD', 'Διακράτηση.'),
        'sell': ('🔴 SELL', 'Σύσταση πώλησης.'),
        'strong_sell': ('🔴 STRONG SELL', 'Ισχυρή πώληση.')
    }
    return mapping.get(str(rec_key).lower(), ('⚪ N/A', 'Δεν υπάρχει διαθέσιμη σύσταση.'))

def get_risk_profile(beta):
    if beta == "N/A" or beta is None: return "⚪ Άγνωστο"
    if beta > 1.5: return "🔴 Υψηλό Ρίσκο (Επιθετική)"
    elif beta > 1.0: return "🟡 Μέτριο προς Υψηλό (Κινητική)"
    elif beta > 0.8: return "🟢 Κανονικό Ρίσκο (Σταθερή)"
    else: return "🔵 Χαμηλό Ρίσκο (Αμυντική)"

# Η καρδιά της νέας AI Ανάλυσης
def generate_ultimate_analysis(ticker, current, target, upside, pe, beta, div, rec_badge, sma50, sma200):
    analysis = f"### 🧠 Στρατηγική & Πρόβλεψη Χρόνου\n\n"
    
    # 1. Χρόνος & Στόχος
    analysis += f"**⏳ Ορίζοντας (12 Μήνες):** Για να πιάσει τον στόχο των **${target:.2f}**, η μετοχή πρέπει να αναπτύσσεται κατά μέσο όρο **+{(upside/12):.1f}% / μήνα**.\n\n"
        
    # 2. Χρόνος Διακράτησης
    analysis += "**📅 Πόσο καιρό να την κρατήσεις;** "
    if upside > 20:
        analysis += "Αναμένεται τεράστια άνοδος. Προτείνεται **Μακροπρόθεσμη Διακράτηση (6-12 μήνες)**. Άφησε την επένδυση να ωριμάσει.\n\n"
    elif upside > 8:
        analysis += "Καλή ευκαιρία. Προτείνεται **Μεσοπρόθεσμη Διακράτηση (3-6 μήνες)**.\n\n"
    else:
        analysis += "Μικρό περιθώριο. Ιδανική μόνο για **Βραχυπρόθεσμο Trading**.\n\n"

    # 3. Τάση (Momentum)
    if sma50 != "N/A" and sma200 != "N/A":
        analysis += "**📈 Τεχνική Τάση (Momentum):** "
        if current > sma50 and sma50 > sma200:
            analysis += "Η μετοχή βρίσκεται σε **Ισχυρό Ανοδικό Κανάλι**. Έχει 'φόρα' και είναι πολύ πιθανό να φτάσει τον στόχο της νωρίτερα!\n\n"
        elif current < sma50:
            analysis += "Αυτή τη στιγμή **διορθώνει (πέφτει)** βραχυπρόθεσμα. Ίσως είναι πιο έξυπνο να περιμένεις λίγες μέρες για να την αγοράσεις ακόμα πιο φθηνά.\n\n"
        else:
            analysis += "Η τάση είναι ουδέτερη αυτή την περίοδο.\n\n"

    # 4. Ποιότητα & Ρίσκο
    analysis += "**🛡️ Ποιότητα & Ασφάλεια:**\n"
    analysis += f"- **Μεταβλητότητα:** {get_risk_profile(beta)}. "
    if div and div != "N/A" and float(div) > 0:
        analysis += f"\n- **Παθητικό Εισόδημα:** Η εταιρεία σε πληρώνει **{float(div)*100:.1f}%** τον χρόνο, απλά και μόνο για να κρατάς τη μετοχή!"
    else:
        analysis += f"\n- **Παθητικό Εισόδημα:** Δεν πληρώνει μέρισμα."
        
    return analysis

# --- 2. ΣΑΡΩΤΗΣ ΕΥΚΑΙΡΙΩΝ ---
st.subheader("🔥 Top Ευκαιρίες της Ημέρας")
popular_tickers = ['AAPL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'PLTR', 'META', 'GOOGL', 'AMD', 'COIN']

@st.cache_data(ttl=1800)
def fetch_opportunities(tickers):
    data = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            current = info.get('currentPrice', info.get('regularMarketPrice'))
            target = info.get('targetMedianPrice')
            rec_key = info.get('recommendationKey', 'N/A')
            
            if current and target and current > 0:
                upside = ((target - current) / current) * 100
                if upside > 5 and ('buy' in str(rec_key).lower()):
                    data.append({
                        'Ticker': t, 'Current': current, 'Target': target,
                        'Upside': upside, 'Rec': rec_key,
                        'PE': info.get('trailingPE', "N/A"),
                        'Beta': info.get('beta', "N/A"),
                        'Div': info.get('dividendYield', "N/A"),
                        'SMA50': info.get('fiftyDayAverage', "N/A"),
                        'SMA200': info.get('twoHundredDayAverage', "N/A")
                    })
        except:
            continue
    return pd.DataFrame(data).sort_values(by='Upside', ascending=False)

opp_df = fetch_opportunities(popular_tickers)

if not opp_df.empty:
    for _, row in opp_df.iterrows():
        rec_badge, _ = get_recommendation_badge(row['Rec'])
        with st.container():
            # Αλλαγή για να φαίνονται όλα όμορφα στο κινητό
            st.markdown(f"### {row['Ticker']} | {rec_badge}")
            st.markdown(f"**Τιμή:** ${row['Current']:.2f} &nbsp;➔&nbsp; **Στόχος:** ${row['Target']:.2f} <span style='color:#00C853; font-weight:bold;'>(+{row['Upside']:.1f}%)</span>", unsafe_allow_html=True)
            
            # Το αναδιπλούμενο μενού της Ανάλυσης επέστρεψε
            with st.expander("🧠 Διάβασε την AI Ανάλυση της μετοχής"):
                st.write(generate_ultimate_analysis(
                    row['Ticker'], row['Current'], row['Target'], row['Upside'],
                    row['PE'], row['Beta'], row['Div'], rec_badge, row['SMA50'], row['SMA200']
                ))
            st.divider()
else:
    st.info("Δεν βρέθηκαν άμεσες ευκαιρίες >5% στη βασική λίστα αυτή τη στιγμή.")

# --- 3. ΒΑΘΙΑ ΑΝΑΛΥΣΗ ΜΕΤΟΧΗΣ ---
st.subheader("🔍 Αναζήτηση & Πρόβλεψη")
search_ticker = st.text_input("Πληκτρολόγησε σύμβολο (π.χ. RIVN, INTC, PLTR):").upper().strip()

if search_ticker:
    try:
        stock = yf.Ticker(search_ticker)
        info = stock.info
        
        current = info.get('currentPrice', info.get('regularMarketPrice', 0))
        target = info.get('targetMedianPrice', 0)
        upside = ((target - current) / current) * 100 if current > 0 and target > 0 else 0
        pe = info.get('trailingPE', "N/A")
        beta = info.get('beta', "N/A")
        div = info.get('dividendYield', "N/A")
        sma50 = info.get('fiftyDayAverage', "N/A")
        sma200 = info.get('twoHundredDayAverage', "N/A")
        
        rec_key = info.get('recommendationKey', 'N/A')
        rec_badge, _ = get_recommendation_badge(rec_key)
        
        st.markdown(f"## {info.get('longName', search_ticker)}")
        st.markdown(f"**Σύσταση:** {rec_badge}")
        
        # 3 Στήλες που χωράνε άνετα στο κινητό
        c1, c2, c3 = st.columns(3)
        c1.metric("Τιμή", f"${current:.2f}")
        c2.metric("Στόχος 12m", f"${target:.2f}" if target else "N/A", f"{upside:.1f}%" if target else None)
        c3.metric("Μέρισμα", f"{div*100:.1f}%" if div != "N/A" else "0%")

        # Γράφημα
        hist = stock.history(period="6mo")
        fig = go.Figure(data=[go.Candlestick(x=hist.index,
                        open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'],
                        increasing_line_color='#00C853', decreasing_line_color='#D50000')])
        
        if sma50 != "N/A":
            fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'].rolling(window=20).mean(), line=dict(color='orange', width=1.5), name="Τάση 20 ημερών"))
            
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=300, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        
        # AI Report
        st.info(generate_ultimate_analysis(search_ticker, current, target, upside, pe, beta, div, rec_badge, sma50, sma200))

    except Exception as e:
        st.error("Δεν βρέθηκαν δεδομένα. Σιγουρέψου ότι το σύμβολο είναι σωστό.")
        

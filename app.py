import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Ρύθμιση για Mobile οθόνες
st.set_page_config(page_title="Trading 212 AI Assistant", page_icon="📈", layout="centered")

st.title("📈 Trading 212 AI Assistant")
st.write("Ο προσωπικός σου σύμβουλος για μετοχές σε πραγματικό χρόνο.")

# --- SECTION 1: ΜΕΓΑΛΕΣ ΕΥΚΑΙΡΙΕΣ ---
st.header("🚀 AI Σαρωτής Ευκαιριών")
st.caption("Μετοχές με το μεγαλύτερο αναμενόμενο περιθώριο ανόδου (Upside) σύμφωνα με τους αναλυτές:")

# Λίστα με δημοφιλείς μετοχές της Trading 212 για έλεγχο
popular_tickers = ['AAPL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'NIO', 'PLTR', 'BABA', 'AMD', 'COIN']

@st.cache_data(ttl=3600)  # Ανανέωση δεδομένων κάθε 1 ώρα
def get_opportunities(tickers):
    opportunities = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            current = info.get('currentPrice', info.get('regularMarketPrice'))
            target = info.get('targetMedianPrice')
            
            if current and target:
                upside = ((target - current) / current) * 100
                opportunities.append({
                    'Μετοχή': t,
                    'Τρέχουσα Τιμή': f"${current:.2f}",
                    'Στόχος Αναλυτών': f"${target:.2f}",
                    'Αναμενόμενη Άνοδος': upside
                })
        except:
            continue
    df = pd.DataFrame(opportunities)
    if not df.empty:
        return df.sort_values(by='Αναμενόμενη Άνοδος', ascending=False)
    return df

opp_df = get_opportunities(popular_tickers)
if not opp_df.empty:
    for index, row in opp_df.iterrows():
        # Αν η άνοδος είναι πάνω από 15%, το δείχνει σαν ευκαιρία
        if row['Αναμενόμενη Άνοδος'] > 0:
            st.success(f"**{row['Μετοχή']}** | Αναμενόμενη Άνοδος: **+{row['Αναμενόμενη Άνοδος']:.1f}%**\n"
                       f"Τρέχουσα: {row['Τρέχουσα Τιμή']} -> Στόχος: {row['Στόχος Αναλυτών']}")
else:
    st.write("Δεν βρέθηκαν άμεσες ευκαιρίες αυτή τη στιγμή.")

st.markdown("---")

# --- SECTION 2: ΑΝΑΛΥΣΗ ΜΕΤΟΧΗΣ ---
st.header("🔍 Αναζήτηση & AI Ανάλυση")
ticker_input = st.text_input("Εισάγετε το Ticker της μετοχής (π.χ. AAPL, TSLA, PLTR):", "AAPL").upper().strip()

if ticker_input:
    try:
        stock = yf.Ticker(ticker_input)
        info = stock.info
        
        # Βασικά Στοιχεία
        st.subheader(f"📊 {info.get('longName', ticker_input)}")
        st.write(f"**Κλάδος:** {info.get('industry', 'N/A')} | **Χώρα:** {info.get('country', 'N/A')}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Τρέχουσα Τιμή", f"${info.get('currentPrice', info.get('regularMarketPrice', 0)):.2f}")
        with col2:
            st.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A')}")

        # Εκτιμήσεις Αναλυτών
        st.subheader("🎯 Εκτιμήσεις Αναλυτών")
        recommendation = info.get('recommendationKey', 'N/A').upper()
        st.info(f"**Γενική Πρόταση:** {recommendation}")
        
        # Διάγραμμα
        st.subheader("📈 Διάγραμμα 30 Ημερών")
        hist = stock.history(period="30d")
        fig = go.Figure(data=[go.Candlestick(x=hist.index,
                        open=hist['Open'], high=hist['High'],
                        low=hist['Low'], close=hist['Close'])])
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        # AI Συμπέρασμα
        st.subheader("🤖 AI Σύμβουλος")
        current_price = info.get('currentPrice', 1)
        target_price = info.get('targetMedianPrice', 0)
        
        if target_price > current_price:
            st.write(f"Η μετοχή παρουσιάζει θετικό momentum. Οι αναλυτές βλέπουν την τιμή στα **${target_price}**, γεγονός που δικαιολογεί μια προσεκτική τοποθέτηση αν συμφωνεί και η στρατηγική σου.")
        else:
            st.write("Η μετοχή βρίσκεται κοντά ή πάνω από την δίκαιη τιμή των αναλυτών. Ίσως είναι καλύτερα να περιμένεις κάποιο correction (διόρθωση).")

    except Exception as e:
        st.error("Δεν βρέθηκαν στοιχεία για το συγκεκριμένο Ticker. Σιγουρευτείτε ότι είναι σωστό.")

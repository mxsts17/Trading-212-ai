import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from yahooquery import Ticker as YQTicker

# --- 1. UI & ΒΑΣΙΚΕΣ ΡΥΘΜΙΣΕΙΣ ---
st.set_page_config(page_title="Trading 212 AI Pro", page_icon="📊", layout="centered")

st.markdown("""
    <h1 style='text-align: center; color: #00C853;'>📊 Trading 212 AI Analytics</h1>
    <p style='text-align: center; font-size: 15px; color: #aaa;'>Deep Fundamental Analysis & Wall Street Targets</p>
    <hr style='margin-bottom: 25px;'>
""", unsafe_allow_html=True)

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

def generate_deep_analysis(info, current):
    target_high = info.get('targetHighPrice')
    target_mean = info.get('targetMeanPrice')
    target_low = info.get('targetLowPrice')
    
    rev_growth = info.get('revenueGrowth', 0)
    profit_margin = info.get('profitMargins', 0)
    
    analysis = "### 🧠 Βαθιά Ανάλυση (Fundamental & Targets)\n\n"
    
    analysis += "**🎯 Τιμές-Στόχοι (Επόμενοι 12 Μήνες):**\n"
    if target_high and target_mean and target_low:
        high_upside = ((target_high - current) / current) * 100
        mean_upside = ((target_mean - current) / current) * 100
        low_upside = ((target_low - current) / current) * 100
        
        analysis += f"* 🟢 **Αισιόδοξο (High):** ${target_high:.2f} ({'+' if high_upside > 0 else ''}{high_upside:.1f}%)\n"
        analysis += f"* 🟡 **Μέσο (Average):** ${target_mean:.2f} ({'+' if mean_upside > 0 else ''}{mean_upside:.1f}%)\n"
        analysis += f"* 🔴 **Απαισιόδοξο (Low):** ${target_low:.2f} ({'+' if low_upside > 0 else ''}{low_upside:.1f}%)\n\n"
    else:
        analysis += "*Δεν υπάρχουν επαρκή δεδομένα αναλυτών για αυτή τη μετοχή.*\n\n"

    analysis += "**🏢 Υγεία Εταιρείας (Fundamentals):**\n"
    if rev_growth and rev_growth != "N/A":
        growth_pct = float(rev_growth) * 100
        if growth_pct > 20:
            analysis += f"* 🚀 **Ανάπτυξη:** Τρομερή αύξηση εσόδων κατά **{growth_pct:.1f}%**. Η εταιρεία αναπτύσσεται επιθετικά (Growth status).\n"
        elif growth_pct > 0:
            analysis += f"* 📈 **Ανάπτυξη:** Σταθερή αύξηση εσόδων κατά **{growth_pct:.1f}%**.\n"
        else:
            analysis += f"* ⚠️ **Ανάπτυξη:** Προσοχή, τα έσοδα συρρικνώνονται κατά **{growth_pct:.1f}%**.\n"
            
    if profit_margin and profit_margin != "N/A":
        margin_pct = float(profit_margin) * 100
        if margin_pct > 20:
            analysis += f"* 💰 **Κερδοφορία:** Εξαιρετικό περιθώριο κέρδους **{margin_pct:.1f}%**. Η εταιρεία 'τυπώνει' χρήμα (High cash flow potential).\n"
        elif margin_pct > 0:
            analysis += f"* 💵 **Κερδοφορία:** Θετικό περιθώριο κέρδους **{margin_pct:.1f}%**. Η εταιρεία είναι βιώσιμη.\n"
        else:
            analysis += f"* 🩸 **Κερδοφορία:** Η εταιρεία αυτή τη στιγμή 'καίει' μετρητά (Περιθώριο: **{margin_pct:.1f}%**).\n"

    return analysis

# --- Το δίκτυο μετοχών μας ---
ticker_pool = {
    "Mega": ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AMD', 'NFLX', 'DIS', 'NKE', 'PFE'],
    "MidSmall": ['PLTR', 'SOFI', 'HOOD', 'RIVN', 'NU', 'S', 'DKNG', 'U', 'PINS', 'SNAP', 'UPST', 'AFRM'],
    "CryptoEV": ['COIN', 'MARA', 'RIOT', 'CLSK', 'NIO', 'XPEV', 'LI', 'PLUG', 'FCEL', 'BLINK', 'BABA', 'JD']
}

@st.cache_data(ttl=900)
def run_scan_bulk(tickers_list):
    # Χρήση του yahooquery για ΤΑΥΤΟΧΡΟΝΗ λήψη δεδομένων χωρίς μπλοκάρισμα!
    t = YQTicker(tickers_list, asynchronous=True)
    fin_data = t.financial_data
    price_data = t.price
    
    data = []
    for ticker in tickers_list:
        try:
            # Αν το yahooquery επέστρεψε string αντί για λεξικό, σημαίνει ότι δεν βρήκε τη μετοχή
            if isinstance(fin_data.get(ticker), str) or isinstance(price_data.get(ticker), str):
                continue
            
            f_info = fin_data.get(ticker, {})
            p_info = price_data.get(ticker, {})
            
            current = p_info.get('regularMarketPrice')
            target = f_info.get('targetMedianPrice')
            mean_score = f_info.get('recommendationMean', "N/A")
            
            if current and target and current > 0:
                upside = ((target - current) / current) * 100
                
                # Φτιάχνουμε το "λεξικό" info για να τροφοδοτήσουμε τη συνάρτηση ανάλυσης
                info = {
                    'targetHighPrice': f_info.get('targetHighPrice'),
                    'targetMeanPrice': f_info.get('targetMeanPrice'),
                    'targetLowPrice': f_info.get('targetLowPrice'),
                    'revenueGrowth': f_info.get('revenueGrowth'),
                    'profitMargins': f_info.get('profitMargins')
                }
                
                data.append({
                    'Ticker': ticker, 'Current': current, 'Target': target, 'Upside': upside,
                    'MeanScore': mean_score, 'Info': info
                })
        except:
            continue
            
    return pd.DataFrame(data)

# --- 2. ΚΟΥΜΠΙ TOP 3 ΕΠΙΛΟΓΩΝ ---
st.subheader("🏆 Το Top 3 της Ημέρας (Βάσει Αναλυτών)")
if st.button("Εμφάνισε τις Top 3 Ευκαιρίες Τώρα!", use_container_width=True):
    with st.spinner("Αστραπιαία σάρωση μέσω bulk API..."):
        all_tickers = ticker_pool["Mega"] + ticker_pool["MidSmall"] + ticker_pool["CryptoEV"]
        df_all = run_scan_bulk(all_tickers)
        
        if not df_all.empty and 'MeanScore' in df_all.columns:
            df_all['ScoreNum'] = pd.to_numeric(df_all['MeanScore'], errors='coerce')
            top3_df = df_all[(df_all['ScoreNum'] > 0) & (df_all['ScoreNum'] <= 2.5)].sort_values(by='Upside', ascending=False).head(3)
            
            if not top3_df.empty:
                medals = ['🥇', '🥈', '🥉']
                for i, row in top3_df.reset_index(drop=True).iterrows():
                    with st.container():
                        st.markdown(f"## {medals[i]} #{i+1}: {row['Ticker']}")
                        st.markdown(f"**Τιμή:** ${row['Current']:.2f} &nbsp;➔&nbsp; **Στόχος:** ${row['Target']:.2f} <span style='color:#00C853; font-weight:bold; font-size:18px;'>(+{row['Upside']:.1f}%)</span>", unsafe_allow_html=True)
                        st.markdown(draw_revolut_gauge(row['MeanScore']), unsafe_allow_html=True)
                        
                        with st.expander("Δες την Βαθιά Ανάλυση & Τιμές-Στόχους"):
                             st.markdown(generate_deep_analysis(row['Info'], row['Current']))
                        st.divider()
            else:
                st.info("Δεν βρέθηκαν μετοχές με σήμα 'Buy' που να πληρούν τα κριτήρια αυτή τη στιγμή.")
        else:
            st.error("⚠️ Σφάλμα σύνδεσης με τα δεδομένα. Δοκίμασε την Ατομική Αναζήτηση.")

st.divider()

# --- 3. ΑΤΟΜΙΚΗ ΑΝΑΖΗΤΗΣΗ (DEEP DIVE) ---
st.subheader("🔍 Χειροκίνητη Αναζήτηση (Deep Dive)")
search_ticker = st.text_input("Πληκτρολόγησε σύμβολο για πλήρη ανάλυση (π.χ. NU, SOFI, S):").upper().strip()

if search_ticker:
    try:
        with st.spinner("Άντληση Θεμελιωδών και Αναλύσεων Wall Street..."):
            stock = yf.Ticker(search_ticker)
            info = stock.info
            
            current = info.get('currentPrice', info.get('regularMarketPrice', 0))
            mean_score = info.get('recommendationMean', "N/A")
            
            st.markdown(f"## {info.get('longName', search_ticker)}")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Τρέχουσα Τιμή", f"${current:.2f}")
            c2.metric("P/E (Forward)", f"{info.get('forwardPE', 'N/A'):.1f}" if type(info.get('forwardPE')) in [int, float] else "N/A")
            c3.metric("Χρηματιστηριακή Αξία", f"${info.get('marketCap', 0) / 1e9:.2f}B")
            
            st.markdown(draw_revolut_gauge(mean_score), unsafe_allow_html=True)
            
            hist = stock.history(period="6mo")
            fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], increasing_line_color='#00C853', decreasing_line_color='#D50000')])
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=280, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            
            st.info(generate_deep_analysis(info, current))
    except:
        st.error("Δεν βρέθηκαν δεδομένα. Σιγουρέψου ότι έγραψες σωστά το σύμβολο.")
        

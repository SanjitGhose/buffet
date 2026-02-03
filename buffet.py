import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import concurrent.futures

# ==========================================
# 1. ULTIMATE HIGH-CONTRAST CSS
# ==========================================
st.set_page_config(page_title="The Buffett Way", layout="wide", page_icon="🏦")

st.markdown("""
<style>
    /* Force Background and Text Colors for Maximum Readability */
    .stApp { background-color: #ffffff !important; }
    
    /* Global Text: High-Contrast Charcoal Black */
    h1, h2, h3, p, span, label, .stSelectbox label {
        color: #0f172a !important; 
        font-family: 'Inter', -apple-system, sans-serif;
        font-weight: 700 !important;
    }

    /* Sidebar: Steel Grey with Deep Navy Text */
    [data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        border-right: 2px solid #e2e8f0;
    }
    [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] label {
        color: #1e293b !important;
        font-weight: 800 !important;
        font-size: 1.1rem !important;
    }

    /* Groww-Green Button */
    .stButton>button {
        background-color: #00d09c;
        color: #ffffff !important;
        border-radius: 10px;
        padding: 0.8rem;
        font-weight: 800;
        font-size: 1.2rem;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #00b386;
        box-shadow: 0 10px 15px -3px rgba(0, 208, 156, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. THE COMPLETE ANALYTICS ENGINE
# ==========================================

def get_nifty_tickers(universe):
    url = "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty500list.csv" if universe == "Nifty 500" else "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty50list.csv"
    try:
        df = pd.read_csv(url)
        return [str(s) + ".NS" for s in df['Symbol'].tolist()]
    except:
        return ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ITC.NS", "SBIN.NS"]

def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # --- DATA EXTRACTION ---
        roe = info.get('returnOnEquity', 0) * 100
        pe = info.get('trailingPE', 0)
        rev_growth = info.get('revenueGrowth', 0) * 100
        gross_margin = info.get('grossMargins', 0) * 100
        eps = info.get('trailingEps', 0)
        book_val = info.get('bookValue', 0)
        price = info.get('currentPrice', 0)
        
        # Graham Formula: sqrt(22.5 * EPS * BVPS)
        graham_val = np.sqrt(22.5 * eps * book_val) if (eps > 0 and book_val > 0) else 0

        # --- THE MASTER FILTER ---
        # Quality (ROE > 15) | Growth (Rev > 5) | Moat (Margin > 15) | Value (PE < 30)
        if (15 < roe < 100 and rev_growth > 5 and gross_margin > 15 and 0 < pe < 30):
            return {
                "Ticker": ticker.replace(".NS", ""),
                "Price": price,
                "Graham Val": round(graham_val, 2),
                "ROE (%)": round(roe, 2),
                "Rev Growth (%)": round(rev_growth, 2),
                "Gross Margin (%)": round(gross_margin, 2),
                "P/E": round(pe, 2),
                "Debt/Eq": round(info.get('debtToEquity', 0), 2)
            }
    except: return None

# ==========================================
# 3. INTERFACE EXECUTION
# ==========================================

st.title("🏛️ The Buffett Way")
st.markdown("### The Complete Growth, Quality & Value Screener")

with st.sidebar:
    st.markdown("## SCANNER SETTINGS")
    universe = st.selectbox("Market Selection", ["Nifty 50", "Nifty 500"])
    st.markdown("---")
    st.markdown("💡 **Strict Logic Applied:**")
    st.write("1. ROE > 15% (Efficiency)")
    st.write("2. Rev Growth > 5% (Momentum)")
    st.write("3. Gross Margin > 15% (Moat)")
    st.write("4. P/E < 30 (Value)")

if st.button(f"🚀 RUN {universe} AUDIT"):
    tickers = get_nifty_tickers(universe)
    
    with st.spinner(f"Auditing {len(tickers)} companies via Multi-Threaded Engine..."):
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            future_to_ticker = {executor.submit(analyze_stock, t): t for t in tickers}
            for future in concurrent.futures.as_completed(future_to_ticker):
                res = future.result()
                if res: results.append(res)
    
    if results:
        df = pd.DataFrame(results).sort_values("ROE (%)", ascending=False)
        
        # --- UI DESIGN: READABLE PASTEL HEATMAP ---
        # Using light palettes so black text stays sharp
        styled_df = df.style.background_gradient(subset=["ROE (%)"], cmap="YlGn") \
                           .background_gradient(subset=["Gross Margin (%)"], cmap="BuGn") \
                           .background_gradient(subset=["P/E"], cmap="YlOrRd") \
                           .format({
                               "Price": "₹{:.2f}", 
                               "Graham Val": "₹{:.2f}",
                               "ROE (%)": "{:.1f}%",
                               "Rev Growth (%)": "{:.1f}%",
                               "Gross Margin (%)": "{:.1f}%"
                           })

        st.dataframe(styled_df, use_container_width=True, height=650)
    else:
        st.error("No stocks met the strict 4-point Buffett criteria today.")

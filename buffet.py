import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import concurrent.futures

# ==========================================
# 1. ULTIMATE CONTRAST & UI OVERRIDE
# ==========================================
st.set_page_config(page_title="The Buffett Way", layout="wide", page_icon="🏦")

st.markdown("""
<style>
    /* Force Background and Header Colors */
    .stApp { background-color: #ffffff !important; }
    h1, h2, h3 { color: #0f172a !important; font-weight: 800 !important; }

    /* SIDEBAR & DROPDOWN CONTRAST FIX */
    [data-testid="stSidebar"] {
        background-color: #f1f5f9 !important;
        border-right: 2px solid #cbd5e1;
    }
    
    /* Targeting the specific Dropdown (Selectbox) for High Contrast */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #0f172a !important;
    }
    
    /* Ensuring the text inside the dropdown is dark */
    div[data-baseweb="select"] * {
        color: #0f172a !important;
        font-weight: 600 !important;
    }

    /* Sidebar text contrast */
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] label {
        color: #0f172a !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
    }

    /* Groww-Green Button */
    .stButton>button {
        background-color: #00d09c;
        color: white !important;
        border-radius: 8px;
        padding: 0.8rem;
        font-weight: 800;
        border: none;
        width: 100%;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #00b386;
        box-shadow: 0 4px 12px rgba(0, 208, 156, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ANALYTICS ENGINE (P/E < 25)
# ==========================================

def get_nifty_tickers(universe):
    url = "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty500list.csv" if universe == "Nifty 500" else "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty50list.csv"
    try:
        df = pd.read_csv(url)
        return [str(s) + ".NS" for s in df['Symbol'].tolist()]
    except:
        # Static Fallback List
        return ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ITC.NS", "HINDUNILVR.NS", "ICICIBANK.NS"]

def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Financial Metrics
        roe = info.get('returnOnEquity', 0) * 100
        pe = info.get('trailingPE', 0)
        rev_growth = info.get('revenueGrowth', 0) * 100
        gross_margin = info.get('grossMargins', 0) * 100
        eps = info.get('trailingEps', 0)
        book_val = info.get('bookValue', 0)
        price = info.get('currentPrice', 0)
        
        # Graham Number Calculation
        graham_val = np.sqrt(22.5 * eps * book_val) if (eps > 0 and book_val > 0) else 0

        # --- THE STRICT BUFFETT-GRAHAM FILTER ---
        # ROE > 15 | Growth > 5 | Margin > 15 | PE < 25
        if (15 < roe < 100 and rev_growth > 5 and gross_margin > 15 and 0 < pe < 25):
            return {
                "Ticker": ticker.replace(".NS", ""),
                "Price": price,
                "Graham Val": round(graham_val, 2),
                "ROE (%)": round(roe, 2),
                "Rev Growth (%)": round(rev_growth, 2),
                "Gross Margin (%)": round(gross_margin, 2),
                "P/E": round(pe, 2)
            }
    except: return None

# ==========================================
# 3. DASHBOARD EXECUTION
# ==========================================

st.markdown('<h1>🏛️ The Buffett Way</h1>', unsafe_allow_html=True)
st.markdown('<h3>Premium Value & Quality Screener</h3>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## ⚙️ SETTINGS")
    universe = st.selectbox("Market Selection", ["Nifty 50", "Nifty 500"])
    st.markdown("---")
    st.markdown("### 📊 Active Filters")
    st.write("✅ **ROE:** > 15%")
    st.write("✅ **Revenue Growth:** > 5%")
    st.write("✅ **Gross Margin:** > 15%")
    st.write("✅ **P/E Ratio:** < 25")

if st.button(f"🔍 SCAN {universe}"):
    tickers = get_nifty_tickers(universe)
    
    with st.spinner(f"Auditing {len(tickers)} stocks..."):
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            future_to_ticker = {executor.submit(analyze_stock, t): t for t in tickers}
            for future in concurrent.futures.as_completed(future_to_ticker):
                res = future.result()
                if res: results.append(res)
    
    if results:
        df = pd.DataFrame(results).sort_values("ROE (%)", ascending=False)
        
        # UI Formatting
        styled_df = df.style.background_gradient(subset=["ROE (%)"], cmap="YlGn") \
                           .background_gradient(subset=["P/E"], cmap="YlOrRd_r") \
                           .format({
                               "Price": "₹{:.2f}", 
                               "Graham Val": "₹{:.2f}",
                               "ROE (%)": "{:.1f}%",
                               "Rev Growth (%)": "{:.1f}%",
                               "Gross Margin (%)": "{:.1f}%"
                           })

        st.dataframe(styled_df, use_container_width=True, height=600)
    else:
        st.error("No companies met the strict criteria. The market might be currently overvalued.")

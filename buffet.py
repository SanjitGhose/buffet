import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import concurrent.futures

# ==========================================
# 1. ULTIMATE READABILITY & CONTRAST CSS
# ==========================================
st.set_page_config(page_title="The Buffett Way", layout="wide", page_icon="🏦")

st.markdown("""
<style>
    /* Main App Contrast */
    .stApp { background-color: #ffffff !important; }
    
    /* Global Text: High-Contrast Navy Black */
    h1, h2, h3, p, span, div, label {
        color: #0f172a !important; 
        font-family: 'Inter', sans-serif;
    }

    /* SIDEBAR CONTRAST FIX */
    /* Force sidebar background and high-contrast text */
    [data-testid="stSidebar"] {
        background-color: #f1f5f9 !important;
        border-right: 2px solid #cbd5e1;
    }
    
    /* Targeting all sidebar elements: labels, text, radio buttons */
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] .stSelectbox div,
    [data-testid="stSidebar"] .stRadio div {
        color: #0f172a !important;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
    }

    /* Groww-style Button */
    .stButton>button {
        background-color: #00d09c;
        color: #ffffff !important;
        border-radius: 8px;
        padding: 0.8rem;
        font-weight: 800;
        border: none;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA ENGINE
# ==========================================

def get_nifty_tickers(universe):
    url = "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty500list.csv" if universe == "Nifty 500" else "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty50list.csv"
    try:
        df = pd.read_csv(url)
        return [str(s) + ".NS" for s in df['Symbol'].tolist()]
    except:
        return ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ITC.NS"]

def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        roe = info.get('returnOnEquity', 0) * 100
        pe = info.get('trailingPE', 0)
        rev_growth = info.get('revenueGrowth', 0) * 100
        gross_margin = info.get('grossMargins', 0) * 100
        eps = info.get('trailingEps', 0)
        book_val = info.get('bookValue', 0)
        price = info.get('currentPrice', 0)
        
        # Graham Formula
        graham_val = np.sqrt(22.5 * eps * book_val) if (eps > 0 and book_val > 0) else 0

        # Quality Filter
        if (15 < roe < 100 and rev_growth > 5 and gross_margin > 15 and 0 < pe < 35):
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
# 3. INTERFACE
# ==========================================

st.markdown('<h1>🏛️ The Buffett Way</h1>', unsafe_allow_html=True)
st.markdown('<h3>Intrinsic Value & Growth Engine</h3>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## SCANNER CONTROLS")
    universe = st.selectbox("Market Selection", ["Nifty 50", "Nifty 500"])
    st.markdown("---")
    st.markdown("### 📋 Filter Criteria")
    st.write("• ROE > 15%")
    st.write("• Growth > 5%")
    st.write("• Margin > 15%")
    st.write("• P/E < 35")

if st.button(f"🚀 RUN {universe} SCAN"):
    tickers = get_nifty_tickers(universe)
    
    with st.spinner(f"Analyzing {len(tickers)} companies..."):
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            future_to_ticker = {executor.submit(analyze_stock, t): t for t in tickers}
            for future in concurrent.futures.as_completed(future_to_ticker):
                res = future.result()
                if res: results.append(res)
    
    if results:
        df = pd.DataFrame(results).sort_values("ROE (%)", ascending=False)
        
        # Pastel Heatmaps (Safe for Black Text)
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

        st.dataframe(styled_df, use_container_width=True, height=600)
    else:
        st.error("No companies currently pass the strict Value + Growth criteria.")

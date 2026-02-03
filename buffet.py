import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import concurrent.futures

# ==========================================
# 1. READABILITY & CONTRAST CSS
# ==========================================
st.set_page_config(page_title="The Buffett Way", layout="wide", page_icon="🏛️")

st.markdown("""
<style>
    /* Force Background to Pure White */
    .stApp { background-color: #ffffff; }
    
    /* High-Contrast Title: Deep Navy */
    .main-title {
        color: #0f172a; 
        font-size: 3.5rem !important;
        font-weight: 800 !important;
        margin-bottom: 0px !important;
    }
    
    /* High-Contrast Subheader: Muted Steel Blue */
    .sub-title {
        color: #334155;
        font-size: 1.5rem !important;
        font-weight: 500 !important;
        margin-top: -10px !important;
        margin-bottom: 25px !important;
    }

    /* Groww-Green Button */
    .stButton>button {
        background-color: #00d09c;
        color: white;
        font-weight: 700;
        border: none;
        border-radius: 8px;
        padding: 0.8rem;
    }
    
    /* Fix Sidebar Contrast */
    [data-testid="stSidebar"] {
        background-color: #f1f5f9;
        border-right: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. THE ANALYTICS ENGINE (Graham & ROE)
# ==========================================

def calculate_graham(eps, bvps):
    # Graham Number = sqrt(22.5 * EPS * BVPS)
    if eps <= 0 or bvps <= 0: return 0
    return np.sqrt(22.5 * eps * bvps)

def scan_logic(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Pulling Core Metrics
        roe = info.get('returnOnEquity', 0) * 100
        eps = info.get('trailingEps', 0)
        bvps = info.get('bookValue', 0)
        price = info.get('currentPrice', 0)
        
        graham = calculate_graham(eps, bvps)
        
        # The 'Buffett-Graham' Filter
        if (15 < roe < 100 and info.get('trailingPE', 0) < 30):
            upside = ((graham - price) / price) * 100 if graham > 0 else -100
            
            return {
                "Ticker": ticker.replace(".NS", ""),
                "Price": price,
                "Graham Val": round(graham, 2),
                "Upside (%)": round(upside, 1),
                "ROE (%)": round(roe, 2),
                "Sector": info.get('sector', 'N/A')
            }
    except: return None

# ==========================================
# 3. INTERFACE EXECUTION
# ==========================================

# CUSTOM HTML HEADERS FOR PERFECT READABILITY
st.markdown('<p class="main-title">The Buffett Way</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Intrinsic Value & Quality Screener</p>', unsafe_allow_html=True)

universe = st.sidebar.radio("Select Universe", ["Nifty 50", "Nifty 500"])

if st.button(f"🚀 Analyze {universe}"):
    # Ticker Fetching
    url = "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty500list.csv" if universe == "Nifty 500" else "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty50list.csv"
    try:
        tickers = [s + ".NS" for s in pd.read_csv(url)['Symbol'].tolist()]
    except:
        tickers = ["TCS.NS", "RELIANCE.NS", "INFY.NS", "HDFCBANK.NS"]

    with st.spinner("Calculating 'Margin of Safety'..."):
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_ticker = {executor.submit(scan_logic, t): t for t in tickers}
            for future in concurrent.futures.as_completed(future_to_ticker):
                res = future.result()
                if res: results.append(res)

    if results:
        df = pd.DataFrame(results).sort_values("Upside (%)", ascending=False)
        
        # Pastel Heatmap for the table (Safe for Black Text)
        def color_map(val):
            # Soft Green for positive upside, Soft Red for negative
            color = '#e6fffa' if val > 0 else '#fff5f5'
            return f'background-color: {color}; color: #1a202c;'

        styled_df = df.style.applymap(color_map, subset=['Upside (%)']) \
                            .background_gradient(subset=['ROE (%)'], cmap='YlGnBu') \
                            .format({"Price": "₹{:.2f}", "Graham Val": "₹{:.2f}"})

        st.dataframe(styled_df, use_container_width=True, height=500)
    else:
        st.error("No stocks passed the safety criteria.")

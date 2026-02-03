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

    /* SIDEBAR CONTRAST FIX */
    [data-testid="stSidebar"] {
        background-color: #f1f5f9 !important;
        border-right: 2px solid #cbd5e1;
    }
    
    /* DROPDOWN (SELECTBOX) READABILITY FIX */
    /* Target the container, the input, and the text inside */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 2px solid #0f172a !important; /* Thick contrast border */
        border-radius: 8px !important;
    }
    
    /* Force the text inside the Market Selection to be Deep Navy */
    div[data-baseweb="select"] * {
        color: #0f172a !important;
        font-weight: 700 !important;
    }

    /* SLIDER & LABEL CONTRAST */
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] label,
    [data-testid="stWidgetLabel"] p {
        color: #0f172a !important;
        font-weight: 800 !important;
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
# 2. ANALYTICS ENGINE
# ==========================================

def get_nifty_tickers(universe):
    url = "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty500list.csv" if universe == "Nifty 500" else "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty50list.csv"
    try:
        df = pd.read_csv(url)
        return [str(s) + ".NS" for s in df['Symbol'].tolist()]
    except:
        return ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ITC.NS"]

def analyze_stock(ticker, u_roe, u_pe, u_growth, u_margin):
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
        
        graham_val = np.sqrt(22.5 * eps * book_val) if (eps > 0 and book_val > 0) else 0

        # Logic using adjustable user thresholds
        if (u_roe <= roe < 100 and rev_growth > u_growth and gross_margin > u_margin and 0 < pe < u_pe):
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
st.markdown('<h3>Intrinsic Value & Quality Screener</h3>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## ⚙️ SETTINGS")
    # Market selection with forced contrast
    universe = st.selectbox("Market Selection", ["Nifty 50", "Nifty 500"])
    
    st.markdown("---")
    st.markdown("### 🛠️ ADJUST FILTERS")
    user_pe = st.slider("Max P/E Ratio", 5, 50, 25)
    user_roe = st.slider("Min ROE (%)", 5, 30, 15)
    user_margin = st.slider("Min Gross Margin (%)", 5, 40, 15)
    user_growth = st.slider("Min Revenue Growth (%)", 0, 30, 5)

if st.button(f"🔍 EXECUTE {universe} SCAN"):
    tickers = get_nifty_tickers(universe)
    
    with st.spinner(f"Auditing {len(tickers)} companies..."):
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            future_to_ticker = {executor.submit(analyze_stock, t, user_roe, user_pe, user_growth, user_margin): t for t in tickers}
            for future in concurrent.futures.as_completed(future_to_ticker):
                res = future.result()
                if res: results.append(res)
    
    if results:
        df = pd.DataFrame(results).sort_values("ROE (%)", ascending=False)
        
        # Pastel Heatmaps (Safe for Black Text)
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
        st.error("No stocks matched these criteria. Try loosening the filters in the sidebar.")

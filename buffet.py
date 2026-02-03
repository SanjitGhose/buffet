import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import concurrent.futures

# ==========================================
# 1. HIGH-CONTRAST READABILITY CSS
# ==========================================
st.set_page_config(page_title="The Buffett Way", layout="wide", page_icon="🏦")

st.markdown("""
<style>
    /* Force Pure White Background for Main App */
    .stApp { background-color: #ffffff; }
    
    /* Global Text Contrast: Deep Charcoal */
    h1, h2, h3, p, span, label {
        color: #111827 !important; 
        font-family: 'Inter', -apple-system, sans-serif;
    }

    /* Sidebar Contrast: Light Grey Background with Dark Text */
    [data-testid="stSidebar"] {
        background-color: #f3f4f6 !important;
        border-right: 1px solid #d1d5db;
    }
    [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] label {
        color: #111827 !important;
        font-weight: 700 !important;
    }

    /* Groww-Green Button: High Contrast White Text */
    .stButton>button {
        background-color: #00d09c;
        color: #ffffff !important;
        border: none;
        border-radius: 8px;
        padding: 0.8rem;
        font-weight: 700;
        width: 100%;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA ENGINE: QUALITY + GROWTH + VALUE
# ==========================================

def get_nifty_tickers(universe):
    url = "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty500list.csv" if universe == "Nifty 500" else "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty50list.csv"
    try:
        df = pd.read_csv(url)
        return [str(s) + ".NS" for s in df['Symbol'].tolist()]
    except:
        return ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "ITC.NS"]

def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Pulling Metrics
        roe = info.get('returnOnEquity', 0) * 100
        pe = info.get('trailingPE', 0)
        rev_growth = info.get('revenueGrowth', 0) * 100
        eps = info.get('trailingEps', 0)
        book_val = info.get('bookValue', 0)
        price = info.get('currentPrice', 0)
        
        # Graham Formula: sqrt(22.5 * EPS * BVPS)
        graham_val = np.sqrt(22.5 * eps * book_val) if (eps > 0 and book_val > 0) else 0

        # STRICT FILTER: Quality > 15% | Growth > 5% | Value P/E < 30
        if (15 < roe < 100 and rev_growth > 5 and 0 < pe < 30):
            return {
                "Ticker": ticker.replace(".NS", ""),
                "Price": price,
                "Graham Val": round(graham_val, 2),
                "ROE (%)": round(roe, 2),
                "Rev Growth (%)": round(rev_growth, 2),
                "P/E": round(pe, 2),
                "Debt/Eq": round(info.get('debtToEquity', 0), 2)
            }
    except: return None

# ==========================================
# 3. INTERFACE EXECUTION
# ==========================================

st.title("🏛️ The Buffett Way")
st.markdown("### Fundamental Growth & Value Dashboard")

with st.sidebar:
    st.markdown("## Filter Settings")
    universe = st.selectbox("Market Selection", ["Nifty 50", "Nifty 500"])
    st.write("---")
    st.markdown("**Criteria:**")
    st.write("✅ ROE > 15%")
    st.write("✅ Rev Growth > 5%")
    st.write("✅ P/E < 30")

if st.button(f"🚀 Analyze {universe}"):
    tickers = get_nifty_tickers(universe)
    
    with st.spinner(f"Processing {len(tickers)} companies..."):
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_ticker = {executor.submit(analyze_stock, t): t for t in tickers}
            for future in concurrent.futures.as_completed(future_to_ticker):
                res = future.result()
                if res: results.append(res)
    
    if results:
        df = pd.DataFrame(results).sort_values("ROE (%)", ascending=False)
        
        # --- UI DESIGN: HIGH CONTRAST DATASET ---
        # Using light pastel gradients to keep text black and readable
        styled_df = df.style.background_gradient(subset=["ROE (%)"], cmap="YlGn") \
                           .background_gradient(subset=["Rev Growth (%)"], cmap="BuGn") \
                           .background_gradient(subset=["P/E"], cmap="YlOrRd") \
                           .format({
                               "Price": "₹{:.2f}", 
                               "Graham Val": "₹{:.2f}",
                               "ROE (%)": "{:.1f}%",
                               "Rev Growth (%)": "{:.1f}%"
                           })

        st.dataframe(styled_df, use_container_width=True, height=600)
    else:
        st.error("No stocks currently meet the Quality + Growth + Value criteria.")

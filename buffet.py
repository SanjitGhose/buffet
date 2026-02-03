import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import concurrent.futures

# ==========================================
# 1. UI/UX HIGH-CONTRAST "GROWW" STYLING
# ==========================================
st.set_page_config(page_title="The Buffett Way", layout="wide", page_icon="🏦")

st.markdown("""
<style>
    /* Force High Contrast for Main App */
    .stApp { background-color: #ffffff; }
    
    /* Make Titles & Headers Bold and Dark Charcoal */
    h1, h2, h3, .stMarkdown p {
        color: #0f172a !important; 
        font-family: 'Inter', sans-serif;
    }
    
    /* Force Sidebar Text to be Deep Navy for Readability */
    [data-testid="stSidebar"] {
        background-color: #f1f5f9 !important;
        border-right: 1px solid #cbd5e1;
    }
    [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] label {
        color: #1e293b !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
    }

    /* Groww Green Button */
    .stButton>button {
        background-color: #00d09c;
        color: white; border: none; border-radius: 8px;
        padding: 0.75rem 2rem; font-weight: 700; width: 100%;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA LOGIC & GRAHAM FORMULA
# ==========================================

def get_nifty_tickers(universe):
    url = "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty500list.csv" if universe == "Nifty 500" else "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty50list.csv"
    try:
        df = pd.read_csv(url)
        return [str(s) + ".NS" for s in df['Symbol'].tolist()]
    except:
        return ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "ITC.NS", "SBIN.NS"]

def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Fundamental Data
        roe = info.get('returnOnEquity', 0) * 100
        pe = info.get('trailingPE', 0)
        eps = info.get('trailingEps', 0)
        book_val = info.get('bookValue', 0)
        price = info.get('currentPrice', 0)
        
        # Graham Calculation: sqrt(22.5 * EPS * BVPS)
        if eps > 0 and book_val > 0:
            graham_val = np.sqrt(22.5 * eps * book_val)
        else:
            graham_val = 0

        # The Filter Gate
        if (15 < roe < 100 and 0 < pe < 30):
            return {
                "Ticker": ticker.replace(".NS", ""),
                "Price": price,
                "Graham Val": round(graham_val, 2),
                "ROE (%)": round(roe, 2),
                "P/E": round(pe, 2),
                "Gross Margin (%)": round(info.get('grossMargins', 0) * 100, 2),
                "Debt/Eq": round(info.get('debtToEquity', 0), 2)
            }
    except: return None

# ==========================================
# 3. INTERFACE EXECUTION
# ==========================================

st.title("🏛️ The Buffett Way")
st.markdown("### Intrinsic Value & Quality Screener")

with st.sidebar:
    st.markdown("## Configuration")
    universe = st.selectbox("Market Selection", ["Nifty 50", "Nifty 500"])
    st.info("Logic: Graham Number vs Market Price")

if st.button(f"🔍 Scan {universe}"):
    tickers = get_nifty_tickers(universe)
    
    with st.spinner(f"Auditing {len(tickers)} stocks..."):
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_ticker = {executor.submit(analyze_stock, t): t for t in tickers}
            for future in concurrent.futures.as_completed(future_to_ticker):
                res = future.result()
                if res: results.append(res)
    
    if results:
        df = pd.DataFrame(results).sort_values("ROE (%)", ascending=False)
        
        # --- UI FIX: READABLE PASTEL STYLING ---
        # Using light pastels (Mint & Peach) so black text is 100% visible
        def style_logic(df):
            return df.style.background_gradient(subset=["ROE (%)"], cmap="GnBu") \
                           .background_gradient(subset=["P/E"], cmap="OrRd") \
                           .format({
                               "Price": "₹{:.2f}", 
                               "Graham Val": "₹{:.2f}",
                               "ROE (%)": "{:.1f}%",
                               "Debt/Eq": "{:.2f}"
                           })

        st.dataframe(style_logic(df), use_container_width=True, height=600)
    else:
        st.error("No stocks passed the Graham-Buffett safety threshold.")

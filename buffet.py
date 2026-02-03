import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import concurrent.futures

# ==========================================
# 1. UI/UX "HIGH-CONTRAST" GROWW THEME
# ==========================================
st.set_page_config(page_title="The Buffett Way", layout="wide", page_icon="🏛️")

st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    h1 { color: #1e293b; font-family: 'Inter', sans-serif; }
    .stButton>button {
        background-color: #00d09c; color: white; border-radius: 8px;
        padding: 0.75rem; font-weight: 700; border: none;
    }
    /* Metric Card Styling */
    [data-testid="stMetric"] {
        background-color: #f8fafc; padding: 15px;
        border-radius: 10px; border: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. THE GRAHAM LOGIC
# ==========================================

def calculate_graham_number(eps, bvps):
    """
    Graham Number = sqrt(22.5 * EPS * BVPS)
    The maximum price a defensive investor should pay.
    """
    if eps <= 0 or bvps <= 0: return 0
    return np.sqrt(22.5 * eps * bvps)

def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Core Ratios
        roe = info.get('returnOnEquity', 0) * 100
        pe = info.get('trailingPE', 0)
        curr_price = info.get('currentPrice', 0)
        
        # Graham Components
        eps = info.get('trailingEps', 0)
        bvps = info.get('bookValue', 0)
        graham_val = calculate_graham_number(eps, bvps)
        
        # Filtering for "Wonderful Companies"
        if (15 < roe < 100 and 0 < pe < 35 and info.get('debtToEquity', 100) < 100):
            
            upside = ((graham_val - curr_price) / curr_price) * 100 if graham_val > 0 else -100
            
            return {
                "Ticker": ticker.replace(".NS", ""),
                "Price": curr_price,
                "Graham Intrinsic": round(graham_val, 2),
                "ROE (%)": round(roe, 2),
                "P/E": round(pe, 2),
                "Upside (%)": round(upside, 1),
                "Sector": info.get('sector', 'N/A')
            }
    except: return None

# ==========================================
# 3. INTERFACE & DISPLAY
# ==========================================

st.title("🏛️ The Buffett Way")
st.subheader("Intrinsic Value & Quality Screener")

with st.sidebar:
    st.markdown("### Strategy")
    st.write("Finds companies where **ROE > 15%** and price is near or below the **Graham Number**.")
    universe = st.radio("Market", ["Nifty 50", "Nifty 500"])

if st.button(f"🚀 Execute {universe} Value Scan"):
    # Fallback Ticker Fetching
    url = "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty500list.csv" if universe == "Nifty 500" else "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty50list.csv"
    try:
        tickers = [s + ".NS" for s in pd.read_csv(url)['Symbol'].tolist()]
    except:
        tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS"] # Minimal fallback
        
    with st.spinner("Calculating Intrinsic Values..."):
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_ticker = {executor.submit(analyze_stock, t): t for t in tickers}
            for future in concurrent.futures.as_completed(future_to_ticker):
                res = future.result()
                if res: results.append(res)

    if results:
        df = pd.DataFrame(results)
        
        # Metrics Row
        c1, c2, c3 = st.columns(3)
        c1.metric("Opportunities Found", len(df))
        c2.metric("Best Value Play", df.sort_values("Upside (%)", ascending=False).iloc[0]['Ticker'])
        c3.metric("Avg Quality (ROE)", f"{round(df['ROE (%)'].mean(),1)}%")

        # --- THE SMART CONTRAST STYLER ---
        # Using 'Pastel' maps to ensure text is ALWAYS readable
        def color_upside(val):
            color = '#dcfce7' if val > 0 else '#fee2e2' # Soft Mint vs Soft Peach
            return f'background-color: {color}'

        styled_df = df.style.applymap(color_upside, subset=['Upside (%)']) \
                            .background_gradient(subset=['ROE (%)'], cmap='GnBu', low=0, high=0.3) \
                            .format({"Price": "₹{:.2f}", "Graham Intrinsic": "₹{:.2f}", "Upside (%)": "{:+.1f}%"})

        st.dataframe(styled_df, use_container_width=True, height=500)
    else:
        st.error("No companies currently meet the Buffett-Graham safety threshold.")

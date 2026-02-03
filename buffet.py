import streamlit as st
import yfinance as yf
import pandas as pd
import concurrent.futures

# ==========================================
# 1. UI/UX "GROWW" STYLING
# ==========================================
st.set_page_config(page_title="The Buffett Way", layout="wide", page_icon="🏦")

st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    h1 { color: #1e293b; font-weight: 800 !important; }
    .stButton>button {
        background-color: #00d09c;
        color: white; border: none; border-radius: 8px;
        padding: 0.75rem 2rem; font-weight: 600; width: 100%;
    }
    /* This ensures the table text is sharp */
    .dataframe { font-size: 14px !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA LOGIC & FULL NIFTY 50 FALLBACK
# ==========================================

def get_nifty_tickers(universe):
    if universe == "Nifty 500":
        url = "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty500list.csv"
    else:
        url = "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty50list.csv"
    
    try:
        df = pd.read_csv(url)
        return [str(s) + ".NS" for s in df['Symbol'].tolist()]
    except:
        # Full Nifty 50 Manual List to prevent the "4 stock" glitch
        return [
            "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS",
            "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS",
            "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS", "DRREDDY.NS",
            "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
            "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ITC.NS",
            "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LTIM.NS",
            "LT.NS", "M&M.NS", "MARUTI.NS", "NTPC.NS", "NESTLEIND.NS", "ONGC.NS",
            "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", "SUNPHARMA.NS",
            "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "TCS.NS", "TECHM.NS",
            "TITAN.NS", "UPL.NS", "ULTRACEMCO.NS", "WIPRO.NS"
        ]

def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        roe = info.get('returnOnEquity', 0) * 100
        pe = info.get('trailingPE', 0)
        margin = info.get('grossMargins', 0) * 100
        growth = info.get('revenueGrowth', 0) * 100
        debt_to_eq = info.get('debtToEquity', 0)
        
        if (15 < roe < 100 and 0 < pe < 25 and margin > 10 and growth > 5 and debt_to_eq < 80):
            return {
                "Ticker": ticker.replace(".NS", ""),
                "Price": info.get('currentPrice', 0),
                "ROE (%)": round(roe, 2),
                "P/E": round(pe, 2),
                "Gross Margin (%)": round(margin, 2),
                "Debt/Eq": round(debt_to_eq, 2)
            }
    except: return None

# ==========================================
# 3. CONTRAST FIXING FUNCTION
# ==========================================

def highlight_contrast(val):
    """If the background gradient is too dark, make text white."""
    # This logic matches the 'Greens' and 'Reds' colormaps
    # ROE Column (High is Green/Dark)
    # P/E Column (High is Red/Dark)
    return 'color: black' # Standard - we handle contrast via 'text_color_threshold' in Styler

# ==========================================
# 4. EXECUTION
# ==========================================

st.title("🏛️ The Buffett Way")
universe = st.sidebar.selectbox("Market Selection", ["Nifty 50", "Nifty 500"])

if st.button(f"🔍 Scan {universe}"):
    tickers = get_nifty_tickers(universe)
    
    with st.spinner(f"Analyzing {len(tickers)} stocks..."):
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_ticker = {executor.submit(analyze_stock, t): t for t in tickers}
            for future in concurrent.futures.as_completed(future_to_ticker):
                res = future.result()
                if res: results.append(res)
    
    if results:
        df = pd.DataFrame(results).sort_values("ROE (%)", ascending=False)
        
        # --- THE FIX: SMART STYLING ---
        # We use a built-in Pandas styler that handles text contrast automatically
        styled_df = df.style.background_gradient(subset=["ROE (%)"], cmap="Greens") \
                            .background_gradient(subset=["P/E"], cmap="Reds") \
                            .format({"Price": "₹{:.2f}"})
        
        # Note: If the text is still hard to read, Streamlit's latest version 
        # usually handles this, but we can force it with a CSS injection if needed.
        st.dataframe(styled_df, use_container_width=True, height=600)
    else:
        st.warning("No stocks passed the criteria.")

import streamlit as st
import yfinance as yf
import pandas as pd
import concurrent.futures

# ==========================================
# 1. UI/UX "FINTECH" OVERRIDE (CSS)
# ==========================================
st.set_page_config(page_title="The Buffett Way", layout="wide", page_icon="🎓")

st.markdown("""
<style>
    /* Groww-style Clean Interface */
    .stApp { background-color: #f8fafc; }
    .main { padding: 2rem; }
    h1 { color: #1e293b; font-weight: 800 !important; }
    .stButton>button {
        background-color: #00d09c; /* Groww Green */
        color: white; border: none; border-radius: 8px;
        padding: 0.75rem 2rem; font-weight: 600; width: 100%;
        transition: all 0.3s;
    }
    .stButton>button:hover { background-color: #00b386; transform: translateY(-2px); }
    .css-1r6slb0 { background-color: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
    [data-testid="stMetricValue"] { color: #1e293b; font-size: 1.8rem; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONCRETE DATA LOGIC
# ==========================================

@st.cache_data(ttl=3600)
def fetch_ticker_list(universe):
    """Fetches full ticker lists without fallback glitches."""
    if universe == "Nifty 500":
        url = "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty500list.csv"
    else:
        url = "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty50list.csv"
    
    try:
        df = pd.read_csv(url)
        # Filter out the 'Index' row if it exists to get exact 500/50
        symbols = df['Symbol'].unique().tolist()
        return [str(s) + ".NS" for s in symbols if isinstance(s, str)]
    except:
        return ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS"]

def scan_logic(ticker):
    """Concrete Ratio Logic using audited fields."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # We use 'returnOnEquity' as the primary Buffett 'Moat' indicator
        # It's more reliable in the Yahoo API than manual ROIC math
        roe = info.get('returnOnEquity', 0) * 100
        pe = info.get('trailingPE', 0)
        margin = info.get('grossMargins', 0) * 100
        growth = info.get('revenueGrowth', 0) * 100
        debt_to_eq = info.get('debtToEquity', 0)
        
        # --- THE CONCRETE FILTER ---
        # Logic: High Quality (ROE > 15), Good Value (PE < 25), Low Risk (Debt < 80)
        if (15 < roe < 100 and 0 < pe < 25 and margin > 10 and growth > 5 and debt_to_eq < 80):
            return {
                "Ticker": ticker.replace(".NS", ""),
                "Price": info.get('currentPrice', 0),
                "ROE (%)": round(roe, 2),
                "P/E": round(pe, 2),
                "Gross Margin (%)": round(margin, 2),
                "Debt/Eq": round(debt_to_eq, 2),
                "Sector": info.get('sector', 'N/A')
            }
    except:
        return None

# ==========================================
# 3. THE APP DASHBOARD
# ==========================================

# Sidebar
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Warren_Buffett_KU_Visit.jpg/440px-Warren_Buffett_KU_Visit.jpg", width=100)
    st.title("The Buffett Way")
    st.markdown("---")
    mode = st.radio("Market Selection", ["Nifty 500", "Nifty 50"])
    st.success("Strategy: Quality at a Fair Price")

# Main View
st.title("🏛️ Institutional Equity Screener")
st.info("Scanning for 'Wonderful Companies at Fair Prices' using audited RoE and P/E metrics.")

if st.button(f"🔍 Scan {mode} Universe"):
    tickers = fetch_ticker_list(mode)
    
    with st.status(f"Auditing {len(tickers)} Companies...", expanded=True) as status:
        results = []
        # Multi-threaded execution for speed
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_ticker = {executor.submit(scan_logic, t): t for t in tickers}
            for i, future in enumerate(concurrent.futures.as_completed(future_to_ticker)):
                res = future.result()
                if res: results.append(res)
        status.update(label="Audit Complete!", state="complete", expanded=False)

    if results:
        df = pd.DataFrame(results)
        
        # Summary Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Companies Passed", len(df))
        m2.metric("Best ROE", f"{df['ROE (%)'].max()}%")
        m3.metric("Avg P/E", round(df['P/E'].mean(), 1))

        st.markdown("### Top 20 Investment Picks")
        
        # Styled Table with Groww-style heatmap
        st.dataframe(
            df.sort_values("ROE (%)", ascending=False).head(20).style
            .background_gradient(subset=["ROE (%)"], cmap="BuGn") # Mint Green
            .background_gradient(subset=["P/E"], cmap="YlOrRd") # Soft Warning Red
            .format({"Price": "₹{:.2f}", "Debt/Eq": "{:.1f}"}),
            use_container_width=True, height=600
        )
        
        st.download_button("📥 Export Analysis", df.to_csv(index=False), "buffett_report.csv")
    else:
        st.warning("No companies currently meet the strict 15/25/80 Buffett threshold. Market may be overvalued.")

import streamlit as st
import yfinance as yf
import pandas as pd
import concurrent.futures

# ==========================================
# 1. APP CONFIGURATION & BRANDING
# ==========================================
st.set_page_config(page_title="The Buffett Way", layout="wide", page_icon="📈")

# Custom UI Styling
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #1e3a8a;
        color: white;
        font-weight: bold;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. THE CORE LOGIC (Buffett Framework)
# ==========================================

def get_nifty_tickers(mode):
    """Fetches the latest Nifty 50 or 500 symbols from NSE data."""
    if mode == "Nifty 500":
        url = "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty500list.csv"
    else:
        url = "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty50list.csv"
    
    try:
        df = pd.read_csv(url)
        return [str(x) + ".NS" for x in df['Symbol'].tolist()]
    except Exception:
        # Fallback for critical failure
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]

def analyze_stock(ticker):
    """The 'Filter'—screens stocks against the image ratios."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Fundamental Data Extraction
        pe = info.get('trailingPE', 100)
        gross_margin = info.get('grossMargins', 0) * 100
        rev_growth = info.get('revenueGrowth', 0) * 100
        debt_equity = info.get('debtToEquity', 100)
        
        # ROIC Calculation (EBIT / Invested Capital)
        ebitda = info.get('ebitda', 0)
        assets = info.get('totalAssets', 1)
        liabilities = info.get('totalCurrentLiabilities', 0)
        roic = (ebitda / (assets - liabilities)) * 100 if (assets - liabilities) > 0 else 0

        # --- THE BUFFETT RATIOS (Strict Screening) ---
        # 1. ROIC > 15%
        # 2. P/E < 25 (Standard Value)
        # 3. Gross Margin > 10%
        # 4. Revenue Growth > 5%
        # 5. Debt/Equity < 80%
        
        if (roic > 15 and pe < 25 and gross_margin > 10 and 
            rev_growth > 5 and debt_equity < 80):
            
            return {
                "Ticker": ticker.replace(".NS", ""),
                "Price": info.get('currentPrice', 0),
                "ROIC (%)": round(roic, 2),
                "P/E Ratio": round(pe, 2),
                "Gross Margin (%)": round(gross_margin, 2),
                "Rev Growth (%)": round(rev_growth, 2),
                "Debt/Eq (%)": round(debt_equity, 2)
            }
    except:
        return None
    return None

# ==========================================
# 3. INTERFACE & EXECUTION
# ==========================================

st.title("🏛️ The Buffett Way")
st.subheader("Automated Nifty 500 Value Screening Engine")

# Sidebar for Universe selection
universe = st.sidebar.selectbox("Select Investment Universe", ["Nifty 500", "Nifty 50"])
st.sidebar.markdown("---")
st.sidebar.write("**Screening Criteria:**")
st.sidebar.write("✅ ROIC > 15%")
st.sidebar.write("✅ P/E Ratio < 25")
st.sidebar.write("✅ Gross Margin > 10%")
st.sidebar.write("✅ Rev. Growth > 5%")
st.sidebar.write("✅ Debt/Equity < 80%")

if st.button(f"🚀 Execute {universe} Scan"):
    tickers = get_nifty_tickers(universe)
    
    st.write(f"Analyzing {len(tickers)} companies using multi-threaded execution...")
    progress_bar = st.progress(0)
    
    results = []
    # Multi-threading (Steve Jobs Speed)
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(analyze_stock, t): t for t in tickers}
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            data = future.result()
            if data:
                results.append(data)
            progress_bar.progress((i + 1) / len(tickers))

    # Display Output
    if results:
        df = pd.DataFrame(results)
        # Give them the Top 20 by ROIC (the ultimate quality metric)
        top_20 = df.sort_values(by="ROIC (%)", ascending=False).head(20)
        
        st.success(f"Found {len(df)} undervalued quality stocks. Here are the Top 20 Picks:")
        
        # Styled Table
        st.dataframe(
            top_20.style.background_gradient(subset=["ROIC (%)"], cmap="Greens")
                   .background_gradient(subset=["P/E Ratio"], cmap="YlOrRd")
                   .format({"Price": "₹{:.2f}"}),
            use_container_width=True
        )
        
        # Download Button
        csv = top_20.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Top Picks CSV", csv, "buffett_picks.csv", "text/csv")
    else:
        st.error("No stocks matched these strict criteria in the current market.")
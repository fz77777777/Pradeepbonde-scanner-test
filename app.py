import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==========================================
# PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Stockbee Episodic Pivot Scanner",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Minimal UI Theme (Muted accents, bold typography)
st.markdown("""
    <style>
    .reportview-container { background: #fafafa; }
    .stButton>button { 
        background-color: #2b5797; 
        color: white; 
        border-radius: 6px; 
        font-weight: bold;
        padding: 0.5rem 2rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: #1e3f66;
        color: #eeeeee;
    }
    h1 { color: #111111; font-family: 'Helvetica Neue', Arial, sans-serif; font-weight: 800; }
    h2, h3 { color: #222222; font-family: 'Helvetica Neue', Arial, sans-serif; font-weight: 700; }
    div[data-testid="stSidebarUserContent"] {
        background-color: #f4f6f9;
        padding: 1.5rem;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# Title Header
st.title("🚀 Pradeep Bonde's Stockbee EP/LEP Scanner")
st.markdown("### **Real-Time Institutional Momentum Engine (Indian Stock Market)**")
st.write("---")

# ==========================================
# SIDEBAR CONTROL PANEL & RULES
# ==========================================
with st.sidebar:
    st.header("🎯 Strategy Parameters")
    
    st.markdown("### **Core EP Rules:**")
    min_gain = st.slider("Minimum Price Gain (%)", min_value=4.0, max_value=15.0, value=8.0, step=0.5)
    vol_multiplier = st.slider("Volume Multiplier (x Volume SMA50)", min_value=1.5, max_value=5.0, value=3.0, step=0.1)
    lookback_days = st.slider("Lookback Scan Window (Days)", min_value=5, max_value=30, value=15, step=1)
    
    st.write("---")
    st.markdown("""
    ### **Pradeep Bonde (Stockbee) Definitions:**
    1. **Fresh Episodic Pivot (EP):** An explosive gap-up or intraday blast (>8% gain) driven by a **Catalyst** (Earnings, Big Orders) on massive institutional volume (>3x of 50-day average volume).
    2. **Late Episodic Pivot (LEP):** Occurs when the stock consolidates orderly for 2-15 days after a fresh EP, drifting quietly into the **10 EMA** or **20 EMA** on dry volumes, offering a low-risk entries.
    """)
    st.info("💡 **Entry Execution Tip:** As sikhaya gaya in videos, allow a 1-minute delay after open to bypass initial market shakeouts before execution via Opening Range Breakouts (ORB).")

# ==========================================
# MASTER TICKER LIST (High-Momentum Liquid Indian Stocks)
# ==========================================
# Extensively covered across Nifty Midcap and Smallcap spaces for high explosive potential (< $10B market cap rule)
TICKER_LIST = [
    "CDSL.NS", "BSE.NS", "RVNL.NS", "IRCON.NS", "ZOMATO.NS", "HUDCO.NS", "ANGELONE.NS",
    "SUZLON.NS", "MAHSEAMLES.NS", "COCHINSHIP.NS", "MAZDOCK.NS", "NBCC.NS", "TATAINVEST.NS",
    "IREDA.NS", "FACT.NS", "RITES.NS", "PPLPHARMA.NS", "HBLPOWER.NS", "MOTILALOFS.NS",
    "MANINDS.NS", "TEXRAIL.NS", "RAILTEL.NS", "NCC.NS", "JWL.NS", "TITAGARH.NS", "IRFC.NS",
    "JIOFIN.NS", "OLAELEC.NS", "KFINTECH.NS", "CENTURYTEX.NS", "TATAELXSI.NS", "BDL.NS",
    "BEL.NS", "HINDCOPPER.NS", "NATIONALUM.NS", "SAIL.NS", "GMRINFRA.NS", "POONAWALLA.NS"
]

# ==========================================
# DATA FETCHING ENGINE (CACHED)
# ==========================================
@st.cache_data(ttl=1800)  # Cache for 30 minutes to optimize rate limits
def fetch_ticker_data(ticker):
    try:
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%d')
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        return df
    except Exception:
        return None

# ==========================================
# SCANNING LOGIC FRAMEWORK
# ==========================================
def scan_stockbee_criteria(df, min_gain, vol_mult, scan_window):
    if df is None or len(df) < 55:
        return []
    
    # Structural Cleaning for Multi-Level Columns (yfinance update standard)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    df = df.copy()
    
    # Calculate Quantitative Technical Indicators
    df['Vol_SMA'] = df['Volume'].rolling(window=50).mean()
    df['Pct_Change'] = df['Close'].pct_change() * 100
    df['EMA_10'] = ta.ema(df['Close'], length=10)
    df['EMA_20'] = ta.ema(df['Close'], length=20)
    
    results = []
    total_len = len(df)
    
    # Run loop over the requested trailing scan window
    for idx in range(total_len - scan_window, total_len):
        if idx < 0:
            continue
            
        row = df.iloc[idx]
        
        # Extracted parameters converted to native floats safely
        close_p = float(row['Close'])
        pct_chg = float(row['Pct_Change'])
        volume = float(row['Volume'])
        vol_sma = float(row['Vol_SMA'])
        
        # Evaluate Strict Stockbee EP Logic Match
        if pct_chg >= min_gain and volume >= (vol_mult * vol_sma):
            days_ago = total_len - 1 - idx
            
            # Latest state comparison for current market day setup mapping
            latest_close = float(df.iloc[-1]['Close'])
            latest_ema10 = float(df.iloc[-1]['EMA_10'])
            latest_ema20 = float(df.iloc[-1]['EMA_20'])
            
            if days_ago == 0:
                status = "🚨 FRESH EP TRIGGERED TODAY"
            else:
                # Late EP Verification: Checking pullback compression near key tracking lines
                near_10_ema = abs(latest_close - latest_ema10) / latest_ema10 <= 0.025
                near_20_ema = abs(latest_close - latest_ema20) / latest_ema20 <= 0.025
                
                if near_10_ema or near_20_ema:
                    status = f"⏳ LATE EP (EMA Pullback Consolidation, EP {days_ago} Days Ago)"
                else:
                    status = f"ℹ️ Past EP ({days_ago} Days Ago - Currently Extended)"
            
            results.append({
                "Date of EP": df.index[idx].strftime('%Y-%m-%d'),
                "Current Close": round(float(df.iloc[-1]['Close']), 2),
                "Breakout Gain %": round(pct_chg, 2),
                "Volume Multiple": round(volume / vol_sma, 2),
                "Setup Status": status,
                "Actionable Order Route": "OPG Route (If High Conviction) / 1-Min Range Breakout"
            })
            break  # Break loop on latest significant cluster to prevent multi-tagging single ticker
            
    return results

# ==========================================
# INTERACTIVE CONTROL WORKFLOW
# ==========================================
if st.button("🔍 RUN INTENSITY MARKET SCANNER"):
    st.write("Initializing data pipelines to cross-verify structural chart setups...")
    
    scanned_data_pool = []
    
    # Progress indication for smoother UI
    progress_bar = st.progress(0)
    for index, ticker in enumerate(TICKER_LIST):
        raw_df = fetch_ticker_data(ticker)
        findings = scan_stockbee_criteria(raw_df, min_gain, vol_multiplier, lookback_days)
        
        if findings:
            for item in findings:
                item['Ticker Symbol'] = ticker.replace('.NS', '')
                scanned_data_pool.append(item)
        progress_bar.progress((index + 1) / len(TICKER_LIST))
        
    st.write("---")
    
    if scanned_data_pool:
        final_reporting_df = pd.DataFrame(scanned_data_pool)
        
        # Columns arrangement
        cols_order = ['Ticker Symbol', 'Setup Status', 'Breakout Gain %', 'Volume Multiple', 'Current Close', 'Date of EP', 'Actionable Order Route']
        final_reporting_df = final_reporting_df[cols_order]
        
        st.success(f"Tracked {len(final_reporting_df)} stocks fulfilling strict institutional rules.")
        
        # Render stylized color gradient charts data grid
        st.dataframe(
            final_reporting_df.style.background_gradient(cmap='YlOrRd', subset=['Volume Multiple'])
            .format({"Breakout Gain %": "{:.2f}%", "Volume Multiple": "{:.2f}x", "Current Close": "₹{:.2f}"})
        )
        
        # Display Visual Plot for the first prioritized scanned candidate
        st.write("---")
        priority_ticker = final_reporting_df.iloc[0]['Ticker Symbol']
        st.subheader(f"📈 Real-Time Technical Visual Dashboard: NSE: {priority_ticker}")
        
        chart_source = fetch_ticker_data(priority_ticker + ".NS")
        if isinstance(chart_source.columns, pd.MultiIndex):
            chart_source.columns = chart_source.columns.get_level_values(0)
            
        # Truncate to recent 90 candles for clear perspective visibility
        plot_df = chart_source.tail(90)
        
        fig = go.Figure()
        
        # Main Candlestick Tracks
        fig.add_trace(go.Candlestick(
            x=plot_df.index,
            open=plot_df['Open'],
            high=plot_df['High'],
            low=plot_df['Low'],
            close=plot_df['Close'],
            name="Candlestick Price"
        ))
        
        # Overlay moving dynamic averages
        plot_df['EMA_10'] = ta.ema(plot_df['Close'], length=10)
        plot_df['EMA_20'] = ta.ema(plot_df['Close'], length=20)
        
        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['EMA_10'], line=dict(color='#2b5797', width=1.5), name="10 Period EMA"))
        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['EMA_20'], line=dict(color='#d9534f', width=1.5), name="20 Period EMA"))
        
        fig.update_layout(
            title=f"Tracking Layout Framework (90 Dynamic Sessions for {priority_ticker})",
            xaxis_rangeslider_visible=False,
            template="plotly_white",
            height=600,
            xaxis_title="Timeline Sessions Date",
            yaxis_title="Price Range (INR)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.warning("Filters Active: No liquid assets found displaying high volume institutional accumulation today. Try relaxing parameter slider thresholds.")

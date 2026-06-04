import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==========================================
# PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Stockbee Nifty 500 Ultra-Fast Scanner",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Minimal UI Theme
st.markdown("""
    <style>
    .stButton>button { 
        background-color: #2b5797; 
        color: white; 
        border-radius: 6px; 
        font-weight: bold;
        padding: 0.5rem 2rem;
    }
    .stButton>button:hover { background-color: #1e3f66; color: #eeeeee; }
    h1 { color: #111111; font-family: 'Helvetica Neue', Arial, sans-serif; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Stockbee EP/LEP Nifty 500 Fast-Scanner")
st.markdown("### **Optimized Institutional Momentum Engine (Large, Mid & Small Cap)**")
st.write("---")

# ==========================================
# SIDEBAR CONTROL PANEL
# ==========================================
with st.sidebar:
    st.header("🎯 Strategy Parameters")
    min_gain = st.slider("Minimum Price Gain (%)", min_value=4.0, max_value=15.0, value=7.0, step=0.5)
    vol_multiplier = st.slider("Volume Multiplier (x Volume SMA50)", min_value=1.5, max_value=5.0, value=2.5, step=0.1)
    lookback_days = st.slider("Lookback Scan Window (Days)", min_value=5, max_value=30, value=15, step=1)
    
    st.write("---")
    market_segment = st.multiselect(
        "Select Market Segment",
        options=["LARGE CAP", "MID CAP", "SMALL CAP"],
        default=["LARGE CAP", "MID CAP"]
    )

# ==========================================
# DYNAMIC NIFTY 500 TICKER LOADER
# ==========================================
@st.cache_data(ttl=86400)
def load_nifty500_tickers():
    try:
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        df = pd.read_csv(url)
        df['Segment'] = 'SMALL CAP'
        df.iloc[0:100, df.columns.get_loc('Segment')] = 'LARGE CAP'
        df.iloc[100:250, df.columns.get_loc('Segment')] = 'MID CAP'
        df['Symbol_YF'] = df['Symbol'] + ".NS"
        return df[['Symbol_YF', 'Symbol', 'Company Name', 'Segment']]
    except Exception as e:
        st.error(f"Error fetching Nifty 500 list: {e}")
        return pd.DataFrame({'Symbol_YF': ["RELIANCE.NS"], 'Symbol': ["RELIANCE"], 'Company Name': ["Reliance"], 'Segment': ["LARGE CAP"]})

master_universe = load_nifty500_tickers()
filtered_universe = master_universe[master_universe['Segment'].isin(market_segment)]
TICKER_LIST = filtered_universe['Symbol_YF'].tolist()
TICKER_MAP = dict(zip(filtered_universe['Symbol_YF'], filtered_universe['Company Name']))

st.info(f"📊 Current Scan Universe: **{len(TICKER_LIST)} Stocks** active from selected segments.")

# ==========================================
# ULTRA-FAST BATCH FETCH ENGINE
# ==========================================
@st.cache_data(ttl=1800)
def fetch_all_data_batch(tickers):
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%d')
    # Ek sath saare tickers ka data single request mein pull karega (No loops = No slowness)
    df = yf.download(tickers, start=start_date, end=end_date, group_by='ticker', progress=False)
    return df

# ==========================================
# MAIN EXECUTION
# ==========================================
if st.button("🔍 RUN NIFTY 500 FAST SCANNER"):
    st.write("⚡ Fetching market matrix via Parallel Batch Engine...")
    
    with st.spinner("Downloading historical data structure..."):
        all_data = fetch_all_data_batch(TICKER_LIST)
        
    st.write("⚙️ Processing Stockbee mathematical filters...")
    scanned_data_pool = []
    
    # Process data instantly from local memory dataframes
    for ticker in TICKER_LIST:
        try:
            # MultiIndex handling for batch download
            if len(TICKER_LIST) > 1:
                df = all_data[ticker].dropna()
            else:
                df = all_data.dropna()
                
            if len(df) < 55:
                continue
                
            df = df.copy()
            df['Vol_SMA'] = df['Volume'].rolling(window=50).mean()
            df['Pct_Change'] = df['Close'].pct_change() * 100
            df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
            df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
            
            total_len = len(df)
            
            for idx in range(total_len - lookback_days, total_len):
                if idx < 0: continue
                row = df.iloc[idx]
                pct_chg = float(row['Pct_Change'])
                volume = float(row['Volume'])
                vol_sma = float(row['Vol_SMA'])
                
                if pct_chg >= min_gain and volume >= (vol_multiplier * vol_sma):
                    days_ago = total_len - 1 - idx
                    latest_close = float(df.iloc[-1]['Close'])
                    latest_ema10 = float(df.iloc[-1]['EMA_10'])
                    latest_ema20 = float(df.iloc[-1]['EMA_20'])
                    
                    if days_ago == 0:
                        status = "🚨 FRESH EP TODAY"
                    else:
                        near_10 = abs(latest_close - latest_ema10) / latest_ema10 <= 0.025
                        near_20 = abs(latest_close - latest_ema20) / latest_ema20 <= 0.025
                        status = f"⏳ LATE EP ({days_ago} Days Ago)" if (near_10 or near_20) else f"ℹ️ Past EP ({days_ago} Days Ago)"
                    
                    scanned_data_pool.append({
                        "Ticker Symbol": ticker.replace('.NS', ''),
                        "Company Name": TICKER_MAP.get(ticker, "Unknown"),
                        "Setup Status": status,
                        "Breakout Gain %": f"{round(pct_chg, 2)}%",
                        "Volume Multiple": f"{round(volume / vol_sma, 2)}x",
                        "Current Close": f"₹{round(latest_close, 2)}",
                        "Date of EP": df.index[idx].strftime('%Y-%m-%d')
                    })
                    break
        except Exception:
            continue
            
    st.write("---")
    
    if scanned_data_pool:
        final_df = pd.DataFrame(scanned_data_pool)
        st.success(f"Tracked {len(final_df)} institutional momentum setups!")
        st.dataframe(final_df, use_container_width=True)
        
        # Plot priority asset chart
        priority_ticker = final_df.iloc[0]['Ticker Symbol'] + ".NS"
        try:
            chart_df = all_data[priority_ticker].dropna().tail(90) if len(TICKER_LIST) > 1 else all_data.dropna().tail(90)
            chart_df['EMA_10'] = chart_df['Close'].ewm(span=10, adjust=False).mean()
            chart_df['EMA_20'] = chart_df['Close'].ewm(span=20, adjust=False).mean()
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=chart_df.index, open=chart_df['Open'], high=chart_df['High'], low=chart_df['Low'], close=chart_df['Close'], name="Price"))
            fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['EMA_10'], line=dict(color='#2b5797', width=1.5), name="10 EMA"))
            fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['EMA_20'], line=dict(color='#d9534f', width=1.5), name="20 EMA"))
            fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_white", height=500, title=f"📈 Chart Structure: {priority_ticker.replace('.NS','')}")
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.info("Chart rendering skipped for the selected asset format.")
    else:
        st.warning("No institutional structures detected today. Try widening lookback or lowering volume thresholds.")

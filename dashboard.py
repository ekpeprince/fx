import streamlit as st
import pandas as pd
import os
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="ICT Trading Suite", layout="wide")

st.title("📈 Autonomous ICT Trading Suite")
st.markdown("Monitoring high-probability setups across Forex, Crypto, and Indices.")

@st.cache_data(ttl=60)
def load_trade_logs():
    if os.path.exists("live_trades.csv"):
        return pd.read_csv("live_trades.csv")
    return pd.DataFrame(columns=["Timestamp", "Setup Type", "Entry Price", "Stop Loss", "Position Size"])

logs_df = load_trade_logs()

# Create layout
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🤖 Recent Alerts & Executions")
    if logs_df.empty:
        st.info("No live trades logged yet.")
    else:
        # Sort by newest first
        st.dataframe(logs_df.sort_index(ascending=False), use_container_width=True)
        
        st.metric(label="Total Signals Generated", value=len(logs_df))

with col2:
    st.subheader("📊 Live Market Scanner")
    
    # Let user select asset
    ticker = st.selectbox("Select Asset to View:", ["EURUSD=X", "GBPUSD=X", "BTC-USD", "^GSPC"])
    
    with st.spinner(f"Fetching live data for {ticker}..."):
        try:
            # Fetch last day of 5m data to visualize
            df = yf.download(ticker, period="1d", interval="5m", progress=False)
            
            if not df.empty:
                # Handle potential multi-index in newer yfinance versions
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.droplevel(1)
                    
                fig = go.Figure(data=[go.Candlestick(x=df.index,
                                open=df['Open'],
                                high=df['High'],
                                low=df['Low'],
                                close=df['Close'])])
                                
                fig.update_layout(
                    title=f"{ticker} (5m Timeframe)",
                    yaxis_title="Price",
                    xaxis_rangeslider_visible=False,
                    template="plotly_dark"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"No data returned for {ticker}.")
        except Exception as e:
            st.error(f"Error loading chart: {e}")

st.markdown("---")
st.caption("Powered by Antigravity Autonomous Engine")

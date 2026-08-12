import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from analyst import analyze_market_data
from risk import RiskManager
from execution import connect_mt5, send_limit_order, get_market_data
import MetaTrader5 as mt5
import os
import time
import json
import subprocess
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Antigravity Trading Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- Dark Theme CSS Customization ---
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .metric-card {
        background-color: #262730;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Antigravity MT5 Command Center")

# --- Bot Controls & Status ---
st.sidebar.header("Bot Controls")

def get_bot_status():
    if os.path.exists("bot_status.json"):
        try:
            with open("bot_status.json", "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"status": "OFFLINE", "last_scan": "-", "message": "No data"}

status_data = get_bot_status()
is_active = status_data.get("status") == "ACTIVE"

status_color = "#00FF00" if is_active else "#FF0000"
st.sidebar.markdown(f"**Status:** <span style='color:{status_color}; font-weight:bold;'>{status_data.get('status')}</span>", unsafe_allow_html=True)
st.sidebar.text(f"Last Scan: {status_data.get('last_scan')}")
st.sidebar.text(f"Info: {status_data.get('message')}")

if st.sidebar.button("Start Bot", disabled=is_active):
    # Start bot in background
    subprocess.Popen(["python", "bot.py"])
    time.sleep(1)
    st.rerun()

if st.sidebar.button("Stop Bot", disabled=not is_active):
    # Stop bot by deleting PID file (bot.py handles cleanup but we force kill if needed)
    if os.path.exists("bot.pid"):
        with open("bot.pid", "r") as f:
            pid = f.read().strip()
        try:
            # Quick kill on windows
            os.system(f"taskkill /F /PID {pid}")
        except:
            pass
        os.remove("bot.pid")
    
    # Update status immediately
    with open("bot_status.json", "w") as f:
        json.dump({"status": "OFFLINE", "last_scan": "-", "message": "Force stopped"}, f)
    time.sleep(1)
    st.rerun()

# --- Top Metrics ---
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="metric-card"><h3>Account Balance</h3><h2>$10,000.00</h2></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="metric-card"><h3>Win Rate</h3><h2>68%</h2></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="metric-card"><h3>Daily Signals</h3><h2>3</h2></div>', unsafe_allow_html=True)

st.markdown("---")

# --- Interactive Candlestick Chart (Live Data) ---
st.subheader("Market Visualizer")
selected_symbol = st.selectbox("Select Pair", ["EURUSD", "GBPUSD", "USDJPY"])

login = os.environ.get("MT5_LOGIN")
if login and connect_mt5(int(login), os.environ.get("MT5_PASSWORD"), os.environ.get("MT5_SERVER")):
    df = get_market_data(selected_symbol, mt5.TIMEFRAME_H1, 50)
else:
    df = None

if df is not None:
    fig = go.Figure(data=[go.Candlestick(x=df['time'],
                    open=df['open'], high=df['high'],
                    low=df['low'], close=df['close'])])
    fig.update_layout(template='plotly_dark', margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Failed to connect to MT5 or fetch live data.")

# --- Analysis & Execution ---
st.subheader("Signal Generation & Execution")
if st.button("Generate ICT Signal (Gemini)"):
    with st.spinner("Analyzing market context with Gemini 3.6 Flash..."):
        df_h1 = get_market_data(selected_symbol, mt5.TIMEFRAME_H1, 50)
        df_m15 = get_market_data(selected_symbol, mt5.TIMEFRAME_M15, 50)
        if df_h1 is not None and df_m15 is not None:
            recent_h1 = df_h1.tail(10).to_string(index=False)
            recent_m15 = df_m15.tail(10).to_string(index=False)
            market_context = f"--- {selected_symbol} H1 Timeframe (Macro Trend) ---\n{recent_h1}\n\n--- {selected_symbol} M15 Timeframe (Entries) ---\n{recent_m15}"
        else:
            market_context = f"{selected_symbol} data unavailable. Please connect to MT5."
            
        signal = analyze_market_data(market_context)
        st.session_state['latest_signal'] = signal
        st.session_state['latest_symbol'] = selected_symbol
        st.success(f"[{selected_symbol}] Signal Generated: {signal['signal']}")
        st.json(signal)

if 'latest_signal' in st.session_state and st.session_state['latest_signal']['signal'] != "NO_TRADE":
    signal = st.session_state['latest_signal']
    if st.button("Approve & Execute Trade"):
        with st.spinner("Validating Risk and Sending to MT5..."):
            risk_manager = RiskManager()
            if risk_manager.validate_signal(signal, 10000.0, 1.0):
                lot_size = risk_manager.calculate_lot_size(10000.0, signal['entry_price'], signal['stop_loss'])
                st.info(f"Risk validated. Calculated lot size: {lot_size}")
                
                # Mock MT5 connection for demo if credentials aren't set
                login = os.environ.get("MT5_LOGIN")
                if login:
                    if connect_mt5(int(login), os.environ.get("MT5_PASSWORD"), os.environ.get("MT5_SERVER")):
                        order_type = mt5.ORDER_TYPE_BUY_LIMIT if signal['signal'] == "BUY" else mt5.ORDER_TYPE_SELL_LIMIT
                        res = send_limit_order(st.session_state.get('latest_symbol', 'EURUSD'), order_type, lot_size, signal['entry_price'], signal['stop_loss'], signal['take_profit'])
                        if res:
                            st.success(f"[{st.session_state.get('latest_symbol', 'EURUSD')}] Trade Executed Successfully! Ticket: {res.get('order')}")
                        else:
                            st.error(f"[{st.session_state.get('latest_symbol', 'EURUSD')}] Failed to execute trade.")
                    else:
                        st.error("Failed to connect to MT5.")
                else:
                    st.warning("MT5_LOGIN not set in .env. Simulating execution.")
                    st.success("Simulated Trade Executed Successfully!")
            else:
                st.error("Risk validation failed. Trade aborted.")

# --- Real-Time Log Stream ---
st.markdown("---")
st.subheader("Bot Terminal Logs")

def read_logs():
    if os.path.exists("bot.log"):
        with open("bot.log", "r") as f:
            lines = f.readlines()
            return "".join(lines[-20:]) # Show last 20 lines
    return "No logs yet."

st.text_area("Live Logs", value=read_logs(), height=300, disabled=True)

# Auto refresh if bot is active (rudimentary polling)
if is_active:
    time.sleep(5)
    st.rerun()

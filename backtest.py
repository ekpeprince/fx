import os
import sys
import time
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import MetaTrader5 as mt5

from analyst import analyze_market_data
from bot import calculate_rsi, calculate_atr
from execution import connect_mt5

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s", force=True)
logger = logging.getLogger(__name__)

def fetch_historical_data(symbol, timeframe, count):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None or len(rates) == 0:
        logger.error(f"Failed to fetch historical data for {symbol}, error code: {mt5.last_error()}")
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def run_backtest():
    load_dotenv()
    login = os.environ.get("MT5_LOGIN")
    password = os.environ.get("MT5_PASSWORD")
    server = os.environ.get("MT5_SERVER")
    
    if not connect_mt5(int(login), password, server):
        logger.error("Failed to connect to MT5. Exiting.")
        return

    symbol = "EURUSD"
    
    # Fetch ~3 days of M15 data (3 * 24 * 4 = 288 candles)
    # Fetch more to allow for 50-candle history for the first iteration
    logger.info("Fetching historical data...")
    df_m15 = fetch_historical_data(symbol, mt5.TIMEFRAME_M15, 338) 
    df_h1 = fetch_historical_data(symbol, mt5.TIMEFRAME_H1, 150) # H1 history
    
    if df_m15 is None or df_h1 is None:
        return

    df_m15['RSI'] = calculate_rsi(df_m15['close'], 14)
    df_m15['ATR'] = calculate_atr(df_m15, 14)

    trades = []
    initial_balance = 10000.0
    balance = initial_balance

    # Sliding window starting from index 50 to the end
    logger.info("Starting sliding window simulation...")
    
    for i in range(50, len(df_m15) - 1):
        # The window of data available up to time 'i'
        current_m15_time = df_m15.iloc[i]['time']
        window_m15 = df_m15.iloc[i-50:i+1]
        
        current_rsi = window_m15['RSI'].iloc[-1]
        current_atr = window_m15['ATR'].iloc[-1]
        
        # PRE-FILTER to save Gemini API calls!
        # If RSI is > 70 or < 30, our RiskManager would reject it anyway.
        # If RSI is < 50 for BUY or > 50 for SELL, it lacks momentum.
        # We will only query Gemini if RSI is in the "sweet spot" (e.g. 40-60)
        # For this test, let's just use 35-65 to give some room.
        if pd.isna(current_rsi) or current_rsi > 65 or current_rsi < 35:
            continue
            
        # Also require some volatility to justify an entry
        if current_atr < 0.0005: # less than 5 pips ATR
            continue
            
        # Fetch corresponding H1 data up to this point
        window_h1 = df_h1[df_h1['time'] <= current_m15_time].tail(50)
        if window_h1.empty:
            continue

        recent_h1 = window_h1.tail(10).to_string(index=False)
        recent_m15 = window_m15.tail(10).to_string(index=False)
        
        market_context = f"--- {symbol} H1 Timeframe (Macro Trend) ---\n{recent_h1}\n\n--- {symbol} M15 Timeframe (Entries) ---\n{recent_m15}"
        
        logger.info(f"[{current_m15_time}] Criteria met. Querying Gemini... (RSI: {current_rsi:.2f})")
        
        # Query Gemini
        signal = analyze_market_data(market_context)
        
        # Mandatory rate limit sleep for free tier (15 RPM)
        time.sleep(5)
        
        direction = signal.get('signal')
        if direction in ["BUY", "SELL"]:
            entry_price = signal.get('entry_price', 0)
            sl = signal.get('stop_loss', 0)
            tp = signal.get('take_profit', 0)
            
            # Basic validation
            if sl == 0 or tp == 0:
                continue
                
            # Verify SL distance based on ATR
            sl_distance = abs(entry_price - sl)
            if sl_distance < 1.5 * current_atr:
                logger.info(f"[{current_m15_time}] Trade rejected: SL too tight.")
                continue
                
            logger.info(f"[{current_m15_time}] Trade Executed: {direction} @ {entry_price}")
            
            # Simulate Trade Resolution
            # Look forward in time to see which hits first: SL or TP
            trade_result = None
            for j in range(i+1, len(df_m15)):
                future_candle = df_m15.iloc[j]
                
                if direction == "BUY":
                    if future_candle['low'] <= sl:
                        trade_result = "LOSS"
                        break
                    elif future_candle['high'] >= tp:
                        trade_result = "WIN"
                        break
                elif direction == "SELL":
                    if future_candle['high'] >= sl:
                        trade_result = "LOSS"
                        break
                    elif future_candle['low'] <= tp:
                        trade_result = "WIN"
                        break
                        
            if trade_result:
                # Basic P&L calculation assuming 1% risk
                risk_amount = balance * 0.01
                if trade_result == "WIN":
                    # Reward based on R:R ratio
                    rr_ratio = abs(tp - entry_price) / sl_distance
                    profit = risk_amount * rr_ratio
                    balance += profit
                else:
                    profit = -risk_amount
                    balance += profit
                    
                trades.append({
                    "time": current_m15_time,
                    "direction": direction,
                    "entry": entry_price,
                    "result": trade_result,
                    "pnl": profit,
                    "balance": balance
                })
                logger.info(f"[{current_m15_time}] Trade Closed: {trade_result} (P&L: ${profit:.2f})")
            else:
                logger.info(f"[{current_m15_time}] Trade left open at end of backtest.")

    mt5.shutdown()
    
    # Generate Report
    wins = len([t for t in trades if t['result'] == 'WIN'])
    losses = len([t for t in trades if t['result'] == 'LOSS'])
    total = wins + losses
    win_rate = (wins / total * 100) if total > 0 else 0
    
    report = f"""# Phase 5 Backtest Results

## Performance Summary
- **Initial Balance:** ${initial_balance:.2f}
- **Final Balance:** ${balance:.2f}
- **Net Profit:** ${(balance - initial_balance):.2f}
- **Total Trades:** {total}
- **Win Rate:** {win_rate:.2f}%
- **Wins:** {wins} | **Losses:** {losses}

## Trade Log
| Time | Direction | Entry | Result | P&L | Balance |
|------|-----------|-------|--------|-----|---------|
"""
    for t in trades:
        report += f"| {t['time']} | {t['direction']} | {t['entry']:.5f} | {t['result']} | ${t['pnl']:.2f} | ${t['balance']:.2f} |\n"
        
    with open("backtest_results.md", "w") as f:
        f.write(report)
        
    logger.info("Backtest complete. Results written to backtest_results.md")

if __name__ == "__main__":
    run_backtest()

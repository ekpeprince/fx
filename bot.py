import os
import sys
import time
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
import MetaTrader5 as mt5

from analyst import analyze_market_data
from risk import RiskManager
from execution import connect_mt5, send_limit_order, get_market_data

# PID File and Log setup
PID_FILE = "bot.pid"
LOG_FILE = "bot.log"
STATUS_FILE = "bot_status.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    force=True,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def update_status(status: str, last_scan: str = "", message: str = ""):
    data = {
        "status": status,
        "last_scan": last_scan,
        "message": message,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f)

def calculate_rsi(series, period=14):
    import pandas as pd
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_atr(df, period=14):
    import pandas as pd
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return true_range.rolling(window=period).mean()

def check_pid():
    if os.path.exists(PID_FILE):
        with open(PID_FILE, "r") as f:
            pid = f.read().strip()
        try:
            # Check if process is still running (Windows approach is tricky, we'll just check if file exists for now)
            # In production, we'd use psutil or similar
            logger.error(f"Bot already running with PID {pid}")
            sys.exit(1)
        except Exception:
            pass
            
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

def cleanup_pid():
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    update_status("OFFLINE", message="Bot stopped.")

def bot_loop():
    logger.info("Antigravity Trading Bot Started.")
    update_status("ACTIVE", message="Bot initialized.")
    
    load_dotenv()
    login = os.environ.get("MT5_LOGIN")
    password = os.environ.get("MT5_PASSWORD")
    server = os.environ.get("MT5_SERVER")
    
    if not connect_mt5(int(login), password, server):
        logger.error("Failed to connect to MT5. Exiting.")
        return

    risk_manager = RiskManager(max_risk_per_trade_pct=1.0)
    SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY"]
    
    last_processed = {sym: None for sym in SYMBOLS}

    try:
        while True:
            for symbol in SYMBOLS:
                df_h1 = get_market_data(symbol, mt5.TIMEFRAME_H1, 50)
                df_m15 = get_market_data(symbol, mt5.TIMEFRAME_M15, 50)
                
                if df_h1 is None or df_h1.empty or df_m15 is None or df_m15.empty:
                    continue
                    
                current_candle_time = df_m15.iloc[-1]['time']
                
                if current_candle_time == last_processed[symbol]:
                    update_status("ACTIVE", last_scan=str(current_candle_time), message=f"[{symbol}] Waiting for new M15 candle...")
                    continue
                    
                df_m15['RSI'] = calculate_rsi(df_m15['close'], 14)
                df_m15['ATR'] = calculate_atr(df_m15, 14)
                
                current_rsi = df_m15['RSI'].iloc[-2] # Use closed candle
                current_atr = df_m15['ATR'].iloc[-2]
                
                logger.info(f"[{symbol}] Scanning market at {current_candle_time} (RSI: {current_rsi:.2f}, ATR: {current_atr:.5f})")
                update_status("ACTIVE", last_scan=str(current_candle_time), message=f"[{symbol}] Scanning... RSI: {current_rsi:.1f}")
                
                recent_h1 = df_h1.tail(10).to_string(index=False)
                recent_m15 = df_m15.tail(10).to_string(index=False)
                market_context = f"--- {symbol} H1 Timeframe (Macro Trend) ---\n{recent_h1}\n\n--- {symbol} M15 Timeframe (Entries) ---\n{recent_m15}"
                
                signal = analyze_market_data(market_context)
                
                if signal.get('signal') in ["BUY", "SELL"]:
                    # Sometimes Gemini returns 'entry' instead of 'entry_price'
                    entry_p = signal.get('entry_price') or signal.get('entry')
                    signal['entry_price'] = entry_p
                    
                    logger.info(f"[{symbol}] Signal received: {signal['signal']} @ {signal.get('entry_price')}")
                    
                    account_info = mt5.account_info()
                    if not account_info:
                        continue
                        
                    balance = account_info.balance
                    
                    # Fetch real-time tick to ensure accuracy
                    tick = mt5.symbol_info_tick(symbol)
                    current_price = tick.ask if signal['signal'] == "BUY" else tick.bid
                    logger.info(f"[{symbol}] Current Real-Time Tick Price: {current_price}")
                    
                    if risk_manager.validate_signal(signal, balance, 0.0, rsi=current_rsi, atr=current_atr):
                        lot_size = risk_manager.calculate_lot_size(balance, signal['entry_price'], signal['stop_loss'])
                        logger.info(f"[{symbol}] Risk OK. Calculated Lot Size: {lot_size}")
                        
                        order_type = mt5.ORDER_TYPE_BUY_LIMIT if signal['signal'] == "BUY" else mt5.ORDER_TYPE_SELL_LIMIT
                        
                        res = send_limit_order(symbol, order_type, lot_size, signal['entry_price'], signal['stop_loss'], signal['take_profit'])
                        if res:
                            logger.info(f"[{symbol}] Trade Executed: Ticket {res.get('order')}")
                        else:
                            logger.error(f"[{symbol}] Execution failed.")
                    else:
                        logger.warning(f"[{symbol}] Risk validation rejected the trade.")
                else:
                    logger.info(f"[{symbol}] No setup found (NO_TRADE).")
                    
                last_processed[symbol] = current_candle_time
                update_status("ACTIVE", last_scan=str(current_candle_time), message=f"[{symbol}] Waiting for next cycle.")
                
                # PAUSE BETWEEN PAIRS TO PROTECT API QUOTA
                time.sleep(15)
                
            time.sleep(30)
            
    except KeyboardInterrupt:
        logger.info("Bot shutting down...")
    finally:
        mt5.shutdown()
        cleanup_pid()

if __name__ == "__main__":
    check_pid()
    bot_loop()

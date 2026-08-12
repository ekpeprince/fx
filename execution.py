import MetaTrader5 as mt5
import logging
import pandas as pd
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connect_mt5(login: int, password: str, server: str) -> bool:
    if not mt5.initialize():
        logger.error(f"MT5 initialization failed, error code = {mt5.last_error()}")
        return False
    
    authorized = mt5.login(login, password=password, server=server)
    if authorized:
        logger.info(f"Connected to MT5 server: {server}")
        return True
    else:
        logger.error(f"Failed to connect at account #{login}, error code: {mt5.last_error()}")
        return False

def send_limit_order(symbol: str, order_type: int, volume: float, price: float, sl: float, tp: float) -> Optional[dict]:
    request = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": symbol,
        "volume": float(volume),
        "type": order_type,
        "price": float(price),
        "sl": float(sl),
        "tp": float(tp),
        "deviation": 10,
        "magic": 100200,
        "comment": "Antigravity Gemini ICT Signal",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    logger.info(f"Sending order request: {request}")
    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logger.error(f"Order send failed, retcode={result.retcode}")
        return None
        
    logger.info(f"Order placed successfully: ticket={result.order}")
    return result._asdict()

def get_market_data(symbol: str, timeframe: int, count: int) -> Optional[pd.DataFrame]:
    """
    Fetches the last N candles for a symbol.
    timeframe: e.g. mt5.TIMEFRAME_H1
    """
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None or len(rates) == 0:
        logger.error(f"Failed to fetch market data for {symbol}, error code: {mt5.last_error()}")
        return None
        
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df


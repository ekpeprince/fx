from datetime import datetime
import pandas as pd

def is_in_killzone(timestamp_str):
    """
    Checks if the timestamp falls within the London or New York Killzones.
    London: 2:00 AM - 5:00 AM NY Time (approx 7:00-10:00 UTC)
    New York: 7:00 AM - 10:00 AM NY Time (approx 12:00-15:00 UTC)
    Note: For simplicity with yfinance default UTC data, we will check UTC hours:
    London (UTC): 07:00 - 10:00
    New York (UTC): 12:00 - 15:00
    """
    try:
        # yfinance timestamps look like: "2023-10-27 09:30:00-04:00"
        dt = pd.to_datetime(timestamp_str)
        # Convert to UTC to standardize
        if dt.tzinfo is not None:
            dt_utc = dt.tz_convert('UTC')
        else:
            dt_utc = dt
            
        hour = dt_utc.hour
        
        in_london = 7 <= hour < 10
        in_ny = 12 <= hour < 15
        
        return in_london or in_ny
    except Exception:
        return False

def detect_order_block(ohlcv_data, index, direction):
    """
    Detects if there was an Order Block near the FVG.
    Looks back a few candles from `index` to find the last opposing candle.
    """
    lookback = 5
    start_idx = max(0, index - lookback)
    
    for i in range(index - 1, start_idx - 1, -1):
        candle = ohlcv_data[i]
        is_bullish_candle = candle['close'] > candle['open']
        is_bearish_candle = candle['close'] < candle['open']
        
        if direction == "Bullish FVG" and is_bearish_candle:
            # Found the last down candle before the up move
            return True, candle['low']
        elif direction == "Bearish FVG" and is_bullish_candle:
            # Found the last up candle before the down move
            return True, candle['high']
            
    return False, None

def detect_fvg(ohlcv_data):
    """
    Scans a list of OHLCV dictionaries for Fair Value Gaps (FVG).
    Requires a minimum of 3 candles.
    """
    setups = []
    if len(ohlcv_data) < 3:
        return setups

    for i in range(2, len(ohlcv_data)):
        candle1 = ohlcv_data[i-2]
        candle3 = ohlcv_data[i]
        
        timestamp = candle3['timestamp']
        
        # Confluence Check 1: Killzone
        if not is_in_killzone(timestamp):
            continue

        # Bullish FVG: low of 3rd candle > high of 1st candle
        if candle3['low'] > candle1['high']:
            gap_size = candle3['low'] - candle1['high']
            
            # Confluence Check 2: Order Block
            has_ob, ob_level = detect_order_block(ohlcv_data, i, "Bullish FVG")
            
            if has_ob:
                setups.append({
                    "type": "Bullish FVG + OB",
                    "timestamp": timestamp,
                    "gap_top": candle3['low'],
                    "gap_bottom": candle1['high'],
                    "size": gap_size,
                    "ob_level": ob_level
                })

        # Bearish FVG: high of 3rd candle < low of 1st candle
        elif candle3['high'] < candle1['low']:
            gap_size = candle1['low'] - candle3['high']
            
            has_ob, ob_level = detect_order_block(ohlcv_data, i, "Bearish FVG")
            
            if has_ob:
                setups.append({
                    "type": "Bearish FVG + OB",
                    "timestamp": timestamp,
                    "gap_top": candle1['low'],
                    "gap_bottom": candle3['high'],
                    "size": gap_size,
                    "ob_level": ob_level
                })

    return setups

def evaluate_market_data(ohlcv_data):
    """
    Ingests structured market data (OHLCV format) and evaluates against ICT rules.
    Outputs trade setup recommendations.
    """
    recommendations = []
    
    # 1. Detect FVGs with Confluence
    fvg_setups = detect_fvg(ohlcv_data)
    for setup in fvg_setups:
        recommendation = {
            "setup_type": setup["type"],
            "entry_zone": (setup["gap_bottom"], setup["gap_top"]),
            "timestamp": setup["timestamp"],
            "ob_level": setup["ob_level"],
            "reason": f"High-probability {setup['type']} formed in a Killzone."
        }
        recommendations.append(recommendation)

    return recommendations

if __name__ == "__main__":
    pass

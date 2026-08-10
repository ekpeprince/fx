import yfinance as yf
import pandas as pd

def fetch_live_ohlcv(ticker="EURUSD=X", period="1d", interval="5m"):
    """
    Fetches real market OHLCV data using yfinance.
    Default gets 1 day of 5-minute candles for EUR/USD.
    
    Args:
        ticker (str): The Yahoo Finance ticker symbol (e.g., 'BTC-USD', 'EURUSD=X', 'SPY')
        period (str): Data period to download (e.g., '1d', '5d', '1mo')
        interval (str): Data interval (e.g., '1m', '5m', '15m', '1h', '1d')
        
    Returns:
        list of dict: Structured OHLCV data matching analyzer.py expectations.
    """
    try:
        print(f"Fetching data for {ticker} (Interval: {interval}, Period: {period})...")
        df = yf.download(tickers=ticker, period=period, interval=interval, progress=False)
        
        if df.empty:
            print("Warning: No data returned from yfinance.")
            return []

        structured_data = []
        for index, row in df.iterrows():
            # Get the values, handling potential MultiIndex columns from newer yfinance versions
            open_price = row['Open'].iloc[0] if isinstance(row['Open'], pd.Series) else row['Open']
            high_price = row['High'].iloc[0] if isinstance(row['High'], pd.Series) else row['High']
            low_price = row['Low'].iloc[0] if isinstance(row['Low'], pd.Series) else row['Low']
            close_price = row['Close'].iloc[0] if isinstance(row['Close'], pd.Series) else row['Close']
            volume = row['Volume'].iloc[0] if isinstance(row['Volume'], pd.Series) else row['Volume']
            
            # Use index as string timestamp
            timestamp_str = str(index)
            
            structured_data.append({
                "timestamp": timestamp_str,
                "open": float(open_price),
                "high": float(high_price),
                "low": float(low_price),
                "close": float(close_price),
                "volume": float(volume)
            })
            
        print(f"Successfully fetched {len(structured_data)} candles.")
        return structured_data
    
    except Exception as e:
        print(f"Error fetching market data: {e}")
        return []

def fetch_historical_data(ticker="EURUSD=X", period="60d", interval="1h"):
    """
    Fetches historical OHLCV data using yfinance for backtesting.
    """
    return fetch_live_ohlcv(ticker=ticker, period=period, interval=interval)

if __name__ == "__main__":
    # Test script
    data = fetch_live_ohlcv("BTC-USD", "1d", "15m")
    if data:
        print("Latest candle:", data[-1])

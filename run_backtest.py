from data_pipeline.market_data import fetch_historical_data
from analysis_engine.analyzer import evaluate_market_data
from analysis_engine.backtester import run_backtest

def main():
    print("--- ICT Backtesting Framework ---")
    
    # 1. Fetch historical data (e.g., 60 days of 1-hour candles)
    ticker = "EURUSD=X"
    print(f"\n[1] Fetching Historical Data for {ticker} (60 days, 1-hour interval)...")
    historical_data = fetch_historical_data(ticker=ticker, period="60d", interval="1h")
    
    if not historical_data:
        print("Failed to fetch historical data. Exiting.")
        return
        
    print(f"Loaded {len(historical_data)} historical candles.")

    # 2. Evaluate market data using the Confluence Engine
    print("\n[2] Running Analysis Engine (Detecting high-probability FVGs)...")
    setups = evaluate_market_data(historical_data)
    
    if not setups:
        print("No setups found in the historical data.")
        return
        
    print(f"Detected {len(setups)} valid setups that meet Confluence criteria.")

    # 3. Run the Backtester
    print("\n[3] Simulating Trades (1:2 R:R)...")
    run_backtest(historical_data, setups)

if __name__ == "__main__":
    main()

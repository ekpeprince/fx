from data_pipeline.scraper import fetch_transcript
from analysis_engine.analyzer import evaluate_market_data
from risk_management.guardrails import RiskEngine

def main():
    print("--- ICT Trading Analysis Pipeline ---")
    
    # Initialize Risk Engine (e.g., $10,000 account, 5% max daily drawdown, 2% max per trade)
    risk_engine = RiskEngine(account_balance=10000, max_daily_drawdown_pct=0.05, max_risk_per_trade_pct=0.02)
    print(f"Risk Engine Initialized. Max Risk Per Trade: ${risk_engine.max_risk_per_trade_amount}")

    # Phase 1: Data Pipeline (Fetching Transcript)
    # Using a known YouTube video ID as a dummy test for fetching text
    test_video_id = "jNQXAC9IVRw" 
    print(f"\n[1] Fetching Transcript for Video ID: {test_video_id}")
    transcript_json = fetch_transcript(test_video_id)
    if transcript_json:
        print("Transcript Data Pipeline OK (truncated for brevity).")
    else:
        print("Failed to fetch transcript.")
        return

    # Phase 3: Analysis Engine (Using Live Market Data)
    print("\n[2] Ingesting Live Market Data & Evaluating Setup")
    from data_pipeline.market_data import fetch_live_ohlcv
    
    # Fetch EUR/USD 5-minute data
    live_ticker = "EURUSD=X"
    live_market_data = fetch_live_ohlcv(ticker=live_ticker, period="1d", interval="5m")
    
    if not live_market_data:
        print("Could not fetch live market data.")
        return
        
    setups = evaluate_market_data(live_market_data)
    
    if not setups:
        print(f"No setups detected for {live_ticker} in the recent data.")
        return

    print("\n[3] Validating High-Probability Setups with Risk Guardrails")
    for setup in setups:
        print(f"\nAnalyzing Setup: {setup['setup_type']} at {setup['timestamp']}")
        
        # Simulated trade parameters based on the setup
        entry_price = setup['entry_zone'][1] # Enter at top of gap
        
        # Use the order block level as the structural stop loss, plus a small buffer (e.g., 2 pips = 0.0002)
        if "Bullish" in setup['setup_type']:
            stop_loss = setup['ob_level'] - 0.0002
        else:
            stop_loss = setup['ob_level'] + 0.0002
            
        position_size = 50000 # 50,000 units (half a standard lot in Forex)
        
        print(f"Proposed Trade -> Entry: {entry_price}, SL: {stop_loss}, Size: {position_size}")
        
        is_approved, message = risk_engine.validate_trade(entry_price, stop_loss, position_size)
        
        if is_approved:
            print(f"[APPROVED] {message}")
        else:
            print(f"[REJECTED] {message}")

if __name__ == "__main__":
    main()

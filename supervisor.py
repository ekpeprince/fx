import time
from data_pipeline.market_data import fetch_live_ohlcv
from analysis_engine.analyzer import evaluate_market_data
from risk_management.guardrails import RiskEngine
from risk_management.notifier import Notifier
from risk_management.broker_api import BrokerAPI
from analysis_engine.market_sentiment import generate_market_sentiment_summary

def run_supervisor(interval_minutes=5):
    """
    Autonomous loop to continuously monitor the market.
    """
    print(f"--- ICT Autonomous Multi-Asset Supervisor Started ---")
    
    assets = ["EURUSD=X", "GBPUSD=X", "BTC-USD", "^GSPC"]
    print(f"Monitoring Assets: {assets} every {interval_minutes} minutes...\n")
    
    risk_engine = RiskEngine(account_balance=10000, max_daily_drawdown_pct=0.05, max_risk_per_trade_pct=0.02)
    notifier = Notifier()
    broker = BrokerAPI()
    
    # Keep track of timestamps we've already alerted to avoid duplicate alerts
    seen_setups = set()
    
    # We will run just 1 loop for demonstration/testing purposes, 
    # but in reality this would be `while True:`
    for _ in range(1):
        try:
            print(f"\n[Supervisor Check] Waking up at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            for ticker in assets:
                print(f"--- Scanning {ticker} ---")
                # 1. Fetch live data
                live_data = fetch_live_ohlcv(ticker, period="1d", interval="5m")
                if not live_data:
                    continue
                    
                # 2. Analyze for setups
                setups = evaluate_market_data(live_data)
                
                # Print LLM Sentiment Summary
                sentiment = generate_market_sentiment_summary(ticker, live_data, setups)
                print(f"\n{sentiment}\n")
                
                # 3. Check Risk and Send Alerts
                for setup in setups:
                    setup_id = f"{ticker}_{setup['timestamp']}_{setup['setup_type']}"
                    
                    if setup_id not in seen_setups:
                        new_setups_found = True
                        seen_setups.add(setup_id)
                        
                        # Simulated execution logic
                        entry_price = setup['entry_zone'][1]
                        if "Bullish" in setup['setup_type']:
                            stop_loss = setup['ob_level'] - 0.0002
                            direction = "BUY"
                        else:
                            stop_loss = setup['ob_level'] + 0.0002
                            direction = "SELL"
                            
                        # Adjust position size based on asset (mocking logic)
                        position_size = 50000 if "USD=X" in ticker else 1 
                        
                        is_approved, msg = risk_engine.validate_trade(entry_price, stop_loss, position_size)
                        
                        if is_approved:
                            print(f"*** {ticker} LIVE TRADE SIGNAL DETECTED ***")
                            print(f"Time: {setup['timestamp']} | Setup: {setup['setup_type']}")
                            print(f"Entry: {entry_price} | SL: {stop_loss} | Size: {position_size}")
                            
                            # Log locally
                            notifier.send_alert(setup, entry_price, stop_loss, position_size)
                            # Execute mock Broker Order
                            broker.place_order(ticker, direction, entry_price, stop_loss, position_size)
            
            if not new_setups_found:
                print("\nNo new high-probability setups detected across the basket. Waiting for next interval...")
                
        except Exception as e:
            print(f"Supervisor Error: {e}")
            
        # In a real loop, we would uncomment this:
        # time.sleep(interval_minutes * 60)

if __name__ == "__main__":
    run_supervisor(interval_minutes=5)

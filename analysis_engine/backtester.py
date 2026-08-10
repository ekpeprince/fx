def run_backtest(ohlcv_data, setups):
    """
    Simulates trades for all detected setups to calculate a win rate.
    Uses a standard 1:2 Risk-to-Reward ratio.
    """
    wins = 0
    losses = 0
    total_trades = len(setups)
    
    print(f"Starting Backtest on {total_trades} setups...")
    
    for setup in setups:
        setup_time = setup['timestamp']
        setup_type = setup['setup_type']
        
        # Calculate Risk and Target based on 1:2 R:R
        # For a Bullish FVG, entry is top of gap, SL is the OB level
        if "Bullish" in setup_type:
            entry_price = setup['entry_zone'][1] # gap_top
            stop_loss = setup['ob_level'] - 0.0002 # 2 pip buffer
            risk = entry_price - stop_loss
            take_profit = entry_price + (risk * 2) # 1:2 R:R
        else:
            entry_price = setup['entry_zone'][0] # gap_bottom
            stop_loss = setup['ob_level'] + 0.0002
            risk = stop_loss - entry_price
            take_profit = entry_price - (risk * 2)

        if risk <= 0:
            print(f"Skipping setup at {setup_time}: Invalid risk calculation.")
            total_trades -= 1
            continue
            
        # Find the setup index in the OHLCV data to simulate forward
        setup_idx = -1
        for i, candle in enumerate(ohlcv_data):
            if candle['timestamp'] == setup_time:
                setup_idx = i
                break
                
        if setup_idx == -1 or setup_idx == len(ohlcv_data) - 1:
            # Data ended, trade couldn't play out
            total_trades -= 1
            continue
            
        # Simulate the trade forward candle-by-candle
        trade_resolved = False
        for i in range(setup_idx + 1, len(ohlcv_data)):
            candle = ohlcv_data[i]
            
            if "Bullish" in setup_type:
                if candle['low'] <= stop_loss:
                    losses += 1
                    trade_resolved = True
                    break
                elif candle['high'] >= take_profit:
                    wins += 1
                    trade_resolved = True
                    break
            else:
                if candle['high'] >= stop_loss:
                    losses += 1
                    trade_resolved = True
                    break
                elif candle['low'] <= take_profit:
                    wins += 1
                    trade_resolved = True
                    break
                    
        if not trade_resolved:
            # Trade is still open at the end of the dataset
            total_trades -= 1
            
    print("\n--- Backtest Results ---")
    print(f"Total Completed Trades: {total_trades}")
    print(f"Wins: {wins}")
    print(f"Losses: {losses}")
    
    if total_trades > 0:
        win_rate = (wins / total_trades) * 100
        print(f"Win Rate: {win_rate:.2f}%")
        
        # Calculate theoretical return assuming 2% risk per trade and 1:2 R:R
        # Win = +4%, Loss = -2%
        total_return = (wins * 4) - (losses * 2)
        print(f"Theoretical Return: {total_return}%")
    else:
        print("Win Rate: N/A")

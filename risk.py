import logging
import MetaTrader5 as mt5

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self, max_risk_per_trade_pct: float = 1.0, max_drawdown_pct: float = 5.0):
        self.max_risk_per_trade_pct = max_risk_per_trade_pct
        self.max_drawdown_pct = max_drawdown_pct

    def validate_signal(self, signal: dict, account_balance: float, current_drawdown_pct: float, rsi: float = None, atr: float = None) -> bool:
        """
        Validates an incoming trading signal against hard risk limits and indicator guards.
        """
        if current_drawdown_pct >= self.max_drawdown_pct:
            logger.warning("Max drawdown reached. Trading halted.")
            return False
            
        positions = mt5.positions_get()
        if positions is not None:
            total_risk = len(positions) * self.max_risk_per_trade_pct
            if total_risk + self.max_risk_per_trade_pct > self.max_drawdown_pct:
                logger.warning(f"Total risk across all pairs ({total_risk}%) plus new trade exceeds max drawdown ({self.max_drawdown_pct}%). Trading halted.")
                return False
            
        direction = signal.get('signal')
        if direction not in ['BUY', 'SELL']:
            logger.info("Signal is NO_TRADE or invalid. Ignoring.")
            return False
            
        if not signal.get('stop_loss') or not signal.get('entry_price'):
            logger.warning("Signal missing entry or stop loss. Aborting.")
            return False
            
        if rsi is not None:
            if direction == 'BUY':
                if rsi > 70:
                    logger.warning(f"RSI {rsi:.2f} is overbought. Rejecting BUY.")
                    return False
                if rsi <= 50:
                    logger.warning(f"RSI {rsi:.2f} lacks bullish momentum. Rejecting BUY.")
                    return False
            elif direction == 'SELL':
                if rsi < 30:
                    logger.warning(f"RSI {rsi:.2f} is oversold. Rejecting SELL.")
                    return False
                if rsi >= 50:
                    logger.warning(f"RSI {rsi:.2f} lacks bearish momentum. Rejecting SELL.")
                    return False
                    
        if atr is not None:
            sl_distance = abs(signal['entry_price'] - signal['stop_loss'])
            min_sl_distance = 1.5 * atr
            if sl_distance < min_sl_distance:
                logger.warning(f"Stop loss distance ({sl_distance:.5f}) is too tight. Minimum: {min_sl_distance:.5f} (1.5x ATR).")
                return False
            
        return True
        
    def calculate_lot_size(self, account_balance: float, entry_price: float, stop_loss: float, symbol_pip_value: float = 10.0) -> float:
        """
        Calculates dynamic lot sizing based on max % risk per trade.
        Basic formula assuming specific pip value structure. 
        """
        risk_amount = account_balance * (self.max_risk_per_trade_pct / 100.0)
        risk_pips = abs(entry_price - stop_loss)
        
        if risk_pips == 0:
            return 0.01 # Minimum lot
            
        # Simplified lot calculation, assumes standard 1 lot = $10/pip structure
        lot_size = risk_amount / (risk_pips * symbol_pip_value)
        return max(0.01, round(lot_size, 2))

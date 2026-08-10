class RiskEngine:
    """
    Immutable Risk Management engine to validate all agent recommendations.
    Enforces maximum daily drawdown limits and per-position risk limits.
    """
    def __init__(self, account_balance, max_daily_drawdown_pct=0.05, max_risk_per_trade_pct=0.02):
        self._account_balance = account_balance
        self._max_daily_drawdown_pct = max_daily_drawdown_pct
        self._max_risk_per_trade_pct = max_risk_per_trade_pct
        self._current_daily_drawdown = 0.0

    @property
    def max_risk_per_trade_amount(self):
        return self._account_balance * self._max_risk_per_trade_pct

    def validate_trade(self, entry_price, stop_loss_price, position_size_units):
        """
        Validates if a proposed trade setup meets risk guardrails.
        """
        # Calculate monetary risk
        risk_per_unit = abs(entry_price - stop_loss_price)
        total_risk_amount = risk_per_unit * position_size_units

        # 1. Check max risk per trade
        if total_risk_amount > self.max_risk_per_trade_amount:
            return False, f"Trade risk ({total_risk_amount}) exceeds max risk per trade ({self.max_risk_per_trade_amount})"

        # 2. Check daily drawdown
        projected_drawdown = self._current_daily_drawdown + total_risk_amount
        max_daily_drawdown_amount = self._account_balance * self._max_daily_drawdown_pct
        
        if projected_drawdown > max_daily_drawdown_amount:
            return False, "Trade violates maximum daily drawdown limit."

        return True, "Trade approved by Risk Engine."

    def update_daily_drawdown(self, realized_loss):
        """Updates the running daily drawdown."""
        if realized_loss > 0:
            self._current_daily_drawdown += realized_loss

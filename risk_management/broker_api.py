import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

class BrokerAPI:
    """
    Live integration layer for Alpaca REST API.
    Loads credentials securely from the .env file.
    """
    def __init__(self):
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY")
        self.environment = os.getenv("ALPACA_ENVIRONMENT", "paper")
        
        domain = "paper-api.alpaca.markets" if self.environment == "paper" else "api.alpaca.markets"
        self.endpoint = f"https://{domain}/v2/orders"

    def place_order(self, ticker, direction, entry_price, stop_loss, position_size):
        """
        Simulates placing a limit/market order with a stop loss.
        """
        # Alpaca API Order Payload structure
        symbol = ticker.replace("=X", "").replace("-", "") # Format EURUSD=X to EURUSD
        side = "buy" if direction == "BUY" else "sell"
        
        payload = {
            "symbol": symbol,
            "qty": str(abs(position_size)),
            "side": side,
            "type": "market",
            "time_in_force": "ioc",
            "stop_loss": {
                "stop_price": str(round(stop_loss, 5))
            }
        }
        
        print("\n[BROKER API] Executing Live Order...")
        
        if not self.api_key or "your_" in self.api_key:
            print("[X] Alpaca API Key missing in .env! Order aborted.")
            return False, "Missing API Key"
            
        try:
            headers = {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key,
                "Content-Type": "application/json"
            }
            response = requests.post(self.endpoint, json=payload, headers=headers)
            
            if response.status_code in [200, 201]:
                print(f"[OK] Order Executed Successfully!")
                return True, "Order Executed Successfully"
            else:
                print(f"[X] Order Failed: {response.status_code} - {response.text}")
                return False, response.text
                
        except Exception as e:
            print(f"[X] Error sending order to broker: {e}")
            return False, str(e)

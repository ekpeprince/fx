import csv
import os
from datetime import datetime

class Notifier:
    """
    Handles alerts and logging for the Autonomous Supervisor.
    """
    def __init__(self, log_file="live_trades.csv"):
        self.log_file = log_file
        # Create CSV header if it doesn't exist
        if not os.path.exists(self.log_file):
            with open(self.log_file, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Timestamp", "Setup Type", "Entry Price", "Stop Loss", "Position Size"])

    def send_alert(self, setup, entry_price, stop_loss, position_size):
        """
        Sends a live alert (currently logs to CSV).
        Can be extended to trigger a Discord Webhook.
        """
        try:
            with open(self.log_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    setup['timestamp'],
                    setup['setup_type'],
                    entry_price,
                    stop_loss,
                    position_size
                ])
            print(f"[ALERT NOTIFIER] Logged new live trade to {self.log_file}")
            
        except Exception as e:
            print(f"[ALERT NOTIFIER ERROR] {e}")

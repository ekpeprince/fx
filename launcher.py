import threading
import subprocess
import time
import sys
import os

def run_supervisor():
    """Runs the supervisor loop in the background."""
    print("[Launcher] Starting AI Supervisor in the background...")
    try:
        from supervisor import run_supervisor
        run_supervisor(interval_minutes=5)
    except Exception as e:
        print(f"Error starting supervisor: {e}")

def run_dashboard():
    """Launches the Streamlit dashboard."""
    print("[Launcher] Starting Web Dashboard...")
    try:
        # Use subprocess to launch Streamlit using the current python executable
        subprocess.Popen([sys.executable, "-m", "streamlit", "run", "dashboard.py"])
    except Exception as e:
        print(f"Error starting dashboard: {e}")

if __name__ == "__main__":
    print("========================================")
    print("      ICT Autonomous Trading Suite      ")
    print("========================================")
    
    # Check if .env exists
    if not os.path.exists(".env"):
        print("\nWARNING: '.env' file not found! API Keys are missing.")
        print("Please create a .env file and add your keys before running.\n")
        time.sleep(5)
    
    # Start supervisor on a separate thread
    sup_thread = threading.Thread(target=run_supervisor, daemon=True)
    sup_thread.start()
    
    # Give supervisor a second to print its header
    time.sleep(2)
    
    # Launch Streamlit dashboard
    run_dashboard()
    
    print("\n[Launcher] System is LIVE. Close this window to stop the bot.\n")
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")

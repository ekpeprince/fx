import os
import subprocess
import time
from pyngrok import ngrok
from dotenv import load_dotenv

def start_tunnel():
    # Load environment variables
    load_dotenv()
    
    # Set authtoken if available
    auth_token = os.environ.get("NGROK_AUTH_TOKEN")
    if auth_token:
        ngrok.set_auth_token(auth_token)

    # Start Streamlit in a subprocess
    print("Starting Streamlit server on port 8501...")
    streamlit_process = subprocess.Popen(["python", "-m", "streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"])
    
    time.sleep(3) # Give streamlit time to start
    
    # Open ngrok tunnel
    print("Opening ngrok tunnel...")
    public_url = ngrok.connect(8501)
    
    print("=" * 50)
    print("🚀 Antigravity Trading Dashboard is LIVE!")
    print(f"🔗 Public URL: {public_url.public_url}")
    print("=" * 50)
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        streamlit_process.terminate()
        ngrok.kill()

if __name__ == "__main__":
    start_tunnel()

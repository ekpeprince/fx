import os
import sys
from dotenv import load_dotenv
from google import genai
import MetaTrader5 as mt5

def verify_gemini():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[FAIL] GEMINI_API_KEY not found in environment.")
        return False
        
    try:
        client = genai.Client(api_key=api_key)
        # Attempt a very simple query to verify the key
        interaction = client.interactions.create(
            model='gemini-3.6-flash',
            input="Ping test. Respond with OK.",
            store=False
        )
        if interaction.output_text:
            print("[OK] Gemini API connected successfully via Interactions API.")
            return True
    except Exception as e:
        print(f"[FAIL] Gemini API connection failed: {e}")
        return False

def verify_mt5():
    login = os.environ.get("MT5_LOGIN")
    password = os.environ.get("MT5_PASSWORD")
    server = os.environ.get("MT5_SERVER")
    
    if not login or not password or not server:
        print("[FAIL] MT5 credentials incomplete in environment.")
        return False
        
    if not mt5.initialize():
        print(f"[FAIL] MT5 initialize() failed, error code = {mt5.last_error()}")
        return False
        
    authorized = mt5.login(int(login), password=password, server=server)
    if authorized:
        print("[OK] MT5 connected successfully.")
        mt5.shutdown()
        return True
    else:
        print(f"[FAIL] MT5 login failed, error code = {mt5.last_error()}")
        mt5.shutdown()
        return False

if __name__ == "__main__":
    load_dotenv()
    print("--- Starting Verification ---")
    gemini_ok = verify_gemini()
    mt5_ok = verify_mt5()
    
    if gemini_ok and mt5_ok:
        print("All connections verified! Ready for Phase 2.")
        sys.exit(0)
    else:
        print("Verification failed. Please check your .env file.")
        sys.exit(1)

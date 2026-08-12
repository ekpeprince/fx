import os
import json
import logging
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import Literal

logger = logging.getLogger(__name__)

class TradingSignal(BaseModel):
    signal: Literal["BUY", "SELL", "NO_TRADE"]
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: int

def analyze_market_data(market_context: str) -> dict:
    """
    Analyzes the market context using Gemini 2.5 Flash and returns an ICT setup signal.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found in environment")
        return {"signal": "NO_TRADE", "entry_price": 0, "stop_loss": 0, "take_profit": 0, "confidence": 0}

    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are an expert ICT (Inner Circle Trader) algorithmic trading analyst.
    Analyze the following multi-timeframe market context.
    
    1. Determine overall market direction/bias using the H1 (1-Hour) candles.
    2. Identify specific Fair Value Gaps (FVG) or Order Blocks (OB) ONLY on the M15 (15-Minute) candles that ALIGN with the H1 macro bias.
    
    Market Context (H1 and M15):
    {market_context}
    
    Return a strict JSON response adhering to the TradingSignal structure (use EXACTLY 'entry_price', 'stop_loss', 'take_profit').
    If no clear setup exists that aligns with the H1 trend, return "signal": "NO_TRADE".
    """
    
    import time
    for attempt in range(3):
        try:
            interaction = client.interactions.create(
                model='gemini-3.6-flash',
                input=prompt,
                store=False
            )
            
            signal_data = json.loads(interaction.output_text.strip("```json\n").strip("```").strip())
            logger.info(f"Generated signal: {signal_data}")
            return signal_data
            
        except Exception as e:
            if "429" in str(e) or "too_many_requests" in str(e).lower():
                logger.warning(f"Rate limited (429). Retrying in 20 seconds... (Attempt {attempt + 1})")
                time.sleep(20)
            else:
                logger.error(f"Error during Gemini analysis: {e}")
                return {"signal": "NO_TRADE", "entry_price": 0, "stop_loss": 0, "take_profit": 0, "confidence": 0}
                
    return {"signal": "NO_TRADE", "entry_price": 0, "stop_loss": 0, "take_profit": 0, "confidence": 0}

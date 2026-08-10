import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def generate_market_sentiment_summary(ticker, recent_data, setups):
    """
    Live AI Engine using Google Gemini.
    Ingests numeric data and requests a short market sentiment analysis.
    """
    if not recent_data:
        return "Insufficient data to generate market sentiment."
        
    last_candle = recent_data[-1]
    current_price = last_candle['close']
    
    # Calculate simple short-term trend
    start_price = recent_data[0]['close']
    trend = "Bullish" if current_price > start_price else "Bearish"
    
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or "your_" in api_key:
        # Fallback to heuristic if key is missing
        return f"**{ticker} Heuristic Summary:** Trading at {current_price:.4f}. Trend is {trend}. Please configure GEMINI_API_KEY in .env for full AI summary."
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        setup_text = str(setups[-1]) if setups else "None"
        
        prompt = f"You are a professional ICT quantitative analyst. Briefly summarize the market state in 2 sentences based on the provided data.\nAsset: {ticker}. Current Price: {current_price}. Trend: {trend}. Recent Setups: {setup_text}"
        
        response = model.generate_content(prompt)
        
        summary = response.text.strip()
        return f"**[AI] Sentiment ({ticker}):**\n{summary}"
        
    except Exception as e:
        return f"**AI Sentiment Error:** {str(e)}"

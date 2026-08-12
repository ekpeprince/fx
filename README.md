# Antigravity AI Trading Suite

An institutional-grade algorithmic trading bot that leverages Google's Gemini AI to scan the market for Inner Circle Trader (ICT) concepts (Fair Value Gaps, Order Blocks, Liquidity Sweeps) across multiple currency pairs.

## Features
- **Multi-Pair Scanning**: Monitors EURUSD, GBPUSD, and USDJPY simultaneously.
- **AI-Powered Analysis**: Feeds multi-timeframe data (H1 & M15) into Gemini 3.6 Flash for institutional bias and entry signals.
- **Holistic Risk Management**: Dynamically scales lot sizes and monitors global account drawdown across all active pairs.
- **Streamlit Command Center**: A beautiful dashboard for real-time market visualization, manual AI generation, and bot management.
- **Smart Throttling**: Built-in API rate limit protections to gracefully handle free-tier API quotas.

## Prerequisites
1. **Windows OS** (Required for MetaTrader 5 terminal integration).
2. **MetaTrader 5 (MT5)** installed and logged into your broker account.
3. **Python 3.10+** installed.
4. A **Gemini API Key** from Google AI Studio.

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone https://github.com/ekpeprince/fx.git
   cd fx
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   - Copy `.env.example` and rename it to `.env`.
   - Open `.env` and fill in your details:
     ```env
     MT5_LOGIN=your_mt5_account_number
     MT5_PASSWORD=your_mt5_password
     MT5_SERVER=your_broker_server_name
     GEMINI_API_KEY=your_google_gemini_api_key
     ```

## Running the Dashboard
The system is managed entirely through a clean web dashboard.

1. Open your terminal in the project folder and run:
   ```bash
   streamlit run app.py
   ```
2. The dashboard will open in your browser (usually at `http://localhost:8501`).
3. From the sidebar, click **"Start Bot"** to launch the multi-pair background scanner. 

You can monitor the bot's logs in real-time at the bottom of the dashboard!

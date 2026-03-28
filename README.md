# Algorithmic Trading System

A Python-based algorithmic trading system that automates stock screening, position monitoring, and order execution using data from Discord, Yahoo Finance, and Alpha Vantage.

## Overview

The system runs a daily pipeline:

1. **Discord Briefing Ingestion** — Pulls the morning briefing from a stock trading Discord channel via the Discord HTTP API, parsing catalyst plays, support/resistance levels, retail watchlist tickers, and alarm plays.
2. **Position Monitoring** — Monitors a configurable list of core holdings on a set interval, alerting via SMS when price crosses key EMA levels (e.g., 180 EMA on 30-minute candles).
3. **Order Execution** — Submits market buy, stop-loss, and trailing-stop sell orders through the Alpaca brokerage API with PDT (Pattern Day Trader) rule compliance.

## Core Modules

| File | Description |
|---|---|
| `revised_discord.py` | Fetches and parses the morning briefing from a Discord channel; returns support/resistance maps, retail plays, and alarm plays |
| `mainPositions.py` | Monitors a watchlist of positions on a configurable candle interval; calculates EMAs via Alpha Vantage data and sends SMS alerts on crossovers |
| `alpaca.py` | Alpaca brokerage API wrapper; handles market buy orders, stop-loss orders, trailing-stop sell orders, and full order lifecycle management |
| `record_day_trade.py` | Enforces PDT rules by tracking round-trip day trades over a rolling 5-trading-day window |
| `sms.py` | Sends SMS trade alerts via Textbelt |
| `screener.py` | Intraday stock screener; uses Discord briefing output to rank and filter stocks by RSI, EMA alignment, and volume |

## Additional Strategies

| File | Description |
|---|---|
| `threeBar_yf.py` | Three-bar reversal pattern detection using Yahoo Finance intraday data |
| `resistance_breakout.py` | Identifies resistance/support breakouts and places orders on confirmation |
| `thirtyMin.py` | 30-minute candle momentum strategy with multi-threaded stock monitoring |
| `ema_cross_march.py` | EMA crossover signal detection across multiple timeframes |
| `realtime.py` | Real-time intraday monitoring with EST-aware market hour scheduling |
| `ml_trade.py` | RandomForest classifier trained on OHLCV + technical indicators to generate trade signals |

## Analysis & Data

| File | Description |
|---|---|
| `get_data.py` | Alpha Vantage intraday data fetcher; computes EMA-5/9/20/180, percent change, and relative volume |
| `yf.py` | Yahoo Finance data wrapper; calculates moving averages and price condition flags |
| `RSI.py` | RSI calculation and visualization |
| `Analysis_report.py` | Breakout detection report combining SMA, RSI, and volume analysis |
| `earnings.py` | Finnhub earnings data integration; tracks revenue growth and earnings beats |
| `sentiment.py` | Alpha Vantage news sentiment analysis integrated with trade signals |
| `PE_comparison.py` | P/E ratio analysis across a watchlist |
| `api_rate_limit.py` | Rate-limiting utilities for Alpha Vantage API calls |

## Setup

**1. Clone the repo**
```bash
git clone <repo-url>
cd trade
```

**2. Install dependencies**
```bash
pip install yfinance alpaca-trade-api alpha_vantage ta pandas numpy requests pytz scikit-learn
```

**3. Configure credentials**

Create a `secret.py` file (gitignored) with your API keys:
```python
ALPHA_VANTAGE_KEY = "your_key"
FINNHUB_KEY = "your_key"
TWILIO_ACCOUNT_SID = "your_sid"
TWILIO_AUTH_TOKEN = "your_token"
TWILIO_FROM = "+1xxxxxxxxxx"
```

Set environment variables for SMS and Alpaca:
```bash
export SMS_PHONE="your_phone_number"
export TEXTBELT_API_KEY="your_textbelt_key"
```

Update `alpaca.py` with your Alpaca API credentials:
```python
API_KEY = "your_alpaca_key"
API_SECRET = "your_alpaca_secret"
```

**4. Run**
```bash
# Monitor positions and send EMA crossover alerts
python mainPositions.py

# Run the intraday screener
python screener.py
```

## Architecture

```
Discord Briefing
      │
      ▼
revised_discord.py  ──►  screener.py  ──►  alpaca.py (orders)
                                                │
mainPositions.py ───────────────────────────────┘
      │
      ▼
   sms.py (alerts)       record_day_trade.py (PDT compliance)
```

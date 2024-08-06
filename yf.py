import yfinance as yf
import pandas as pd
import numpy as np
import time
import requests
from datetime import datetime, timedelta
from alpha_vantage.timeseries import TimeSeries

# Initialize variables to track API call rate
BOUGHT = False
calls_made = 0
shortest_interval = 60 / 150
last_time = time.time()

# Constants
API_KEY = 'XB2M6HD2DQMJA5Z1'  # DISCONTINUED - Replace with your actual API key
too_close_thresh = 1.5  # Resistances are duplicates if within 1.5% of one another

def alpha_get_data(stock, interval):
    # Alpha Vantage GET request
    try:
        request_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={stock}&outputsize=full&interval={interval}&apikey={API_KEY}"
        resp = requests.get(request_url)
        print("Response status:", resp.status_code)
        timeseries_json = resp.json()[f'Time Series ({interval})']
    except Exception as e:
        print("Alpha request broken with: ", e)
        return None

    # Access data from timeseries_json
    data_list = [
        {
            'timestamp': timestamp,
            'open': float(data['1. open']),
            'high': float(data['2. high']),
            'low': float(data['3. low']),
            'close': float(data['4. close']),
            'volume': int(data['5. volume'])
        }
        for timestamp, data in timeseries_json.items()
    ]

    # Create DataFrame
    df = pd.DataFrame(data_list)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['percent_change'] = (df['close'] - df['open']) / df['open'] * 100

    # Find the latest market day's timestamp
    latest_market_day = df['timestamp'].max().date()

    # Filter the DataFrame to include only the data for the latest market day
    latest_data = df[df['timestamp'].dt.date == latest_market_day].copy()

    # Calculate EMAs
    latest_data['EMA_5'] = latest_data['close'].ewm(span=5, adjust=False).mean()
    latest_data['EMA_9'] = latest_data['close'].ewm(span=9, adjust=False).mean()
    latest_data['EMA_20'] = latest_data['close'].ewm(span=20, adjust=False).mean()
    latest_data['EMA_180'] = latest_data['close'].ewm(span=180, adjust=False).mean()

    return latest_data[::-1]  # Return the data in reverse order

def yf_data(ticker, interval_time):
    global calls_made, last_time, shortest_interval

    elapsed_time = time.time() - last_time

    if elapsed_time < shortest_interval:
        sleep_time = shortest_interval - elapsed_time
        print(f"Rate limit sleep: {sleep_time}")
        time.sleep(sleep_time)

    calls_made += 1
    last_time = time.time()
    if calls_made % 50 == 0:
        print(f"Calls made: {calls_made} at {last_time}")

    try:
        # Fetch intraday data using the ticker symbol
        stock = yf.Ticker(ticker)
        intraday_data = stock.history(period="1d", interval=interval_time, prepost=True)

        # Calculate SMAs
        intraday_data['SMA_5'] = intraday_data['Close'].rolling(window=5).mean()
        intraday_data['SMA_9'] = intraday_data['Close'].rolling(window=9).mean()
        intraday_data['SMA_20'] = intraday_data['Close'].rolling(window=20).mean()
        intraday_data['SMA_180'] = intraday_data['Close'].rolling(window=180).mean()
        intraday_data['percent_change'] = (intraday_data['Close'] - intraday_data['Open']) / intraday_data['Open'] * 100

        return intraday_data  # Return the intraday data
    except Exception as e:
        print("Error fetching data:", e)

# Example usage
if __name__ == "__main__":
    ticker_symbol = "VBIV"
    print(f"Checking {ticker_symbol} dataframe")
    yahoo_data = yf_data(ticker_symbol, '5m')
    
    if yahoo_data is not None:
        pd.set_option('display.max_rows', None)  # Display all rows
        print(yahoo_data)
    else:
        print("No data returned from Yahoo Finance API.")

import yfinance as yf
from datetime import datetime


import yfinance as yf
import datetime

from datetime import datetime, timedelta
from Discord import get_briefing
from record_day_trade import pdt_rule, record_trade
from sms import text
import pandas as pd
import numpy as np
import time
import requests
from realtimetrade import place_buy, place_sell
import multiprocessing
from alpha_vantage.timeseries import TimeSeries
import ta


# Initialize variables to track API call rate
global BOUGHT  # bought a stock this day
BOUGHT=False

global calls_made
calls_made = 0

global shortest_interval
shortest_interval = 60 / 150

global last_time
last_time = time.time()

texted_plays  =  []

# constants
API_KEY  =  'XB2M6HD2DQMJA5Z1' # DISCONTINUED
too_close_thresh = 1.5 #resistances are duplicates if within 1.5% of one another

# alpha data
def alpha_get_data(stock, interval, date=None):

    # Alpha Vantage GET request
    try:
        request_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={stock}&outputsize=full&interval={interval}&entitlement=realtime&apikey={API_KEY}"
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
    latest_data = df[df['timestamp'].dt.date == latest_market_day].copy()  # Make a copy of the slice

    # Calculate EMA's
    latest_data['EMA_5'] = latest_data['close'].ewm(span=5, adjust=False).mean()
    latest_data['EMA_9'] = latest_data['close'].ewm(span=9, adjust=False).mean()
    latest_data['EMA_20'] = latest_data['close'].ewm(span=20, adjust=False).mean()
    latest_data['EMA_180'] = latest_data['close'].ewm(span=180, adjust=False).mean()
    

    return latest_data[::-1] #alpha data return

def yf_data(ticker, interval_time):
     # rate limit 
    global calls_made, last_time, shortest_interval
    
    elapsed_time = time.time() - last_time

    if elapsed_time<shortest_interval: # calls are being made too fast
        sleep_time=shortest_interval - elapsed_time
        print(f"rate limit sleep: {sleep_time}")
        time.sleep(sleep_time)

    calls_made+=1
    last_time = time.time()
    if calls_made%50==0:
        print("calls made: {calls_made} at {last_time}")
    
    try:
        # Fetch intraday data using the ticker symbol
        stock = yf.Ticker(ticker)
        
        # Get historical market data for the last trading day with 5-minute intervals
        intraday_data = stock.history(period="1d", interval=interval_time, prepost=True)
        intraday_data=intraday_data
        
        # Print the intraday data
        print("Intraday Data for", ticker)

        # Calculate EMAs
        intraday_data['SMA_5'] = intraday_data['Close'].rolling(window=5).mean()
        intraday_data['SMA_9'] = intraday_data['Close'].rolling(window=9).mean()
        intraday_data['SMA_20'] = intraday_data['Close'].rolling(window=20).mean()
        intraday_data['SMA_180'] = intraday_data['Close'].rolling(window=180).mean()
        intraday_data['percent_change'] = (intraday_data['Close']-intraday_data['Open'])/ intraday_data['Open']* 100

        return intraday_data # yahoo data return
    except Exception as e:
        print("Error fetching data:", e)

# Example usage
if __name__ == "__main__":
    ticker_symbol = "MDIA"
    print(f"Checking {ticker_symbol} dataframe")
    yahoo_data = yf_data(ticker_symbol, '1m')
    print("yahoo_data: ", yahoo_data)
    print("time at 0: ", yahoo_data.index[0])
    for i in range(len(yahoo_data)-2):
        if yahoo_data.loc[yahoo_data.index[i], 'percent_change'] > 5 and \
           yahoo_data.loc[yahoo_data.index[i+1], 'percent_change'] < 0 and \
           yahoo_data.loc[yahoo_data.index[i+2], 'percent_change'] > 3:
            print(f"buy at {yahoo_data.index[i+2]}")






    # alpha_data=alpha_get_data(ticker_symbol, "5min")
    # print(f"alpha_data: {alpha_data} \n type yahoo data: {type(alpha_data)}")

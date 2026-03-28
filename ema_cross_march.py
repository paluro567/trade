import yfinance as yf
import datetime

from datetime import datetime, timedelta
from revised_discord import get_briefing
from record_day_trade import pdt_rule, record_trade
from sms import text
import pandas as pd
import numpy as np
import time
import requests
from alpaca import place_buy, place_sell
import multiprocessing
from alpha_vantage.timeseries import TimeSeries
import ta


# constants
# Initialize variables to track API call rate
global BOUGHT  # only place one day trade
global calls_made
global last_time
calls_made = 0
last_time = time.time()
BOUGHT=False
API_KEY  =  'XB2M6HD2DQMJA5Z1'
too_close_thresh = 1.5 #resistances are duplicates if within 1.5% of one another
texted_plays  =  []

def get_data(stock, interval, date=None):

    # LIMIT CALLS
    global calls_made, last_time
    # fastest rate to make api calls
    shortest_interval = 60 / 150

    elapsed_time = time.time() - last_time

    if elapsed_time < shortest_interval: # calls are being made too fast
        time.sleep(shortest_interval - elapsed_time)

    calls_made += 1
    last_time = time.time()
    
    #Alpha Vantage GET request
    try:
        request_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={stock}&interval={interval}&outputsize=full&apikey={API_KEY}"
        resp = requests.get(request_url)
        print("Response status:", resp.status_code)
        timeseries_json = resp.json()[f'Time Series ({interval})']
    except Exception as e:
        print("AV request broken with: ", e)

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

    # Calculate SMAs
    df = df.iloc[::-1].reset_index(drop=True)

    window_sizes = [5, 9, 20]
    for window in window_sizes:
        col_name = f'sma_{window}'
        df[col_name] = df['close'].rolling(window=window).mean()

    return df  # Only consider one day's data

if __name__  ==  '__main__':
    percent_gain=0
    bought=False
    buy_price=0
    sell_price=0
    data= get_data("MARA", "5min")
    print("data here1: ", data)
    data['timestamp'] = pd.to_datetime(data['timestamp'])

    filtered_df = data[data['timestamp'].dt.date == pd.Timestamp('2024-03-22').date()]


    print("filtered_df here1: ", filtered_df)
    
    filtered_df.reset_index(drop=True, inplace=True)

    filtered_df = pd.DataFrame(filtered_df)
    pd.set_option('display.max_rows', None)

 

    print("data: ", filtered_df)

    prev_sma_9 = filtered_df.iloc[0]['sma_9']
    prev_sma_20 = filtered_df.iloc[0]['sma_20']

    # Iterate over rows in the DataFrame
    for index, row in filtered_df.iterrows():
        sma_9 = row['sma_9']
        sma_20 = row['sma_20']
        
        # Check for crossover from below sma_20 to above
        if prev_sma_9 < prev_sma_20 and sma_9 > sma_20:
            buy_price=row['close']
            print(f"BUY: sma_9 crossed above sma_20: {row['timestamp']} at ${buy_price}")
            bought=True
        
        # Check for crossover from above sma_20 to below
        elif prev_sma_9 > prev_sma_20 and sma_9 < sma_20:
            sell_price=row['close']
            print(f"SELL: sma_9 crossed below sma_20: {row['timestamp']} at ${sell_price}")
            if bought:
                bought=False
                gain = (sell_price - buy_price) / buy_price * 100 
                print(f"trade made {round(gain,2)}")
                percent_gain+=gain

        
        # Update previous sma_9 and sma_20 values
        prev_sma_9 = sma_9
        prev_sma_20 = sma_20

    print("total gain: ", percent_gain)



















import time
import requests
import yfinance as yf
import datetime

from datetime import datetime, timedelta
from revised_discord import get_briefing
from sms import text
import pandas as pd
import numpy as np
import time
from alpaca import place_buy, place_sell
import multiprocessing
from alpha_vantage.timeseries import TimeSeries
import ta

API_KEY  =  'XB2M6HD2DQMJA5Z1'


# Initialize variables to track API call rate
calls_made = 0
start_time = time.time()


def get_data(stock, time_interval, date=None):
    global calls_made, start_time

    # Calculate the time elapsed since the last call
    elapsed_time = time.time() - start_time
    print(f"{calls_made} time_exapsed: ", elapsed_time)

    # intended time interval between each call
    shortest_interval = 60 / 150

    if elapsed_time < shortest_interval:
        time_to_sleep = shortest_interval - elapsed_time
        time.sleep(time_to_sleep)
    
    #Alpha Vantage GET request
    request_url=f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={stock}&outputsize=full&interval={time_interval}&entitlement=realtime&apikey={API_KEY}"
    resp= requests.get(request_url)
    timeseries_json=resp.json()[f'Time Series ({time_interval})']

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
    df['percent_change'] = (df['close']-df['open'])/df['open'] * 100

    # Calculate EMA's
    reversed_df = df.iloc[::-1].copy()  # Creating a copy to prevent view-copy issues
    reversed_df.loc[:, 'ema_5'] = ta.trend.ema_indicator(close=reversed_df['close'], window=5)
    reversed_df.loc[:, 'ema_9'] = ta.trend.ema_indicator(close=reversed_df['close'], window=9)
    reversed_df.loc[:, 'ema_20'] = ta.trend.ema_indicator(close=reversed_df['close'], window=20)
    reversed_df.loc[:, 'ema_180'] = ta.trend.ema_indicator(close=reversed_df['close'], window=180)

    # Assign EMA's to df
    df.loc[:, 'ema_5'] = reversed_df['ema_5'].iloc[::-1].values  
    df.loc[:, 'ema_9'] = reversed_df['ema_9'].iloc[::-1].values
    df.loc[:, 'ema_20'] = reversed_df['ema_20'].iloc[::-1].values
    df.loc[:, 'ema_180'] = reversed_df['ema_180'].iloc[::-1].values 

    # print("get_data - df with EMA's: ", df)
    calls_made+=1

    return df[:910] #only considser one day's data


    

    

if __name__=='__main__':
    while True:
        get_data('pltr', '1min')

    

    
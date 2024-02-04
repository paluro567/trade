import yfinance as yf
import datetime
import time


from datetime import datetime, timedelta
from Discord import get_briefing
from sms import text
import pandas as pd
import numpy as np
import time
import requests
from realtimetrade import place_buy, place_sell
import multiprocessing
from alpha_vantage.timeseries import TimeSeries
import ta


# constants
API_KEY  =  'XB2M6HD2DQMJA5Z1'
too_close_thresh = 1.5 #resistances are duplicates if within 1.5% of one another
texted_plays  =  []



def get_data(stock, time, date=None):
    
    #Alpha Vantage GET request
    request_url=f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={stock}&outputsize=full&interval={time}&entitlement=realtime&apikey={API_KEY}"
    resp= requests.get(request_url)
    timeseries_json=resp.json()[f'Time Series ({time})']

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

    return df[:910] #only considser one day's data


def nine_twenty_cross(df):
    return df.iloc[1]['ema_9']<df.iloc[1]['ema_20'] and df.iloc[0]['ema_9']>df.iloc[0]['ema_20']


def monitor_bought_stock(ticker, qty, bought_price):
    # check position every 5 seconds
    while True:
        df = get_data(ticker, '5min')
        current_price = df.iloc[0]['close']
        time_stmp = df.iloc[0]['timestamp']
        below = df.iloc[0]['close']<df.iloc[0]['ema_9'] and df.iloc[1]['close']>df.iloc[1]['ema_9'] #crosses below ema_9
        percent_gain  =  ((current_price - bought_price) / bought_price) * 100
        print(f" sold {ticker} at {time_stmp} and gained {percent_gain}%")

        # sell position
        if(percent_gain<-5 or below):
            place_sell(ticker, qty)
            print(f"Sold position {ticker} at {time_stmp} \nat a price of {current_price} made {round(bought_price*percent_gain,2)}%")
            break
        time.sleep(2) #sleep 2 seconds



if __name__  ==  '__main__':
    start_time = time.time()
    for stock in ['PLTR','AMZN','PYPL','MARA']:
        print(get_data(stock, '5min'))
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time} seconds")
    print("60/elapsed_time:", 60/elapsed_time)























import yfinance as yf
import datetime

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



def get_alpha_data(stock, time, date=None):
    
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

def get_yahoo_data(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period='1d', interval="5m")
    return data








# Convert Yahoo Finance timestamp to match Alpha Vantage format
def convert_timestamp(timestamp):
    return parse(str(timestamp))

if __name__ == '__main__':
    alpha_data = get_alpha_data('pltr', '5min', date=None)
    print("alpha df: ", alpha_data)
    print("iloc 0 alpha:", alpha_data.iloc[0])
    yahoo_data = get_yahoo_data('PLTR')
    print("yahoo: ", yahoo_data)
    difference=0
    count=1

    for index, row in alpha_data.iterrows():
        alpha_p=row['close']
        index_str=str(row['timestamp'])+"-05:00"
        try:
            yahoo_p=yahoo_data.loc[index_str]['Close']
            difference+= yahoo_p-alpha_p

            print("index_str: ", index_str)
            print("yahoo close: ", yahoo_p)
            print("alpha close:", alpha_p)
            print("-----------")
        except:
            x=1
            

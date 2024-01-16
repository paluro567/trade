import yfinance as yf
from datetime import datetime, timedelta
from Discord import get_briefing
from sms import text
import datetime
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


    return df[:910] # only 910 rows


def watch_pos(ticker, interval):

    df = get_data(ticker, interval)
    print(f"watch_pos ({ticker})- get_data df: {df}")

    # df Calculations & values
    average_volume = df['volume'].mean()
    cur_time=df.iloc[0]['timestamp']
    cur_pct_change = df.iloc[0]['percent_change']
    open_price = df.iloc[0]['open']
    close_price = df.iloc[0]['close']
    cur_volume = df.iloc[0]['volume']
    ema_5 = df.iloc[0]['ema_5']
    ema_9 = df.iloc[0]['ema_9']
    ema_20 = df.iloc[0]['ema_20']
    ema_180=df.iloc[0]['ema_180']
    relative_volume=round((cur_volume-average_volume)/average_volume*100,2)

    # 180 check
    if ticker not in texted_plays:
        if open_price>ema_180 and close_price<ema_180:
            
            message = (f"MAIN POSITION -  {ticker} crossed below 180EMA by {round(cur_pct_change,2)}% \n"
                    f"With relative volume as {relative_volume}%"
            )
            text(message)
            texted_plays.append(ticker)
        if open_price<ema_180 and close_price>ema_180 and ticker not in texted_plays:
            
            message = (f"MAIN POSITION -  {ticker} crossed above 180EMA by {round(cur_pct_change,2)}% \n"
                    f"With relative volume as {relative_volume}%"
            )
            text(message)
            texted_plays.append(ticker)


#format iteration string for printing
def ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"


if __name__  ==  '__main__':
    interval_mins=30 # candle aggregation mins
    sleep_dur=30 # sleep between iterations (seconds)
    reset_iterations = int((60 / sleep_dur) * interval_mins) # how many iterations before resetting texted array
    main_positions=['PLTR','UNH','PYPL', 'TSLA', 'AMZN', 'GOOGL', 'T']
    interval=str(interval_mins)+'min'
    iteration =0
    if 'texted_plays' not in locals():
        texted_plays  =  []
    #check every sleep_dur
    while True:
        for stock in main_positions:
            watch_pos(stock, interval)
        iteration+=1
        if iteration==reset_iterations:
            texted_plays=[]
        iteration_ordinal = ordinal(iteration)
        print(f"{iteration_ordinal} iteration complete --- sleeping {sleep_dur} secs...")
        time.sleep(sleep_dur)
        





















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
from multiprocessing import Process
from alpha_vantage.timeseries import TimeSeries
import ta
from realtime import remove_close_values
API_KEY = 'XB2M6HD2DQMJA5Z1'


def get_data(stock, time, date=None):
    
    request_url=f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={stock}&outputsize=full&interval={time}&entitlement=realtime&apikey={API_KEY}"
    resp= requests.get(request_url)
    timeseries_json=resp.json()[f'Time Series ({time})']
    # print(timeseries_a    json)


    # Convert to DataFrame
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
    df['timestamp'] = pd.to_datetime(df['timestamp'])  # Convert timestamp column to datetime
    df['percent_change'] = (df['close']-df['open'])/df['open'] * 100

    # Calculate 5-period EMA
    reversed_df = df.iloc[::-1].copy()  # Creating a copy to prevent view-copy issues
    reversed_df.loc[:, 'ema_5'] = ta.trend.ema_indicator(close=reversed_df['close'], window=5)

    df.loc[:, 'ema_5'] = reversed_df['ema_5'].iloc[::-1].values  # Assigning the reversed EMA values to the original DataFrame


    print(df)

    return df
def calculate_resistance(data, stock_symbol):
    resistance_levels = []
    high_prices = data['high'].values
    percent_changes=data['percent_change'].values
    for i in range(1, len(high_prices) - 1):
        if high_prices[i] > high_prices[i - 1] and high_prices[i] > high_prices[i + 1] and percent_changes[i]>3:
            resistance_levels.append(high_prices[i])
            print("resistance at time:", data.iloc[i])
    # clean resistances array
    resistance_levels=remove_close_values(resistance_levels)
    print(f"{stock_symbol} resistances: ", resistance_levels)
    return resistance_levels

def convert_to_hh_mm(time_stamp):
    return time_stamp.strftime('%I:%M %p')



if __name__=="__main__":
    stock='YCBD'
    # df_five=get_data(stock, '5min')
    df=get_data(stock, '1min')
    average_volume=df['volume'].mean()
    print(df)
    for index, row in df.iterrows():
        print(row)

    resistances=calculate_resistance(df, stock)

    for index, row in df.iterrows():
        cur_open=row['open']
        cur_close=row['close']
        cur_pct_chng=row['percent_change']
        for res in resistances:
            if cur_open<res and cur_close>res and row['volume']>3*average_volume and cur_pct_chng>2.5:
                print("breakout at: ", convert_to_hh_mm(row['timestamp']))


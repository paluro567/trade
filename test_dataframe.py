
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
crossed_n=500


def has_crossed_ma(df):

    for index, row in df.head(5).iterrows():
        open_p=row['open']
        close_p=row['close']
        ema=row['ema_180']
        cur_time=str(row['timestamp'])

        if open_p<ema and close_p>ema and cur_time.startswith('2023-12-29'):
            formatted_time = row['timestamp'].strftime('%I:%M %p')
            print("Crossed the 180 ema at:", formatted_time)

def crossed_180(df, resistances, crossed_n=10):
    for index, row in df.iterrows():
        if index >= crossed_n:
            open_p = row['open']
            close_p = row['close']
            ema = row['ema_180']
            cur_time = str(row['timestamp'])

            # Check for EMA crossover within 10 indices
            if df.loc[index - crossed_n]['ema_180'] > df.loc[index - 1]['ema_180'] and ema < df.loc[index - 1]['ema_180']:
                for resist in resistances:
                    if open_p < resist and close_p > resist:
                        print("Breakout at:", row['timestamp'].strftime('%I:%M %p'))

            


def get_data(stock, time, date=None):
    
    #Alpha Vantage GET request
    request_url=f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={stock}&outputsize=full&interval={time}&entitlement=realtime&apikey={API_KEY}"
    resp= requests.get(request_url)
    timeseries_json=resp.json()[f'Time Series ({time})']

    # Convert to formatted DataFrame
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
    reversed_df.loc[:, 'ema_180'] = ta.trend.ema_indicator(close=reversed_df['close'], window=180)

    df.loc[:, 'ema_5'] = reversed_df['ema_5'].iloc[::-1].values  # Assigning the reversed EMA values to the original DataFrame
    df.loc[:, 'ema_180'] = reversed_df['ema_180'].iloc[::-1].values


    print(df)

    return df
def calculate_resistance(data, stock_symbol):
    resistance_levels = []
    high_prices = data['high'].values
    percent_changes=data['percent_change'].values
    for i in range(1, len(high_prices) - 1):
        if high_prices[i] > high_prices[i - 1] and high_prices[i] > high_prices[i + 1]:
            resistance_levels.append(high_prices[i])
            print("resistance at time:", data.iloc[i])
    # clean resistances array
    resistance_levels=remove_close_values(resistance_levels)
    print(f"{stock_symbol} resistances: ", resistance_levels)
    return resistance_levels



if __name__=="__main__":

    stock='flj'
    df=get_data(stock, '1min')
    print("accessed data: ", df)
    resistances=calculate_resistance(df, stock)
    print("resistances: ", resistances)
    crossed_180(df, resistances)



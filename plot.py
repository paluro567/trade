import yfinance as yf
from datetime import datetime, timedelta
from Discord import get_briefing
from sms import text
import datetime
import pandas as pd
import numpy as np
import time
import requests
import matplotlib.pyplot as plt


API_KEY = 'XB2M6HD2DQMJA5Z1'
texted_plays={}

from alpha_vantage.timeseries import TimeSeries

def calculate_resistance(data, stock_symbol):
    resistance_levels = []
    high_prices = data['high'].values
    for i in range(1, len(high_prices) - 1):
        if high_prices[i] > high_prices[i - 1] and high_prices[i] > high_prices[i + 1]:
            resistance_levels.append(high_prices[i])
            print("resistance at time:", data.iloc[i])
    print(f"{stock_symbol} resistances: ", resistance_levels)
    return resistance_levels

def get_data(stock, time):
    request_url=f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={stock}&outputsize=compact&interval={time}&entitlement=realtime&apikey={API_KEY}"
    resp= requests.get(request_url)
    timeseries_json=resp.json()[f'Time Series ({time})']
    # print(timeseries_json)


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

    print(df)

    return df

def check_play(ticker, type):
    df=get_data(ticker, '5min')
    average_volume=df['volume'].mean()
    levels=calculate_resistance(df, ticker)

    for level in levels:
        if df.iloc[0]['open']<level and df.iloc[0]['close']>level and df.iloc[0]['percent_change']>3 and (ticker not in texted_plays or texted_plays[ticker]<=2):
            message=f"{type} - {ticker} is breaking out by {round(df.iloc[0]['percent_change'],2)}% beyond resistance of {level}!"
            print(message)
            text(message)
            # record ticker as being texted
            texted_plays[ticker] = texted_plays.get(ticker, 0) + 1

def try_check(stock,  type_string):
    try:
        check_play(stock,  type_string)
    except Exception as e:
        print(f"unable to check {stock} with error: {e}")



def plot(df):
    print(df)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['time'] = df['timestamp'].dt.strftime('%H:%M')  # Extract time as string

    x_values = df['time']
    y_values = df['close']

    plt.figure(figsize=(12, 6))  # Adjust the figure size for better readability
    plt.bar(x_values, y_values, color='skyblue')
    plt.xlabel('Time')
    plt.ylabel('Close Price')
    plt.title('Stock Close Price Over Time')

    # Extracting only the rows with 15-minute interval timestamps
    interval = 15
    x_ticks = df[df['timestamp'].dt.minute % interval == 0]['time']

    plt.xticks(x_ticks, rotation=45, ha='right')  # Set x-axis ticks to 15-minute increments

    min_price = min(y_values)
    max_price = max(y_values)
    plt.ylim(min_price - 0.1 * (max_price - min_price), max_price + 0.1 * (max_price - min_price))

    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    plot(get_data('pltr', '5min'))



















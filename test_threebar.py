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


def remove_close_values(arr):
    arr = list(set(arr))
    # Sort the array
    arr.sort()
    
    result  =  [arr[0]]  # Keep the first value by default
    # Iterate through the array
    for i in range(1, len(arr)):
        too_close  =  False
        
        # Compare the current value with all previous values
        for j in range(i):
            if abs(arr[i] - arr[j]) / max(arr[i], arr[j])*100 <=  too_close_thresh:
                too_close  =  True
                break
        
        # If the current value is not too close to any previous value, add it to the result
        if not too_close:
            result.append(arr[i])
    
    return result


def calculate_resistance(data, stock_symbol):
    resistance_levels  =  []
    high_prices  =  data['high'].values
    for i in range(1, len(high_prices) - 1):
        if high_prices[i] > high_prices[i - 1] and high_prices[i] > high_prices[i + 1]:
            resistance_levels.append(high_prices[i])
            print("resistance at time:", data.iloc[i])
    # clean resistances array
    resistance_levels = remove_close_values(resistance_levels)
    print(f"{stock_symbol} resistances: ", resistance_levels)
    return resistance_levels
def get_data(stock, time, start_time=None, end_time=None):
    
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

    print("DF IN GET_DATA: ", df)

    start_time = pd.to_datetime(start)
    end_time = pd.to_datetime(end)
    return df[(df['timestamp'] >= start_time) & (df['timestamp'] <= end_time)]
def get_plays():
    # Morning briefing
    try:
        from datetime import datetime
        from datetime import timezone
        import pytz
        desired_timezone = 'America/New_York'
        # Get current UTC time
        current_utc_time = datetime.now(timezone.utc)
        current_local_time = current_utc_time.astimezone(pytz.timezone(desired_timezone))
        curr_date_local = current_local_time.strftime('%Y-%m-%d')
        resistances, supports, retail, alarm_plays  =  get_briefing(curr_date_local)  # get briefing
        
        # clean tickers
        alarm_plays = [stock for stock in alarm_plays if ' ' not in stock]
        green_plays = list(supports.keys())
        other_on_radar = ['SLNH','PLTR','AI', 'SFWL', 'MDAI']

        # no briefing yet sleep 5 minutes
        if alarm_plays == [] and green_plays == []:
            raise Exception("empty alarm & green plays")
        
        print("today's alarm_plays: ", alarm_plays )
        print("today's green_plays: ", green_plays)


        plays_categories  =  {
            'NORMAL PLAY': green_plays,
            'ALARM PLAY': alarm_plays,
            'OTHER ON RADAR': other_on_radar
        }
        
        print("combined play categories: ", plays_categories)

    except Exception as e:
        print(f"get_plays - unable to get briefing or some error: {e}")
        print("sleeping 5 minutes...")
        time.sleep(300)  # Sleep for 5 minutes
        print("running run_main again")
        get_plays()
    return plays_categories


def run_main(interval):
    global texted_plays
    iteration = 1

    print("running run_main")
    plays_categories = get_plays()

    
    dashes = '-' * 20 # formatting

    # iterative check
    while True:
        print("checking stocks!")
        for category, stocks in plays_categories.items():
            for priority, stock in enumerate(stocks):
                try:
                    print(f"{dashes}checking {stock} {dashes}")
                    check_play(stock, category, priority+1, interval)
                    
                except Exception as e:
                    print(f"run_main - unable to check {stock} with error: {e}")

        print("Iteration complete - sleeping 15 seconds...")
        time.sleep(15)
        iteration += 1


        #reset texted_plays after 6.25 minutes minutes
        if iteration  == 25:
            iteration=1
            texted_plays = []
        print(f"minute {iteration} - texted plays: ", texted_plays)

if __name__  ==  '__main__':
    print("running test_threebar")
    day =input("Which day in January to check: ")
    specific_day = '2024-01-'+day
    start_hour=input("start hour: ")
    end_hour=input("end hour: ")
    start=specific_day+ f" {start_hour}:00:00"
    end=specific_day+ f" {end_hour}:00:00"
    print(f"time period: {start} to {end}")
    stock=input(f"Which stock to check on 1/{day}: ")

    df=get_data(stock,'5min', start, end)[::-1]
    pd.set_option('display.max_rows', None)

    print(f"df for {stock} on {specific_day}: \n",df)

    for i in range(3, len(df)):
        if df.iloc[i]['percent_change']>2 \
            and df.iloc[i-1]['percent_change']<0 \
            and df.iloc[i-2]['percent_change']>2:
                print(f"{stock} 3 bar at : ", df.iloc[i]['timestamp'])
        if df.iloc[i]['percent_change']>2 and df.iloc[i-1]['percent_change']>2 \
            and df.iloc[i-1]['percent_change']<0 \
            and df.iloc[i-2]['percent_change']<0 \
            and df.iloc[i-3]['percent_change']>2:
                print(f"{stock} 4 bar at : ", df.iloc[i]['percent_change'])






















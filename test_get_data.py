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

def sleep_until(target_hour, target_minute, datetime_module, time_module):
    # Get the current time
    current_time = datetime_module.now()

    # Set the target time
    target_time = current_time.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)

    # If the target time has already passed for today, set it for tomorrow
    if current_time > target_time:
        target_time += timedelta(days=1)

    # Calculate the time difference
    time_difference = (target_time - current_time).total_seconds()

    # Sleep until the target time
    time_module.sleep(time_difference)


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

def get_data(stock, interval, date=None):

    # LIMIT CALLS
    global calls_made, last_time
    # fastest rate to make api calls
    shortest_interval = 60 / 150

    elapsed_time = time.time() - last_time

    if elapsed_time<shortest_interval: # calls are being made too fast
        print("sleeping: ", shortest_interval - elapsed_time)
        time.sleep(shortest_interval - elapsed_time)

    calls_made+=1
    last_time = time.time()
    
    #Alpha Vantage GET request
    request_url=f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={stock}&outputsize=full&interval={interval}&entitlement=realtime&apikey={API_KEY}"
    resp= requests.get(request_url)
    timeseries_json=resp.json()[f'Time Series ({interval})']

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

    return df[:910] #only considser one day's data


def nine_twenty_cross(df):
    return df.iloc[1]['ema_9']<df.iloc[1]['ema_20'] and df.iloc[0]['ema_9']>df.iloc[0]['ema_20']


def monitor_bought_stock(ticker, qty, bought_price):
    # check position every 5 seconds
    while True:
        df = get_data(ticker, '30min')
        current_price = df.iloc[0]['close']
        below=df.iloc[0]['ema_9']<df.iloc[0]['ema_20']
        percent_gain  =  ((current_price - bought_price) / bought_price) * 100
        print(f" position {ticker} is up {percent_gain}")

        # sell position
        if(percent_gain<-5 or below):
            place_sell(ticker, qty)
            print(f"selling position {ticker} of {qty} shares at a price of {current_price} made {round(percent_gain,2)}%")
            break
        time.sleep(5) #sleep 5 seconds

def check_play(ticker, play_type, priority):

    df = get_data(ticker, '30min')
    print("check_play - get_data df: ", df)

    # df Calculations
    average_volume = df['volume'].mean()
    resistances = calculate_resistance(df, ticker)
    crossed=nine_twenty_cross(df)

    # most recent values to check from df
    cur_time=df.iloc[0]['timestamp']
    cur_pct_change = df.iloc[0]['percent_change']
    open_price = df.iloc[0]['open']
    close_price = df.iloc[0]['close']
    cur_volume = df.iloc[0]['volume']
    ema_5 = df.iloc[0]['ema_5']

    # -----------------------------------------CONDITIONS TO BUY--------------------------------------------------------------------------
    # only check resistances if the 180 EMA has recently been crossed within past 20 minutes

    if crossed and cur_volume>3*average_volume \
    and cur_pct_change > 1.5 \
    and (ticker not in texted_plays):
        
        # send text alert
        message = f"{play_type} - {priority} -  {ticker} is breaking out by {round(cur_pct_change,2)}% \
        and crossed 9EMA crossed above 20!"
        print(f"texting: {message}")
        text(message)

        # place Alpaca buy orders
        print(f"buying ticker: {ticker} at {cur_time}")
        try:
            if play_type  ==  'ALARM PLAY':
                qty =  10  #10000//close_price
                place_buy(str(ticker), qty)
                print(f"{ticker} - Bought amount: {qty} at a price: {close_price}")
            else:
                qty =  5    #5000//close_price
                place_buy(ticker, qty)
                print(f"{ticker} - Bought amount: {qty} at a price: {close_price}")
            separate_process  =  multiprocessing.Process(target = monitor_bought_stock(ticker, qty, close_price))
            separate_process.start()
        except Exception as e:
            print(f"check_play - UNABLE TO BUY {ticker} with an error: {e}")


def try_check(stock,  type_string, priority):
    try:
        check_play(stock,  type_string, priority)
    except Exception as e:
        print(f"try_check - unable to check {stock} with error: {e}")

def run_main():
    global texted_plays
    iteration = 1

    print("running run_main")

    # Morning briefing
    try:
        curr_date  =  datetime.datetime.now().strftime('%Y-%m-%d')
        resistances, supports, retail, alarm_plays  =  get_briefing(curr_date)  # get briefing
        alarm_plays = [stock for stock in alarm_plays if ' ' not in stock]
        green_plays = list(supports.keys())
        other_on_radar = ['SLNH','PLTR','AI', 'SFWL']

        print("today's alarm_plays: ", alarm_plays )
        print("today's green_plays: ", green_plays)

        # no briefing yet sleep 5 minutes
        if alarm_plays == [] and green_plays == []:
            raise Exception("empty alarm & green plays")

        plays_categories  =  {
            'NORMAL PLAY': green_plays,
            'ALARM PLAY': alarm_plays,
            'OTHER ON RADAR': other_on_radar
        }
        
        print("combined play categories: ", plays_categories)

    except Exception as e:
        print(f"run_main - unable to get briefing or some error: {e}")
        print("sleeping 5 minutes...")
        time.sleep(300)  # Sleep for 5 minutes
        print("running run_main again")
        run_main()

    # iterative check
    dashes='-' * 20
    while True:
        try:
            print("checking stocks!")
            for category, stocks in plays_categories.items():
                for priority, stock in enumerate(stocks):
                    print(f"{dashes}checking {stock} {dashes}")
                    try_check(stock, category, priority+1)
                
        except Exception as e:
            print("run_main - unable to minute iterate with error: ", e)

        print("Iteration complete - sleeping 15 seconds...")
        time.sleep(15)
        iteration+= 1

        #reset iteration dict after 5 minutes
        if iteration  == 20:
            texted_plays = []
        print(f"minute {iteration} - texted plays: ", texted_plays)

if __name__  ==  '__main__':
    pd.set_option('display.max_rows', None)  # None means display all rows
    pd.set_option('display.max_columns', None)  # None means display all columns

    data=get_data("MDAI", "30min")
    print("data: ", data)



















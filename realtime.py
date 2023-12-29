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
too_close_thresh = 0.015 #resistances are duplicates if within 0.5% of one another
texted_plays  =  {}  # Initializing texted_plays dictionary here


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
            if abs(arr[i] - arr[j]) / max(arr[i], arr[j]) <=  too_close_thresh:
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

    df.loc[:, 'ema_5'] = reversed_df['ema_5'].iloc[::-1].values  # Assigning the reversed EMA values to the original DataFrame


    print(df)

    return df

def monitor_bought_stock(ticker, qty, bought_price, bought_below_five):
    
    # check position every 5 seconds
    while True:
        df = get_data(ticker, '1min')
        current_price = df.iloc[0]['close']
        currently_below_five = current_price<df.iloc[0]['ema_5']
        percent_gain  =  ((current_price - bought_price) / bought_price) * 100
        print(f" position {ticker} is up {percent_gain}")

        # sell position
        if((currently_below_five and not bought_below_five) or percent_gain<-2):
            place_sell(ticker, qty)
            print(f"selling position {ticker} of {qty} shares at a price of {current_price} made {percent_gain}%")
            break
        time.sleep(5)

def check_play(ticker, play_type, priority):
    df = get_data(ticker, '1min')
    print("check_play - get_data df: ", df)
    average_volume = df['volume'].mean()
    resistances = calculate_resistance(df, ticker)

    # most recent values to check from df
    cur_pct_change = df.iloc[0]['percent_change']
    open_price = df.iloc[0]['open']
    close_price = df.iloc[0]['close']
    cur_volume = df.iloc[0]['volume']
    cur_ema = df.iloc[0]['ema_5']

    # -----------------------------------------CONDITIONS TO BUY--------------------------------------------------------------------------
    for cur_res in resistances:
        if cur_volume>3*average_volume and open_price<cur_res and close_price>cur_res and cur_pct_change > 1.5 and (ticker not in texted_plays):
            message = f"{play_type} - {priority} -  {ticker} is breaking out by {round(cur_pct_change,2)}% beyond resistance of {cur_res}!"
            print(f"texting: {message}")
            text(message)
            print("buying ticker: ",ticker)
            print("type of ticker: ", type(ticker))

            # place Alpaca buy orders
            try:
                if play_type  ==  'ALARM PLAY':
                    qty =  10  #10000//close_price
                    place_buy(str(ticker), qty)
                    print(f"{ticker} - Bought amount: {qty} at a price: {close_price}")
                else:
                    qty =  5    #5000//close_price
                    place_buy(ticker, qty)
                    print(f"{ticker} - Bought amount: {qty} at a price: {close_price}")
                bought_below_five = close_price<cur_ema
                separate_process  =  multiprocessing.Process(target = monitor_bought_stock(ticker, qty, close_price, bought_below_five))
                separate_process.start()
            except Exception as e:
                print(f"UNABLE TO BUY {ticker} with an error: {e}")

            # record ticker as being texted/bought
            texted_plays[ticker]  =  texted_plays.get(ticker, 0) + 1
            break

def try_check(stock,  type_string, priority):
    try:
        check_play(stock,  type_string, priority)
    except Exception as e:
        print(f"unable to check {stock} with error: {e}")

def run_main():
    global texted_plays 
    
    iteration = 1
    print("running main")

    # Morning briefing
    try:
        curr_date  =  datetime.datetime.now().strftime('%Y-%m-%d')
        resistances, supports, retail, alarm_plays  =  get_briefing(curr_date)  # get briefing
        alarm_plays = [stock for stock in alarm_plays if ' ' not in stock]
        green_plays = list(supports.keys())
        other_on_radar = ['SLNH','PLTR','AI', 'SFWL']

        print("today's alarm_plays: ", alarm_plays )
        print("today's retail: ", retail)
        print("today's green_plays: ", green_plays)

        # no briefing yet sleep 5 minutes
        if alarm_plays is [] and green_plays == []:
            raise Exception("no briefing yet error")

        plays_categories  =  {
            'NORMAL PLAY': green_plays,
            'ALARM PLAY': alarm_plays,
            'OTHER ON RADAR': other_on_radar
        }
        
        print("play categories: ", plays_categories)
    except Exception as e:
        print(f"unable to get briefing or some error: {e}")
        print("sleeping 5 minutes...")
        time.sleep(300)  # Sleep for 5 minutes
        run_main()

    # iterative check
    while True:
        try:
            print("checking stocks!")
            for category, stocks in plays_categories.items():
                for priority, stock in enumerate(stocks):
                    print(f"{'-' * 20}checking {stock} {'-' * 20}")
                    try_check(stock, category, priority+1)
                
        except Exception as e:
            print("unable to minute iterate with error: ", e)
        print("Iteration complete - sleeping 15 seconds...")
        time.sleep(15)
        iteration+= 1
        #reset iteration dict after 10 minutes
        if iteration  == 20:
            texted_plays = {}
        print("texted plays: ", texted_plays)

def sleep_to_nine_fifteen():
    #sleep until 9:15AM
    from datetime import datetime, time
    import time as t

    # Get the current time
    current_time  =  datetime.now().time()

    # Define the target time (9:15 AM)
    target_time  =  time(9, 15)

    # Calculate the number of seconds until 9:15 AM
    if current_time < target_time:
        delta  =  datetime.combine(datetime.today(), target_time) - datetime.now()
        seconds  =  delta.total_seconds()
    else:
        # If it's already past 9:15 AM, calculate the seconds until the next day's 9:15 AM
        tomorrow  =  datetime.combine(datetime.today(), target_time)
        tomorrow +=  timedelta(days = 1)
        delta  =  tomorrow - datetime.now()
        seconds  =  delta.total_seconds()

    # Sleep until 9:15 AM
    print(f"sleeping {seconds} seconds")
    t.sleep(seconds)
    print("Wake up at 9:15 AM!")

if __name__  ==  '__main__':
    # sleep_to_nine_fifteen()

    # Initialize texted_plays only once
    if 'texted_plays' not in locals():
        texted_plays  =  {}  # Initializing texted_plays dictionary here
    try:
        run_main()
    except Exception as e:
        print(f"unable to run_main error: {e}")

    # get_data('pltr', '1min')



















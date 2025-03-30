import yfinance as yf
import datetime
from datetime import timezone
import pytz

from datetime import datetime, timedelta
from Discord import get_briefing
from record_day_trade import pdt_rule, record_trade
from sms import text
import pandas as pd
import numpy as np
import time
import requests
from multiprocessing import Process
import ta
from alpaca import try_orders
import pytz



# GLOBALS
global BOUGHT_PLAYS  # bought a stock this day
BOUGHT_PLAYS=[]

global calls_made
calls_made = 0

global shortest_interval
shortest_interval = 1.8 # 2,000 calls are allowed per hour using YF

global last_time
last_time = time.time()

global TEXTED_PLAYS
TEXTED_PLAYS  =  []

global BOUGHT_AMT
BOUGHT_AMT=0

def is_before_noon_est():
    est = pytz.timezone('America/New_York')
    current_time_est = datetime.now(est)
    return current_time_est.hour < 12

def sleep_until(target_hour, target_minute):
    # Get the current time
    current_time = datetime.now()

    # Set the target time
    target_time = current_time.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)

    # If the target time has already passed for today, set it for tomorrow
    if current_time > target_time:
        target_time += timedelta(days=1)

    # Calculate the time difference
    time_difference = (target_time - current_time).total_seconds()

    # Sleep until the target time
    time.sleep(time_difference)

def yf_data(ticker, interval_time):
    global calls_made, last_time, shortest_interval

    elapsed_time = time.time() - last_time
    if elapsed_time < shortest_interval:
        sleep_time = shortest_interval - elapsed_time
        print(f"rate limit sleep: {sleep_time}")
        time.sleep(sleep_time)

    last_time = time.time()
    calls_made += 1
    if calls_made % 50 == 0:
        print(f"calls made: {calls_made} at {last_time}")

    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1d", interval=interval_time, prepost=True)
        print(f"{ticker} raw data shape: {df.shape}")
        if df.empty:
            print(f"{ticker} returned empty DataFrame.")
            return df

        print(f"{ticker} raw data head:\n{df.head()}")
        if df.index.tz is None:
            print(f"{ticker}: Data index has no timezone info, localizing to UTC.")
            df.index = df.index.tz_localize('UTC')

        df.index = df.index.tz_convert('America/New_York')

        df = df[::-1]  # Reverse
        df['SMA_5'] = df['Close'].rolling(window=5).mean()
        df['SMA_9'] = df['Close'].rolling(window=9).mean()
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_180'] = df['Close'].rolling(window=180).mean()
        df['percent_change'] = (df['Close'] - df['Open']) / df['Open'] * 100
        print("percent_change data:\n", df['percent_change'])

        return df

    except Exception as e:
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} - ERROR -  fetching data for {ticker}: {e}")
        return pd.DataFrame()


def find_resistance_points(data):
    # Identify points of resistance where both open and close prices are less than the high of the bar.
    resistance_points = data[(data['Open'] < data['High']) & (data['Close'] < data['High'])]
    
    # Convert to list to ensure an empty list is returned if no resistance points are found
    return resistance_points['High'].tolist()

def check_play(ticker, play_type, priority, interval):
    BUY_AMT = 1400
    global BOUGHT_AMT, BOUGHT_PLAYS

    print(f"Checking {ticker} play (type: {play_type}, priority: {priority}) PDT rule: {pdt_rule()}")
    try:
        df = yf_data(ticker, interval)

        if df.empty or len(df) < 4:
            print(f"{ticker}: Data not usable (empty or too short). Skipping play check.")
            return

        print(f"{ticker}: Using first 4 rows for bar logic.")
        cur_open = df.iloc[0]['Open']
        close_price = df.iloc[0]['Close']
        cur_vol = df.iloc[0]['Volume']
        time_stmp = df.index[0]
        print("time_stmp:", time_stmp)

        avg_vol = df['Volume'].mean()
        resistances = find_resistance_points(df)

        cur_pch = round(df.iloc[0]['percent_change'], 2)
        prior_pch = round(df.iloc[1]['percent_change'], 2)
        two_prior_pch = round(df.iloc[2]['percent_change'], 2)
        three_prior_pch = round(df.iloc[3]['percent_change'], 2)

        print(f"cur_pch: {cur_pch}, prior_pch: {prior_pch}, two_prior_pch: {two_prior_pch}, three_prior_pch: {three_prior_pch}")

        # Resistance check
        for resistance in resistances:
            if cur_open < resistance < close_price and cur_pch > 5 and ticker not in TEXTED_PLAYS:
                message = f"{ticker} is breaking resistance at {resistance} and moving {cur_pch}%"
                text(message)
                TEXTED_PLAYS.append(ticker)

        # 3 Bar
        if two_prior_pch > 5 and prior_pch < 0 and cur_pch > 5 and ticker not in TEXTED_PLAYS:
            message = f"{play_type} - {priority} -  {ticker} 3 bar play \n Confirmation {cur_pch}%\n test: {prior_pch}%\nignighting: {two_prior_pch}%"
            print(f"Texting: {message}")
            text(message)
            TEXTED_PLAYS.append(ticker)

        if two_prior_pch > 5 and prior_pch < 0 and cur_pch > 5 and len(BOUGHT_PLAYS) == 0 and not pdt_rule() and is_before_noon_est():
            print(f"placing {ticker} orders => {BUY_AMT // close_price} shares")
            order_process = Process(target=try_orders, args=(ticker, BUY_AMT // close_price, cur_open, {
                "ignighting": two_prior_pch,
                "test": prior_pch,
                "confirmation": cur_pch
            }))
            order_process.start()
            BOUGHT_AMT += close_price * (BUY_AMT // close_price)
            BOUGHT_PLAYS.append(ticker)

        # 4 Bar
        if three_prior_pch > 5 and (two_prior_pch < 0 or prior_pch < 0) and cur_pch > 5 and ticker not in TEXTED_PLAYS:
            message = f"{play_type} - {priority} -  {ticker} 4 bar play\n Confirmation {cur_pch}%\n test: {prior_pch}%\n test: {two_prior_pch}%\nignighting: {three_prior_pch}%"
            text(message)
            TEXTED_PLAYS.append(ticker)

        if three_prior_pch > 5 and (two_prior_pch < 0 or prior_pch < 0) and cur_pch > 5 and len(BOUGHT_PLAYS) == 0 and not pdt_rule() and is_before_noon_est():
            print(f"placing {ticker} orders => {BUY_AMT // close_price} shares")
            order_process = Process(target=try_orders, args=(ticker, BUY_AMT // close_price, cur_open, {
                "ignighting": three_prior_pch,
                "test1": two_prior_pch,
                "test2": prior_pch,
                "confirmation": cur_pch
            }))
            order_process.start()
            BOUGHT_AMT += close_price * (BUY_AMT // close_price)
            BOUGHT_PLAYS.append(ticker)

        # Single bar
        if cur_pch > 10 and ticker not in TEXTED_PLAYS:
            message = f"{play_type} - {priority} -  {ticker} is breaking out by {cur_pch}%"
            print(f"Texting: {message}")
            text(message)
            TEXTED_PLAYS.append(ticker)

    except Exception as e:
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} - ERROR - check_play - unable to check {ticker} with error: {e}")


def get_plays():

    # Morning briefing
    try:
        
        

        # Get current UTC time
        desired_timezone = 'America/New_York'
        current_utc_time = datetime.now(timezone.utc)
        current_local_time = current_utc_time.astimezone(pytz.timezone(desired_timezone))
        curr_date_local = current_local_time.strftime('%Y-%m-%d')
        alarm_plays, green_plays  =  get_briefing(curr_date_local)  # get briefing
        
        
        other_on_radar = ['PLTR','AI', 'MDAI', 'SOFI']

        # no briefing yet sleep 5 minutes
        if alarm_plays == [] and green_plays == []:
            raise Exception(f"{datetime.now():%Y-%m-%d %H:%M:%S} - ERROR - empty alarm & green plays")
        
        print("today's alarm_plays: ", alarm_plays, flush=True)
        print("today's green_plays: ", green_plays, flush=True)


        plays_categories  =  {
            'NORMAL PLAY': green_plays,
            'ALARM PLAY': alarm_plays,
            'OTHER ON RADAR': other_on_radar
        }
        
        print("combined play categories: ", plays_categories, flush=True)

    except Exception as e:
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} - ERROR - get_plays - unable to get briefing or some error: {e}", flush=True)
        print("sleeping 5 minutes...", flush=True)
        time.sleep(300)  # Sleep for 5 minutes
        print("running watch_zip_plays again", flush=True)
        return get_plays()
    return plays_categories

def watch_zip_plays(interval):

    print("watch_zip_plays", flush=True)
    global BOUGHT_PLAYS
    global TEXTED_PLAYS
    TEXTED_PLAYS=[]
    iteration = 1
    dashes = '-' * 20 # formatting

    # sleep_until(9, 29) # start executing 9:29
    print("test 1", flush=True)

    print("running watch_zip_plays", flush=True)
    plays_categories = get_plays()

    july_august_zip=['SERV', 'MARA']  # TODO add JULY/AUGUST
    # stock_watch_june=["MU", "ONON", "COIN", "FXI", "FUTU", "BABA", "FFIE"] 



    print("test 2", flush=True)
    # iterative check
    iter_count=0
    while True:
        iter_count+=1

        # only watch_zip_plays while still before 8pm
        current_time = datetime.now().time()
        if current_time.hour >= 20:  
            return 0 # exit for today

        print(f"checking stocks iteration! - {iter_count}", flush=True)
        # zip plays
        for category, stocks in plays_categories.items():
            for priority, stock in enumerate(stocks):
                try:
                    print(f"{dashes}Checking {stock} {dashes}", flush=True)
                    check_play(stock, category, priority+1, interval)

                except Exception as e:
                    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} - ERROR - watch_zip_plays - unable to check {stock} with error: {e}", flush=True)
        # stock watch plays
        for stock in july_august_zip:
            print("test 3", flush=True)
            check_play(stock, "july_august_zip", 5, interval)
            print("test 4", flush=True)
    
        iteration += 1

        #reset TEXTED_PLAYS after 6.25 minutes minutes (changed from 50)
        if iteration  == 40:
            iteration=1
            TEXTED_PLAYS = []
        print(f"minute {iteration} - texted plays: ", TEXTED_PLAYS)

if __name__  ==  '__main__':
    print("main running")
    # print("is_before_noon_est:", is_before_noon_est())
    try:
        watch_zip_plays('5m')
    except Exception as e:
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} - ERROR - unable to run watch_zip_plays with: {e}")
        



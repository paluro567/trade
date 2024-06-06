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
from multiprocessing import Process
from alpha_vantage.timeseries import TimeSeries
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
     # rate limit 
    global calls_made, last_time, shortest_interval
    
    elapsed_time = time.time() - last_time

    if elapsed_time<shortest_interval: # calls are being made too fast
        sleep_time=shortest_interval - elapsed_time
        print(f"rate limit sleep: {sleep_time}")
        time.sleep(sleep_time)

    last_time = time.time()
    calls_made+=1
    # track every 50'th call
    if calls_made%50==0:
        print("calls made: {calls_made} at {last_time}")
    
    try:
        # Fetch intraday data using the ticker symbol
        stock = yf.Ticker(ticker)
        
        # Get market data 
        intraday_data = stock.history(period="1d", interval=interval_time, prepost=True)
        intraday_data=intraday_data[::-1]  # reverse for calculating the EMA values
        

        # Calculate EMAs
        intraday_data['SMA_5'] = intraday_data['Close'].rolling(window=5).mean()
        intraday_data['SMA_9'] = intraday_data['Close'].rolling(window=9).mean()
        intraday_data['SMA_20'] = intraday_data['Close'].rolling(window=20).mean()
        intraday_data['SMA_180'] = intraday_data['Close'].rolling(window=180).mean()
        intraday_data['percent_change'] = (intraday_data['Close']-intraday_data['Open'])/ intraday_data['Open']* 100
        print("percent_change data: ", intraday_data['percent_change'])

        return intraday_data # yahoo data return
    except Exception as e:
        print("ERROR -  fetching data:", e)

def check_play(ticker, play_type, priority, interval):
    global BOUGHT_AMT  # 0
    global BOUGHT_PLAYS  #[]

    print(f" {ticker} check play pdt_rule(): ",  pdt_rule())

    # DATA
    try:
        df = yf_data(ticker, interval)
        close_price = df.iloc[0]['Close']
        cur_vol = df.iloc[0]['Volume']
        time_stmp = df.index[0]  # Extracting datetime from index
        print("time_stmp: ",time_stmp)
        avg_vol = df['Volume'].mean()

        cur_open = df.iloc[0]['Open']
        cur_pch = df.iloc[0]['percent_change']
        print("cur_pch: ",cur_pch)

        prior_pch = df.iloc[1]['percent_change']
        print("prior_pch: ",prior_pch)

        two_prior_pch= df.iloc[2]['percent_change']
        print("two_prior_pch: ",two_prior_pch)

        three_prior_pch= df.iloc[3]['percent_change']
        print("three_prior_pch: ",three_prior_pch)


        # Threshholds
        three_thresh=5
        four_thresh=5
        bar_thresh=10

        # 3 bar
        if two_prior_pch>three_thresh and prior_pch<0 and cur_pch>three_thresh and ticker not in TEXTED_PLAYS:
            message = f"{play_type} - {priority} -  {ticker} 3 bar play \n Confirmation {round(cur_pch,2)}%\n test: {round(prior_pch,2)}%\nignighting: {round(two_prior_pch,2)}%"
          
            print(f"Texting: {message}")
            text(message)
            # place orders
            if ticker not in BOUGHT_PLAYS and BOUGHT_AMT<100 and not pdt_rule() and is_before_noon_est():
                print(f"placing {ticker} orders => {(100-BOUGHT_AMT)//close_price} shares")
                order_process = Process(target=try_orders, args=(ticker, (100-BOUGHT_AMT) // close_price, cur_open)) #  submit orders
                order_process.start()
                BOUGHT_AMT+= close_price*((100-BOUGHT_AMT)//close_price)
                BOUGHT_PLAYS.append(ticker)
            TEXTED_PLAYS.append(ticker)

        # 4 bar
        if three_prior_pch>four_thresh and (two_prior_pch<0 or prior_pch<0) and cur_pch>four_thresh and ticker not in TEXTED_PLAYS:
            message = f"{play_type} - {priority} -  {ticker} 4 bar play\n Confirmation {round(cur_pch,2)}%\n test: {round(prior_pch,2)}%\n test: {round(two_prior_pch,2)}%\nignighting: {round(three_prior_pch,2)}%"
            text(message)
            if ticker not in BOUGHT_PLAYS and BOUGHT_AMT<100 and not pdt_rule() and is_before_noon_est():
                print(f"placing {ticker} orders => {(100-BOUGHT_AMT)//close_price} shares")
                order_process = Process(target=try_orders, args=(ticker, (100-BOUGHT_AMT) // close_price, cur_open)) #  submit orders
                order_process.start()
                BOUGHT_AMT+= close_price*((100-BOUGHT_AMT)//close_price)
                BOUGHT_PLAYS.append(ticker)
            TEXTED_PLAYS.append(ticker)
              
        # single bar 
        if cur_pch >bar_thresh and ticker not in TEXTED_PLAYS: 
    
            message = f"{play_type} - {priority} -  {ticker} is breaking out by {round(cur_pch,2)}"
          
            print(f"Texting: {message}")
            text(message)
            TEXTED_PLAYS.append(ticker)

    except Exception as e:
        print(f"ERROR - check_play - unable to check {ticker} with error: {e}")


def get_plays():

    # Morning briefing
    try:
        
        from datetime import timezone
        import pytz

        # Get current UTC time
        desired_timezone = 'America/New_York'
        current_utc_time = datetime.now(timezone.utc)
        current_local_time = current_utc_time.astimezone(pytz.timezone(desired_timezone))
        curr_date_local = current_local_time.strftime('%Y-%m-%d')
        alarm_plays, green_plays  =  get_briefing(curr_date_local)  # get briefing
        
        
        other_on_radar = ['SLNH','PLTR','AI', 'SFWL', 'MDAI', 'SURG', 'SOFI']

        # no briefing yet sleep 5 minutes
        if alarm_plays == [] and green_plays == []:
            raise Exception("ERROR - empty alarm & green plays")
        
        print("today's alarm_plays: ", alarm_plays)
        print("today's green_plays: ", green_plays)


        plays_categories  =  {
            'NORMAL PLAY': green_plays,
            'ALARM PLAY': alarm_plays,
            'OTHER ON RADAR': other_on_radar
        }
        
        print("combined play categories: ", plays_categories)

    except Exception as e:
        print(f"ERROR - get_plays - unable to get briefing or some error: {e}")
        print("sleeping 5 minutes...")
        time.sleep(300)  # Sleep for 5 minutes
        print("running watch_zip_plays again")
        return get_plays()
    return plays_categories

def watch_zip_plays(interval):

    print("watch_zip_plays")
    global BOUGHT_PLAYS
    global TEXTED_PLAYS
    TEXTED_PLAYS=[]
    iteration = 1
    dashes = '-' * 20 # formatting

    sleep_until(9, 29) # start executing 9:29
    print("test 1")

    print("running watch_zip_plays")
    plays_categories = get_plays()
    stock_watch_june=["MU", "ONON", "COIN", "FXI", "FUTU", "BABA", "FFIE"]



    # iterative check
    print("test 2")
    while True:

        # only watch_zip_plays while still before 8pm
        current_time = datetime.now().time()
        if current_time.hour >= 20:  
            return 0

        print("checking stocks!")
        # zip plays
        for category, stocks in plays_categories.items():
            for priority, stock in enumerate(stocks):
                try:
                    print(f"{dashes}Checking {stock} {dashes}")
                    check_play(stock, category, priority+1, interval)

                    
                except Exception as e:
                    print(f"ERROR - watch_zip_plays - unable to check {stock} with error: {e}")
        # stock watch plays
        for stock in stock_watch_june:
            print("test 3")
            check_play(stock, "stock_watch_june", 5, interval)
            print("test 4")
        
        
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
        print(f"ERROR - unable to run watch_zip_plays with: {e}")
        



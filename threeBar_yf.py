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
from alpaca import try_buy


# Initialize variables to track API call rate
global BOUGHT  # bought a stock this day
BOUGHT=False

global calls_made
calls_made = 0

global shortest_interval
shortest_interval = 1.8 # 2,000 calls are allowed per hour using YF

global last_time
last_time = time.time()

texted_plays  =  []
bought=[]
bought_amt=0

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

    calls_made+=1
    last_time = time.time()
    if calls_made%50==0:
        print("calls made: {calls_made} at {last_time}")
    
    try:
        # Fetch intraday data using the ticker symbol
        stock = yf.Ticker(ticker)
        
        # Get historical market data for the last trading day with 5-minute intervals
        intraday_data = stock.history(period="1d", interval=interval_time, prepost=True)
        intraday_data=intraday_data[::-1]
        
        # Print the intraday data
        print("Intraday Data for", ticker)

        # Calculate EMAs
        intraday_data['SMA_5'] = intraday_data['Close'].rolling(window=5).mean()
        intraday_data['SMA_9'] = intraday_data['Close'].rolling(window=9).mean()
        intraday_data['SMA_20'] = intraday_data['Close'].rolling(window=20).mean()
        intraday_data['SMA_180'] = intraday_data['Close'].rolling(window=180).mean()
        print("Close data: ", intraday_data['Close'])
        print("open data: ", intraday_data['Open'])
        intraday_data['percent_change'] = (intraday_data['Close']-intraday_data['Open'])/ intraday_data['Open']* 100
        print("percent_change data: ", intraday_data['percent_change'])

        return intraday_data # yahoo data return
    except Exception as e:
        print("Error fetching data:", e)



def nine_twenty_cross(df):
    return df.iloc[1]['SMA_9']<df.iloc[1]['SMA_20'] and df.iloc[0]['SMA_9']>df.iloc[0]['SMA_20']


def crosses_below(df, threshold):
    return (df.iloc[0]['Close'] < threshold and df.iloc[0]['Open'] > threshold) \
           or (df.iloc[0]['Close'] < threshold and df.iloc[1]['Open'] > threshold)

def monitor_bought_stock(ticker, qty, bought_price, support, bought_date):
    global BOUGHT
    
    while True:
        df = yf_data(ticker, '1m')
        current_price = df.iloc[0]['Close']
        cur_time = df.index[0]

        #  price weakening
        ema_cross = crosses_below(df, df.iloc[0]['SMA_9'])
        support_cross = crosses_below(df, support)

        percent_gain  =  round(((current_price - bought_price) / bought_price),2) * 100

        # sell position
        if percent_gain < -2:
            print(f"SOLD: percent_gain: {percent_gain} at {cur_time}")
            place_sell(ticker, qty)
            break

        elif ema_cross:
            print(f"SOLD: EMA crossover ~ percent_gain: {percent_gain} at {cur_time}")
            place_sell(ticker, qty)
            break

        elif support_cross:
            print(f"SOLD: Support crossover ~ percent_gain: {percent_gain} at {cur_time}")
            place_sell(ticker, qty)
            break

        elif percent_gain > 25:
            print(f"SOLD: percent_gain > 25% ~ percent_gain: {percent_gain} at {cur_time}")
            place_sell(ticker, qty)
            break

        elif percent_gain < -5:
            print(f"SOLD: percent_gain < -5% ~ percent_gain: {percent_gain} at {cur_time}")
            place_sell(ticker, qty)
            break


def check_play(ticker, play_type, priority, interval):
    # global BOUGHT 
    # print(" pdt_rule(): ",  pdt_rule())

    try:
        # DATA
        df = yf_data(ticker, interval)
        close_price = df.iloc[0]['Close']
        cur_vol = df.iloc[0]['Volume']
        time_stmp = df.index[0]  # Extracting datetime from index
        print("time_stmp: ",time_stmp)
        avg_vol = df['Volume'].mean()

        cur_pch = df.iloc[0]['percent_change']
        print("cur_pch: ",cur_pch)

        prior_pch = df.iloc[1]['percent_change']
        print("prior_pch: ",prior_pch)

        prior_prior_pch= df.iloc[2]['percent_change']
        print("prior_prior_pch: ",prior_prior_pch)

        prior_prior_prior_pch= df.iloc[3]['percent_change']
        print("prior_prior_prior_pch: ",prior_prior_prior_pch)

        support = df.iloc[1]['Close']
        igniting_three = df.iloc[2]['percent_change']  # 3 bar igniting
        prior_support = df.iloc[2]['Close']
        igniting_four = df.iloc[3]['percent_change']  # 4 bar igniting

        # Threshholds
        three_thresh=5
        four_thresh=5
        bar_thresh=10

        # 3 bar
        if prior_prior_pch>three_thresh and prior_pch<0 and cur_pch>three_thresh and ticker not in texted_plays:
            message = f"{play_type} - {priority} -  {ticker} 3 bar play \n Confirmation {round(cur_pch,2)}%\n test: {round(prior_pch,2)}%\nignighting: {round(prior_prior_pch,2)}%"
          
            print(f"Texting: {message}")
            text(message)
            if ticker not in bought and bought_amt<100:
                try_buy(ticker, 100//close_price) # buy at most $100
                bought_amt+= close_price*(100//close_price)
                bought.append(ticker)
            texted_plays.append(ticker)

        # 4 bar
        if prior_prior_prior_pch>four_thresh and (prior_prior_pch<0 or prior_pch<0) and cur_pch>four_thresh and ticker not in texted_plays:
            message = f"{play_type} - {priority} -  {ticker} 4 bar play\n Confirmation {round(cur_pch,2)}%\n test: {round(prior_pch,2)}%\n test: {round(prior_prior_pch,2)}%\nignighting: {round(prior_prior_prior_pch,2)}%"
            text(message)
            if ticker not in bought and bought_amt<100:
                try_buy(ticker, 100//close_price) # buy at most $100
                bought_amt+= close_price*(100//close_price)
                bought.append(ticker)
            texted_plays.append(ticker)
              
        # single bar 
        if cur_pch >bar_thresh and ticker not in texted_plays: 
    
            message = f"{play_type} - {priority} -  {ticker} is breaking out by {cur_pch}"
            if ticker not in bought and bought_amt<100:
                try_buy(ticker, 100//close_price) # buy at most $100
                bought_amt+= close_price*(100//close_price)
                bought.append(ticker)
          
            print(f"Texting: {message}")
            text(message)
            texted_plays.append(ticker)

    except Exception as e:
        print(f"check_play - unable to check {ticker} with error: {e}")


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
            raise Exception("empty alarm & green plays")
        
        print("today's alarm_plays: ", alarm_plays)
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
        print("running watch_zip_plays again")
        return get_plays()
    return plays_categories

def watch_zip_plays(interval):
    global BOUGHT
    sleep_until(9, 29) # start executing 9:29
    global texted_plays
    texted_plays=[]
    iteration = 1

    print("running watch_zip_plays")
    plays_categories = get_plays()

    dashes = '-' * 20 # formatting

    # iterative check
    while True: # not BOUGHT:

        # only run while still before 8pm
        current_time = datetime.now().time()
        if current_time.hour >= 20:  
            return 1

        print("checking stocks!")
        for category, stocks in plays_categories.items():
            for priority, stock in enumerate(stocks):
                try:
                    print(f"{dashes}Checking {stock} {dashes}")
                    check_play(stock, category, priority+1, interval)
                    
                except Exception as e:
                    print(f"watch_zip_plays - unable to check {stock} with error: {e}")
        
        
        iteration += 1


        #reset texted_plays after 6.25 minutes minutes (changed from 50)
        if iteration  == 40:
            iteration=1
            texted_plays = []
        print(f"minute {iteration} - texted plays: ", texted_plays)

if __name__  ==  '__main__':
    # df = yf_data('pltr', '5m')
    # print("cur pch [0]: ", df.iloc[0]['percent_change'])

    try:
        watch_zip_plays('5m')
    except Exception as e:
        print(f"unable to run watch_zip_plays with: {e}")
        



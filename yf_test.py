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


# Initialize variables to track API call rate
global BOUGHT  # bought a stock this day
BOUGHT=False
texted={}



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
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    try:
        # Fetch intraday data using the ticker symbol
        stock = yf.Ticker(ticker)
        
        # Get historical market data for the last trading day with 5-minute intervals
        intraday_data = yf.download(ticker, start=start_date, end=end_date, interval=interval_time, progress=False, prepost=True)
        intraday_data=intraday_data[::-1]

        # Calculate EMAs
        intraday_data=intraday_data[::-1]
        intraday_data['EMA_5'] = intraday_data['Close'].ewm(span=5, adjust=False).mean()
        intraday_data['EMA_9'] = intraday_data['Close'].ewm(span=9, adjust=False).mean()
        intraday_data['EMA_20'] = intraday_data['Close'].ewm(span=20, adjust=False).mean()
        intraday_data['EMA_180'] = intraday_data['Close'].ewm(span=180, adjust=False).mean()
        intraday_data=intraday_data[::-1]
        intraday_data['percent_change'] = (intraday_data['Close']-intraday_data['Open'])/ intraday_data['Open']* 100

        return intraday_data # yahoo data return
    except Exception as e:
        print("Error fetching data:", e)


def run_monitor_holdings(interval):
    # sleep_until(9, 29) # start executing 9:29

    iteration = 1

    dashes = '-' * 20 # formatting

    # iterative check
    main_positions=['AMZN', 'PLTR', 'PYPL', 'TSLA', 'MARA', 'GOOGL']
    print(f"checking main_positions:\n- " + '\n- '.join(main_positions))

    while True: 
        print(f"-- Iteration {iteration} {dashes}")
        for stock in main_positions:
            try:
                print(f"{dashes}Checking {stock} {dashes}")
                check_play(stock,interval)
            except Exception as e:
                print(f"run_monitor_holdings - unable to check {stock} with error: {e}")
        iteration +=1
        time.sleep(11) #sleep 11 seconds to avoid rate limit of 2000/hour
        
        
if __name__  ==  '__main__':
    interval="30m"
    df=yf_data('tsla', interval)
    pd.set_option('display.max_rows', None)
    print(df)
    print("\npercent_change (last row): ", df.iloc[0]['percent_change'])


    # print("index 0: ", df.iloc[0])
    # print("\nindex -1: ",df.iloc[-1])
    # print("percent_change: ", df['percent_change'].dtype)
    # print("df.columns: ",  df.columns)
    # print("df.tail(): ",df.tail())      

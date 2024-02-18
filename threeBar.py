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
global BOUGHT  # only place one day trade
global TIME_LIMIT # time in between continuous AV calls (150 limit)
TIME_LIMIT=0.144
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

def get_data(stock, time, date=None):
    
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

    # print("get_data - df with EMA's: ", df)

    return df[:910] #only considser one day's data


def nine_twenty_cross(df):
    return df.iloc[1]['ema_9']<df.iloc[1]['ema_20'] and df.iloc[0]['ema_9']>df.iloc[0]['ema_20']


def monitor_bought_stock(ticker, qty, bought_price, support):
    
    while True:
        df = get_data(ticker, '1min')
        current_price = df.iloc[0]['close']
        time_stmp = df.iloc[0]['timestamp']

        ema_cross = df.iloc[0]['open']>df.iloc[0]['ema_9'] and df.iloc[0]['close']<df.iloc[0]['ema_9'] \
            or df.iloc[1]['close']>df.iloc[0]['ema_9'] and df.iloc[0]['close']<df.iloc[0]['ema_9']  # crosses below ema_9
        
        support_cross = df.iloc[0]['close']<support and df.iloc[0]['open']>support \
            or df.iloc[0]['close']<support and df.iloc[1]['close']>support  # crosses below support

        percent_gain  =  ((current_price - bought_price) / bought_price) * 100

        # sell position
        if(df.iloc[0]['percent_change']<-2 or ema_cross or support_cross or percent_gain>-5 or percent_gain>25):
            place_sell(ticker, qty)
            print(f"Sold position {ticker} at {time_stmp} \nat a price of {current_price} made {round(percent_gain,2)}%")
            break
        time.sleep(TIME_LIMIT)


def check_play(ticker, play_type, priority, interval):

    try:
        # DATA
        df = get_data(ticker, interval)
        close_price=df.iloc[0]['close']
        cur_vol=df.iloc[0]['volume']
        time_stmp=df.iloc[0]['timestamp']
        avg_vol = df['volume'].mean()
        cur_pch=df.iloc[0]['percent_change']
        prior_pch=df.iloc[1]['percent_change']
        support=df.iloc[1]['close']
        igniting_three=prior_prior_pch=df.iloc[2]['percent_change'] # 3 bar igniting
        prior_support=df.iloc[2]['close']
        igniting_four=df.iloc[3]['percent_change'] # 4 bar igniting

        # 3 BAR PLAY 
        if cur_pch > 2 \
        and prior_pch < 0 \
        and igniting_three > 2 \
        and cur_vol > 3*avg_vol \
        and (ticker not in texted_plays):
            
            # text message
            message = (f"{play_type} - {priority} -  {ticker} is breaking out with 3 bar play! \n"
            f"Igniting: {round(igniting_three,2)}% \n"
            f"test:{round(prior_pch, 2)}% \n"
            f"Confirmation: {round(cur_pch,2)}%")
            print(f"Texting: {message}")
            text(message)
            texted_plays.append(ticker)

            # place Alpaca buy order
            print(f"buying ticker: {ticker} at {df.iloc[0]['timestamp']}")
            try:
                if play_type  ==  'ALARM PLAY':
                    qty =  66//close_price
                    place_buy(str(ticker), qty)
                    print(f"{ticker} - 3 bar Bought amount: {qty} at a price: {close_price} ~ {time_stmp}")
                else:  # regular play
                    qty =  50//close_price
                    place_buy(str(ticker), qty)
                    print(f"{ticker} - 3 bar Bought amount: {qty} at a price: {close_price} ~ {time_stmp}")
                BOUGHT=True
                monitor_process = multiprocessing.Process(target=monitor_bought_stock, args=(ticker, qty, close_price, support))

                monitor_process.start()
            except Exception as e:
                print(f"check_play - UNABLE TO BUY {ticker} with an error: {e}")

        # 4 bar play
        if cur_pch > 3 \
        and (prior_pch < 0 \
        or prior_prior_pch < 0) \
        and igniting_four > 2 \
        and cur_vol > 3*avg_vol \
        and (ticker not in texted_plays):
            
            # find support
            four_bar_support = prior_support if prior_pch > 0 else support

            # text message
            message = (f"{play_type} - {priority} -  {ticker} is breaking out with 4 bar play! \n"
            f"Igniting: {round(igniting_four,2)}% \n"
            f"test:{round(prior_prior_pch, 2)}% \n"
            f"test:{round(prior_pch, 2)}% \n"
            f"Confirmation: {round(cur_pch,2)}%")
            print(f"texting: {message}")
            text(message)
            texted_plays.append(ticker)

            # place Alpaca buy order
            print(f"buying ticker: {ticker} at {time_stmp}")
            try:
                if play_type  ==  'ALARM PLAY':
                    qty =  50//close_price
                    place_buy(str(ticker), qty)
                    print(f"{ticker} - 4 bar Bought amount: {qty} at a price: {close_price} ~ {time_stmp}")
                else:
                    qty = 50//close_price
                    place_buy(str(ticker), qty)
                    print(f"{ticker} - 4 bar Bought amount: {qty} at a price: {close_price} ~ {time_stmp}")
                BOUGHT=True
                monitor_process = multiprocessing.Process(target=monitor_bought_stock, args=(ticker, qty, close_price, four_bar_support))

                monitor_process.start()
            except Exception as e:
                print(f"check_play - UNABLE TO BUY {ticker} with an error: {e}")
    except Exception as e:
        print(f"check_play - unable to check {ticker} with error: {e}")


def get_plays():

    # Morning briefing
    try:
        from datetime import datetime
        from datetime import timezone
        import pytz

        # Get current UTC time
        desired_timezone = 'America/New_York'
        current_utc_time = datetime.now(timezone.utc)
        current_local_time = current_utc_time.astimezone(pytz.timezone(desired_timezone))
        curr_date_local = current_local_time.strftime('%Y-%m-%d')
        resistances, supports, retail, alarm_plays  =  get_briefing(curr_date_local)  # get briefing
        
        
        # clean tickers
        alarm_plays = [stock for stock in alarm_plays if ' ' not in stock]
        green_plays = list(supports.keys())
        other_on_radar = ['SLNH','PLTR','AI', 'SFWL', 'MDAI', 'SURG', 'SOFI']

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
        print("running run_three_bar again")
        return get_plays()
    return plays_categories


def run_three_bar(interval):
    sleep_until(9, 30, datetime, time)
    global texted_plays
    texted_plays=[]
    iteration = 1

    print("running run_three_bar")
    plays_categories = get_plays()

    dashes = '-' * 20 # formatting

    # iterative check
    while not BOUGHT:
        print("checking stocks!")
        for category, stocks in plays_categories.items():
            for priority, stock in enumerate(stocks):
                try:
                    print(f"{dashes}checking {stock} {dashes}")
                    if not BOUGHT:
                        check_play(stock, category, priority+1, interval)
                    time.sleep(TIME_LIMIT) # avoid exceding api limit
                    
                except Exception as e:
                    print(f"run_three_bar - unable to check {stock} with error: {e}")
        
        
        iteration += 1


        #reset texted_plays after 6.25 minutes minutes
        if iteration  == 60:
            iteration=1
            texted_plays = []
        print(f"minute {iteration} - texted plays: ", texted_plays)

if __name__  ==  '__main__':
    run_three_bar('1min')




















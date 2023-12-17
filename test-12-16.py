import yfinance as yf
from datetime import datetime, timedelta
from Discord import get_briefing
from sms import text
import datetime
import pandas as pd
import numpy as np


import time
import pandas as pandas
from alpha_vantage.timeseries import TimeSeries

#  Declarations
ALPHA_VINTAGE_API_KEY='XB2M6HD2DQMJA5Z1'
last_text_time={}

def calculate_resistance(data, stock_symbol):
    resistance_levels = []
    high_prices = data['High'].values
    for i in range(1, len(high_prices) - 1):
        if high_prices[i] > high_prices[i - 1] and high_prices[i] > high_prices[i + 1]:
            resistance_levels.append(high_prices[i])
            print("resistance at time:", data.iloc[i])
    print(f"{stock_symbol} resistances: ", resistance_levels)
    return resistance_levels


def get_stock_data_for_date(stock_symbol, date):
    ts = TimeSeries(key=ALPHA_VINTAGE_API_KEY, output_format='pandas')
    data, meta_data = ts.get_intraday(symbol=stock_symbol, interval='5min', outputsize='full')
    
    print(f"{stock_symbol} - accessed data: ", data.loc[date])
    return data.loc[date]

def check_latest_price_for_breakout(stock_symbol, date, stock_type):
    stock_data = get_stock_data_for_date(stock_symbol, date)
    # Rename columns
    new_columns = {'1. open': 'Open', '2. high': 'High', '3. low': 'Low', '4. close': 'Close', '5. volume': 'Volume'}
    stock_data.rename(columns=new_columns, inplace=True)
    resistance_levels=calculate_resistance(stock_data, stock_symbol)

    try:
        print("--------------------")
        print("stock_data: ", stock_data)
        print("0 index: ", stock_data.iloc[0])
        latest_price = stock_data.iloc[0]['Close']  # Get the latest price
        second_latest_price = stock_data.iloc[1]['Close']
        print("latest_price: ", latest_price)
        print("second_latest_price: ", second_latest_price)
    except:
        print("too small stock_data")
        latest_price = stock_data.iloc[0]['Close']  # Get the latest price
        second_latest_price = stock_data.iloc[1]['Close']
        
    breakout_message = False
    
    for level in resistance_levels:
        print(f"resistance level is: {level} open: {second_latest_price} close: {latest_price}")
        if (latest_price - level) / level > 0.03 and second_latest_price<level and latest_price>level:
            print(f"{stock} is breaking past {level}")
            #check volume
            current_volume = stock_data.iloc[0]['Volume']
            average_volume = stock_data['Volume'].mean()
            
            if current_volume > 2.5 * average_volume:
                print(f"{stock_symbol} breaking out!")
                message=f"{stock_type} - {stock_symbol} is breaking through resistance {round(level, 2)} by {round((latest_price - level) / level * 100, 2)}% and has {round((current_volume - average_volume) / average_volume * 100, 2)}% unusual volume."
                if stock_symbol not in last_text_time or (datetime.now() - last_text_time[stock_symbol]).total_seconds() >= 600: # check that the stock was not texted for the last 10 minutes
                    print("texting:",message)
                    text(message)
                    last_text_time[stock_symbol] = datetime.now()  # Update last text time
                    breakout_message = True
                    break  # Exit the loop after printing breakout message once
        
    if not breakout_message:
        print(f"{stock_symbol} hasn't broken any resistance levels.")
   
    


def run_main():
    print("running main")
    from datetime import datetime

    
    curr_date = datetime.now().strftime('%Y-%m-%d')
    # curr_date = datetime.strptime('2023-12-15', '%Y-%m-%d').strftime('%Y-%m-%d')


    # Morning briefing
    try:
        resistances, supports, retail, alarm_plays = get_briefing(curr_date)  # get briefing
        alarm_plays=[stock for stock in alarm_plays if ' ' not in stock]
        green_plays=list(supports.keys())
        other_on_radar=['SLNH','PLTR','AI']

        print("today's alarm_plays: ", alarm_plays )
        print("today's retail: ", retail)
        print("today's green_plays: ", green_plays)
    except Exception as e:
        print(f"unable to get briefing or some error: {e}")
        print("sleeping 5 minutes...")
        time.sleep(300)  # Sleep for 5 minutes
        run_main()

    # Minute iteration
    try:
        while True:
            print("checking stocks!")
            for stock in green_plays:
                try:
                    check_latest_price_for_breakout(stock, curr_date, 'NORMAL PLAY')
                except Exception as e:
                    print(f"unable to check {stock} with error: {e}")
            for stock in alarm_plays:
                try:
                    check_latest_price_for_breakout(stock, curr_date, 'ALARM PLAY')
                except Exception as e:
                    print(f"unable to check {stock} with error: {e}")

            for stock in other_on_radar:
                try:
                    check_latest_price_for_breakout(stock, curr_date, 'OTHER ON RADAR')
                except Exception as e:
                    print(f"unable to check {stock} with error: {e}")
            print("Iteration complete - sleeping 1 minute...")
            time.sleep(60)
    except Exception as e:
        print("unable to minute iterate with error: ", e)

if __name__ == '__main__':
    run_main()

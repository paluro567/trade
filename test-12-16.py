import yfinance as yf
from datetime import datetime, timedelta
from Discord import get_briefing
from sms import text
import datetime
import pandas as pd


import time
import pandas as pandas
from alpha_vantage.timeseries import TimeSeries

api_key='XB2M6HD2DQMJA5Z1'
last_text_time={}


def calculate_resistance(data):
    resistance_levels = []
    # Adjust how you access high prices in your data
    for i in range(1, len(data) - 1):
        if data['2. high'].iloc[i] > data['2. high'].iloc[i - 1] and data['2. high'].iloc[i] > data['2. high'].iloc[i + 1]:
            resistance_levels.append(data['2. high'].iloc[i])
            print("resistance at time:", data.iloc[i])
    print("resistances: ", resistance_levels)
    return resistance_levels


def get_stock_data_for_date(stock_symbol, date):
    ts = TimeSeries(key=api_key, output_format='pandas')
    data, meta_data = ts.get_intraday(symbol=stock_symbol, interval='5min', outputsize='full')
    
    
    print(f"{stock_symbol} - accessed data: ", data.loc[date])
    return data.loc[date]

def check_latest_price_for_breakout(stock_symbol, date, stock_type):
    stock_data = get_stock_data_for_date(stock_symbol, date)
    resistance_levels=calculate_resistance(stock_data)

    try:
        print("0 index: ", stock_data.iloc[0])
        latest_price = stock_data.iloc[0]['4. close']  # Get the latest price
        second_latest_price = stock_data.iloc[1]['4. close']
    except:
        print("too small stock_data")
        latest_price = stock_data.iloc[0]['4. close']  # Get the latest price
        second_latest_price = stock_data.iloc[0]['4. close']
        
    breakout_message = False
    
    for level in resistance_levels:
        print(f"resistance level is: {level} open: {second_latest_price} close: {latest_price}")
        if (latest_price - level) / level > 0.03 and second_latest_price<level and latest_price>level:
            print(f"{stock} is breaking past {level}")
            #check volume
            average_volume = stock_data['5. volume'].mean()
            current_volume = stock_data.iloc[-1]['5. volume']
            
            if current_volume > 2.5 * average_volume:
                print(f"{stock_symbol} breaking out!")
                message=f"{stock_type} - {stock_symbol} is breaking through resistance {round(level, 2)} by {round((latest_price - level) / level * 100, 2)}% and has unusual volume."
                if stock_symbol not in last_text_time or (datetime.now() - last_text_time[stock_symbol]).total_seconds() >= 600:
                    print("texting:",message)
                    # text(message)
                    last_text_time[stock_symbol] = datetime.now()  # Update last text time
                    breakout_message = True
                    break  # Exit the loop after printing breakout message once
        
    if not breakout_message:
        print(f"{stock_symbol} hasn't broken any resistance levels.")
   
    


def run_main():
    print("running main")
    
    # curr_date = datetime.now().strftime('%Y-%m-%d')
    curr_date = datetime.datetime.strptime('2023-12-15', '%Y-%m-%d').strftime('%Y-%m-%d')


    # Morning briefing
    try:
        resistances, supports, retail, alarm_plays = get_briefing(curr_date)  # get briefing
        alarm_plays=[stock for stock in alarm_plays if ' ' not in stock]
        supports=list(supports.keys())
        other_on_radar=['SLNH']

        print("today's alarm_plays: ", alarm_plays )
        print("today's retail: ", retail)
        print("today's supports: ", supports)
    except Exception as e:
        time.sleep(300)  # Sleep for 5 minutes
        print(f"unable to get briefing or some error: {e}")
        run_main()

    # Minute iteration
    try:
        while True:
            print("checking stocks!")
            for stock in supports + alarm_plays+other_on_radar:
                if stock in supports:
                    try:
                        check_latest_price_for_breakout(stock, curr_date, 'NORMAL PLAY')
                    except Exception as e:
                        print(f"unable to check {stock} with error: {e}")
                elif stock in alarm_plays:
                    try:
                        check_latest_price_for_breakout(stock, curr_date, 'ALARM PLAY')
                    except Exception as e:
                        print(f"unable to check {stock} with error: {e}")

                elif stock in other_on_radar:
                    try:
                        check_latest_price_for_breakout(stock, curr_date, 'OTHER ON RADAR')
                    except Exception as e:
                        print(f"unable to check {stock} with error: {e}")
            print("Iteration complete - sleeping a minute")
            time.sleep(60)
    except Exception as e:
        print("unable to minute iterate with error: ", e)

if __name__ == '__main__':
    run_main()

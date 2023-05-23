import yfinance as yf
from IPython.display import display
import pandas as pd
import Discord
from datetime import date
import os
import time
import screener
from text_msg import *

def calc_percent_change(previous, current):
    return (current-previous)/previous*100


def three_bar_func(ticker, period_val, interval_val, bars):
    ticker_yahoo = yf.Ticker(ticker)
    data = ticker_yahoo.history(period=period_val, interval=interval_val, prepost=True)  # get premarket and regular market hours data
    display(data)
    prices_arr = data['Close'].to_numpy()  # convert time series prices to array
    print("array: ", prices_arr)

    for i, price in enumerate(prices_arr):
        print(f"{i}:{price}")

    for i in range(bars):  # check 3 and 4-bar plays
        if len(prices_arr) > 4:  # make sure prices array has enough prices to check
            initial_price = prices_arr[-4-i]
            igniting_price = prices_arr[-3-i]
            igniting_percent = calc_percent_change(initial_price, igniting_price)
            baby_price = prices_arr[-2]
            baby_percent = calc_percent_change(igniting_price, baby_price)
            conf_price = prices_arr[-1]
            conf_percent = calc_percent_change(baby_price, conf_price)

            if igniting_percent > 2 and baby_percent < 0 and conf_percent > 1:  # latest price is 3-bar play confirmation!

                message = f"{ticker} has a 3 bar upward trend! (interval {interval_val})" if i==0 else \
                f"{ticker} has a 4 bar upward trend! (interval {interval_val})"

                twilio_text(message)  # notification text



if __name__ != '__main__': 
    minute_count = 1
    while True:
        os.system('python sleep.py')  # todo add back!
        print("Running Main (Market is open)!")
        today = str(date.today())
        # today = "2023-01-13"
        try:
            resistances, supports, retail, alarm_plays = Discord.get_briefing(today)
            # extra stocks to track
            long_stocks = ['PLTR', 'CHPT', 'TSLA', 'UNH', 'COIN', 'MMAT', 'MRNA']
            january_fda = ['PHAT', 'ACER', 'SGEN', 'GMDA', 'IONS']
            stocks = set(list(resistances.keys()) + retail + alarm_plays + long_stocks + january_fda)

        except Exception as e:
            print("no briefing posted for today yet!")
            print(f"Exception is: {e}")

        for stock in stocks:
            print(f"checking stock: {stock}")
            three_bar_func(stock,'1d','5m', 2) # 3-bar and 4-bar plays are checked

        time.sleep(60)  # check stocks every 1 min
        minute_count += 1     



import yfinance as yf
import os
import datetime
from datetime import date
from twilio.rest import Client
from IPython.display import display
# import pandas_datareader as web
# from RSI import *
from secret import *
# from resistance import *
import time
import json
from Discord import *
import pandas as pd
import numpy as np
import sys
import Discord

# Globals
recent={}
# Constants
message_interval=5
oversold_threshhold=25
overbought_thes=70
periods=14
dashes="-"*10


#-------------------FUNCTION DEFs---------------------------------

# check if the index is premarket
def index_pre(index):
    time_str=str(index).split(' ')[1].split('-')[0]

    # Convert the time string to a datetime.time object
    time_obj = datetime.datetime.strptime(time_str, '%H:%M:%S').time()
    return 4 <= time_obj.hour < 9

def twilio_text(message):
    cl = Client(SID, auth_token)
    cl.messages.create(body=message, from_= twilio_number, to= cell_phone)
    print("Successful text message sent: ", message)

def check_play(play, category, exit=False):
    print(f"{dashes} checking {play}")

    # get price data
    stock = yf.Ticker(play)
    stockdata = stock.history(period='1d', interval="5m", prepost=True)
    stockdata['Percent Change'] = round(stockdata['Close'].pct_change() * 100,2)

    # calculate RSI
    stockdata['delta'] = close_delta = stockdata['Close'].diff()  # Calculates Deltas
    stockdata['up'] = up = close_delta.clip(lower=0)  # positive deltas
    stockdata['down'] = down = -1 * close_delta.clip(upper=0)  # negative deltas
    ema_up = up.ewm(com=periods-1, adjust=True, min_periods = periods).mean()  # average up
    ema_down = down.ewm(com=periods-1, adjust=True, min_periods = periods).mean()  # average down

    #RSI Formula
    rsi = ema_up / ema_down
    stockdata['RSI'] = round(100-(100/(1+rsi)),2)
    stockdata.dropna(inplace=True)
    try:
        #oversold to breaking out
        if ((stockdata['RSI'].iloc[-1]<oversold_threshhold or stockdata['RSI'].iloc[-2]<30)  
        and stockdata['Percent Change'].iloc[-1]>1  #potential reversal percentage
        and recent[play]<=0):
            message=f"{category} - {play} recently oversold and is now moving up by {stockdata['Percent Change'].iloc[-1]}%"
            twilio_text(message)
            recent[play]=message_interval

        # check if play is oversold at current price
        # print("tail RSI:", stockdata.iloc[-1]['RSI'])
        cur_rsi=stockdata.iloc[-1]['RSI']

        # if cur_rsi<oversold_threshhold and recent[play]<=0:
        #     message=f"{category} - {play} is below 40 RSI at {cur_rsi} RSI"
        #     twilio_text(message)
        #     recent[play]=message_interval

        #very oversold plays
        # if cur_rsi<oversold_threshhold:
        #     message=f"{category} - {play} very oversold at {cur_rsi} RSI"
        #     twilio_text(message)
        #     recent[play]=message_interval

        # exit plays (overbought - consider selling)
        print("tail RSI:", stockdata.iloc[-1]['RSI'])
        cur_rsi=stockdata.iloc[-1]['RSI']
        if cur_rsi>overbought_thes and recent[play]<=0 and exit:
            message=f"{category} - {play} is above {overbought_thes} RSI at {cur_rsi} RSI"
            twilio_text(message)
            recent[play]=message_interval
    except:
        print(f"unable to get stock data or RSI - {play}")

def main():

    print("running Main!")

    # os.system('python sleep.py')  # sleep until 9:10 (briefing should be posted!)
    print("Waking up main (get plays now)!")

    #--------------------------------- GET BRIEFING -------------------------------------------
    today = str(date.today())
    print("today:",today)
    try:
        from Discord import get_briefing
        
        resistances, supports, retail, alarm_plays = get_briefing(today)  # get briefing
        print("resistances: ", resistances)
        print(f"Here are today's plays: \nGreen Checks (Supports):{supports}\nRetail Mention:{retail}\nAlarm Plays:{alarm_plays}")

    except Exception as e:
        print("Unable to get briefing!")
        print(f"Exception is: {e}")

    

#-------------------MINUTE ITERATIONS------------------------------------------------------

    iteration_count=1

    while True:  # iterate every minute - check each unique stock 

        # ----------alarm plays------------------
        for stock in alarm_plays:
            if stock not in recent:
                recent[stock]=0

            check_play(stock,'ALARM')
            recent[stock]-=1

        # ----------regular plays------------------
        for stock in set(list(supports.keys())+list(resistances.keys())):
            if stock not in recent:
                recent[stock]=0
            check_play(stock,'GREEN')
            recent[stock]-=1

        # ---------------AI---------------------
        for stock in ['BBAI','GFAI','AI','SOUN','MARK','VERI']:
            if stock not in recent:
                recent[stock]=0
            check_play(stock,'AI')
            recent[stock]-=1

        #-------------crypto-----------------------
        for stock in ['MARA', 'RIOT']:
            if stock not in recent:
                recent[stock]=0
            check_play(stock,'CRYPTO')
            recent[stock]-=1
            
        #--------market/volatility-----------------
        for stock in ['UVXY']:
            if stock not in recent:
                recent[stock]=0
            check_play(stock,'MARKET')
            recent[stock]-=1


        #---------nightly video suggestions----------
        video_suggestions=['PXMD', 'BRDS', 'NMTC']
        
        for stock in video_suggestions:
            if stock not in recent:
                recent[stock]=0
            check_play(stock,'NIGHTLY VIDEO')
            recent[stock]-=1

        #---------EXIT----------
        exit=['PLTR','UNH','AMZN']
        
        for stock in exit:
            if stock not in recent:
                recent[stock]=0
            check_play(stock,'EXIT', True)
            recent[stock]-=1


        time.sleep(60)  # check stocks every 1 min
        iteration_count += 1


if __name__=="__main__":

    print("STARTING MAIN")

    main()
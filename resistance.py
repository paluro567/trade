import yfinance as yf
import datetime
from text_msg import *
import json

def calc_percent_change(previous, current):
    return (current-previous)/previous*100

def breakout(ticker, alarm):
    #notify each stock at most by 5 minute frequency
    notify_every=5

    # breakout threshold (3%)
    breakout_theshold=3

    # check for ticker in recently notified json
    with open('recent.json','r') as file:
        recent_json=json.load(file)
    if ticker not in recent_json["notified"]:
        recent_json["notified"][ticker]=0

    # Get the stock data
    ticker_yahoo = yf.Ticker(ticker)
    data = ticker_yahoo.history(period='1d', interval='5m', prepost=True)
    print ("DATA: ",data)

    # reassign data variable

    # Calculate the resistance levels
    data["resistance"] = data["High"].rolling(window=5).max()

    # Compare the current stock price to the resistance levels
    current_price = data['Close'].iloc[-1]
    cur_resistance = data["resistance"].iloc[-1]
    cur_resistance2 = data["resistance"].iloc[-2]

    if alarm:
        alm="ALARM PLAY: "
    else:
        alm=""
    
    
    #check for breakout past cur_resistance
    if current_price > cur_resistance:
        breakout_percentage=calc_percent_change(cur_resistance,current_price)
        print("Breaking out!!")
        #only send text message if the breakout is more than 1% past resistance 
        #and the ticker not notified within 5 minutes
        if breakout_percentage>=1 and recent_json["notified"][ticker]<=0:
            twilio_text(f"\n {alm}{ticker} is breaking out past resistance {round(cur_resistancen,2)} by {round(breakout_percentage,2)}%")
            recent_json["notified"][ticker]=5

    #check for breakout past cur_resistance2
    elif current_price > cur_resistance2:
        breakout_percentage=calc_percent_change(cur_resistance2,current_price)
        print("Breaking out!!")
        #only send text message if the breakout is more than 1% past resistance 
        #and the ticker not notified within 5 minutes
        if breakout_percentage>=breakout_theshold and recent_json["notified"][ticker]<=0:
            twilio_text(f"{ticker} is breaking out past resistance {round(cur_resistance2,2)} by {round(breakout_percentage,2)}%")
            recent_json["notified"][ticker]=notify_every

    else:
        print("Not breaking out past resistance levels")
        recent_json["notified"][ticker]-=1
        print("updated:", recent_json)

    # Write the JSON object back to the file
    with open('recent.json', 'w') as f:
        json.dump(recent_json, f)

if __name__=='__main__':
    breakout('sunw', True)


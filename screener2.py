import yfinance as yf
import os

from datetime import date
# from pydub import AudioSegment
# from pydub.playback import play
from twilio.rest import Client
from IPython.display import display
# import pandas_datareader as web
# from RSI import *
from secret import *
# from resistance import *
import time
import json
from Discord import *
# from three_bar_play import *
from resistance import breakout

def detect_volume(ticker):
    ticker_yahoo = yf.Ticker(ticker)
    data = ticker_yahoo.history(period='60d', interval='5m',prepost=True)

    # Calculate rolling metrics
    window_size=30
    rolling_mean = data["Volume"].rolling(window=window_size).mean()
    rolling_std = data["Volume"].rolling(window=window_size).std()

    # Get the current day's volume
    current_volume = data.iloc[-1]["Volume"]

    # Calculate the z-score of the current day's volume
    try:
        z_score = (current_volume - rolling_mean.iloc[-1]) / rolling_std.iloc[-1]

        # If the z-score is greater than 2, the current day's volume is considered abnormally high (True)
        return z_score > 2
    except:
        return False


def test_ema(ticker, ema_period, minutes, is_alarm):
    ticker_yahoo = yf.Ticker(ticker)
    data = ticker_yahoo.history(period='60d', interval=minutes, prepost=True)
    # Calculate the EMA
    data["EMA"] = data["Close"].ewm(span=ema_period).mean()
    data['percent_change'] = ((data["Close"] - data["Close"].shift(1))/data["Close"].shift(1))*100

    cur_price= data["Close"].iloc[-1]
    em=data["EMA"].iloc[-1]
    percent_change = round(data["percent_change"].iloc[-1])

    #todo - add a column to data
    data['above_ema'] = data['Close'] > data['EMA']
    display(data)
    prev_above = data.iloc[-2]['above_ema']

    #texting logic
    if is_alarm:
        alarm_str="ALARM PLAY: "
    else:
        alarm_str=""
    try:
        unusual_volume=detect_volume(ticker)
    except:
        unusual_volume=False
    if unusual_volume:
        volume_str="\n Unusual volume!"
    else:
        volume_str="\n normal volume!"

    if not prev_above and percent_change > 5 and data.iloc[-1]['above_ema']:
        message = f"{alarm_str} {ticker} is breaking above EMA by {percent_change}% {volume_str}"
        twilio_text(message)


    print(f"current price: {cur_price} EMA{em} percent_change: {percent_change}")

    return em


def twilio_text(message):
    cl = Client(SID, auth_token)
    cl.messages.create(body=message, from_= twilio_number, to= cell_phone)
    print("Successful text message sent: ", message)


def get_current_price(ticker):
    try:
        ticker_yahoo = yf.Ticker(ticker)
        data = ticker_yahoo.history(period='1d', interval='1m')
        return data['Close'].iloc[-1]  # return latest minute price in dataframe
    except Exception as e:
        print("some error occurred accessing last price entry for ", ticker)
        print(f"Error message is: {e}")
        return -1  # some error occurred accessing last price entry


# get the percent change from an initial price to a closing price
def calc_percent_change(previous, current):
    return (current-previous)/previous *100 


def json_exists(ticker, filename='previous.json'):
    with open(filename, 'r+') as file:
        # First we load existing data into a dict.
        file_data = json.load(file)
    print(f"Current file_data: {file_data}")
    matches=[val for val in file_data['stocks'] if val['ticker'] == ticker]
    print(f"matches array: {matches}")
    return len(matches) > 0

# writes support and resistance values to the previous.json file
def write_json(new_data, filename='previous.json'):
    with open(filename, 'r+') as file:
        # load existing data into a dict
        file_data = json.load(file)
        print("writing json: ", new_data)
        print("file_data['stocks']", file_data["stocks"])
        for i in range(0, len(file_data["stocks"])):
            print("value of i: ", i)
            updated=False
            if file_data["stocks"][i]['ticker'] == new_data['ticker']:
                updated = True
                file_data["stocks"][i]['notified'] = 'True'
                print("after update:", file_data["stocks"])
                break

        if not updated:
            file_data["stocks"].append(new_data)

    # close previous.json and write new updated json
    with open(filename, 'w') as file:
        json.dump(file_data, file, indent=4)


def main():

    print("running Main!")

    os.system('python sleep.py')  # sleep until 9:10 (briefing should be posted!)
    print("Waking up main (get plays now)!")

    today = str(date.today())
    # today = '2023-01-26'  # todo comment out!
    try:
        from Discord import get_briefing

        resistances, supports, retail, alarm_plays = get_briefing(today)  # get briefing

        # create a stock json in previous.json if one does not already exist for the stock (for stocks that have supports)
        for ticker in supports.keys():

            new_json = {
                "ticker": ticker,
                "support": supports[ticker],
                "resistance": resistances[ticker],
                "date": today,
                "notified": "False",
                "resistances": []
            }

            # record all ticker supports/resistances in previous.json
            if not json_exists(ticker, filename='previous.json'):
                print("writing new json to previous: ", new_json)
                write_json(new_json)

        print(
            f"Here are today's plays: \nGreen Checks (Supports):{supports}\nRetail Mention:{retail}\nAlarm Plays:{alarm_plays}")

    except Exception as e:
        print("no briefing posted for today or error writing json to previous.json")
        print(f"Exception is: {e}")

    iteration_count=1

    while True:  # iterate every minute

        # check each unique stock
        for stock in list(set(list(supports.keys())+list(resistances.keys())+retail+alarm_plays)):

            #run checks
            try:
                test_ema(stock,200,'5m', stock in alarm_plays)
                breakout(stock, stock in alarm_plays)
            except:
                print(f"unable to check {stock}")

        #check for breakout past Ziptrader resistances
        with open('previous.json', 'r+') as file:
            # First we load existing data into a dict.
            file_data = json.load(file)
        print(f"Current file_data: {file_data}")
        for cur_json in file_data['stocks']:
            try:
                cur_ticker= cur_json['ticker']
                cur_resistance=cur_json['resistance']
                ticker_yahoo = yf.Ticker(cur_ticker)
                data = ticker_yahoo.history(period='1d', interval='5m',prepost=True)  #necessary for each previous play check
                #check that the current previous stock is breaking past Ziptrader resistance with momentum
                cur_open=data.iloc[-1]['Open']
                cur_close=data.iloc[-1]['Close']
                cur_change = calc_percent_change(cur_open,cur_close)
                try:
                    unusual_volume=detect_volume(cur_ticker)
                except:
                    unusual_volume=False
                if unusual_volume:
                    volume_str="\n Unusual volume!"
                else:
                    volume_str="\n normal volume!"
                if cur_open < cur_resistance and cur_close > cur_resistance and cur_change > 3:
                    message= f"{cur_ticker} is breaking past ziptrade resistance of ${cur_resistance} with a {round(cur_change,2)}% move \n{volume_str}"
                    twilio_text(message)
            except Exception as e:
                print(f"unable to process {cur_json} with an error {e}")



        print(f"sleeping minute {iteration_count}")
        time.sleep(60)  # check stocks every 1 min
        iteration_count += 1


if __name__=="__main__":

    print("running main")
    main()
    # get_ema('akan',200,'5m')
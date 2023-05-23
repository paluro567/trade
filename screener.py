import yfinance as yf
import os
import datetime
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
# from resistance import breakout

# Globals
recent={}
sent_messages=[]
#-------------------FUNCTION DEFs---------------------------------

def day_RSI(stock):
    ticker = yf.Ticker(stock)

    # Get the stock's historical data
    data = ticker.history(period='1d', interval='5m')

    # Calculate the stock's RSI
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    # Get the current RSI
    current_rsi = rsi[-1]

    return current_rsi

# send text alerts if EMA crosses occur from breakout_check
def ma_crosses(stock,play, resistance=0):

    sent=False # has a text been sent

    # cur_RSI = day_RSI(stock)
    cur_RSI = True
    # pct_change, ziptrader,ma_crossed, red_cross = breakout_check(stock, 20, 0)
    # if crossed and pct_change*100>5 and cur_RSI<0.5: # price crosses above 20 MA with >%5 move
    #     message=f"{play} PLAY {stock} crossed above 20 day MA with a {round(pct_change*100,2)}% move"
    #     twilio_text(message)

    # percent change,ziptrader resistance b/o, 10EMA crosses above 20EMA, price crosses 200 EMA, three_bar
    pct_change, ziptrader, ma_crossed, red_cross, three_bar, two_percent = breakout_check(stock, resistance)
    # if crossed and pct_change*100>5 and cur_RSI<0.7: # price crosses above 200 MA with >%5 move
    #     message=f"{play} PLAY {stock} crossed above 200 day MA with a {round(pct_change*100,2)}% move"
    #     twilio_text(message)

    # text ziptrader alert
    if ziptrader and pct_change*100>2:
        message = f"{play} PLAY - {stock} -  is above ziptrader resistance ({resistance}) with a {round(pct_change*100,2)}% move"
        #  check if duplicate message
        if message not in set(sent_messages):
            twilio_text(message)
            sent_messages.append(message)
            sent=True


    # text three bar play
    if three_bar and recent[stock]<=0 and pct_change*100>2:
        message = f"{play} PLAY - {stock} -  three bar play with{round(pct_change*100,2)}% move"
        #  check if duplicate message
        if message not in set(sent_messages):
            twilio_text(message)
            sent_messages.append(message)
            sent=True

    # text MA's crossed play
    if ma_crossed and recent[stock]<=0 and pct_change*100>2:
        message = f"{play} PLAY - {stock} -  EMAs crossed {round(pct_change*100,2)}% move"
        #  check if duplicate message
        if message not in set(sent_messages):
            twilio_text(message)
            sent_messages.append(message)
            sent=True

    #text 200 EMA crossed play
    if red_cross and recent[stock]<=0 and pct_change*100>2:
        message = f"{play} PLAY - {stock} -  200 EMA crossed {round(pct_change*100,2)}% move"
        #  check if duplicate message
        if message not in set(sent_messages):
            twilio_text(message)
            sent_messages.append(message)
            sent=True

    #text ziptrader resistance crossed play
    if ziptrader and recent[stock]<=0 and pct_change*100>2:
        message = f"{play} PLAY - {stock} -  200 EMA crossed {round(pct_change*100,2)}% move"
        #  check if duplicate message
        if message not in set(sent_messages):
            twilio_text(message)
            sent_messages.append(message)
            sent=True

    #text 2 percent above 200EMA (this notification should be less frequent)
    if two_percent and recent[stock]<=-3:
        message = f"{play} PLAY - {stock} -  2% above 200EMA by a {round(pct_change*100,2)}% move"
        #  check if duplicate message
        if message not in set(sent_messages):
            twilio_text(message)
            sent_messages.append(message)
            sent=True

    if sent:
        recent[stock]=5
    else:
        recent[stock]-=1

def test_ema(ticker, ema_period, minutes):
    ticker_yahoo = yf.Ticker(ticker)
    data = ticker_yahoo.history(period='60d', interval=minutes)
    # Calculate the EMA
    data["EMA"] = data["Close"].ewm(span=ema_period).mean()
    data['percent_change'] = ((data["Close"] - data["Close"].shift(1))/data["Close"].shift(1))*100

    cur_price= data["Close"].iloc[-1]
    em=data["EMA"].iloc[-1]
    percent_change = round(data["percent_change"].iloc[-1])

    #todo - add a column to data
    data['above_ema'] = data['Close'] > data['EMA']
    display(data)
    prev_above = data[-2]['above_ema']
    #texting logic
    if not prev_above and percent_change > 5 and data[-1]['above_ema']:
        message = f"{ticker} is breaking above EMA by {percent_change}%"
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


# checks if stock has broken past the n-day MA within the past 1-minute interval
def breakout_check(stock, resistance):


    # Get the stock data for the past n days
    end_time = datetime.datetime.now()
    # start_time = end_time - datetime.timedelta(days=10)

    # get dataframes
    data = yf.download(stock, period="1y", interval="1d")  # moving average DF
    five_min_data= yf.download(stock.replace("🚨",''), period="1d", interval="5m", prepost=True)  # 5 minute interval DF
    
    five_min_data['percent change']=five_min_data['Close'].pct_change()
    open_price=five_min_data.iloc[-1]['Open']
    close_price=five_min_data.iloc[-1]['Close']
    
    print(five_min_data)

    #three bar play prices
    try:
        last_pct_change=five_min_data.iloc[-1]['percent change']*100
        second_last_pct_change=five_min_data.iloc[-2]['percent change']*100
        third_last_pct_change=five_min_data.iloc[-3]['percent change']*100
    except:
        print(f"No stock data for {stock}")
        return (0, False, False, False, False)

    if close_price>resistance and recent[stock]<0:
        msg=f"{stock} is above ziptrader resistance"
        twilio_text(msg)
    


    if five_min_data.empty:
        print(f"no data for {stock}")
        return (0,False,False,False)


    #calculate EMA's
    short_ema = five_min_data['Close'].ewm(span=9, adjust=False).mean()
    medium_ema = five_min_data['Close'].ewm(span=20, adjust=False).mean()
    long_ema = five_min_data['Close'].ewm(span=200, adjust=False).mean()


    # initial EMA values
    short_initial = short_ema.tail(2).iloc[0]
    medium_initial = medium_ema.tail(2).iloc[0]
    long_initial = long_ema.tail(2).iloc[0]
    
    # latest EMA values
    short_final = short_ema.tail(1).iloc[0]
    medium_final = medium_ema.tail(1).iloc[0]
    long_final = long_ema.tail(1).iloc[0]

    



    # Check if the last Close price is greater than the 200-day MA
    return ( 
    last_pct_change,  # percent change
    resistance is not 0 and open_price<resistance and close_price>resistance and ((last_pct_change>5) or (second_last_pct_change+last_pct_change)>5 ),  # ziptrader resistance bo
    (short_initial<medium_initial) and (short_final>medium_final),  # 10EMA crosses above 20EMA
    open_price<long_initial and close_price>long_final,  # price crosses 200 EMA
    third_last_pct_change>=2 and second_last_pct_change<0 and last_pct_change>=1, #three bar play (boolean)
    ((close_price-long_final)/long_final)*100>=3)  # 3 percent above 200EMA


def main():

    print("running Main!")

    os.system('python sleep.py')  # sleep until 9:10 (briefing should be posted!)
    print("Waking up main (get plays now)!")

    #--------------------------------- GET BRIEFING -------------------------------------------
    today = str(date.today())
    try:
        from Discord import get_briefing
        print("today:",today)

        resistances, supports, retail, alarm_plays = get_briefing(today)  # get briefing
        print("resistances: ", resisstances)
        # print(f"resistances: {resistances}, \nalarm_plays: {alarm_plays}")
        # '''
        # Hashmaps:
        #     supports
        #     resisstances
        # lists:
        #     alarm_plays
        #     retail
        # '''

        # # create a stock json in previous.json if one does not already exist for the stock (for stocks that have supports)
        # for ticker in supports.keys():

        #     new_json = {
        #         "ticker": ticker,
        #         "support": supports[ticker],
        #         "resistance": resistances[ticker],
        #         "date": today,
        #         "notified": "False",
        #         "resistances": []
        #     }

        #     # record all ticker supports/resistances in previous.json
        #     if not json_exists(ticker, filename='previous.json'):
        #         print("writing new json to previous: ", new_json)
        #         write_json(new_json)

        print(f"Here are today's plays: \nGreen Checks (Supports):{supports}\nRetail Mention:{retail}\nAlarm Plays:{alarm_plays}")

    except Exception as e:
        print("no briefing posted for today!")
        print(f"Exception is: {e}")

    

#-------------------MINUTE ITERATIONS------------------------------------------------------

    iteration_count=1

    while True:  # iterate every minute - check each unique stock

        #todo refactor how these plays are iterated through
        '''
        HM={}
        HM['ALARM']= alarm_plays
        HM['CRYPTO']= ['MARA', 'RIOT']
        HM['MARKET']= ['UVXY', 'SQQQ']
        '''
        # alarm_plays=['FCNCA','FRC']
        # resistances={'CYCN':0.62,
        #                 'MULN': 0.12,
        #                 'PXMD':2.10,
        #                 'GRRR':9.87
        #             }

        # alarm plays
        for stock in alarm_plays:
            if stock not in recent:
                recent[stock]=0

            ma_crosses(stock,'ALARM')

        # regular plays
        for stock in set(list(supports.keys())+list(resistances.keys())):
            if stock not in recent:
                recent[stock]=0
            ma_crosses(stock,'GREEN')

        #crypto
        for stock in ['MARA', 'RIOT']:
            if stock not in recent:
                recent[stock]=0
            ma_crosses(stock,'CRYPTO')
            
        #market/volatility
        for stock in ['UVXY', 'SQQQ']:
            if stock not in recent:
                recent[stock]=0
            ma_crosses(stock,'MARKET')


        #nightly video suggestions
        video_suggestions=['PXMD']
        
        for stock in video_suggestions:
            if stock not in recent:
                recent[stock]=0
            ma_crosses(stock,'NIGHTLY VIDEO')


        #--------------------------------- PREVIOUS TESTING -----------------------------------------------

        '''

        for stock in list(set(supports.keys()+resistances.keys()+retail+alarm_plays)):

            cur_price = get_current_price(stock)

            #run checks
            test_ema(stock)
            breakout(stock)
        #check for breakout past Ziptrader resistances
        with open('previous.json', 'r+') as file:
            # First we load existing data into a dict.
            file_data = json.load(file)
        print(f"Current file_data: {file_data}")
        for cur_json in file_data['stocks']:
            cur_ticker= cur_json['ticker']
            cur_resistance=cur_json['resistance']
            ticker_yahoo = yf.Ticker(cur_ticker)
            data = ticker_yahoo.history(period='1d', interval='5m')
            #check that the current previous stock is breaking past Ziptrader resistance with momentum
            cur_open=data[-1]['Open']
            cur_close=data[-1]['Close']
            cur_change = calc_percent_change(cur_open,cur_close)
            if cur_open < cur_resistance and cur_close > cur_resistance and cur_change > 3:
                message= f"{cur_ticker} is breaking past ziptrade resistance of ${cur_resistance} with a {cur_change}% move"
                twilio_text(message)
        '''
        #sleep 8pm to 9am
        import time
        current_time=time.localtime()
        if current_time.tm_hour>=20 or current_time.tm_hour<9:
            seconds_until_nine=((9-current_time.tm_hour)*3600)-(current_time.tm_min*60)-current_time.tm_sec
            time.sleep(seconds_until_nine)



        time.sleep(60)  # check stocks every 1 min
        iteration_count += 1


if __name__=="__main__":

    print("STARTING MAIN")

    main()
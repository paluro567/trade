import os
import Discord
from datetime import date
from screener import *
from alpaca import *
from RSI import *

import time
from pydub import AudioSegment
from pydub.playback import play

order_sound = AudioSegment.from_wav('/Users/pluro/Desktop/trade/order.wav')  # notification sound

# sleep until market open (9:30AM)
os.system('python sleep.py')
today = str(date.today())

# num days for each moving average
long_days = 20
short_days = 9

# get Ziptrader plays
resistances, supports, retail, alarm_plays = Discord.get_briefing(today)
stocks = set(list(resistances.keys()) + retail + alarm_plays)

# Initialize hashmaps
recent_prices = {}  # recent prices of each stock
prev_above_ma = {}  # short_ma > long_ma
prev_above_short = {}  # current_price > short_ma
prev_above_long = {}  # current_price > long_ma
prev_rsi = {}
for stock in stocks:
    prev_rsi[stock] = True
    recent_prices[stock] = []  # 5 most recent prices of each stock
    # Initialize prev above MA values
    prev_above_ma[stock] = True
    prev_above_short[stock] = True
    prev_above_long[stock] = True
holdings = {}  # Keep track of shares bought

run_one = True

while True:

    # check all stocks
    for stock in stocks:

        current_price = get_current_price(stock)
        recent_prices[stock].append(current_price)
        if len(recent_prices[stock]) > 5:  # keep only the 5 most recent prices
            recent_prices[stock].pop(0)

        try:
            rsi = current_rsi(stock)
        except Exception as e:
            print(f"unable to get an RSI for {stock}")
            print("Error is : ", e)

        # Current moving average values
        try:
            long_ma = day_ma(stock, long_days)
            short_ma = day_ma(stock, short_days)
        except Exception as e:
            print(f"paper-trade - the stock {stock} is unable to get the day_ma with an ERROR: {e}")
            continue  # skip this stock => maybe an error when parsing the ticker?

        # Max percent movement over the past 5 minute interval (in each direction)
        upward_change = calc_percent_change(min(recent_prices[stock]), current_price)*100
        down_change = calc_percent_change(max(recent_prices[stock]), current_price)*100

        ''' Buy order conditions (MA's not previously above):
            - Short MA crosses above the long MA 
            - Current price crosses above the long MA with at least 3% strength
            - Current price crosses above the short MA with at least 3% strength
        - RSI crosses above 30
        '''
        # ------------------------------- BUY ORDER?? ---------------------------------------------
        if (short_ma > long_ma and not prev_above_ma[stock]) \
            or (upward_change > 3 and (current_price > long_ma and not prev_above_long[stock])) \
            or (upward_change > 3 and (current_price > short_ma and not prev_above_short[stock])) \
            or (rsi > 30 and not prev_rsi[stock]) \
                and not run_one:  # place buy order!

            buy_dollars = 1000  # dollar limit to buy of stock

            # how much to buy
            if short_ma > long_ma and not prev_above_ma[stock]:
                buy_dollars += 2000
            elif upward_change > 3 and (current_price > long_ma and not prev_above_long[stock]):
                buy_dollars += 1000
            elif rsi > 30 and not prev_rsi[stock]:  # RSI strength
                buy_dollars += 1000
            elif upward_change > 3 and (current_price > short_ma and not prev_above_short[stock]):
                buy_dollars += 500

            num_shares = 1
            while num_shares * current_price <= buy_dollars:  # buy at most $buy_dollars of the stock
                num_shares += 1
            # buy num_shares of the current stock!
            try:
                response = create_order(stock, num_shares, 'buy', 'market', 'gtc')
                print("placed buy order: ", response)
                twilio_text(f"placed a buy order to buy  {num_shares} of {stock}!")
                # add stock to holdings
                if stock in holdings.keys():
                    holdings[stock] = (holdings[stock][0]+num_shares, holdings[stock][1])  # add additional purchase to the current position
                else:
                    holdings[stock] = (num_shares, current_price)  # created a new position at the current_price

                # notification sounds
                play(order_sound)
                phrase = f' say buying {num_shares} of {stock} at{current_price} dollars per share'
                os.system(f"say {phrase}")

            except Exception as e:
                print("unable to place buy order!")
                print(f"Exception is: {e}")

        # ------------------------------- SELL ORDER?? ---------------------------------------------
        ''' Sell conditions:
            - short MA crosses below the long MA
            - stock crosses below the short MA with a <-3% downward move
            - stock crosses below the long MA with a <-3% downward move
            - below_five - current price is below the 5MA
        '''
        if stock in list(holdings.keys()):
            below_five = current_price<day_ma(stock, 5)
        else:
            below_five=False
        sell_conditions = down_change < -3 and (((short_ma < long_ma and prev_above_ma[stock])) \
                or (current_price < short_ma and prev_above_short[stock]) \
                or (current_price < long_ma and prev_above_long[stock]) \
                or below_five)

        if stock in list(holdings.keys()) and sell_conditions and not run_one:  # 9MA crossed below the 20MA
            # sell current position of the stock from holdings!
            try:
                response = create_order(stock, holdings[stock][0], 'sell', 'market', 'gtc')
                print("placed SELL order: ", response)
                play(order_sound)
                phrase = f' say selling {holdings[stock][0]} of {stock} at{current_price} dollars per share'
                os.system(f"say {phrase}")
                holdings.pop(stock)
            except Exception as e:
                print("unable to place SELL order!")
                print(f"Exception is: {e}")

        # update previous values for next minute
        prev_rsi[stock] = rsi > 30
        prev_above_ma[stock] = short_ma > long_ma
        prev_above_short[stock] = current_price > short_ma
        prev_above_long[stock] = current_price > long_ma
        run_one = False  # all hashmaps have been populated

    print(f"----------- {stock} values-----------------")
    print(f"---prev_above_ma[{stock}]: {prev_above_ma[stock]}")
    print(f"---prev_above_short[{stock}]: {prev_above_short[stock]}")
    print(f"---prev_above_long[{stock}]: {prev_above_long[stock]}")

    print(f"Sleeping 1 Minute - current state:\n\n holdings:{holdings}\nprev_above_ma: {prev_above_ma}")
    time.sleep(60)  # check stocks every 1 minute




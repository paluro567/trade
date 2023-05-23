import yfinance as yf
from IPython.display import display
import pandas as pd
import matplotlib.pyplot as plt



def calc_percent_change(previous, current):
    return (current-previous)/previous


def index_price(ticker, minute_idx):
    ticker_yahoo = yf.Ticker(ticker)
    data = ticker_yahoo.history(period='1d', interval='1m')
    # display(data['Close'])
    return data['Close'].iloc[minute_idx]  # closing price of the minute index


'''
Modification from day_ma in screener and paper-trade.
Removes the latest price in the average and averages 
the minute/index price to the rolling period
'''


def day_ma(stock, num_days, i):
    try:
        # get prices
        latest_price = index_price(stock, -1)  # remove the latest price (5pm) from the MA
        minute_price = index_price(stock, i)  # add minute price to MA
        print("latest_price is ", latest_price)
        print(f"minute price is ({i}): ", minute_price)

        stock_obj = yf.Ticker(stock)
        tickerdata = stock_obj.history(period='1y', interval="1d")  # daily stock history over past 2 years
        print("full dataframe")
        display(tickerdata)
        print("accessed stock data")
        tickerdata["day-MA"] = tickerdata["Close"].rolling(window=str(num_days)+'d').mean()
        stockdata = tickerdata[['Close', 'day-MA']]  # remove all other columns in stockdata other than close and day-ma
        # print("stockdata['day-MA']: ", tickerdata["day-MA"])
        latest_ma = tickerdata["day-MA"].iloc[-1]  # access latest day-MA in stockdata
        print(f" latest_ma: {latest_ma}")
        print("display data 1")
        display(stockdata)
        print("latest_ma: ", latest_ma)
        # Adjust latest MA calculation to use the minute price
        adjusted_average = ((latest_ma*num_days) - latest_price + minute_price) / num_days  # adjust the latest MA to include the minute_price
        print(f"calculated new MA: {adjusted_average}")

    except Exception as e:
        print(" could not recalculate the day minute index day MA")
        moving_average = adjusted_average = tickerdata["day-MA"].iloc[-1]  # if not correct moving average, use latest minute ma
        print("Using the latest day MA index (-1)")
        print(f"Exception is: {e}")

    return adjusted_average

# ---------------------------run test------------------------




def simulate(stock_str):
    time_minute = 30
    time_hour = 9


    current_money = 100000  # starting value: $100,000
    holdings = 0  # number shares of the stock owned

    # Moving Average days
    short_days = 5
    long_days = 20
    state = pd.DataFrame(columns=('stock', 'time', 'Price',f'price>{str(short_days)}' + 'MA',
                                  str(short_days) + 'MA', str(long_days) + 'MA',
                                  str(short_days)+'MA' + '>' + str(long_days) + 'MA'))

    # Get ticker data
    ticker_yahoo = yf.Ticker(stock_str)
    data = ticker_yahoo.history(period='1d', interval='1m')  # one day of Minute data
    display(data)

    #moving average booleans and 5 monst recent prices
    recent_prices = []
    prev_above_ma = True
    prev_above_long = True
    prev_above_short = True

    run_one = True

    for i in range(len(data['Close'])):  # iterate over each minute of stockdata history for testing
        new_price = data['Close'].iloc[i]
        recent_prices.append(int(new_price))
        if len(recent_prices) > 5:  # keep only the 5 most recent prices
            recent_prices.pop(0)

        print("get MA vals")
        # Current minute moving average values
        try:
            long_ma = day_ma(stock_str, long_days, i)
            short_ma = day_ma(stock_str, short_days, i)

            # create a time string for the state DF
            time_minute += 1
            if time_minute == 60:
                time_hour = (time_hour+1) % 12
                time_minute = 0
            if time_hour == 0:
                time_hour = 12
            if time_hour < 10:
                hour_str = "0" + str(time_hour)
            else:
                hour_str=str(time_hour)
            if time_minute < 10:
                minute_str = '0' + str(time_minute)
            else:
                minute_str=str(time_minute)

            time_str=hour_str + ':' + minute_str


            state.loc[i]=[ stock_str, time_str, new_price,new_price>short_ma, short_ma, long_ma, short_ma>long_ma]
            print("MA state:")
            print(state)

        except Exception as e:
            print(f"paper-trade - the stock {stock_str} is unable to get the day_ma with an ERROR: {e}")
            continue  # skip this stock => maybe an error when parsing the ticker?

        # Max percent movement over the past 5 minute interval (in each direction)
        upward_change = calc_percent_change(min(recent_prices), int(new_price)) * 100
        down_change = calc_percent_change(max(recent_prices), int(new_price)) * 100

        ''' Buy order conditions (MA's not previously above => crosses above):
            - Short MA crosses above the long MA 
            - Current price crosses above the long MA with at least 3% strength
            - Current price crosses above the short MA with at least 3% strength
        - RSI crosses above 30 (TODO)
        '''
        # ------------------------------- BUY ORDER?? ---------------------------------------------
        if (short_ma > long_ma and not prev_above_ma) \
                or (upward_change > 3 and (new_price > long_ma and not prev_above_long)) \
                or (upward_change > 3 and (new_price > short_ma and not prev_above_short)) \
                and not run_one:  # place buy order!

            buy_dollars = 1000  # dollar limit to buy of stock

            # how much to buy
            if short_ma > long_ma and not prev_above_ma[stock_str]:
                buy_dollars += 2000
            elif upward_change > 3 and (new_price > long_ma and not prev_above_long):
                buy_dollars += 1000
            elif upward_change > 3 and (new_price > short_ma and not prev_above_short):
                buy_dollars += 500

            num_shares = 1
            while num_shares * new_price <= buy_dollars:  # buy at most $buy_dollars of the stock
                num_shares += 1
            # buy num_shares of the current stock!
            try:

                if buy_dollars<current_money:
                    current_money-=num_shares*new_price
                    holdings += num_shares
                    print(f"X-X-X-X-X-X-X-X-X-X-X-X-X---- placing BUY order of {num_shares} at a price of {new_price}")
                else:
                    print("must sell shares first!")

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
        below_five=False
        if holdings > 0:
            five_ma = day_ma(stock_str, 5, i)
            below_five = new_price < five_ma
        sell_conditions = down_change < -3 and ((short_ma < long_ma and prev_above_ma) \
                                                or (new_price < short_ma and prev_above_short) \
                                                or (new_price < long_ma and prev_above_long) \
                                                or below_five)

        if holdings > 0 and sell_conditions and not run_one:  # 9MA crossed below the 20MA
            # sell current position of the stock from holdings!
            try:
                if short_ma < long_ma and prev_above_ma:
                    sell_shares = holdings  # sell all shares
                else:
                    sell_shares = holdings//2  # sell half of holdings

                holdings -= sell_shares
                current_money += (sell_shares*new_price)
                print(f"-X-X-X-X-X-X-X-X-X-X-X-X---SELLING {sell_shares} at {new_price}\nCurrent money is {current_money}\nHoldings is {holdings}")
            except Exception as e:
                print("unable to place SELL order!")
                print(f"Exception is: {e}")

        # update previous values for next minute
        prev_above_ma = short_ma > long_ma
        prev_above_short = new_price > short_ma
        prev_above_long = new_price > long_ma
        run_one = False  # all hashmaps have been populated

    print(f"----------- {stock_str} values-----------------")
    print(f"---prev_above_ma[{stock_str}]: {prev_above_ma}")
    print(f"---prev_above_short[{stock_str}]: {prev_above_short}")
    print(f"---prev_above_long[{stock_str}]: {prev_above_long}")

if __name__ =='__main__':
    simulate('APE')
    # day_ma('APE', 5, 0)
    # print("fifth minute 20-day MA is: ", day_ma('pltr', 20, 5))


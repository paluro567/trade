import alpaca_trade_api as tradeapi
import time
from datetime import datetime
from sms import text
from record_day_trade import pdt_rule, record_trade


# Alpaca API credentials
BASE_URL = "https://api.alpaca.markets"
API_KEY = "AK0N7FM1XU3EIZZAN6UR"
API_SECRET = "rMPuDwYNDXLmQGXjhOe3BOluqdkwkMn2o1xPM01u"

# Initialize the Alpaca API
api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

def get_current_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# buy order
def place_buy_order(ticker,qty):
    buy_order = api.submit_order(
        symbol=ticker,
        qty=qty,
        side='buy',
        type='market',
        time_in_force='gtc'  # Good till canceled
    )
    print(f"{get_current_timestamp()} - {ticker} -  buy order placed: {buy_order}")
    return buy_order

# stop loss order
def place_stop_loss_order(ticker, qty, cur_open):
    sell_order = api.submit_order(
        symbol=ticker,
        qty=qty,
        side='sell',
        type='stop',
        time_in_force='gtc',
        stop_price=cur_open
    )  
    print(f"{get_current_timestamp()} - {ticker} -  stop loss order placed: {sell_order}")
    return sell_order

def try_orders(ticker, qty, cur_open):
    try:

        # Place market buy order
        buy_order = place_buy_order(ticker,qty)
        
        # Wait for the buy order to be filled
        order_filled = False
        while not order_filled:
            order = api.get_order(buy_order.id)
            if order.status == 'filled':
                buy_fill_time = datetime.now().date() # day date
                order_filled = True
            else:
                time.sleep(1)  # Wait for 1 second before checking again
        text(f"{get_current_timestamp()} - filled buy: {qty} shares of {ticker}")

        '''
        # Place trailing stop sell order
        sell_order = api.submit_order(
            symbol=ticker,
            qty=qty,
            side='sell',
            type='trailing_stop',
            trail_percent=10.0,  # 10% trailing stop
            time_in_force='gtc'  # Good till canceled
        )
        print(f"{get_current_timestamp()} - {ticker} - Trailing stop sell order placed: {sell_order}")
        '''

        # place stop loss order
        sell_order=place_stop_loss_order(ticker, qty, cur_open)

        # Wait for the sell_order to be filled
        order_filled = False
        while not order_filled:
            order = api.get_order(sell_order.id)
            if order.status == 'filled':
                sell_fill_time = datetime.now().date() # day date
                order_filled = True
            else:
                time.sleep(1)  # Wait for 1 second before checking again
        if buy_fill_time==sell_fill_time:
            record_trade(ticker)
    except Exception as e:
        print(f"{get_current_timestamp()} - Unable to place orders for {ticker}: {e}")

if __name__=='__main__':
    t1=datetime.now().date()
    time.sleep(5)
    t2=datetime.now().date()
    print(t1)
    print(t2)
    print(t1==t2)


import alpaca_trade_api as tradeAPI
import time
from datetime import datetime
from sms import text
from record_day_trade import pdt_rule, record_trade


# Alpaca API credentials
BASE_URL = "https://api.alpaca.markets"
API_KEY = "AK0N7FM1XU3EIZZAN6UR"
API_SECRET = "rMPuDwYNDXLmQGXjhOe3BOluqdkwkMn2o1xPM01u"

# Initialize the Alpaca API
API = tradeAPI.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

def get_current_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# buy order
def place_buy_order(ticker,qty):
    buy_order = API.submit_order(
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
    try:
        stop_loss_order = API.submit_order(
            symbol=ticker,
            qty=qty,
            side='sell',
            type='stop',
            time_in_force='gtc',
            stop_price=cur_open
        )  
        print(f"{get_current_timestamp()} - {ticker} -  stop loss order placed: {stop_loss_order}")
        return stop_loss_order
    except Exception as e:
        print(f"unable to place place_stop_loss_order=> {e}")
        return 1

def place_trailing_stop_order(ticker, qty, trailing_pct):
    # Place trailing stop sell order
    try:
        trailing_stop_order = API.submit_order(
            symbol=ticker,
            qty=qty,
            side='sell',
            type='trailing_stop',
            trail_percent=trailing_pct,  # 10% trailing stop
            time_in_force='gtc'  # Good till canceled
        )
        print(f"{get_current_timestamp()} - {ticker} - Trailing stop sell order placed: {trailing_stop_order}")
        return trailing_stop_order
    except Exception as e:
        print(f"unable to place trailing_stop_order=> {e}")
        return 1


# place buy and sell orders consecutively
def try_orders(ticker, qty, cur_open):
    trailing_pct=10.0
    try:

        # Place market buy order
        buy_order = place_buy_order(ticker,qty)
        
        # Wait for the buy order to be filled
        buy_order_filled = False
        while not buy_order_filled:
            buy_order_obj = API.get_order(buy_order.id)
            if buy_order_obj.status == 'filled':
                buy_fill_time = datetime.now().date() # day date
                buy_order_filled = True
            else:
                time.sleep(1)  # Wait for 1 second before checking again
        text(f"{get_current_timestamp()} - filled buy: {qty} shares of {ticker}")

        # place sell orders
        # trailing_order=place_trailing_stop_order(ticker, qty,  trailing_pct)
        stop_order=place_stop_loss_order(ticker, qty, cur_open)

        # Wait for the sell_order to be filled
        order_filled = False
        while not order_filled:
            # order objects
            # trailing_order_obj = API.get_order(trailing_order.id)
            stop_order_obj = API.get_order(stop_order.id)
            # if trailing_order_obj.status == 'filled' or stop_order_obj.status == 'filled':
            if stop_order_obj.status == 'filled':
                sell_fill_time = datetime.now().date() # day date
                order_filled = True
            else:
                time.sleep(1)  # Wait for 1 second before checking again

        text(f"{get_current_timestamp()} - filled Sell: {qty} shares of {ticker}")

        if buy_fill_time==sell_fill_time:
            record_trade(ticker)
    except Exception as e:
        print(f"{get_current_timestamp()} - Unable to place orders for {ticker}: {e}")

if __name__=='__main__':
    place_buy_order('PLTR', 5)


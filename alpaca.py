import alpaca_trade_api as tradeapi
import time
from datetime import datetime

# Alpaca API credentials
BASE_URL = "https://api.alpaca.markets"
API_KEY = "AK0N7FM1XU3EIZZAN6UR"
API_SECRET = "rMPuDwYNDXLmQGXjhOe3BOluqdkwkMn2o1xPM01u"

# Initialize the Alpaca API
api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

# TODO => pip install alpaca-trade-api

def get_current_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def try_buy(ticker, qty, cur_open):
    try:
        # Place market buy order
        buy_order = api.submit_order(
            symbol=ticker,
            qty=qty,
            side='buy',
            type='market',
            time_in_force='gtc'  # Good till canceled
        )
        print(f"{get_current_timestamp()} - {ticker} - Buy order placed: {buy_order}")

        # Wait for the buy order to be filled
        order_filled = False
        while not order_filled:
            order = api.get_order(buy_order.id)
            if order.status == 'filled':
                order_filled = True
            else:
                time.sleep(1)  # Wait for 1 second before checking again

        print(f"{get_current_timestamp()} - Buy order filled.")

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
        sell_order = api.submit_order(
            symbol=ticker,
            qty=qty,
            side='sell',
            type='stop',
            time_in_force='gtc',  
            stop_price=cur_open
        )  
        print(f"{get_current_timestamp()} - {ticker} -  stop loss order placed: {sell_order}")
        '''

    except Exception as e:
        print(f"{get_current_timestamp()} - Unable to place orders for {ticker}: {e}")

if __name__=='__main__':
    try:
        print('testing try_buy in alpaca.py ')
        try_buy('PLTR', 5)
    except Exception as e:
        print(f"Exception in main: {e}")


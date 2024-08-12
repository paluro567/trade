import alpaca_trade_api as tradeAPI
import time
from datetime import datetime
from sms import text
from record_day_trade import pdt_rule, record_trade


# Alpaca API credentials
BASE_URL = "https://api.alpaca.markets"
API_SECRET = "WPQhnKIKbs2XIBlwiYze9IoSDmIceMetVdzijvqY"
API_KEY = 'AKNP95FFF31SO61LUUFA'

# Initialize the Alpaca API
API = tradeAPI.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

def get_current_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Buy order
def place_buy_order(ticker, qty):
    buy_order = API.submit_order(
        symbol=ticker,
        qty=qty,
        side='buy',
        type='market',
        time_in_force='gtc'  # Good till canceled
    )
    print(f"{get_current_timestamp()} - {ticker} - Buy order placed: {buy_order}")
    return buy_order

# Stop loss order
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
        print(f"{get_current_timestamp()} - {ticker} - Stop loss order placed: {stop_loss_order}")
        return stop_loss_order
    except Exception as e:
        print(f"Unable to place stop loss order => {e}")
        return None

# Trailing stop order
def place_trailing_stop_order(ticker, qty, trailing_pct):
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
        print(f"Unable to place trailing stop order => {e}")
        return None

# Place buy and sell orders consecutively
def try_orders(ticker, qty, cur_open, bars):
    trailing_pct = 10.0
    try:
        # Place market buy order
        buy_order = place_buy_order(ticker, qty)
        
        # Wait for the buy order to be filled
        buy_order_filled = False
        buy_filled_price = 0
        sell_filled_price = 0
        while not buy_order_filled:
            
            buy_order_obj = API.get_order(buy_order.id)
            if buy_order_obj.status == 'filled':
                try:
                    buy_filled_price = float(buy_order_obj.filled_avg_price)
                except Exception as e:
                    print(f"unable to get buy_order_obj filled price with: {e}")
                buy_fill_time = datetime.now().date()  # Day date
                buy_order_filled = True
            else:
                time.sleep(1)  # Wait for 1 second before checking again
        text(f"{get_current_timestamp()} - Filled buy: {qty} shares of {ticker}\n\n{bars}")

        # Place sell orders
        trailing_order = place_trailing_stop_order(ticker, qty, trailing_pct)
        stop_order = place_stop_loss_order(ticker, qty, cur_open)

        # Wait for the sell order to be filled
        order_filled = False
        while not order_filled:
            trailing_order_obj = trailing_order and API.get_order(trailing_order.id)
            stop_order_obj = stop_order and API.get_order(stop_order.id)
            if (trailing_order_obj and trailing_order_obj.status == 'filled') or (stop_order_obj and stop_order_obj.status == 'filled'):
                try:
                    if trailing_order_obj.status == 'filled':
                        sell_filled_price = float(trailing_order_obj.filled_avg_price)
                    else:
                        sell_filled_price = float(stop_order_obj.filled_avg_price)
                except Exception as e:
                    print(f"unable to get stop_order_obj filled price with: {e}")
                sell_fill_time = datetime.now().date()  # Day date
                order_filled = True
            else:
                time.sleep(1)  # Wait for 1 second before checking again

        text(f"{get_current_timestamp()} - Filled sell: {qty} shares of {ticker} \nprofit is ${qty*(sell_filled_price-buy_filled_price)}")

        if buy_fill_time == sell_fill_time:
            record_trade(ticker)
    except Exception as e:
        print(f"{get_current_timestamp()} - Unable to place orders for {ticker}: {e}")

if __name__ == '__main__':
    order_obj = place_trailing_stop_order('AMZN', 5, 5)
    order_obj = API.get_order(order_obj.id)
    print("order_obj: ", order_obj)
    print("Order status: ", order_obj.status)

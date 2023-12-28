# Your Alpaca API credentials
API_KEY = 'PKZCWSK3UAQMJFD6DCR2'
SECRET_KEY = '7DcKGHD71HhR1Z7Sc1LRX2EqoAA7cPxjciEH7SX4'
BASE_URL = 'https://paper-api.alpaca.markets'  # Use 'https://api.alpaca.markets' for live trading

import alpaca_trade_api as tradeapi

# Initialize the Alpaca API
api = tradeapi.REST(API_KEY, SECRET_KEY, base_url=BASE_URL, api_version='v2')

# Place a buy order
symbol = 'AAPL'  # Replace 'AAPL' with the symbol you want to trade
qty = 10  # Number of shares/quantity you want to buy
order_type = 'limit'  # Order type: 'limit', 'market', 'stop', etc.
limit_price = 150.0  # Specify the limit price if order_type is 'limit' (optional)
def place_buy(symbol, buy_qty):
    # symbol=str(symbol)
    symbol=symbol.upper()
    buy_order = api.submit_order(
        symbol=symbol,
        qty=buy_qty,
        side='buy',
        type=order_type,
        time_in_force='gtc',  # Time in force: 'gtc' (good till cancel), 'day', etc.
        limit_price=limit_price if order_type == 'limit' else None
    )
    print("Placed a Buy Order ID:", buy_order.id)

def place_sell(symbol, buy_qty):
    # symbol=str(symbol)
    symbol=symbol.upper()

    # Place a sell order
    sell_order = api.submit_order(
        symbol=symbol,
        qty=buy_qty,
        side='sell',
        type=order_type,
        time_in_force='gtc',  # Time in force: 'gtc' (good till cancel), 'day', etc.
        limit_price=limit_price if order_type == 'limit' else None
    )

    # Check order status
    print("Placed a Sell Order ID:", sell_order.id)

# test orders
if __name__=='__main__':
    place_buy("CING", 1000)
    # place_sell("pltr", 5)



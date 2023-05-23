import requests
import json
# from alpaca.trading.client import TradingClient

'''
# Importing the API and instantiating the REST client according to our keys
from alpaca.trading.client import TradingClient

API_KEY = "<Your API Key>"
SECRET_KEY = "<Your Secret Key>"

trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)

# Getting account information and printing it
account = trading_client.get_account()
for property_name, value in account:
  print(f"\"{property_name}\": {value}")
  '''


# from alpaca.trading.client import TradingClient
from alpaca_config import *
import json, requests





BASE_URL= "https://paper-api.alpaca.markets"
ACCOUNT_URL="{}/v2/account".format(BASE_URL)
ORDERS_URL="{}/v2/orders".format(BASE_URL)
HEADERS={"APCA-API-KEY-ID": API_KEY, "APCA-API-SECRET-KEY": SECRET_KEY}



#----------youtube implementation https://www.youtube.com/watch?v=GsGeLHTOGAg&t=828s -------------------------
def get_account():
    r=requests.get(ACCOUNT_URL, headers=HEADERS)
    return json.loads(r.content)

    # return trading_client.get_account()


def create_order(symbol, qty, side, order_type, time_in_force):
    data={
        'symbol': symbol,
        'qty': qty,
        'side': side,
        'type': order_type,
        'time_in_force': time_in_force
    }

    r = requests.post(ORDERS_URL, json=data, headers=HEADERS)
    json_object = json.loads(r.content)
    pretty_json = json.dumps(json_object, indent=2)

    return pretty_json


def get_orders():
    r = requests.get(ORDERS_URL, headers=HEADERS)
    json_object = json.loads(r.content)
    pretty_json = json.dumps(json_object, indent=2)
    print(pretty_json)

    return json.loads(r.content)


# following Alpaca Docs
'''
from alpaca.trading.client import TradingClient

trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
'''


# ----------------------TESTS---------------------------
# print(create_order())
# response=create_order('PLTR', 100, 'buy', 'market', 'gtc')
# print("sell order: ", response)
print(get_account())

# print(response)
# print(get_orders())

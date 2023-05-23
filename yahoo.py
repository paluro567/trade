'''import yfinance as yf
from yahoofinancials import YahooFinancials
import json



ticker_yahoo=yf.Ticker('pltr')

stock_info=ticker_yahoo.info

for key,val in stock_info.items():
    if "volume" in key or "Volume" in key:
        print(f"{key}:{val}")

data=ticker_yahoo.history(interval='1m', period='1d')
# print("data: ", data)
# print("slose", data['Close'].iloc[-1])
'''

import yfinance as yf

apple= yf.Ticker("aapl")
print("apple actions:", apple.actions)









import yfinance as yf
import pandas_datareader as web
import locale
locale.setlocale(locale.LC_ALL, '')  # Use '' for auto, or force e.g. to 'en_US.UTF-8'


import Discord
import os
import json

cap = web.get_quote_yahoo('pltr')['marketCap']
print(f'{cap:d}')

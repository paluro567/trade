import yfinance as yf
import os
import datetime
from datetime import date
from twilio.rest import Client
from IPython.display import display
# import pandas_datareader as web
# from RSI import *
from secret import *
# from resistance import *
import time
import json
from Discord import *
import pandas as pd
import numpy as np
import sys
import Discord

stock = yf.Ticker('PLTR')
stockdata = stock.history(period='1d', interval="5m", prepost=True)
print(stockdata)
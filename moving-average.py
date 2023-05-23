import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display

stock=yf.Ticker("PLTR")
stockdata=stock.history(period='180d', interval="1d")
display(stockdata)

print(type(stockdata))
stockdata.drop(["Volume", "Dividends", "Stock Splits"], inplace=True, axis=1)
stockdata["9-MA"] =stockdata[["Close"]].rolling(9).mean()
display(stockdata)
latest_index = str(stockdata.tail(1).index[0])
moving_average = stockdata._get_value(latest_index, "9-MA")
print("the latest value:", moving_average)
stockdata["180MA"]=stockdata[["Close"]].rolling(100).mean()
stockdata["200MA"]=stockdata[["Close"]].rolling(200).mean()
# display(stockdata)
# print("should be: ", stockdata.loc["2022-12-15 10:05-05:00", "180MA"])

stockdata.dropna(inplace=True)
plt.figure(figsize=(20, 10))

plt.plot(stockdata["Close"], label="Close")
plt.legend(loc='upper center', fontsize="x-large")


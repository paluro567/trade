import yfinance as yf
from IPython.display import display

yahoo_stock = yf.Ticker('pltr')
stockdata = yahoo_stock.history(period='1mo', interval='30m')  # 1 minute interval stock history
display(stockdata)
print("20-day val: ", stockdata[["Close"]].rolling('20d').mean())
print("9-day val: ", stockdata[["Close"]].rolling('9d').mean())





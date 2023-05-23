import pandas as pd
import yfinance as yf
import ta
from IPython.display import display
import matplotlib.pyplot as plt

'''
import pandas_ta as pta

symbol='pltr'
stock = yf.Ticker(symbol)
stockdata = stock.history(period='1y', interval="1d")
rsi_data=pta.rsi(stockdata['Close'], length=14)
print(f"rsi_data: {rsi_data}")
'''


def get_rsi(symbol):
    stock = yf.Ticker(symbol)
    stockdata = stock.history(period='50d', interval="1d")

    stockdata['change'] = change = stockdata['Close'].diff()  # difference from today's price vs yesterday's price
    stockdata['up'] = up = change.clip(lower=0)  # removes negative changes
    stockdata['down'] = down = -1 * change.clip(upper=0)  # removes positive changes

    ema_up = up.ewm(com=13, adjust=False).mean()
    ema_down = down.ewm(com=13, adjust=False).mean()

    rs = ema_up/ema_down
    stockdata['RSI'] = 100-(100/(1+rs))

    stockdata.dropna(inplace=True)

    return stockdata


def current_rsi(stock):
    rsi_df = get_rsi(stock)
    return rsi_df['RSI'].iloc[-1]


def plot_rsi(stock):

    rsi=get_rsi(stock)
    rsi.dropna(inplace=True)

    plt.style.use('fivethirtyeight')
    plt.rcParams['figure.figsize'] = (20, 10)

    ax1=plt.subplot2grid((10, 1), (0, 0), rowspan=4, colspan=1)
    ax2=plt.subplot2grid((10, 1), (5, 0), rowspan=4, colspan=1)

    stock = yf.Ticker(stock)
    stockdata = stock.history(period='50d', interval="1d")

    ax1.plot(stockdata['Close'], linewidth=2)
    ax1.set_title('stock close price')
    ax2.plot(rsi, linewidth=1, color='orange')
    ax1.set_title('RSI')

    ax2.axhline(30, linestyle='--', linewidth=1.5, color='green')
    ax2.axhline(70, linestyle='--', linewidth=1.5, color='red')

    ax1.set_title(f'Relative Strength Index ({stock})')

    plt.show()


if __name__ == '__main__':
    print("current RSI: ", current_rsi('pltr'))
    plot_rsi('pltr')


'''
display(rsi)
plt.plot(rsi)
plt.show()

display(rsi)
'''

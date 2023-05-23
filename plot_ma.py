import matplotlib.pyplot as plt
import yfinance as yf
from IPython.display import display


def rolling_dataframe(stock, num_days):
    try:
        stock = yf.Ticker(stock)
        stockdata = stock.history(period='2y', interval="1d")

        # Window must be an int!
        stockdata["day-MA"] = stockdata["Close"].rolling(window=num_days).mean()
        return stockdata["day-MA"]
    except Exception as e:
        print(f'unable to create rolling MA on the {stock}')


def plot(stock,  num_days, df):
    try:
        stock_obj = yf.Ticker(stock)
        tickerdata = stock_obj.history(period='1y', interval="1d")  # daily stock history over past 1 years

        display(tickerdata)
        print("accessed stock data")
        '''
        tickerdata["day-MA"] = tickerdata["Close"].rolling(window=str(num_days) + 'd').mean()
        day_ma=tickerdata["day-MA"]
        '''
        data = rolling_dataframe(stock,num_days)
    except Exception as e:
        print(f"unable to load {stock} history with an error: {e}")

    try:
        plt.rcParams['figure.figsize'] = (20, 10)
        plt.style.use('fivethirtyeight')
        plt.plot(data, label=f"{stock} {num_days}-MA", linewidth=1.5)
        plt.plot(tickerdata["Close"], label=f"{stock} Close price", linewidth=1.5)
        plt.title(f'{stock} Close Price History')
        plt.xlabel(f'1 year {num_days} rolling window')
        plt.ylabel('Close price USD ($)')
        plt.legend(loc='upper left')
        plt.show()
    except  Exception as e:
        print(f" Unable to plot the {stock} history data with a {num_days}-MA")



    '''
    ax1 = plt.subplot2grid((10, 1), (0, 0), rowspan=4, colspan=1)
    ax2 = plt.subplot2grid((10, 1), (5, 0), rowspan=4, colspan=1)

    stock = yf.Ticker(stock)
    stockdata = stock.history(period='50d', interval="1d")
    plt.plot(day_ma,stockdata['Close'])
    ax1.plot(stockdata['Close'], linewidth=2)
    ax1.set_title('stock close price')
    ax2.plot(day_ma, linewidth=1, color='orange')
    ax1.set_title('RSI')

    ax2.axhline(stockdata['Close'], linestyle='--', linewidth=1.5, color='green')
    ax2.axhline(day_ma, linestyle='--', linewidth=1.5, color='red')

    ax1.set_title(f'Relative Strength Index ({stock})')

    plt.show()
    '''


if __name__=='__main__':
    plot('pltr', 200)
import yfinance as yf
import os

def detect_volume(ticker):
    ticker_yahoo = yf.Ticker(ticker)
    data = ticker_yahoo.history(period='60d', interval='5m')
    print(data)

    # Calculate the rolling mean and standard deviation of the volume
    rolling_mean = data["Volume"].rolling(window=30).mean()
    rolling_std = data["Volume"].rolling(window=30).std()

    # Get the current day's volume
    current_volume = data.iloc[-2]["Volume"]

    # Calculate the z-score of the current day's volume
    z_score = (current_volume - rolling_mean.iloc[-2]) / rolling_std.iloc[-2]

    # If the z-score is greater than 2, the current day's volume is considered abnormally high
    return z_score > 2:

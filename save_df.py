import yfinance as yf
import pandas as pd
from datetime import datetime

def get_intraday_data(ticker):
    # Get today's date in YYYY-MM-DD format
    today = datetime.today().strftime('%Y-%m-%d')

    # Fetch 1-minute interval data for the current day
    stock = yf.Ticker(ticker)
    df = stock.history(period='1d', interval='1m')

    # Check if data is empty
    if df.empty:
        print(f"No intraday data found for {ticker}. It may be delisted or have no available data.")
        return None

    # Print all rows of the DataFrame
    pd.set_option('display.max_rows', None)
    print(df)
    return df

if __name__ == "__main__":
    ticker = input("Enter stock ticker: ").upper()
    df = get_intraday_data(ticker)

import yfinance as yf
import pandas as pd

def fetch_stock_data():
    # Get user input
    stock_ticker = input("Enter the stock ticker (e.g., AAPL, TSLA): ").strip().upper()
    interval = input("Enter the interval (e.g., 1m, 5m, 15m, 1h): ").strip()

    valid_intervals = ['1m', '2m', '5m', '15m', '30m', '1h', '1d', '1wk', '1mo']
    if interval not in valid_intervals:
        print(f"Invalid interval. Please choose one of the following: {', '.join(valid_intervals)}")
        return

    try:
        # Fetch the stock data
        data = yf.Ticker(stock_ticker).history(period='1d', interval=interval)
        if data.empty:
            print(f"No data found for ticker '{stock_ticker}' at interval '{interval}'.")
        else:
            # Add a percent change column
            data['Percent Change'] = data['Close'].pct_change() * 100
            # Display the DataFrame
            pd.set_option("display.max_rows", None)  # Show all rows
            print(data)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    fetch_stock_data()

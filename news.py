import yfinance as yf
import pandas as pd
from datetime import datetime

def get_stock_data(ticker, start_date, end_date):
    """Fetch historical stock data for the specified date range."""
    stock = yf.Ticker(ticker)
    data = stock.history(start=start_date, end=end_date)
    return data

def analyze_declines(ticker, start_year, end_year, days_in_december=5):
    """Analyze how many years the stock market declined at the end of December 
    and continued to decline in January."""
    decline_years = []

    for year in range(start_year, end_year + 1):
        # Define date ranges
        dec_start_date = datetime(year, 12, 31) - pd.Timedelta(days=days_in_december - 1)
        dec_end_date = datetime(year, 12, 31)
        jan_start_date = datetime(year + 1, 1, 1)
        jan_end_date = datetime(year + 1, 1, 31)

        # Fetch stock data
        try:
            dec_data = get_stock_data(ticker, dec_start_date.strftime('%Y-%m-%d'), dec_end_date.strftime('%Y-%m-%d'))
            jan_data = get_stock_data(ticker, jan_start_date.strftime('%Y-%m-%d'), jan_end_date.strftime('%Y-%m-%d'))

            if dec_data.empty or jan_data.empty:
                print(f"No data available for {year}. Skipping.")
                continue

            # Calculate percentage change
            dec_return = (dec_data['Close'].iloc[-1] - dec_data['Close'].iloc[0]) / dec_data['Close'].iloc[0] * 100
            jan_return = (jan_data['Close'].iloc[-1] - jan_data['Close'].iloc[0]) / jan_data['Close'].iloc[0] * 100

            # Check for declines in both periods
            if dec_return > 0 and jan_return > 0:
                decline_years.append(year)

        except Exception as e:
            print(f"Error processing data for {year}: {e}")

    return decline_years

if __name__ == "__main__":
    ticker = "^GSPC"  # S&P 500 index
    start_year = 2000
    end_year = 2023
    days_in_december = 5  # Number of trading days to analyze

    # Call the function with days_in_december as an argument
    decline_years = analyze_declines(ticker, start_year, end_year, days_in_december)

    if decline_years:
        print(f"Years when the stock market declined in the last {days_in_december} trading days of December and continued to decline in January:")
        print(decline_years)
    else:
        print("No such years found in the specified range.")

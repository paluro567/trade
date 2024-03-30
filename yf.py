import yfinance as yf
from datetime import datetime

def fetch_intraday_data(ticker):
    try:
        # Fetch intraday data using the ticker symbol
        stock = yf.Ticker(ticker)
        
        # Get historical market data for the last trading day with 5-minute intervals
        intraday_data = stock.history(period="1d", interval="5m", prepost = True)
        
        # Print the intraday data
        print("Intraday Data for", ticker)
        print(intraday_data)
    except Exception as e:
        print("Error fetching data:", e)

# Example usage
if __name__ == "__main__":
    ticker_symbol = "AAPL"  # Example ticker symbol (Apple Inc.)
    fetch_intraday_data(ticker_symbol)

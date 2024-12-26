import requests
from bs4 import BeautifulSoup

def get_next_earnings_date(ticker):
    """
    Scrape Yahoo Finance to find the next earnings date of a stock.

    Args:
        ticker (str): Stock ticker symbol.

    Returns:
        str: Next earnings date or a message if not found.
    """
    try:
        # Yahoo Finance URL for the stock's summary page
        url = f"https://finance.yahoo.com/quote/{ticker}/"
        
        # Send a GET request to the URL
        response = requests.get(url)
        
        # Raise an HTTPError for bad responses (4xx and 5xx)
        response.raise_for_status()

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Locate the earnings date
        earnings_section = soup.find('td', text='Earnings Date')
        if earnings_section:
            earnings_date = earnings_section.find_next_sibling('td').text.strip()
            return earnings_date
        else:
            return f"Earnings date not found for ticker: {ticker}."

    except requests.exceptions.RequestException as e:
        return f"An error occurred while fetching the data: {e}"

if __name__ == "__main__":
    ticker_symbol = input("Enter the stock ticker symbol: ").strip().upper()
    earnings_date = get_next_earnings_date(ticker_symbol)
    print(f"Next earnings date for {ticker_symbol}: {earnings_date}")

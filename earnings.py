import requests
import pandas as pd
from datetime import datetime, timedelta

# Finnhub API key
FINNHUB_API_KEY = "cu1at21r01qqr3sgcka0cu1at21r01qqr3sgckag"


def fetch_historical_earnings(api_key, ticker):
    """
    Fetch historical earnings data for a specific ticker.
    """
    url = f"https://finnhub.io/api/v1/stock/earnings"
    params = {"symbol": ticker, "token": api_key}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching historical earnings for {ticker}: {response.status_code}")
        return []


def calculate_revenue_growth(current_revenue, past_revenue):
    """
    Calculate the percentage growth in revenue.
    """
    if past_revenue and current_revenue:
        return ((current_revenue - past_revenue) / past_revenue) * 100
    return None

def get_earnings_for_tickers(api_key, tickers, days_ahead=30):
    """
    Fetch earnings results for a specific list of tickers within the next `days_ahead` days,
    including revenue growth calculations.
    """
    today = datetime.today()
    end_date = today + timedelta(days=days_ahead)

    # API endpoint for earnings calendar
    url = "https://finnhub.io/api/v1/calendar/earnings"
    params = {
        "from": today.strftime('%Y-%m-%d'),
        "to": end_date.strftime('%Y-%m-%d'),
        "token": api_key,
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json().get("earningsCalendar", [])
        if data:
            # Convert to DataFrame
            earnings_df = pd.DataFrame(data)

            # Ensure the necessary columns are present
            for col in ["symbol", "date", "time", "epsEstimate", "revenueEstimate"]:
                if col not in earnings_df.columns:
                    earnings_df[col] = None

            # Ensure tickers are uppercase
            tickers = [ticker.upper() for ticker in tickers]
            earnings_df = earnings_df[earnings_df["symbol"].isin(tickers)]

            # Parse the date column and sort by it
            earnings_df["date"] = pd.to_datetime(earnings_df["date"], errors="coerce")
            earnings_df = earnings_df.sort_values("date").reset_index(drop=True)

            # Add revenue growth calculations
            growth_data = []
            for ticker in tickers:
                historical_earnings = fetch_historical_earnings(api_key, ticker)
                print(f"Historical earnings for {ticker}:\n", historical_earnings)  # Debug

                # Extract revenue data for calculations
                if len(historical_earnings) >= 2:
                    last_quarter = historical_earnings[0]
                    prior_quarter = historical_earnings[1]

                    # Use `actual` for revenue
                    if "actual" in last_quarter and "actual" in prior_quarter:
                        try:
                            past_revenue = float(prior_quarter["actual"])
                            last_revenue = float(last_quarter["actual"])
                            past_growth = calculate_revenue_growth(last_revenue, past_revenue)

                            # Check if `ticker` exists in `earnings_df`
                            if ticker in earnings_df["symbol"].values:
                                current_revenue = earnings_df.loc[
                                    earnings_df["symbol"] == ticker, "revenueEstimate"
                                ].values[0]
                                current_growth = calculate_revenue_growth(
                                    float(current_revenue), last_revenue
                                )
                            else:
                                print(f"Ticker {ticker} not found in earnings_df.")
                                current_growth = None

                            growth_data.append(
                                {
                                    "symbol": ticker,
                                    "past_growth": past_growth,
                                    "current_growth": current_growth,
                                }
                            )
                        except ValueError as e:
                            print(f"Error processing revenue for {ticker}: {e}")
                    else:
                        print(f"Revenue data missing for {ticker} in historical earnings.")

            # Handle empty growth data
            if growth_data:
                growth_df = pd.DataFrame(growth_data)
                earnings_df = earnings_df.merge(growth_df, on="symbol", how="left")
            else:
                print("No growth data available.")
                earnings_df["past_growth"] = None
                earnings_df["current_growth"] = None

            return earnings_df
    else:
        print(f"Error fetching data: {response.status_code}, {response.text}")
        return pd.DataFrame()

if __name__ == "__main__":
    # List of tickers to track
    tickers_of_interest = [
        "TSLA",
        "PLTR",
        "AMZN",
        "PYPL",
        "AMD",
        "MARA",
        "CELH",
        "UPST",
        "ELF",
    ]

    # Fetch earnings calendar
    earnings_calendar = get_earnings_for_tickers(
        FINNHUB_API_KEY, tickers_of_interest, days_ahead=30
    )

    if not earnings_calendar.empty:
        print("Upcoming Earnings Calendar:")
        print(
            earnings_calendar[
                ["symbol", "date", "revenueEstimate", "past_growth", "current_growth"]
            ]
        )
    else:
        print("No upcoming earnings found.")

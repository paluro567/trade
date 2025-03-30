import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

def get_data_for_date(ticker, target_date_str, interval='5m'):
    # Target date in YYYY-MM-DD
    target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
    print(f"Fetching data for {ticker} on {target_date_str} using interval {interval}...")

    try:
        # Download 5 days to ensure the target date is included
        stock = yf.Ticker(ticker)
        df = stock.history(period='5d', interval=interval, prepost=True)
    except Exception as e:
        print(f"Error retrieving data for {ticker}: {e}")
        return pd.DataFrame()

    if df.empty:
        print(f"{ticker} returned empty DataFrame from yfinance.")
        return pd.DataFrame()

    print(f"Raw data shape: {df.shape}")
    print(f"Raw data head:\n{df.head()}")

    # Check index timezone info
    if df.index.tz is None:
        print(f"{ticker}: Data has no timezone info; assuming UTC.")
        df.index = df.index.tz_localize('UTC')

    # Convert index to US/Eastern and filter for target date
    df.index = df.index.tz_convert('America/New_York')
    df_filtered = df[df.index.date == target_date]

    if df_filtered.empty:
        print(f"No rows found for {ticker} on {target_date_str} after timezone filtering.")
        print(f"Available dates in dataset: {sorted(set(df.index.date))}")
    else:
        print(f"\nFiltered data for {ticker} on {target_date_str}:\n{df_filtered.head()}")

    return df_filtered

# Example usage
if __name__ == '__main__':
    ticker = 'SOFI'  # Replace as needed
    target_date = '2025-03-28'
    df = get_data_for_date(ticker, target_date, interval='5m')

    if not df.empty:
        print(f"\n✅ Returned {len(df)} rows of data for {ticker} on {target_date}")
    else:
        print(f"\n❌ No data returned for {ticker} on {target_date}")

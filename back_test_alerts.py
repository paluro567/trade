import alpaca_trade_api as tradeapi
import pandas as pd
from datetime import datetime, timedelta, timezone

# Alpaca API credentials (Replace with your actual API keys)
API_KEY = 'PKC880CJJ8208OXDWR3N'
API_SECRET = '5p9Eq0xiQ5ZlHJWOtmu0EsXRFvNDw1mPVmiSaUap'
BASE_URL = 'https://paper-api.alpaca.markets'  # Use 'https://api.alpaca.markets' for live trading

class TimeFrame:
    Minute = "1Min"
    Hour = "1Hour"
    Day = "1Day"

# Initialize the Alpaca API client
api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

def august_day(p_day):
    # Set the time to market open (9:30 AM Eastern Time)
    return datetime(2024, 8, int(p_day), 9, 30, 0, tzinfo=timezone.utc) - timedelta(hours=4)

def alpaca_df(p_stock, aug_day, p_interval=TimeFrame.Minute):
    p_date = august_day(aug_day)
    start_time = p_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_time = (p_date + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Retrieve 1-minute data for the specified day using Alpaca API
    bars = api.get_bars(p_stock, p_interval, start=start_time, end=end_time)
    
    # Convert bars to a DataFrame
    df = pd.DataFrame([{
        'Time': bar.t,
        'Open': bar.o,
        'High': bar.h,
        'Low': bar.l,
        'Close': bar.c,
        'Volume': bar.v
    } for bar in bars])
    
    # Set 'Time' as the index and convert it to a pandas datetime index
    df['Time'] = pd.to_datetime(df['Time'], utc=True)
    df.set_index('Time', inplace=True)

    print(df.head())
    print(df.tail())

    return df

def calculate_sma(prices, period):
    """Calculate the Simple Moving Average (SMA)."""
    return prices.rolling(window=period).mean()

def calculate_profit_loss(df, buy_times):
    """Calculate the profit or loss for each buy time."""
    results = []
    for buy_time in buy_times:
        buy_time_str = buy_time.strftime('%H:%M:%S')
        if buy_time_str in df.index:
            buy_price = df.loc[buy_time_str]['Close']
            sell_price = None
            sell_time = None
            
            # Find the sell price when the Close goes below the 9 SMA
            for i in range(df.index.get_loc(buy_time_str) + 1, len(df)):
                if df.iloc[i]['Close'] < df.iloc[i]['SMA']:
                    sell_price = df.iloc[i]['Close']
                    sell_time = df.index[i]
                    break
            
            if sell_price:
                profit_loss = ((sell_price - buy_price) / buy_price) * 100
                results.append({
                    'Buy Time': buy_time_str,
                    'Sell Time': sell_time,  # Already a string, no need to format
                    'Buy Price': buy_price,
                    'Sell Price': sell_price,
                    'Profit/Loss': profit_loss
                })
            else:
                results.append({
                    'Buy Time': buy_time_str,
                    'Sell Time': 'N/A',
                    'Buy Price': buy_price,
                    'Sell Price': 'N/A',
                    'Profit/Loss': 'N/A'
                })
        else:
            results.append({
                'Buy Time': buy_time_str,
                'Sell Time': 'N/A',
                'Buy Price': 'N/A',
                'Sell Price': 'N/A',
                'Profit/Loss': 'N/A'
            })
    
    return pd.DataFrame(results)

def check_trades(stock_symbol, day, buy_times):
    # Fetch 1-minute data for the specified day
    df = alpaca_df(stock_symbol, '30', '1min')
    
    if df is None:
        print(f"No data found for {stock_symbol} on {day}")
        return
    
    # Calculate the 9 SMA
    df['SMA'] = calculate_sma(df['Close'], 20)
    
    # Filter out data to only keep the time portion
    df.index = df.index.strftime('%H:%M:%S')
    
    # Calculate profit/loss for each buy time
    results_df = calculate_profit_loss(df, buy_times)
    
    print(results_df)

'''
input:
    - ticker
    - day to check trades
    - array of buy times     
check_trades will find all trades that would have been made buying at buy times and selling when price crosses below SMA
'''
if __name__ == "__main__":
    stock_symbol = 'FCUV'  # Example stock symbol
    day = '2024-08-30'     # Example date
    buy_times = [
        datetime.strptime('11:42:00', '%H:%M:%S'),
        datetime.strptime('11:54:00', '%H:%M:%S'),
        datetime.strptime('12:16:00', '%H:%M:%S'),
        datetime.strptime('12:17:00', '%H:%M:%S'),
        datetime.strptime('12:33:00', '%H:%M:%S'),
        datetime.strptime('14:34:00', '%H:%M:%S')
    ]
    
    check_trades(stock_symbol, day, buy_times)

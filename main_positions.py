from multiprocessing import Process
import time
from datetime import datetime, timedelta
import pytz
import yfinance as yf
from sms import text


# GLOBALS
global TEXTED_PLAYS
TEXTED_PLAYS = {}

global last_time
last_time = time.time()

def yf_data(ticker, interval_time):
    """Fetch ticker data and calculate SMA indicators."""
    try:
        # Fetch sufficient data for a 180-period MA
        ticker = yf.Ticker(ticker)
        required_period = '14d' if interval_time == '30m' else '1d'  # Adjust based on interval
        intraday_data = ticker.history(period=required_period, interval=interval_time, prepost=True)

        # Calculate SMAs
        intraday_data['SMA_30'] = intraday_data['Close'].rolling(window=30).mean()
        intraday_data['SMA_180'] = intraday_data['Close'].rolling(window=180).mean()
        intraday_data['Percent_Change'] = intraday_data['Close'].pct_change() * 100

        return intraday_data
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None


def can_text(ticker):
    """Check if the ticker was not texted in the last 30 minutes."""
    global TEXTED_PLAYS
    current_time = datetime.now()
    if ticker in TEXTED_PLAYS:
        last_text_time = TEXTED_PLAYS[ticker]
        # Allow texting only if 30 minutes have passed since the last text
        if current_time - last_text_time < timedelta(minutes=30):
            return False
    return True

def update_texted_plays(ticker):
    """Update the last texted time for the ticker."""
    global TEXTED_PLAYS
    TEXTED_PLAYS[ticker] = datetime.now()

def check_play(ticker, interval):
    """Check if the current 30-minute interval begins below and ends above the 180 MA."""
    print(f"Checking play for {ticker} for interval {interval}")
    data = yf_data(ticker, interval)
    
    if data is not None and len(data) >= 2:  # Ensure there is enough data
        # Current price and 180 MA
        current_price = data['Close'].iloc[-1]
        current_sma_180 = data['SMA_180'].iloc[-1]

        # Starting price of the interval and 180 MA
        start_price = data['Close'].iloc[-2]  # The previous close in the interval
        start_sma_180 = data['SMA_180'].iloc[-2]

        # Latest percent change
        latest_percent_change = data['Percent_Change'].iloc[-1]


        # 180MA cross check
        if start_price < start_sma_180 and current_price > current_sma_180:
            print(f"{ticker}: 30-minute interval started below and ended above the 180 MA!")
            if can_text(ticker):
                msg=f"{ticker} crossed above the 180MA! Current % Change: {latest_percent_change:.2f}%"
                print(msg)
                text(msg)
                update_texted_plays(ticker)
        elif start_price > start_sma_180 and current_price < current_sma_180:
            if can_text(ticker):
                msg=f"{ticker} crossed below the 180MA... Current % Change: {latest_percent_change:.2f}%"
                print(msg)
                text(msg)
                update_texted_plays(ticker)
    else:
        print(f"{ticker}: Not enough data or invalid data format.")

def watch_play(ticker, interval):
    """Monitor a single ticker."""
    print(f"Started monitoring: {ticker}")
    while True:
        check_play(ticker, interval)
        time.sleep(60)  # Wait for 1 minute

def terminate_at_8pm(processes):
    """Terminate all processes at 8 PM EST."""
    est = pytz.timezone('America/New_York')
    while True:
        now = datetime.now(est)
        if now.hour == 20 and now.minute == 0:  # 8:00 PM EST
            print("Terminating all processes at 8 PM EST.")
            for process in processes:
                process.terminate()
            break
        time.sleep(30)  # Check every 30 seconds

if __name__ == '__main__':
    main_positions = ['PLTR', 'TSLA', 'PYPL', 'AMZN', 'MARA', 'IWM', 'SOFI', 'GOOGL','T']
    interval = '30m'

    # Create and start a process for each ticker
    processes = []
    for ticker in main_positions:
        process = Process(target=watch_play, args=(ticker, interval))
        processes.append(process)
        process.start()

    # Terminate all processes at 8 PM EST
    terminate_at_8pm(processes)

    # Ensure all processes are joined properly
    for process in processes:
        process.join()

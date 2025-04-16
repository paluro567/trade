import yfinance as yf
import datetime
import pytz

from datetime import datetime, timedelta, timezone
from Discord import get_briefing
from record_day_trade import pdt_rule, record_trade
from sms import text
import pandas as pd
import numpy as np
import os
import time
import requests
from multiprocessing import Process
import ta
from alpaca import try_orders

print(f"[Startup] Time (ET): {datetime.now(pytz.timezone('America/New_York')).strftime('%Y-%m-%d %H:%M:%S %Z')}")
print(f"[Startup] Executable: {os.sys.executable}")
print(f"[Startup] PATH: {os.environ.get('PATH')}")

# GLOBALS
BOUGHT_PLAYS = []
calls_made = 0
shortest_interval = 1.8  # 2,000 calls allowed per hour using YF
last_time = time.time()
TEXTED_PLAYS = []
BOUGHT_AMT = 0

def is_before_noon_est():
    est = pytz.timezone('America/New_York')
    return datetime.now(est).hour < 12

def sleep_until(target_hour, target_minute):
    current_time = datetime.now()
    target_time = current_time.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    if current_time > target_time:
        target_time += timedelta(days=1)
    time.sleep((target_time - current_time).total_seconds())

def debug_yahoo_raw(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=5m&range=1d"
    try:
        resp = requests.get(url)
        print(f"[{ticker}] Raw Yahoo Response (status {resp.status_code}):")
        print(resp.text[:500])
    except Exception as e:
        print(f"[{ticker}] Exception getting raw Yahoo data: {e}")

def find_resistance_points(data):
    resistance_points = data[(data['Open'] < data['High']) & (data['Close'] < data['High'])]
    return resistance_points['High'].tolist()

def yf_data(ticker, interval_time):
    global calls_made, last_time, shortest_interval

    elapsed_time = time.time() - last_time
    if elapsed_time < shortest_interval:
        time.sleep(shortest_interval - elapsed_time)

    last_time = time.time()
    calls_made += 1

    try:
        stock = yf.Ticker(ticker)
        max_retries = 3
        df = pd.DataFrame()

        for attempt in range(1, max_retries + 1):
            print(f"[{ticker}] Attempt {attempt}/{max_retries} to fetch {interval_time} data...")
            try:
                df = stock.history(period="1d", interval=interval_time, prepost=True)
                if df is None or df.empty:
                    print(f"[{ticker}] Returned empty on attempt {attempt}.")
                else:
                    print(f"[{ticker}] ✅ Got {len(df)} rows.")
                    break
            except Exception as e:
                print(f"[{ticker}] ❌ Error during .history(): {e}")
            time.sleep(3)

        if df.empty or len(df) <= 1:
            print(f"[{ticker}] ❌ Failed to get usable {interval_time} data after {max_retries} attempts. Debugging raw response...")
            debug_yahoo_raw(ticker)
            return pd.DataFrame()

        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        df.index = df.index.tz_convert('America/New_York')

        df = df[::-1]  # Reverse: newest bar first
        df['SMA_5'] = df['Close'].rolling(window=5).mean()
        df['SMA_9'] = df['Close'].rolling(window=9).mean()
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_180'] = df['Close'].rolling(window=180).mean()
        df['percent_change'] = (df['Close'] - df['Open']) / df['Open'] * 100

        print(f"[{ticker}] ✅ Final DataFrame has {len(df)} bars")
        return df

    except Exception as e:
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} - ERROR - yf_data({ticker}): {e}")
        debug_yahoo_raw(ticker)
        return pd.DataFrame()

def check_play(ticker, play_type, priority, interval):
    BUY_AMT = 1400
    global BOUGHT_AMT, BOUGHT_PLAYS

    print(f"Checking {ticker} play (type: {play_type}, priority: {priority}) PDT rule: {pdt_rule()}")
    try:
        df = yf_data(ticker, interval)

        if df.empty or len(df) < 4:
            print(f"{ticker}: Data not usable (empty or too short). Skipping play check.")
            return

        print(f"{ticker}: Using first 4 rows for bar logic.")
        cur_open = df.iloc[0]['Open']
        close_price = df.iloc[0]['Close']
        cur_vol = df.iloc[0]['Volume']
        time_stmp = df.index[0]
        print("time_stmp:", time_stmp)

        avg_vol = df['Volume'].mean()
        resistances = find_resistance_points(df)

        cur_pch = round(df.iloc[0]['percent_change'], 2)
        prior_pch = round(df.iloc[1]['percent_change'], 2)
        two_prior_pch = round(df.iloc[2]['percent_change'], 2)
        three_prior_pch = round(df.iloc[3]['percent_change'], 2)

        print(f"cur_pch: {cur_pch}, prior_pch: {prior_pch}, two_prior_pch: {two_prior_pch}, three_prior_pch: {three_prior_pch}")

    except Exception as e:
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} - ERROR - check_play - unable to check {ticker} with error: {e}")

def get_plays():
    try:
        desired_timezone = 'America/New_York'
        current_utc_time = datetime.now(timezone.utc)
        current_local_time = current_utc_time.astimezone(pytz.timezone(desired_timezone))

        alarm_plays, green_plays = get_briefing(current_local_time)
        other_on_radar = ['PLTR', 'AI', 'MDAI', 'SOFI']

        if alarm_plays == [] and green_plays == []:
            raise Exception(f"{datetime.now():%Y-%m-%d %H:%M:%S} - ERROR - empty alarm & green plays")

        print("today's alarm_plays: ", alarm_plays, flush=True)
        print("today's green_plays: ", green_plays, flush=True)

        plays_categories = {
            'NORMAL PLAY': green_plays,
            'ALARM PLAY': alarm_plays,
            'OTHER ON RADAR': other_on_radar
        }

        print("combined play categories: ", plays_categories, flush=True)

    except Exception as e:
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} - ERROR - get_plays - unable to get briefing or some error: {e}", flush=True)
        print("sleeping 5 minutes...", flush=True)
        time.sleep(300)
        print("running watch_zip_plays again", flush=True)
        return get_plays()

    return plays_categories

def watch_zip_plays(interval):
    global BOUGHT_PLAYS, TEXTED_PLAYS
    TEXTED_PLAYS = []
    iteration = 1
    dashes = '-' * 20
    print("running watch_zip_plays", flush=True)
    plays_categories = get_plays()
    july_august_zip = ['SERV', 'MARA']

    iter_count = 0
    while True:
        iter_count += 1
        current_time = datetime.now().time()
        if current_time.hour >= 20:
            return 0

        print(f"checking stocks iteration! - {iter_count}", flush=True)
        for category, stocks in plays_categories.items():
            for priority, stock in enumerate(stocks):
                try:
                    print(f"{dashes}Checking {stock} {dashes}", flush=True)
                    check_play(stock, category, priority + 1, interval)
                except Exception as e:
                    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} - ERROR - watch_zip_plays - unable to check {stock} with error: {e}", flush=True)

        for stock in july_august_zip:
            print("test 3", flush=True)
            check_play(stock, "july_august_zip", 5, interval)
            print("test 4", flush=True)

        iteration += 1
        if iteration == 40:
            iteration = 1
            TEXTED_PLAYS = []
        print(f"minute {iteration} - texted plays: ", TEXTED_PLAYS)

if __name__ == '__main__':
    print("main running")
    try:
        watch_zip_plays('5m')
    except Exception as e:
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} - ERROR - unable to run watch_zip_plays with: {e}")

import yfinance as yf
import datetime
import pytz

from datetime import datetime, timedelta, timezone
from revised_discord import get_briefing
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

def fallback_yahoo_data(ticker, interval='5m'):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval={interval}&range=1d"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 429:
            print(f"[{ticker}] ⚠️ Rate limit hit (429). Sleeping 60 seconds before retry...")
            time.sleep(60)
            return pd.DataFrame()
        elif resp.status_code != 200:
            print(f"[{ticker}] ❌ Unexpected status code: {resp.status_code}")
            return pd.DataFrame()

        data = resp.json()
        timestamps = data["chart"]["result"][0]["timestamp"]
        indicators = data["chart"]["result"][0]["indicators"]["quote"][0]
        df = pd.DataFrame(indicators)
        df["timestamp"] = pd.to_datetime(timestamps, unit="s")
        df.set_index("timestamp", inplace=True)
        df.index = df.index.tz_localize("UTC").tz_convert("America/New_York")

        df = df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
        df['SMA_5'] = df['Close'].rolling(window=5).mean()
        df['SMA_9'] = df['Close'].rolling(window=9).mean()
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_180'] = df['Close'].rolling(window=180).mean()
        df['percent_change'] = (df['Close'] - df['Open']) / df['Open'] * 100

        print(f"[{ticker}] ✅ Fallback DataFrame with {len(df)} bars")
        return df[::-1]  # reverse: newest bar first

    except Exception as e:
        print(f"[{ticker}] ❌ Exception in fallback_yahoo_data: {e}")
        return pd.DataFrame()

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

    print(f"[{ticker}] Fetching {interval_time} data using fallback approach...")
    df = fallback_yahoo_data(ticker, interval_time)

    if df.empty or len(df) <= 1:
        print(f"[{ticker}] ❌ Fallback also returned empty or insufficient data.")
    else:
        print(f"[{ticker}] ✅ Final fallback DataFrame has {len(df)} bars")

    return df

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

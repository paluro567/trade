import pandas as pd
from scrape_yahoo import scrape_stock_price
from Discord import get_briefing
from sms import text
import datetime
from datetime import timezone
import pytz
from threeBar_yf import sleep_until
import threading

class Bar:
    def __init__(self, open_price, close_price, percent_change, open_time):
        self.open_price = open_price
        self.close = close_price
        self.percent_change = percent_change
        self.open_time = open_time
    def __str__(self):
        return f"Open Price: {self.open_price}, Close Price: {self.close}, Percent Change: {self.percent_change}, Open Time: {self.open_time}"


# Calculate percent change
def calculate_percent_change(current_price, previous_price):
    if previous_price is None:
        return None
    return ((current_price - previous_price) / previous_price) * 100

def three_bar_breakout(cur_bars):
    return cur_bars[-1].percent_change>5 \
        and cur_bars[-2].percent_change<0 \
            and cur_bars[-3].percent_change>5

# Function to update the minute_interval_df
def monitor_stock(ticker):
    texted=False # only text once / stock

    watch_bars=[]
    while True:
        current_time = pd.Timestamp.now()
        try:
            current_price = scrape_stock_price(ticker)
        except Exception as e:
            print(f"unable to scrape : {e}")

        # create a new bar object
        if len(watch_bars)<4 \
            or (current_time - watch_bars[-1].open_time).total_seconds() >= 60:
            new_bar= Bar(current_price, current_price, 0, current_time)
            if len(watch_bars)>=4:
                watch_bars.pop(0)
            watch_bars.append(new_bar)
        # update last bar
        else:
            update_bar=watch_bars[-1]
            update_bar.close_price=current_price
            update_bar.percent_change= calculate_percent_change(current_price, update_bar.open_price)
            watch_bars[-1]=update_bar

        if three_bar_breakout(watch_bars) and not texted:
            message =(f"scraped alert! {ticker}")
            for bar in watch_bars:
                message+="\n" + bar.__str__() + "\n"
            text(message)
            texted=True


if __name__=="__main__":
    
    # sleep_until(9, 29) # sleep till market opens to begin execution


    # Get plays for current date
    try:
        desired_timezone = 'America/New_York'
        current_utc_time = datetime.datetime.now(timezone.utc)
        current_local_time = current_utc_time.astimezone(pytz.timezone(desired_timezone))
        curr_date_local = current_local_time.strftime('%Y-%m-%d')
        alarm_plays, green_plays  =  get_briefing(curr_date_local) 
    except Exception as e:
        print(f"Error before scraping: {e}")

    # start monitoring a stock
    for play in alarm_plays:
        try:
            thread = threading.Thread(target=monitor_stock, args=(play,))
            thread.start()
        except Exception as e:
            print(f"Error with thread: {e}")









from Discord import get_briefing
from datetime import datetime, timezone, timedelta
import pytz
import yfinance as yf
import pandas as pd


def august_day(p_day):
    # Get current UTC time
    return datetime(2024, 8, int(p_day), 12, 0, 0, tzinfo=timezone.utc) 

def plays_for_day(p_day):
    return get_briefing(august_day(p_day))

def august_day(p_day):
    # Get current UTC time
    desired_timezone = 'America/New_York'
    return datetime(2024, 8, int(p_day), 12, 0, 0, tzinfo=timezone.utc) 

def plays_for_day(p_day):

    # Specify the desired date and time in UTC
    # p_day=input("what day in august: ")
    specific_utc_time = august_day(p_day)

    # Convert the specific UTC time to the desired local timezone
    desired_timezone = 'America/New_York'  # Replace with your desired timezone
    specific_local_time = specific_utc_time.astimezone(pytz.timezone(desired_timezone))

    # Format the date as 'YYYY-MM-DD'
    specific_date_local = specific_local_time.strftime('%Y-%m-%d')

    print(specific_date_local)

    alarm_plays, green_plays  =  get_briefing(specific_date_local)  # get briefing


    return alarm_plays, green_plays

def consolidate_resistances(resistances, percent_threshold=1):
    """Consolidate nearby resistance levels within a specified percent threshold."""
    if not resistances:
        return []
    
    # Sort the resistances
    resistances.sort()

    consolidated = [resistances[0]]  # Start with the first resistance
    for resistance in resistances[1:]:
        last_consolidated = consolidated[-1]
        # Calculate the percentage difference
        percent_diff = (resistance - last_consolidated) / last_consolidated * 100
        
        # If the percentage difference is greater than the threshold, add it as a new resistance
        if percent_diff > percent_threshold:
            consolidated.append(resistance)
        else:
            # Optionally, you could take the max or average of the grouped resistances
            consolidated[-1] = max(consolidated[-1], resistance)  # or use average: (consolidated[-1] + resistance) / 2

    return consolidated


def yf_df(p_stock, aug_day, p_interval='5m'):
    p_date = august_day(aug_day)
    date_str = p_date.strftime('%Y-%m-%d')

    stock = yf.Ticker(p_stock)
    df = stock.history(start=date_str, end=(p_date + timedelta(days=1)).strftime('%Y-%m-%d'), interval=p_interval)
    # Ensure the DataFrame index is a DatetimeIndex
    df.index = pd.to_datetime(df.index)

    # Filter the DataFrame to only include data after 9:30 AM
    market_open_time = datetime.strptime('09:30', '%H:%M').time()
    df = df.between_time(market_open_time, '23:59')

    resistances = []
    for index, row in df.iterrows():
        # Filter out times before 9:30 AM
        if row['Open'] < row['High'] and row['Close'] < row['High']:
            resistances.append(row['High'])
    resistances=consolidate_resistances(resistances)

    print("\nResistances:", resistances)
    # Now, check for breakthroughs with Open below resistance and Close above resistance
    for index, row in df.iterrows():
        for resistance in resistances:
            if row['Open'] < resistance < row['Close']:
                percent_change = ((row['Close'] - resistance) / resistance) * 100
                if percent_change>3:
                    print(f"Breakthrough at {index}: Open = {row['Open']}, Close = {row['Close']}, Resistance = {resistance}, Percent Change = {percent_change:.2f}%")

    return resistances


def buys_for_day_august(pday, stock):
 return 1

'''this script is hard coded to check August 2024 dates 
- get_plays (from discord.py)
-yf df from yfinance
'''

if __name__=='__main__':
   aug_day=input("Enter August day: ")
   plays_for_day(aug_day)
   check_ticker=input("Enter a ticker: ")
   
   #    CHECK THE DF OF THE ENTERED STOCK ON AUGUST DAY
   yf_df(p_stock=check_ticker,aug_day=aug_day)


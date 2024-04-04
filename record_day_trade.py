from datetime import datetime, timedelta

gcp_trades_path= "/home/peter_luro1/trade/day_trades.txt"
local_trades_path="/Users/peterluro/Desktop/test_logging/day_trades.txt"

# non-trading holidays (exclude when counting)
major_holidays = [
    (1, 1),    # New Year's Day
    (7, 4),    # Independence Day (US)
    (11, 11),  # Veterans Day (US)
    (12, 25)   # Christmas
]

# Function to check if a given date is a trading day
def is_trading_day(date):
    # Exclude weekends (Saturday and Sunday)
    if date.weekday() >= 5:
        return False
    # Exclude major holidays
    if (date.month, date.day) in major_holidays:
        return False
    # Consider it as a trading day otherwise
    return True


# finds the date beginning a 5-day PDT period from the current date
def begin_pdt_period():
    current_date = datetime.now().date()
    days_counted = 0
    while days_counted < 5:
        current_date -= timedelta(days=1)
        if is_trading_day(current_date):
            days_counted += 1
    return current_date

def record_trade(ticker, filename=gcp_trades_path):
    if not pdt_rule(filename):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(filename, "a") as file:
            file.write(f"\nTicker: {ticker}, Time: {current_time}")  # write trade to trades.txt
    else:
        print("PDT reached")

def pdt_rule(filename=gcp_trades_path):
    # Get the day beginning the 5-day period
    begin_date = begin_pdt_period()
    try:
        # Read the content of the file
        with open(filename, "r") as file:
            lines = file.readlines()

        # If the file is empty or has only one line, return False
        if len(lines) < 3:
            print(f"No PDT")
            return False

        # Extract timestamps from each line and convert them to datetime objects
        trade_timestamps = [line.strip().split(", ")[1].split(": ")[1] for line in lines if line.strip()]


        if not trade_timestamps:
            print("No trade timestamps found in the file.")
            return False

        # Convert trade timestamps to datetime objects
        trade_datetimes = [datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S") for timestamp in trade_timestamps]

        # Count the number of trades on or after the day beginning the 5-day period
        count = sum(1 for trade_datetime in trade_datetimes if trade_datetime.date() >= begin_date)

        # PDT is in force => do not allow buys
        print(f"Number day trades: {count}")
        return count >= 3

    except Exception as e:
        print("Error:", e)
        return True

if __name__=='__main__':
    print("Day beginning 5 day PDT period: ", begin_pdt_period())
    print("PDT is met: ", pdt_rule())
    record_trade('PLTR') 


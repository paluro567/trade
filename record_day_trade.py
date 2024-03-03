from datetime import datetime, timedelta
from datetime import datetime, timedelta

# List of major holidays (you may need to customize this list based on your market)
# For demonstration, I'll include New Year's Day, Independence Day, Thanksgiving, and Christmas
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


def record_trade(ticker, filename="/home/peter_luro1/trade/trades.txt"):
    #VM path /home/peter_luro1/trade/trades.txt
    
    
    # After recording the trade, check if 3 or more trades have been executed within a 5-day period
    if not check_trades_within_window(filename):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(filename, "a") as file:
            file.write(f"Ticker: {ticker}, Time: {current_time}\n")
        
    else:
        print("You have placed 3 or more trades within a 5-day trading day window.")
def check_trades_within_window(filename="trades.txt"):
    try:
        # Read the content of the file
        with open(filename, "r") as file:
            lines = file.readlines()

        # If the file is empty or has only one line, return False
        if len(lines) < 2:
            print("There are not enough trades recorded in the file.")
            return False

        # Extract timestamps from each line and convert them to datetime objects
        trade_timestamps = [line.strip().split(", ")[1].split(": ")[1] for line in lines]

        if not trade_timestamps:
            print("No trade timestamps found in the file.")
            return False

        trade_datetimes = [datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S") for timestamp in trade_timestamps]

        # Sort the trade datetimes in ascending order
        trade_datetimes.sort()

        # Iterate through the sorted trade datetimes and count trades within a 5-day window
        count = 0
        for i in range(len(trade_datetimes)):
            # Skip non-trading days
            if not is_trading_day(trade_datetimes[i]):
                continue
            for j in range(i + 1, len(trade_datetimes)):
                # Skip non-trading days
                if not is_trading_day(trade_datetimes[j]):
                    continue
                if trade_datetimes[j] - trade_datetimes[i] <= timedelta(days=5):
                    count += 1
                else:
                    break  # No need to check further, as the trades are sorted by time

        # Return True if there are 3 or more trades within a 5-day window, False otherwise
        return count >= 3

    except Exception as e:
        print("Error:", e)
        return False

# Example usage:
ticker = "AAPL"
record_trade(ticker)

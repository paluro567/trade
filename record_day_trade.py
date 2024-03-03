from datetime import datetime, timedelta

def record_trade(ticker, filename="/home/peter_luro1/trade/trades.txt"):
    #VM path /home/peter_luro1/trade/trades.txt
    
    
    # After recording the trade, check if 3 or more trades have been executed within a 5-day period
    if not check_trades_within_window(filename):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(filename, "a") as file:
            file.write(f"Ticker: {ticker}, Time: {current_time}\n")
        
    else:
        print("You have placed 3 or more trades within a 5-day trading day window.")

def check_trades_within_window(filename="/home/peter_luro1/trade/trades.txt"):
    try:
        # Read the content of the file
        with open(filename, "r") as file:
            lines = file.readlines()

        # Extract timestamps from each line and convert them to datetime objects
        trade_timestamps = [line.strip().split(", ")[1].split(": ")[1] for line in lines]
        trade_datetimes = [datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S") for timestamp in trade_timestamps]

        # Sort the trade datetimes in ascending order
        trade_datetimes.sort()

        # Iterate through the sorted trade datetimes and count trades within a 5-day window
        count = 0
        for i in range(len(trade_datetimes)):
            for j in range(i + 1, len(trade_datetimes)):
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

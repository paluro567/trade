from datetime import datetime, timedelta

def write_trade(file_name, ticker_symbol, date):
    with open(file_name, 'a') as file:
        file.write(f"{date},{ticker_symbol}\n")

def PDT_check(file_name):
    # Calculate the date 5 business days ago
    today = datetime.now()
    five_days_ago = today - timedelta(days=7)  # Assuming 5 business days excluding weekends

    # Read the existing data from the file and filter out entries older than 5 business days
    new_data = []
    with open(file_name, 'r') as file:
        for line in file:
            try:
                date_str, ticker_symbol = line.strip().split(',')
                trade_date = datetime.strptime(date_str, '%Y-%m-%d')
                if trade_date >= five_days_ago:
                    new_data.append((trade_date, ticker_symbol))
            except ValueError:
                print(f"Ignoring line: {line.strip()}. It does not have the expected format.")

    # Write the filtered data back to the file
    with open(file_name, 'w') as file:
        for date, symbol in new_data:
            file.write(f"{date.strftime('%Y-%m-%d')},{symbol}\n")

    # Count the number of trades made within 5 business days
    trade_count = len(new_data)
    return trade_count    

# Example usage
if __name__=="__main__":
    file_name = 'trades.txt'
    ticker_symbol = 'PLTR'
    date = datetime.now().strftime('%Y-%m-%d')  # Get current date in YYYY-MM-DD format
    write_trade(file_name, ticker_symbol, date)
    number_of_trades = PDT_check(file_name)
    print(f"Number of trades made within the last 5 business days: {number_of_trades}. More than 2 trades {number_of_trades>1}")

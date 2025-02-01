import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from tkinter import Tk, Label, Button, Entry, StringVar
from tkcalendar import Calendar

# Function to fetch 1-month data and calculate volume statistics
def fetch_monthly_data(ticker):
    """
    Fetch 1-month interval stock data and calculate volume statistics.

    Args:
        ticker (str): Stock ticker symbol.

    Returns:
        tuple: Full data DataFrame, mean volume, and standard deviation of volume.
    """
    try:
        interval = "5m"
        period = "1mo"

        # Download data from Yahoo Finance
        stock = yf.Ticker(ticker)
        data = stock.history(period=period, interval=interval)

        if data.empty:
            print(f"Warning: No data returned by Yahoo Finance for {ticker} for 1 month.")
            return pd.DataFrame(), None, None

        # Convert date strings to datetime for filtering
        data['Datetime'] = data.index
        data['Date'] = data['Datetime'].dt.date

        # Calculate volume mean and standard deviation
        avg_volume = data['Volume'].mean()
        std_volume = data['Volume'].std()

        print(f"1-Month Volume Statistics: Mean={avg_volume}, StdDev={std_volume}")
        return data, avg_volume, std_volume
    except Exception as e:
        print(f"Error fetching monthly data: {e}")
        return pd.DataFrame(), None, None

# Function to fetch 5-minute interval stock data for a specific day
def fetch_stock_data(full_data, date):
    """
    Filter 5-minute interval stock data for a specific day from the full month's data.

    Args:
        full_data (pd.DataFrame): Full month's stock data.
        date (str): Specific date in 'YYYY-MM-DD' format.

    Returns:
        pd.DataFrame: DataFrame containing 5-minute interval data for the specified day.
    """
    try:
        if full_data.empty:
            print("No full data available to filter.")
            return pd.DataFrame()

        # Filter data for the specific date
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        filtered_data = full_data[full_data['Date'] == target_date]

        if filtered_data.empty:
            print(f"No data found for the specific date: {date}.")
        else:
            print(f"Data fetched successfully for {date}.")
        return filtered_data
    except Exception as e:
        print(f"Error filtering data: {e}")
        return pd.DataFrame()

# Function to visualize the data
def visualize_data(data, ticker, date, avg_volume, std_volume):
    """
    Visualize the 5-minute interval stock data using candlestick plots and volume bars.

    Args:
        data (pd.DataFrame): DataFrame containing stock data.
        ticker (str): Stock ticker symbol.
        date (str): Specific date in 'YYYY-MM-DD' format.
        avg_volume (float): Mean volume for the entire month.
        std_volume (float): Standard deviation of volume for the entire month.
    """
    try:
        if data.empty:
            print("No data to visualize.")
            return

        # Calculate the abnormal volume threshold
        abnormal_threshold = avg_volume + 1 * std_volume

        volume_colors = [
            'red' if vol > abnormal_threshold else 'blue'
            for vol in data['Volume']
        ]

        x = range(len(data))

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True, gridspec_kw={'height_ratios': [3, 1]})

        for i, row in enumerate(data.itertuples()):
            color = 'green' if row.Close >= row.Open else 'red'
            ax1.plot([x[i], x[i]], [row.Low, row.High], color=color, linewidth=1)
            ax1.plot([x[i], x[i]], [row.Open, row.Close], color=color, linewidth=5)

        ax1.set_title(f'{ticker} 5-Minute Interval Candlestick with Volume on {date}')
        ax1.set_ylabel('Price')
        ax1.grid(axis='y', linestyle='--', alpha=0.7)

        bar_width = 0.6
        ax2.bar(x, data['Volume'], color=volume_colors, width=bar_width, align='center')

        ax2.set_title('Volume')
        ax2.set_ylabel('Volume')
        ax2.set_xlabel('Time')
        ax2.grid(axis='y', linestyle='--', alpha=0.7)
        ax2.set_xticks(x[::10])
        ax2.set_xticklabels(data['Datetime'][::10].dt.strftime('%H:%M'), rotation=45)

        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"Error visualizing data: {e}")

# Interactive calendar for selecting a date
def select_date_and_fetch_data():
    """
    Opens a Tkinter GUI for the user to select a date and fetch stock data.
    """
    def fetch_data():
        selected_date = cal.get_date()
        formatted_date = datetime.strptime(selected_date, "%m/%d/%y").strftime("%Y-%m-%d")
        ticker_value = ticker.get()
        root.destroy()
        main(ticker_value, formatted_date)

    root = Tk()
    root.title("Select Date")

    Label(root, text="Select a Date:").pack(pady=10)
    cal = Calendar(root, date_pattern="mm/dd/yy")
    cal.pack(pady=10)

    Label(root, text="Enter Stock Ticker:").pack(pady=5)
    ticker = StringVar()
    ticker_entry = Entry(root, textvariable=ticker)
    ticker_entry.pack(pady=5)

    Button(root, text="Fetch Data", command=fetch_data).pack(pady=20)
    root.mainloop()

# Main function
# Main function
def main(ticker, date):
    """
    Main function to fetch monthly data, calculate volume statistics, and visualize data for a specific day.

    Args:
        ticker (str): Stock ticker symbol.
        date (str): Specific date in 'YYYY-MM-DD' format.
    """
    # Fetch 1-month data and calculate volume statistics
    full_data, avg_volume, std_volume = fetch_monthly_data(ticker)
    if full_data.empty:
        print("Failed to fetch 1-month data. Exiting.")
        return

    # Fetch data for the specific date
    daily_data = fetch_stock_data(full_data, date)
    if daily_data.empty:
        print("No data available for the selected date. Exiting.")
        return

    # Visualize the data
    visualize_data(daily_data, ticker, date, avg_volume, std_volume)


if __name__ == "__main__":
    select_date_and_fetch_data()

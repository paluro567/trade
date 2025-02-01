import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Define key technical indicators
def calculate_indicators(df):
    df['20_SMA'] = df['Close'].rolling(window=20).mean()
    df['50_SMA'] = df['Close'].rolling(window=50).mean()
    df['RSI'] = calculate_rsi(df['Close'])
    df['Volume_Avg'] = df['Volume'].rolling(window=20).mean()
    return df

def calculate_rsi(series, period=14):
    delta = series.diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Analyze stock for breakout and sell points
def analyze_breakouts_and_sells(df):
    breakouts = []
    sell_points = []
    next_breakout_level = None
    rsi_above_70_flag = False

    for i in range(1, len(df)):
        # Breakout logic: 20 SMA crosses above the 50 SMA
        if df['20_SMA'][i] > df['50_SMA'][i] and df['20_SMA'][i - 1] <= df['50_SMA'][i - 1]:
            if df['RSI'][i] > 50 and df['Volume'][i] > 1.5 * df['Volume_Avg'][i]:
                breakout_data = {
                    'Date': df.index[i],
                    'Close': df['Close'][i],
                    'RSI': df['RSI'][i],
                    'Volume': df['Volume'][i],
                    '20_SMA': df['20_SMA'][i],
                    '50_SMA': df['50_SMA'][i],
                }
                breakouts.append(breakout_data)

        # Sell point logic: First RSI > 70 after being below 70
        if df['RSI'][i] > 70 and not rsi_above_70_flag and df['RSI'][i - 1] <= 70:
            sell_data = {
                'Date': df.index[i],
                'Close': df['Close'][i],
                'RSI': df['RSI'][i],
                'Volume': df['Volume'][i],
                '20_SMA': df['20_SMA'][i],
                '50_SMA': df['50_SMA'][i],
                'Reason': 'RSI > 70'
            }
            sell_points.append(sell_data)
            rsi_above_70_flag = True

        # Reset RSI flag when it goes back below 70
        if df['RSI'][i] <= 70:
            rsi_above_70_flag = False

    # Determine the next breakout level
    next_breakout_level = determine_next_breakout(df, breakouts)

    return breakouts, sell_points, next_breakout_level

def determine_next_breakout(df, breakouts):
    if not breakouts:
        # No breakout exists, use recent high and resistance levels
        recent_high = df['Close'].max()
        potential_resistance = recent_high * 1.02  # Placeholder logic for potential resistance
        return potential_resistance
    else:
        # Use the last breakout point and calculate potential targets dynamically
        last_breakout = breakouts[-1]['Close']
        recent_highs = df['Close'][-30:].max()  # Local highs from the last 30 days
        rsi_trend = df['RSI'][-30:].mean()  # RSI trend over the last 30 days

        # Factor in RSI trend: higher RSI suggests stronger breakout potential
        if rsi_trend > 60:
            dynamic_multiplier = 1.05  # More aggressive breakout target
        elif rsi_trend > 50:
            dynamic_multiplier = 1.03  # Moderate breakout target
        else:
            dynamic_multiplier = 1.02  # Conservative breakout target

        potential_resistance = max(recent_highs, last_breakout * dynamic_multiplier)
        return potential_resistance

# Generate a report
def generate_report(breakouts, sell_points, next_breakout_level, ticker):
    if not breakouts:
        print(f"No significant breakouts found for {ticker}.")
        print(f"Potential breakout level: {next_breakout_level:.2f}")
    else:
        print(f"Breakout Analysis Report for {ticker}")
        print("-" * 50)
        print(f"{'Date':<15}{'Close Price':<15}{'RSI':<10}{'Volume':<15}{'20-SMA':<15}{'50-SMA':<15}")
        print("-" * 80)
        for breakout in breakouts:
            print(f"{breakout['Date'].strftime('%Y-%m-%d'):<15}{breakout['Close']:<15.2f}{breakout['RSI']:<10.2f}{breakout['Volume']:<15.0f}{breakout['20_SMA']:<15.2f}{breakout['50_SMA']:<15.2f}")
        print("-" * 50)
        print(f"Next breakout level: {next_breakout_level:.2f}")

    if sell_points:
        print(f"Sell Point Analysis for {ticker}")
        print("-" * 50)
        print(f"{'Date':<15}{'Close Price':<15}{'RSI':<10}{'Volume':<15}{'20-SMA':<15}{'50-SMA':<15}{'Reason':<20}")
        print("-" * 80)
        for sell in sell_points:
            print(f"{sell['Date'].strftime('%Y-%m-%d'):<15}{sell['Close']:<15.2f}{sell['RSI']:<10.2f}{sell['Volume']:<15.0f}{sell['20_SMA']:<15.2f}{sell['50_SMA']:<15.2f}{sell['Reason']:<20}")
        print("-" * 50)

# Main script
def main():
    print("Welcome to the Stock Breakout Analyzer")
    ticker = input("Enter the stock ticker: ").upper()
    print("Fetching data...")

    # Fetch historical data
    stock = yf.Ticker(ticker)
    df = stock.history(period='1mo', interval='30m')

    if df.empty:
        print(f"No data found for ticker {ticker}. Please check the ticker symbol.")
        return

    df = calculate_indicators(df)

    # Analyze breakouts and sell points
    print("Analyzing breakout and sell points...")
    breakouts, sell_points, next_breakout_level = analyze_breakouts_and_sells(df)

    # Generate report
    generate_report(breakouts, sell_points, next_breakout_level, ticker)

    # Optional: Plotting
    plt.figure(figsize=(14, 7))
    plt.plot(df.index, df['Close'], label='Close Price', alpha=0.7)
    plt.plot(df.index, df['20_SMA'], label='20-SMA', linestyle='--')
    plt.plot(df.index, df['50_SMA'], label='50-SMA', linestyle='--')

    if breakouts:
        for breakout in breakouts:
            plt.scatter(breakout['Date'], breakout['Close'], color='red', label='Breakout Point', zorder=5)

    if sell_points:
        for sell in sell_points:
            plt.scatter(sell['Date'], sell['Close'], color='blue', label='Sell Point', zorder=5)

    if next_breakout_level:
        plt.axhline(y=next_breakout_level, color='green', linestyle='--', label=f'Next Breakout Level ({next_breakout_level:.2f})')

    plt.title(f"{ticker} Stock Analysis with Breakout and Sell Points")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.grid()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()

import asyncio
import websockets
import json
from collections import deque
from sms import text
from datetime import datetime, timedelta
from pytz import timezone
from threeBar_yf import get_plays

# Define your API keys
API_KEY = 'PK7LFMKHJV2DVMR0CCWJ'
API_SECRET = 'ei1lIi6PdgsnBQgBoyqsRgdCUduW6wLZHOeoDpRY'
BASE_URL = 'wss://stream.data.alpaca.markets/v2/iex'  # Free tier live data
EST = timezone('US/Eastern')

# Async function to send text
async def send_text(symbol, message):
    await text(message)

def calculate_moving_average(prices, period):
    return sum(prices[-period:]) / period

def detect_crossover(ma_9, ma_20, previous_ma_9, previous_ma_20):
    return previous_ma_9 <= previous_ma_20 and ma_9 > ma_20

def can_send_text(symbol, last_text_sent_time):
    now = datetime.now(EST)
    if last_text_sent_time[symbol] is None:
        return True
    return (now - last_text_sent_time[symbol]) >= timedelta(minutes=5)

def should_close_connection():
    now = datetime.now(EST)
    return now.hour >= 20  # 8 PM EST or later

async def monitor_stocks(SYMBOLS):
    # Adjusted deque to store 21 values to cover current and previous MA calculations
    full_min_price_history = {symbol: deque(maxlen=21) for symbol in SYMBOLS}  # Stores the last 21 closing prices
    last_ma_values = {symbol: {'ma_9': None, 'ma_20': None} for symbol in SYMBOLS}  # Stores the last 9MA and 20MA values
    last_text_sent_time = {symbol: None for symbol in SYMBOLS}  # Stores the last time a text was sent for each symbol

    while True:  # Keep trying to reconnect on failure
        try:
            # Connect to the WebSocket
            async with websockets.connect(BASE_URL, timeout=10) as websocket:

                # Authenticate with your API keys
                auth_data = {
                    "action": "auth",
                    "key": API_KEY,
                    "secret": API_SECRET
                }
                await websocket.send(json.dumps(auth_data))

                # Subscribe to bar & trades data streams
                subscription = {
                    "action": "subscribe",
                    "bars": SYMBOLS,     # Subscribe to 1-minute bar data for calculating MAs
                    "trades": SYMBOLS    # Subscribe to real-time trade data for intra-minute monitoring
                }
                await websocket.send(json.dumps(subscription))

                # Continuously receive and update the latest prices from the WebSocket
                while True:
                    if should_close_connection():
                        print("It's 8 PM EST, closing connection...")
                        await websocket.close()
                        return  # Exit the function
                    
                    message = await websocket.recv()
                    data = json.loads(message)

                    # Process bar data
                    for item in data:
                        # 'T' indicates the type of message ('b' for bars)
                        if item.get('T') == 'b': 
                            print("closing data: ", item) 
                            symbol = item['S']  # 'S' is the symbol
                            close_price = item['c']  # 'c' is the closing price of the bar
                            
                            # Update the price history for the symbol
                            full_min_price_history[symbol].append(close_price)
                            
                            # If we have at least 9 prices, calculate the moving averages
                            if len(full_min_price_history[symbol]) >= 9:
                                ma_9 = calculate_moving_average(full_min_price_history[symbol], 9)
                                last_ma_values[symbol]['ma_9'] = ma_9

                                # If we have at least 21 prices, calculate the 20MA
                                if len(full_min_price_history[symbol]) >= 21:
                                    ma_20 = calculate_moving_average(full_min_price_history[symbol], 20)
                                    last_ma_values[symbol]['ma_20'] = ma_20

                                    # Check for the crossover condition (9MA crosses above 20MA)
                                    previous_ma_9 = sum(list(full_min_price_history[symbol])[-10:-1]) / 9
                                    previous_ma_20 = sum(list(full_min_price_history[symbol])[-21:-1]) / 20
                                    print(f"ma_9: {ma_9},  ma_20: {ma_20}, previous_ma_9: {previous_ma_9}, previous_ma_20: {previous_ma_20}")
                                    
                                    if detect_crossover(ma_9, ma_20, previous_ma_9, previous_ma_20):
                                        print(f"9MA has crossed above 20MA for {symbol} at price: {close_price}")
                                        # Check if we can send a text (at least 5 minutes have passed since the last text)
                                        if can_send_text(symbol, last_text_sent_time):
                                            await send_text(symbol, f"SEBSOCKET: {symbol} 9MA has crossed above 20MA at price: {close_price}")
                                            last_text_sent_time[symbol] = datetime.now(EST)  # Update the last sent time

                        # 't' for trade data (real-time updates)
                        elif item.get('T') == 't':  
                            print("real time data: ", item) 
                            symbol = item['S']
                            trade_price = item['p']

                            # Create a copy of full_min_price_history to simulate with the trade price
                            simulated_prices = deque(full_min_price_history[symbol])
                            simulated_prices.append(trade_price)

                            # Simulate 9MA and 20MA with the current trade price
                            if len(simulated_prices) >= 9:
                                simulated_ma_9 = calculate_moving_average(simulated_prices, 9)
                                if len(simulated_prices) >= 20:
                                    simulated_ma_20 = calculate_moving_average(simulated_prices, 20)

                                    # Check if there's an intra-minute crossover in the simulated MAs
                                    last_ma_9 = last_ma_values[symbol]['ma_9']
                                    last_ma_20 = last_ma_values[symbol]['ma_20']
                                    print(f" last_ma_9: {last_ma_9}, last_ma_20: {last_ma_20}")

                                    if detect_crossover(simulated_ma_9, simulated_ma_20, last_ma_9, last_ma_20):
                                        print(f"9MA is crossing above 20MA intra-minute for {symbol} at price: {trade_price}")
                                        if can_send_text(symbol, last_text_sent_time):
                                            await send_text(symbol, f"SEBSOCKET: {symbol} 9MA is crossing above 20MA at price: {trade_price}")
                                            last_text_sent_time[symbol] = datetime.now(EST)

                                    elif last_ma_9 >= last_ma_20 and simulated_ma_9 < simulated_ma_20:
                                        print(f"9MA is crossing below 20MA intra-minute for {symbol} at price: {trade_price}")
                                        if can_send_text(symbol, last_text_sent_time):
                                            await send_text(symbol, f"SEBSOCKET: {symbol} 9MA is crossing below 20MA at price: {trade_price}")
                                            last_text_sent_time[symbol] = datetime.now(EST)             
        except Exception as e:
            print(f"Unexpected error: {e}")
            print("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)  # Wait before reconnecting

if __name__ == "__main__":
    all_stocks = []
    plays_categories = get_plays()
    for category, stocks in plays_categories.items():
        all_stocks = all_stocks + stocks
    print("Collected all tickers: ", all_stocks)

    # Run the WebSocket connection monitoring today's briefing
    asyncio.run(monitor_stocks(all_stocks))

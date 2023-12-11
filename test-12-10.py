import yfinance as yf
from datetime import datetime, timedelta
from Discord import get_briefing
from sms import text
import time

last_text_time = {}  # Dictionary to keep track of last text time for each stock


def calculate_resistance(data):
    resistance_levels = []
    for i in range(2, len(data) - 2):
        if data['High'].iloc[i] > data['High'].iloc[i - 1] and data['High'].iloc[i] > data['High'].iloc[i + 1]:
            resistance_levels.append(data['High'].iloc[i])
    return resistance_levels

def get_stock_data_for_date(stock_symbol, date):
    date = datetime.strptime(date, '%Y-%m-%d')
    today = datetime.now()
    if (today - date).days > 60:
        print("Data for the requested date is not available within the last 60 days.")
        return None
    start_date = date.strftime('%Y-%m-%d')
    end_date = (date + timedelta(days=1)).strftime('%Y-%m-%d')
    stock_data = yf.download(stock_symbol, start=start_date, end=end_date, interval='5m')
    return stock_data

def check_latest_price_for_breakout(stock_symbol, date):
    stock_data = get_stock_data_for_date(stock_symbol, date)
    if stock_data is None or len(stock_data) == 0:
        return
    
    resistance_levels = calculate_resistance(stock_data)
    
    latest_price = stock_data.iloc[-1]['Close']  # Get the latest price
    
    breakout_message = False
    
    for level in resistance_levels:
        if (latest_price - level) / level > 0.03:
            average_volume = stock_data['Volume'].mean()
            current_volume = stock_data.iloc[-1]['Volume']
            
            if current_volume > 2.5 * average_volume:
                message=f"{stock_symbol} is breaking through resistance {round(level, 2)} by {round((latest_price - level) / level * 100, 2)}% and has unusual volume."
                if stock_symbol not in last_text_time or (datetime.now() - last_text_time[stock_symbol]).total_seconds() >= 600:
                    print(message)
                    text(message)
                    last_text_time[stock_symbol] = datetime.now()  # Update last text time
                    breakout_message = True
                    break  # Exit the loop after printing breakout message once
        
    if not breakout_message:
        print(f"{stock_symbol} hasn't broken any resistance levels.")

# Main  Execution
if __name__ == '__main__':
    
    curr_date = datetime.now().strftime('%Y-%m-%d')
    # curr_date = datetime.strptime('2023-12-06', '%Y-%m-%d').strftime('%Y-%m-%d')

    # Morning briefing
    try:
        resistances, supports, retail, alarm_plays = get_briefing(curr_date)  # get briefing
        alarm_plays=[stock for stock in alarm_plays if ' ' not in stock]
        supports=list(supports.keys())

        print("today's alarm_plays: ", alarm_plays )
        print("today's retail: ", retail)
        print("today's supports: ", supports)
    except Exception as e:
        print(f"unable to get briefing or some error: {e}")

    # Minute iteration
    try:
        while True:
            print("checking stocks!")
            for stock in supports + alarm_plays:
                try:
                    check_latest_price_for_breakout(stock, curr_date)
                except Exception as e:
                    print(f"unable to check {stock} and error: {e}")
            print("sleeping a minute")
            time.sleep(60)
    except Exception as e:
        print("unable to minute iterate with error: ", e)
    


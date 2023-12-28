import yfinance as yf
from datetime import datetime, timedelta
from Discord import get_briefing
from sms import text
import time

last_text_time = {}  # Dictionary to keep track of last text time for each stock


def calculate_resistance(data):
    resistance_levels = []
    for i in range(1, len(data) - 1):
        if data['Close'].iloc[i] > data['Close'].iloc[i - 1] and data['Close'].iloc[i] > data['Close'].iloc[i + 1]:
            resistance_levels.append(data['Close'].iloc[i])
    
    return resistance_levels


def get_stock_data_for_date(stock_symbol):
    # Get the current date
    current_date = datetime.now().date().strftime('%Y-%m-%d')

    # Fetch the data
    data = yf.download(stock_symbol, start=current_date, interval='2m')
    data['Percent Change'] = data['Close'].pct_change() * 100
    print(f"data for {stock_symbol}:", data)

    return data


def check_latest_price_for_breakout(stock_symbol,  stock_type):
    stock_data = get_stock_data_for_date(stock_symbol)
    if stock_data is None or len(stock_data) == 0:
        return
    
    resistance_levels = calculate_resistance(stock_data)
    print(f"{stock_symbol} - resistance levels: {resistance_levels}")
    
    open_latest_price = stock_data.iloc[-1]['Open']
    close_latest_price = stock_data.iloc[-1]['Close']
    average_volume = stock_data['Volume'].mean()
    current_volume = stock_data.iloc[-1]['Volume']
    Percent_change = round(stock_data.iloc[-1]['Percent Change'],2)
    
    breakout_message = False
    
    for level in resistance_levels:
        if (close_latest_price - level) / level > 0.03 and open_latest_price<level:
            print(f"{stock_symbol} moving up by {Percent_change}% and broke resistance {level}")
            
            
            
            if current_volume > 2.5 * average_volume:
                print(f"{stock} breaking out!")
                message=f"{stock_type} - {stock_symbol} is breaking through resistance {round(level, 2)} by {round((close_latest_price - level) / level * 100, 2)}% and has unusual volume."
                # if stock_symbol not in last_text_time or (datetime.now() - last_text_time[stock_symbol]).total_seconds() >= 600:
                print("texting:",message)
                text(message)
                last_text_time[stock_symbol] = datetime.now()  # Update last text time
                breakout_message = True
                break  # Exit the loop after printing breakout message once
    if current_volume > 2.5 * average_volume and not breakout_message:
        message=f"{stock_type} - {stock_symbol} has{round((current_volume-average_volume)/current_volume*100,2)}% unusual volume."
        text(message)
        


# Main  Execution
def run_main():
    print("running main")
    
    curr_date = datetime.now().strftime('%Y-%m-%d')
    # curr_date = datetime.strptime('2023-12-06', '%Y-%m-%d').strftime('%Y-%m-%d')

    # Morning briefing
    try:
        resistances, supports, retail, alarm_plays = get_briefing(curr_date)  # get briefing
        alarm_plays=[stock for stock in alarm_plays if ' ' not in stock]
        supports=list(supports.keys())
        other_on_radar=['SLNH']

        print("today's alarm_plays: ", alarm_plays )
        print("today's retail: ", retail)
        print("today's supports: ", supports)
    except Exception as e:
        time.sleep(300)  # Sleep for 5 minutes
        print(f"unable to get briefing or some error: {e}")
        run_main()

    # Minute iteration
    try:
        while True:
            print("checking stocks!")
            for stock in supports + alarm_plays+other_on_radar:
                try:
                    if stock in supports:
                        check_latest_price_for_breakout(stock,  'NORMAL PLAY')
                    elif stock in alarm_plays:
                        check_latest_price_for_breakout(stock, 'ALARM PLAY')
                    elif stock in other_on_radar:
                        check_latest_price_for_breakout(stock, 'OTHER ON RADAR')
                except Exception as e:
                    print(f"unable to check {stock} and error: {e}")
            print("Iteration complete - sleeping a minute")
            time.sleep(60)
    except Exception as e:
        print("unable to minute iterate with error: ", e)

if __name__ == '__main__':
    run_main()
    


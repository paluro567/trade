import yfinance as yf
from datetime import datetime, timedelta
from Discord import get_briefing
from sms import text
import time

texted_plays = {}  # keep track of how many texts sent for a ticker


def get_data(ticker):
    current_date = datetime.now().date().strftime('%Y-%m-%d')
    data=yf.download(ticker, start=current_date, interval='2m')
    data['Percent_Change'] = data['Close'].pct_change() * 100
    return data


def check_conditions(ticker, play_type):
    stock_data=get_data(ticker)
    latest_data = stock_data.iloc[-1]
    avg_volume = stock_data['Volume'].mean()
    volume_diff = (latest_data['Volume'] - avg_volume)/avg_volume
    latest_price_change = latest_data['Percent_Change']

    if volume_diff>2.5 and latest_price_change > 3 and (ticker not in texted_plays or texted_plays[ticker] < 2):
        message=f"{play_type} - {ticker} is moving up by {latest_price_change}% with {round(volume_diff,2)}% average volume"
        print(f"texting - {message}")
        text(message)

        # record ticker as being texted
        texted_plays[ticker] = texted_plays.get(ticker, 0) + 1
    else:
        print(f"{ticker} has not broken out")



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
                        check_conditions(stock,  'NORMAL PLAY')
                    elif stock in alarm_plays:
                        check_conditions(stock, 'ALARM PLAY')
                    elif stock in other_on_radar:
                        check_conditions(stock, 'OTHER ON RADAR')
                except Exception as e:
                    print(f"unable to check {stock} and error: {e}")
            print("Iteration complete - sleeping a minute")
            time.sleep(60)
    except Exception as e:
        print("unable to minute iterate with error: ", e)
        time.sleep(3600) # 1 hour sleep
        run_main()

if __name__ == '__main__':
    run_main()

        
    

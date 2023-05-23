import yfinance as yf
import talib
import datetime
from datetime import date
from Discord import get_briefing

trades={}
tot_percent=0
monday="2023-03-27"
tuesday="2023-03-28"
wednesday="2023-03-29"
thursday="2023-03-30"
friday="2023-03-31"
week=[monday, tuesday, wednesday, thursday, friday]

# each day of the week
for day in week:

    print("---------------------current day: ",day)
    try:
        # get the day's briefing
        resistances, supports, retail, alarm_plays = get_briefing(day) 
        print(f"resistances:{resistances}")
        print(f"supports:{supports}")
        print(f"retail:{retail}")
        print(f"alarm_plays:{alarm_plays}")
        day_plays=set(list(resistances.keys())+retail+alarm_plays)
        print("day plays:", day_plays)
    except Exception as e:
        print("exception is: ",e)

    # check each symbol for the day
    for symbol in day_plays:
        print(f"currrent symbol: {symbol}")

        trades[symbol]=[] #init trades array
        

        # Dates
        start_date = "2023-03-31"
        end_date = "2023-0-01"
        
        # RSI thresholds
        rsi_low = 40
        rsi_high = 70


        # Download the stock price data using yfinance
        data = yf.download(symbol, start=day, interval="5m", prepost=True)

        # Calculate the RSI using the TA-Lib library
        rsi = talib.RSI(data["Close"], timeperiod=14)
        print(rsi)
        bought=False

        # Iterate over each row in the DataFrame and print out whether the RSI was above or below the specified thresholds
        for i, row in data.iterrows():

            #initializa prev_rsi value
            if  'prev_rsi' not in locals():
                prev_rsi = rsi.loc[i]

            
            # risk management
            if bought and rsi.loc[i]<prev_rsi-5:
                bought=False #selling out of position
                sell_price=row['Close']
                trade_percent=round((sell_price-buy_price)/buy_price*100,2)
                tot_percent+=trade_percent
                trades[symbol].append((buy_price, sell_price,trade_percent))
                break
            prev_rsi=rsi.loc[i]


            if rsi.loc[i] < rsi_low and not bought:
                bought=True
                buy_price=row['Close']
                print(f"BUY at price: {buy_price}")
                print(f"The RSI for {symbol} at {i} was {rsi.loc[i]}, which is below the low threshold of {rsi_low}.")
            
            elif rsi.loc[i] > rsi_high and bought:
                bought=False #selling out of position
                sell_price=row['Close']
                trade_percent=round((sell_price-buy_price)/buy_price*100,2)
                tot_percent+=trade_percent
                trades[symbol].append((buy_price, sell_price,trade_percent))
                print(f"percent made is: {trade_percent}%")
                print(f"SELL at price: {sell_price}")
                print(f"The RSI for {symbol} at {i} was {rsi.loc[i]}, which is above the high threshold of {rsi_high}.")
            last_price=row['Close']
            
        #if still in a position => sell out
        if bought:
            trade_percent=round((last_price-buy_price)/buy_price*100,2)
            tot_percent+=trade_percent
            trades[symbol].append((buy_price, sell_price,trade_percent))


    for play in trades: 
        print(f"------- {play} trades -----------")
        for i, trade in enumerate(trades[play]):
            print(f"trade #{i+1}")
            print(f"bought:{trade[0]}")
            print(f"sell:{trade[1]}")
            print(f"percent made:{trade[2]}%")

    print(f"total percent made{tot_percent}")

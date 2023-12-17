from datetime import datetime, timedelta
import time

stock_symbol='test'
last_text_time={}
while True:
    if stock_symbol not in last_text_time or (datetime.now() - last_text_time[stock_symbol]).total_seconds() >= 5:
        last_text_time[stock_symbol] = datetime.now()
        print("time:", datetime.now())
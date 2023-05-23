import pandas_market_calendars as mcal
from datetime import date
today = str(date.today())
nyse = mcal.get_calendar('NYSE')
nyse.valid_days(start_date=today, end_date=today)
print(DatetimeIndex(nyse))
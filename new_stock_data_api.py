# Alpha vantage API test api key 1O6HCJLDSBUK02HK
import pandas as pandas
from alpha_vantage.timeseries import TimeSeries
import time
api_key='1O6HCJLDSBUK02HK'


# ts = TimeSeries(key=api_key, output_format='pandas')  # Adjust output_format as needed ('json' or 'csv')
# data, meta_data=ts.get_intraday(symbol='CCCC', interval=)

# curr_date = datetime.strptime('2023-12-14', '%Y-%m-%d').strftime('%Y-%m-%d')
ts = TimeSeries(key=api_key, output_format='pandas')  # Adjust output_format as needed ('json' or 'csv')

specific_date='2023-12-14'

data, meta_data = ts.get_intraday(symbol='cccc', interval='5min', outputsize='full')
specific_day_data = data.loc[specific_date]
print("data: ", specific_day_data)

price_930 = specific_day_data.at[specific_date + ' 09:35:00', '1. open']
if not price_930:
    print("Price at 9:30 AM is not available.")
else:
    print(f"The price at 9:30 AM on {specific_date} was: {price_930}")
#pip install numpy
import numpy as np

#pip install matplotlib.pyplot
import matplotlib.pyplot as plt

#pip installpandas
import pandas as pd

#pip install pandas_datareader
import pandas pandas_datareader as web

import yfinance as yf


from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, LSTM

# Load Data
ticker_yahoo = yf.Ticker(ticker)
data = ticker_yahoo.history(period='1d', interval='1m')
#data['Close']

# Prepare Data (convert the prices to a range of (0,1)
scaler= MinMaxScaler(feature_range=(0,1))
scaled_data=scaler.fit_transform(data['Close'].values)

#how many days to base prediction on?
prediction_days = 60

x_train=[]
y_train=[]

for x in range(prediction_days, len(scaled_data)):
    x_train.append(scaled_data[x-prediction_days:x,0])
    y_train.append(scaled_data[x,0])

x_train = np.array(x_train), np.array(y_train)
y_train = np.reshape(x_train,(x_train.shape[0],x_train))



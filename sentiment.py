import yfinance as yf
import datetime

from datetime import datetime, timedelta
from revised_discord import get_briefing
from sms import text
import pandas as pd
import numpy as np
import time
import requests
from alpaca import place_buy, place_sell
import multiprocessing
from alpha_vantage.timeseries import TimeSeries
import ta


# constants
API_KEY  =  'XB2M6HD2DQMJA5Z1'


def get_sentiment(stock,  date=None):
    
    #Alpha Vantage GET request
    stock=stock.upper()
    url=f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={stock}&apikey={API_KEY}"
    r = requests.get(url)
    data = r.json()

    print(data.keys())
    print("items is ", data['items'])
    print("sentiment_score_definition is ", data['sentiment_score_definition'])
    print("relevance_score_definition is ", data['relevance_score_definition'])
    # print("feed is ", data['feed'])
    count=0
    sentiment_scores = [feed_item['overall_sentiment_score'] for feed_item in data['feed']]
    average_sentiment = sum(sentiment_scores) / len(sentiment_scores)

    # Define threshold values for sentiment categories
    bearish_threshold = -0.35
    somewhat_bearish_upper = -0.15
    neutral_upper_threshold = 0.15
    bullish_threshold = 0.35

    # Determine the category based on the average sentiment score
    if average_sentiment <= bearish_threshold:
        sentiment_category = "Bearish"
    elif bearish_threshold < average_sentiment <= somewhat_bearish_upper:
        sentiment_category = "Somewhat Bearish"
    elif somewhat_bearish_upper < average_sentiment < neutral_upper_threshold:
        sentiment_category = "Neutral"
    elif neutral_upper_threshold <= average_sentiment < bullish_threshold:
        sentiment_category = "Somewhat Bullish"
    elif bullish_threshold <= average_sentiment:
        sentiment_category = "Bullish"
    else:
        sentiment_category = "Invalid Score"

    # print(f"Average Overall Sentiment Score: {average_sentiment}")
    print(f"{stock} Sentiment Category: {sentiment_category}")

    return average_sentiment



def sort_stocks_by_sentiment(stocks):
    sentiment_scores = {}
    
    # Calculate sentiment scores for each stock
    for stock in stocks:
        sentiment_scores[stock] = get_sentiment(stock)
    
    # Sort stocks by sentiment value in descending order
    sorted_stocks = sorted(sentiment_scores.items(), key=lambda x: x[1], reverse=True)
    
    return sorted_stocks

if __name__  ==  '__main__':
    # while True:
    #     stock = input("enter stock: ")
    #     get_sentiment(stock,  date=None)
    stocks=['pltr','nvda', 'pypl','baba', 'amzn', 'tsla', 'bbai']
    
    # Sort stocks by sentiment value in descending order
    sorted_stocks = sort_stocks_by_sentiment(stocks)


    # Print sorted stocks and their sentiment values
    for stock, sentiment in sorted_stocks:
        print(f'{stock}: {round(sentiment,2)}')




















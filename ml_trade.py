import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from imblearn.over_sampling import SMOTE
from datetime import datetime, timedelta
import pickle  # For saving and loading the model

# Features for model training
features = ['MA_20', 'MA_50', 'MA_200', 'RSI', 'Price_Change', 'Volume_Change', 'Volume_Relative']

def fetch_stock_data(tickers, start_date, end_date):
    """
    Fetch stock data for the given tickers and date range.
    """
    data = []
    for ticker in tickers:
        print(f"Fetching data for {ticker}...")
        df = yf.download(ticker, start=start_date, end=end_date)
        if df.empty:
            print(f"Warning: No data found for {ticker}. Skipping.")
            continue
        df['Ticker'] = ticker
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
        if 'Volume' not in df.columns:
            print(f"Warning: 'Volume' column missing for {ticker}. Filling with zeros.")
            df['Volume'] = 0
        data.append(df)
    if not data:
        raise ValueError("No valid data fetched for the provided tickers.")
    return pd.concat(data)

def add_technical_indicators(df):
    """
    Add moving averages, RSI, and volume-based indicators.
    """
    required_columns = {'Ticker', 'Close', 'Volume'}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"Input DataFrame must contain columns: {required_columns}")
    df = df.groupby('Ticker').apply(add_indicators_to_group)
    df.dropna(inplace=True)
    return df

def add_indicators_to_group(group):
    """
    Compute indicators for each group of stock data.
    """
    group['MA_20'] = group['Close'].rolling(window=20).mean()
    group['MA_50'] = group['Close'].rolling(window=50).mean()
    group['MA_200'] = group['Close'].rolling(window=200).mean()
    group['RSI'] = compute_rsi(group['Close'])
    group['Price_Change'] = group['Close'].pct_change()
    group['Volume_Change'] = group['Volume'].pct_change()
    group['Volume_MA_20'] = group['Volume'].rolling(window=20).mean()
    group['Volume_Relative'] = group['Volume'] / group['Volume_MA_20']
    return group

def compute_rsi(series, period=14):
    """
    Compute Relative Strength Index (RSI).
    """
    delta = series.diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def prepare_training_data(df, profit_threshold=0.02, holding_period=3):
    """
    Prepare training features and labels.
    """
    df['Buy_Signal'] = (
        (df['MA_20'] > df['MA_50']) &
        (df['MA_20'].shift(1) <= df['MA_50'].shift(1)) &
        (df['Volume_Relative'] > 1.1)
    )
    df['Buy_Signal'] = df['Buy_Signal'].astype(int)
    df['Profit_Percentage'] = (df['Close'].shift(-holding_period) - df['Close']) / df['Close']
    df['Effective_Signal'] = np.where(df['Profit_Percentage'] > profit_threshold, 1, 0).astype(int)

    X = df[features]
    y = df['Effective_Signal']
    print("Class distribution before balancing:")
    print(y.value_counts())
    return X, y

def balance_data(X, y):
    """
    Balance classes using SMOTE.
    """
    if len(np.unique(y)) > 1:  # Apply SMOTE only if both classes are present
        smote = SMOTE(random_state=42, k_neighbors=min(5, sum(y == 1) - 1))
        X_resampled, y_resampled = smote.fit_resample(X, y)
        print("Class distribution after balancing:")
        print(pd.Series(y_resampled).value_counts())
        return X_resampled, y_resampled
    else:
        print("Skipping SMOTE: Not enough minority class samples.")
        return X, y

def train_model(X_train, y_train):
    """
    Train the Random Forest classifier.
    """
    model = RandomForestClassifier(class_weight={0: 1, 1: 10}, random_state=42)
    model.fit(X_train, y_train)
    return model

def predict_buy_signals(model, df):
    """
    Predict buy signals on new data.
    """
    if df.empty or len(df) < 200:  # Ensure sufficient data for all indicators
        raise ValueError("Insufficient data for predictions. Ensure enough historical data is available.")
    predictions = model.predict(df[features])
    df['Buy_Prediction'] = predictions
    return df[df['Buy_Prediction'] == 1]

def adjust_to_last_business_day(date):
    """
    Adjust the given date to the last business day.
    """
    date = pd.to_datetime(date)
    while date.weekday() >= 5:  # Saturday = 5, Sunday = 6
        date -= pd.Timedelta(days=1)
    return date.strftime('%Y-%m-%d')
if __name__ == "__main__":
    model_filename = "stock_model.pkl"
    today = datetime.today()
    two_years_ago = today - timedelta(days=730)  # Fetch 2 years of data for indicators
    prediction_start_date = adjust_to_last_business_day((today - timedelta(days=365)).strftime('%Y-%m-%d'))

    prediction_end_date = adjust_to_last_business_day(today.strftime('%Y-%m-%d'))

    mode = input("Enter 't' (train) to train the model or 'p' (predict): ").strip().lower()

    if mode == "p":
        tickers = input("Enter tickers for prediction (comma-separated): ").split(',')
        try:
            with open(model_filename, "rb") as file:
                model = pickle.load(file)
            print("Model loaded successfully.")
        except FileNotFoundError:
            print("No model found. Train the model first.")
            exit()

        for ticker in tickers:
            try:
                # Fetch longer historical data for prediction
                prediction_data = fetch_stock_data([ticker], prediction_start_date, prediction_end_date)
                prediction_data = add_technical_indicators(prediction_data)

                if prediction_data.empty or len(prediction_data) < 200:
                    print(f"Not enough data to calculate indicators for {ticker}. Skipping.")
                    continue

                buy_signals = predict_buy_signals(model, prediction_data)
                if buy_signals.empty:
                    print(f"No buy signals identified for {ticker}.")
                else:
                    print(f"Buy signals identified for {ticker}:")
                    print(buy_signals[['Ticker', 'Close', 'Buy_Prediction']])
            except ValueError as e:
                print(f"Error during prediction for {ticker}: {e}")
    else:
        print("Invalid mode. Please enter 't' or 'p'.")

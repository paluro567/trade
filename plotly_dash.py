from dash import Dash, dcc, html, Input, Output, State, callback_context
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

# Initialize Dash app
app = Dash(__name__)
app.title = "Stock Analysis Dashboard"

# Store tickers in memory
added_tickers = []

# Default options for period, interval, and RSI thresholds
default_period = '1mo'
default_interval = '30m'
default_overbought = 70
default_oversold = 30

# Function to calculate RSI
def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Fetch stock data and calculate RSI
def fetch_stock_chart(ticker, period, interval):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period, interval=interval)
        if not data.empty:
            data['RSI'] = calculate_rsi(data)
        return data
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

# Fetch P/E ratios
def fetch_pe_ratios(tickers):
    def fetch_single_pe(ticker):
        try:
            stock = yf.Ticker(ticker)
            return {
                'current': stock.info.get('trailingPE', None),
                'forward': stock.info.get('forwardPE', None)
            }
        except Exception as e:
            print(f"Error fetching P/E ratios for {ticker}: {e}")
            return {'current': None, 'forward': None}

    pe_ratios = {}
    with ThreadPoolExecutor() as executor:
        results = executor.map(fetch_single_pe, tickers)
    for ticker, ratios in zip(tickers, results):
        pe_ratios[ticker] = ratios
    return pe_ratios

# Layout
app.layout = html.Div([
    html.H1("Stock Analysis Dashboard", style={'textAlign': 'center'}),
    html.Div([
        html.Label("Enter a Stock Ticker:"),
        dcc.Input(
            id='ticker-input', type='text', placeholder='e.g., AAPL',
            style={'width': '50%', 'padding': '10px'}
        ),
        html.Button('Add Ticker', id='add-button', n_clicks=0,
                    style={'marginLeft': '10px', 'backgroundColor': 'blue', 'color': 'white'}),
    ], style={'textAlign': 'center', 'marginBottom': '10px'}),

    html.Div([
        html.Label("Added Tickers:"),
        dcc.Checklist(
            id='ticker-checklist',
            options=[], value=[],
            style={'maxHeight': '200px', 'overflowY': 'auto'}
        ),
        html.Button('Remove Selected Tickers', id='remove-button', n_clicks=0,
                    style={'marginTop': '10px', 'backgroundColor': 'red', 'color': 'white'}),
    ], style={'textAlign': 'center'}),

    html.Div([
        html.Label("Select Period:"),
        dcc.Dropdown(
            id='period-dropdown',
            options=[{'label': p, 'value': p} for p in ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']],
            value=default_period, style={'width': '50%', 'margin': 'auto'}
        ),
        html.Label("Select Interval:"),
        dcc.Dropdown(
            id='interval-dropdown',
            options=[{'label': i, 'value': i} for i in ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo']],
            value=default_interval, style={'width': '50%', 'margin': 'auto'}
        ),
        html.Label("RSI Overbought Threshold:"),
        dcc.Input(id='overbought-input', type='number', value=default_overbought),
        html.Label("RSI Oversold Threshold:"),
        dcc.Input(id='oversold-input', type='number', value=default_oversold),
    ], style={'textAlign': 'center'}),

    html.Button('Plot All Tickers', id='plot-button', n_clicks=0,
                style={'marginTop': '20px', 'backgroundColor': 'green', 'color': 'white'}),
    html.Div(id='pe-output-div', style={'marginTop': '20px'}),
    html.Div(id='rsi-output-div', style={'marginTop': '20px'})
])

# Callbacks
@app.callback(
    [Output('ticker-checklist', 'options'), Output('ticker-input', 'value')],
    [Input('add-button', 'n_clicks'), Input('ticker-input', 'n_submit'), Input('remove-button', 'n_clicks')],
    [State('ticker-input', 'value'), State('ticker-checklist', 'value')]
)
def modify_ticker_list(add_clicks, n_submit, remove_clicks, ticker_to_add, selected_tickers):
    ctx = callback_context
    if not ctx.triggered:
        return [{'label': ticker, 'value': ticker} for ticker in added_tickers], ''

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id in ['add-button', 'ticker-input'] and ticker_to_add:
        ticker_to_add = ticker_to_add.strip().upper()
        if ticker_to_add and ticker_to_add not in added_tickers:
            added_tickers.append(ticker_to_add)

    if triggered_id == 'remove-button' and selected_tickers:
        for ticker in selected_tickers:
            if ticker in added_tickers:
                added_tickers.remove(ticker)

    return [{'label': ticker, 'value': ticker} for ticker in added_tickers], ''

@app.callback(
    [Output('pe-output-div', 'children'), Output('rsi-output-div', 'children')],
    [Input('plot-button', 'n_clicks')],
    [State('period-dropdown', 'value'), State('interval-dropdown', 'value'),
     State('overbought-input', 'value'), State('oversold-input', 'value')]
)
def generate_plots(plot_clicks, period, interval, overbought, oversold):
    if plot_clicks == 0 or not added_tickers:
        return None, None

    pe_ratios = fetch_pe_ratios(added_tickers)
    pe_fig = go.Figure()
    for ticker, ratios in pe_ratios.items():
        pe_fig.add_trace(go.Bar(name=f"{ticker} Current", x=[ticker], y=[ratios['current']], marker_color='blue'))
        pe_fig.add_trace(go.Bar(name=f"{ticker} Forward", x=[ticker], y=[ratios['forward']], marker_color='orange'))
    pe_fig.update_layout(title="P/E Ratios", barmode='group')

    rsi_figs = []
    for ticker in added_tickers:
        data = fetch_stock_chart(ticker, period, interval)
        if data is not None:
            color = data['RSI'].apply(lambda x: 'red' if x > overbought else 'green' if x < oversold else 'blue')
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=data.index, y=data['Close'], line=dict(color='blue')))
            fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='markers', marker=dict(color=color)))
            fig.update_layout(title=f"{ticker} RSI Analysis")
            rsi_figs.append(dcc.Graph(figure=fig))

    return dcc.Graph(figure=pe_fig), rsi_figs

# Run app
if __name__ == '__main__':
    app.run_server(debug=True)

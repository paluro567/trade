from dash import Dash, dcc, html, Input, Output, State, callback_context
import yfinance as yf
import plotly.graph_objects as go

# Initialize Dash app
app = Dash(__name__)
app.title = "P/E Comparison & RSI Analysis"

# Store tickers in a global list
added_tickers = []

# Default options for period and interval
default_period = '1mo'
default_interval = '30m'

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

# Fetch stock chart data and RSI
def fetch_stock_chart(ticker, period, interval):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period, interval=interval)
        data['RSI'] = calculate_rsi(data)
        return data
    except Exception as e:
        print(f"Error fetching chart data for {ticker}: {e}")
        return None

# Fetch P/E ratios from yfinance
def fetch_pe_ratios(tickers):
    pe_ratios = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            current_pe = stock.info.get('trailingPE', None)
            forward_pe = stock.info.get('forwardPE', None)
            pe_ratios[ticker] = {'current': current_pe, 'forward': forward_pe}
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            pe_ratios[ticker] = {'current': None, 'forward': None}
    return pe_ratios

# Layout of the app
app.layout = html.Div([
    html.H1("Stock Analysis Dashboard", style={'textAlign': 'center'}),
    html.Div([
        html.Label("Enter a Stock Ticker:", style={'fontSize': '16px'}),
        dcc.Input(
            id='ticker-input',
            type='text',
            placeholder='e.g., AAPL',
            style={'width': '50%', 'padding': '10px', 'fontSize': '14px'}
        ),
        html.Button('Add Ticker', id='add-button', n_clicks=0,
                    style={'marginLeft': '10px', 'backgroundColor': 'blue', 'color': 'white', 'border': 'none', 'padding': '10px'}),
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),
    html.Div([
        html.H3("Added Tickers", style={'textAlign': 'center', 'marginBottom': '10px'}),
        dcc.Checklist(
            id='ticker-checklist',
            options=[],
            value=[],
            style={
                'border': '1px solid #ccc',
                'padding': '10px',
                'borderRadius': '5px',
                'backgroundColor': '#f9f9f9',
                'maxHeight': '200px',
                'overflowY': 'auto',
                'textAlign': 'left',
                'fontSize': '14px'
            }
        )
    ], style={'marginBottom': '20px'}),
    html.Button('Remove Selected Tickers', id='remove-button', n_clicks=0,
                style={'marginTop': '10px', 'backgroundColor': 'red', 'color': 'white', 'border': 'none', 'padding': '10px'}),
    html.Div([
        html.Label("Select Period:", style={'fontSize': '16px'}),
        dcc.Dropdown(
            id='period-dropdown',
            options=[
                {'label': p, 'value': p} for p in ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
            ],
            value=default_period,
            style={'width': '50%', 'margin': '0 auto'}
        ),
        html.Label("Select Interval:", style={'fontSize': '16px', 'marginTop': '10px'}),
        dcc.Dropdown(
            id='interval-dropdown',
            options=[
                {'label': i, 'value': i} for i in ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo']
            ],
            value=default_interval,
            style={'width': '50%', 'margin': '10px auto'}
        ),
        html.Label("Set RSI Thresholds:", style={'fontSize': '16px', 'marginTop': '10px'}),
        dcc.Input(id='lower-threshold', type='number', value=30, placeholder='Lower RSI Threshold',
                  style={'marginRight': '10px', 'padding': '5px', 'fontSize': '14px'}),
        dcc.Input(id='upper-threshold', type='number', value=70, placeholder='Upper RSI Threshold',
                  style={'padding': '5px', 'fontSize': '14px'})
    ], style={'marginTop': '20px', 'textAlign': 'center'}),
    html.Button('Plot All Tickers', id='plot-button', n_clicks=0,
                style={'marginTop': '20px', 'backgroundColor': 'green', 'color': 'white', 'border': 'none', 'padding': '10px'}),
    html.Div(id='pe-output-div', style={'marginTop': '20px'}),  # P/E Comparison Section
    html.Div(id='rsi-output-div', style={'marginTop': '20px'})  # RSI Output Section
])

# Callback to update the ticker list and remove selected tickers
@app.callback(
    Output('ticker-checklist', 'options'),
    [Input('add-button', 'n_clicks'), Input('remove-button', 'n_clicks')],
    [State('ticker-input', 'value'), State('ticker-checklist', 'value')]
)
def update_ticker_list(add_clicks, remove_clicks, ticker_to_add, selected_tickers):
    ctx = callback_context
    if not ctx.triggered:
        return [{'label': ticker, 'value': ticker} for ticker in added_tickers]

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'add-button' and ticker_to_add:
        ticker_to_add = ticker_to_add.strip().upper()
        if ticker_to_add and ticker_to_add not in added_tickers:
            added_tickers.append(ticker_to_add)

    if triggered_id == 'remove-button' and selected_tickers:
        for ticker in selected_tickers:
            if ticker in added_tickers:
                added_tickers.remove(ticker)

    return [{'label': ticker, 'value': ticker} for ticker in added_tickers]

# Callback to plot P/E and RSI data
@app.callback(
    [Output('pe-output-div', 'children'), Output('rsi-output-div', 'children')],
    [
        Input('plot-button', 'n_clicks'),
        State('period-dropdown', 'value'),
        State('interval-dropdown', 'value'),
        State('lower-threshold', 'value'),
        State('upper-threshold', 'value')
    ]
)
def plot_data(n_clicks, period, interval, lower_threshold, upper_threshold):
    if n_clicks > 0 and added_tickers:
        # Fetch P/E Ratios
        pe_ratios = fetch_pe_ratios(added_tickers)
        current_pe_values = [pe_ratios[ticker]['current'] for ticker in added_tickers]
        forward_pe_values = [pe_ratios[ticker]['forward'] for ticker in added_tickers]

        pe_fig = go.Figure()
        pe_fig.add_trace(go.Bar(
            x=added_tickers,
            y=current_pe_values,
            name='Current P/E',
            marker_color='blue'
        ))
        pe_fig.add_trace(go.Bar(
            x=added_tickers,
            y=forward_pe_values,
            name='Forward P/E',
            marker_color='green'
        ))
        pe_fig.update_layout(
            title="Current vs Forward P/E Comparison",
            xaxis_title="Tickers",
            yaxis_title="P/E Ratio",
            barmode='group',
            template='plotly_white'
        )

        # Fetch and Plot RSI Charts
        rsi_figures = []
        for ticker in added_tickers:
            data = fetch_stock_chart(ticker, period, interval)
            if data is not None:
                fig = go.Figure()
                for i in range(1, len(data)):
                    color = (
                        'green' if data['RSI'].iloc[i] < lower_threshold else
                        'red' if data['RSI'].iloc[i] > upper_threshold else
                        'blue'
                    )
                    fig.add_trace(go.Scatter(
                        x=data.index[i-1:i+1],
                        y=data['Close'].iloc[i-1:i+1],
                        mode='lines',
                        line=dict(color=color),
                        showlegend=False
                    ))
                fig.update_layout(
                    title=f"{ticker} - {interval} Chart with RSI",
                    xaxis_title="Time",
                    yaxis_title="Price",
                    template='plotly_white'
                )
                rsi_figures.append(dcc.Graph(figure=fig))

        # Combine Outputs
        return dcc.Graph(figure=pe_fig), html.Div(rsi_figures)
    return "No tickers to plot.", "No tickers to plot."

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

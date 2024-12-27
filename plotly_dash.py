from dash import Dash, dcc, html, Input, Output, State, callback_context, dash_table
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

# Fetch financial metrics
def fetch_financial_metrics(tickers):
    metrics = {
        "Metric": ["PEG Ratio", "Free Cash Flow Yield", "Price to Book", "Return on Equity"]
    }
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            metrics[ticker] = [
                info.get("pegRatio", "N/A"),                  # PEG Ratio
                info.get("freeCashflow", "N/A"),              # Free Cash Flow
                info.get("priceToBook", "N/A"),               # Price to Book
                info.get("returnOnEquity", "N/A")             # Return on Equity
            ]
        except Exception as e:
            print(f"Error fetching financial metrics for {ticker}: {e}")
            metrics[ticker] = ["N/A"] * 4  # Fallback in case of error

    return metrics

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
            style={
                'display': 'flex',
                'flexDirection': 'column',
                'border': '1px solid #ccc',
                'padding': '10px',
                'borderRadius': '5px',
                'backgroundColor': '#f9f9f9',
                'maxHeight': '200px',
                'overflowY': 'auto',
                'textAlign': 'left',
                'fontSize': '14px',
                'width': '300px',
                'margin': '0 auto'
            }
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
    html.Div(id='rsi-output-div', style={'marginTop': '20px'}),
    html.Div(id='financial-metrics-div', style={'marginTop': '20px'})
])

# Callback to modify ticker list
@app.callback(
    [Output('ticker-checklist', 'options'), Output('ticker-input', 'value')],
    [Input('add-button', 'n_clicks'), Input('remove-button', 'n_clicks')],
    [State('ticker-input', 'value'), State('ticker-checklist', 'value')]
)
def modify_ticker_list(add_clicks, remove_clicks, ticker_to_add, selected_tickers):
    ctx = callback_context
    if not ctx.triggered:
        return [{'label': ticker, 'value': ticker} for ticker in added_tickers], ''

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'add-button' and ticker_to_add:
        ticker_to_add = ticker_to_add.strip().upper()
        if ticker_to_add and ticker_to_add not in added_tickers:
            added_tickers.append(ticker_to_add)

    if triggered_id == 'remove-button' and selected_tickers:
        for ticker in selected_tickers:
            if ticker in added_tickers:
                added_tickers.remove(ticker)

    return [{'label': ticker, 'value': ticker} for ticker in added_tickers], ''

# Callback to generate plots
@app.callback(
    [Output('pe-output-div', 'children'),
     Output('rsi-output-div', 'children'),
     Output('financial-metrics-div', 'children')],
    [Input('plot-button', 'n_clicks')],
    [State('period-dropdown', 'value'), State('interval-dropdown', 'value'),
     State('overbought-input', 'value'), State('oversold-input', 'value')]
)
def generate_plots(plot_clicks, period, interval, overbought, oversold):
    if plot_clicks == 0 or not added_tickers:
        return None, None, None

    pe_ratios = fetch_pe_ratios(added_tickers)

    # Create P/E Chart
    pe_fig = go.Figure()
    pe_fig.add_trace(go.Bar(
        name="Current P/E",
        x=list(pe_ratios.keys()),
        y=[ratios['current'] for ratios in pe_ratios.values()],
        marker_color="blue"
    ))
    pe_fig.add_trace(go.Bar(
        name="Forward P/E",
        x=list(pe_ratios.keys()),
        y=[ratios['forward'] for ratios in pe_ratios.values()],
        marker_color="yellow"
    ))
    pe_fig.update_layout(
        title="P/E Ratios",
        title_x=0.5,
        xaxis_title="Tickers",
        yaxis_title="P/E Ratio",
        barmode="group",
        template="plotly_white"
    )

    rsi_figs = []
    for ticker in added_tickers:
        data = fetch_stock_chart(ticker, period, interval)
        if data is not None:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data['Close'],
                mode='lines',
                line=dict(color='blue', width=2),
                name="Stock Price"
            ))
            for i in range(len(data) - 1):
                if data['RSI'].iloc[i] > overbought:
                    fig.add_shape(
                        type="rect",
                        x0=data.index[i],
                        x1=data.index[i + 1],
                        y0=0,
                        y1=1,
                        xref="x",
                        yref="paper",
                        fillcolor="rgba(255, 0, 0, 0.2)",
                        line_width=0,
                    )
                elif data['RSI'].iloc[i] < oversold:
                    fig.add_shape(
                        type="rect",
                        x0=data.index[i],
                        x1=data.index[i + 1],
                        y0=0,
                        y1=1,
                        xref="x",
                        yref="paper",
                        fillcolor="rgba(0, 255, 0, 0.2)",
                        line_width=0,
                    )
                fig.update_layout(
                    title={
                        'text': f"{'-'*25}Stock Price/RSI - <b> {ticker}</b>{'-'*25}",  # Bold ticker symbol
                        'x': 0.5,  # Center the title
                        'xanchor': 'center',
                        'yanchor': 'top'
                    },
                    xaxis_title="Date",
                    yaxis_title="Stock Price",
                    template="plotly_white"
                )
            rsi_figs.append(dcc.Graph(figure=fig))

    metrics = fetch_financial_metrics(added_tickers)
    df = pd.DataFrame(metrics)
    financial_table = dash_table.DataTable(
        columns=[{"name": col, "id": col} for col in df.columns],
        data=df.to_dict("records"),
        style_table={'marginTop': '20px'},
        style_cell={'textAlign': 'center'}
    )

    return dcc.Graph(figure=pe_fig), rsi_figs, financial_table

# Run app
if __name__ == '__main__':
    app.run_server(debug=True)

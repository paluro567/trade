from dash import Dash, dcc, html, Input, Output, State, dash_table
from dash.exceptions import PreventUpdate
from yahooquery import Ticker
import plotly.graph_objects as go
import pandas as pd
import dash

# Initialize Dash app
app = Dash(__name__)
app.title = "Stock Analysis Dashboard"

# Store tickers in memory
added_tickers = []

# Fetch stock data using yahooquery
def fetch_stock_data(ticker, period='6mo', interval='1d'):
    stock = Ticker(ticker)
    data = stock.history(period=period, interval=interval).reset_index()
    if not data.empty and 'volume' in data:
        data.set_index('date', inplace=True)
        data.index = pd.to_datetime(data.index)
        data['average_volume'] = data['volume'].mean()
        data['current_volume'] = data['volume']
        data['volume_millions'] = data['volume'] / 1_000_000
        data['high_volume'] = data['volume'] > data['average_volume']  # Identify high-volume regions
        return data
    else:
        return None  # Return None if data is empty or missing required columns

# Fetch P/E ratios using yahooquery
def fetch_pe_ratios(tickers):
    pe_ratios = {}
    stock = Ticker(tickers)
    summary = stock.summary_detail
    for ticker in tickers:
        if ticker in summary:
            pe_ratios[ticker] = {
                'current': summary[ticker].get('trailingPE', None),
                'forward': summary[ticker].get('forwardPE', None)
            }
    return pe_ratios

# Format numbers in millions with commas
def format_millions(value):
    return f"{value:,.2f}M"

# Layout
app.layout = html.Div(
    style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'justifyContent': 'start', 'height': '100vh', 'overflow': 'auto'},
    children=[
        html.Div(
            style={
                'position': 'sticky', 'top': '0', 'zIndex': '1000', 'backgroundColor': 'white',
                'width': '100%', 'padding': '20px', 'boxShadow': '0px 2px 5px rgba(0,0,0,0.1)'
            },
            children=[
                html.H1("Stock Analysis Dashboard", style={'textAlign': 'center'}),
                html.Div([
                    html.Label("Enter a Stock Ticker:"),
                    dcc.Input(
                        id='ticker-input', type='text', placeholder='e.g., AAPL',
                        style={'width': '50%', 'padding': '10px'},
                        n_submit=0  # Track Enter key presses
                    ),
                    html.Button('Add Ticker', id='add-button', n_clicks=0, style={'marginLeft': '10px'}),
                ], style={'textAlign': 'center', 'marginBottom': '20px'}),
                html.Div(
                    style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'justifyContent': 'center'},
                    children=[
                        dcc.Checklist(
                            id='ticker-list',
                            options=[],
                            value=[],
                            inline=False,
                            labelStyle={'marginRight': '10px'}
                        ),
                        html.Button('Remove Selected', id='remove-button', n_clicks=0, style={'marginTop': '10px'}),
                    ]
                ),
                html.Div([
                    html.Label("Select Price Period:"),
                    dcc.Dropdown(
                        id='price-period',
                        options=[{'label': p, 'value': p} for p in ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']],
                        value='6mo',  # Default value
                        style={'width': '50%', 'marginBottom': '20px'}
                    ),
                    html.Label("Select Interval:"),
                    dcc.Dropdown(
                        id='interval',
                        options=[{'label': i, 'value': i} for i in ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo']],
                        value='1d',  # Default value
                        style={'width': '50%', 'marginBottom': '20px'}
                    ),
                ], style={'textAlign': 'center'}),
                html.Button('Plot Charts', id='plot-button', n_clicks=0, style={'marginTop': '20px'}),
            ]
        ),
        html.Div(id='charts-div', style={'marginTop': '20px', 'width': '90%'})
    ]
)

# Callback to manage ticker addition and removal
@app.callback(
    [Output('ticker-input', 'value'),
     Output('ticker-list', 'options'),
     Output('ticker-list', 'value')],
    [Input('add-button', 'n_clicks'),
     Input('ticker-input', 'n_submit'),
     Input('remove-button', 'n_clicks')],
    [State('ticker-input', 'value'),
     State('ticker-list', 'value')]
)
def update_ticker_list(add_clicks, enter_presses, remove_clicks, ticker_input, tickers_to_remove):
    global added_tickers
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    # Determine which event triggered the callback
    trigger = ctx.triggered[0]['prop_id']

    # Add a ticker via the "Add" button or "Enter" key
    if trigger in ['add-button.n_clicks', 'ticker-input.n_submit']:
        if ticker_input and ticker_input.strip():
            ticker = ticker_input.strip().upper()
            if ticker not in added_tickers:
                added_tickers.append(ticker)

    # Remove selected tickers
    elif trigger == 'remove-button.n_clicks':
        added_tickers = [t for t in added_tickers if t not in tickers_to_remove]

    # Update the ticker list options and clear the input field
    ticker_options = [{'label': t, 'value': t} for t in added_tickers]
    return "", ticker_options, added_tickers

# Callback to update charts when the Plot button is clicked
@app.callback(
    Output('charts-div', 'children'),
    [Input('plot-button', 'n_clicks')],
    [State('ticker-list', 'value'),
     State('price-period', 'value'),
     State('interval', 'value')]
)
def update_charts(plot_clicks, tickers_to_display, price_period, interval):
    if not plot_clicks or not tickers_to_display:
        raise PreventUpdate

    # Update P/E ratios
    pe_ratios = fetch_pe_ratios(tickers_to_display)
    pe_fig = go.Figure()
    for metric, color in zip(['current', 'forward'], ['blue', 'orange']):
        pe_fig.add_trace(go.Bar(
            name=f"{metric.capitalize()} P/E",
            x=list(pe_ratios.keys()),
            y=[ratios[metric] for ratios in pe_ratios.values()],
            marker_color=color
        ))
    pe_fig.update_layout(title="P/E Ratios", barmode='group')

    # Stock price charts with volume highlighting
    stock_charts = []
    table_data = []

    for ticker in tickers_to_display:
        data = fetch_stock_data(ticker, period=price_period, interval=interval)
        if data is not None:
            stock_fig = go.Figure()

            # Line for close prices
            stock_fig.add_trace(go.Scatter(
                x=data.index,
                y=data['close'],
                mode='lines',
                name='Close Price',
                line=dict(color='blue')
            ))

            # Add shaded regions for high/low volume
            for i in range(len(data)):
                x_start = data.index[i]
                x_end = data.index[i] + pd.Timedelta(days=1)  # Extend to cover the full day
                if data.iloc[i]['high_volume']:
                    stock_fig.add_vrect(
                        x0=x_start,
                        x1=x_end,   
                        fillcolor="red",
                        opacity=0.2,
                        layer="below",
                        line_width=0,  
                    )
                else:
                    stock_fig.add_vrect(
                        x0=x_start,
                        x1=x_end,
                        fillcolor="blue",
                        opacity=0.2,
                        layer="below",
                        line_width=0,
                    )
                stock_fig.update_layout(
                    title=f"{ticker} Stock Price Chart",
                    xaxis_title="Date",
                    yaxis_title="Price",
                    legend_title="Legend"
                )

            # Add key statistics to the data table
            table_data.append({
                'Ticker': ticker,
                'Average Volume (M)': format_millions(data['average_volume'].iloc[-1]),
                'Current Volume (M)': format_millions(data['current_volume'].iloc[-1]),
                'Trailing P/E': pe_ratios.get(ticker, {}).get('current', 'N/A'),
                'Forward P/E': pe_ratios.get(ticker, {}).get('forward', 'N/A')
            })

            # Append the stock price chart
            stock_charts.append(dcc.Graph(figure=stock_fig))

    # Create the data table
    data_table = dash_table.DataTable(
        columns=[
            {"name": "Ticker", "id": "Ticker"},
            {"name": "Average Volume (M)", "id": "Average Volume (M)"},
            {"name": "Current Volume (M)", "id": "Current Volume (M)"},
            {"name": "Trailing P/E", "id": "Trailing P/E"},
            {"name": "Forward P/E", "id": "Forward P/E"},
        ],
        data=table_data,
        style_table={'width': '100%', 'marginTop': '20px'},
        style_cell={'textAlign': 'center', 'padding': '10px'},
        style_header={'fontWeight': 'bold'}
    )

    return [dcc.Graph(figure=pe_fig)] + stock_charts + [data_table]

# Run app
if __name__ == '__main__':
    app.run_server(debug=True)

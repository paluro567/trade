from dash import Dash, dcc, html, Input, Output, State, callback_context
import yfinance as yf
import plotly.graph_objects as go

# Initialize Dash app
app = Dash(__name__)
app.title = "P/E Comparison & Financials"

# Store tickers in a global list
added_tickers = []

# Layout of the app
app.layout = html.Div([
    # App Header/title
    html.H1("Add Tickers to Analyze", style={'textAlign': 'center'}),
    html.Div([
        html.Label("Enter a Stock Ticker:", style={'fontSize': '16px'}),
        dcc.Input(
            id='ticker-input',
            type='text',
            placeholder='e.g., AAPL',
            style={'width': '50%', 'padding': '10px', 'fontSize': '14px'},
            n_submit=0  # Tracks Enter key presses
        ),
        html.Button(
            'Add Ticker',
            id='add-button',
            n_clicks=0,
            style={'marginLeft': '10px', 'padding': '10px', 'fontSize': '14px'}
        ),
        html.Button(
            'Remove Selected Tickers',
            id='remove-button',
            n_clicks=0,
            style={'marginLeft': '10px', 'padding': '10px', 'fontSize': '14px'}
        ),
        html.Button(
            'Plot All Tickers',
            id='plot-button',
            n_clicks=0,
            style={'marginLeft': '10px', 'padding': '10px', 'fontSize': '14px'}
        ),
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),
    dcc.Checklist(
        id='ticker-checklist',
        options=[],
        value=[],
        style={'marginTop': '10px', 'textAlign': 'left'},
        labelStyle={'display': 'flex', 'alignItems': 'center', 'fontSize': '14px'}
    ),
    html.Div(id='output-div', style={'marginTop': '20px'})
])

# Consolidated callback to handle adding and removing tickers
@app.callback(
    [Output('ticker-checklist', 'options'), Output('ticker-checklist', 'value')],
    [Input('add-button', 'n_clicks'), Input('remove-button', 'n_clicks'), Input('ticker-input', 'n_submit')],
    [State('ticker-input', 'value'), State('ticker-checklist', 'value')]
)
def modify_ticker_list(add_clicks, remove_clicks, n_submit, ticker_to_add, selected_tickers):
    ctx = callback_context
    if not ctx.triggered:
        return [{'label': ticker, 'value': ticker} for ticker in added_tickers], []

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id in ['add-button', 'ticker-input'] and ticker_to_add:
        ticker_to_add = ticker_to_add.strip().upper()
        if ticker_to_add not in added_tickers:
            added_tickers.append(ticker_to_add)

    if triggered_id == 'remove-button' and selected_tickers:
        for ticker in selected_tickers:
            if ticker in added_tickers:
                added_tickers.remove(ticker)

    options = [{'label': ticker, 'value': ticker} for ticker in added_tickers]
    return options, []  # Reset the selection

# Fetch P/E ratios from yfinance
def fetch_pe_ratios(tickers):
    pe_ratios = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            current_pe = stock.info.get('trailingPE', 0)
            forward_pe = stock.info.get('forwardPE', 0)
            pe_ratios[ticker] = {'current': current_pe, 'forward': forward_pe}
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            pe_ratios[ticker] = {'current': 0, 'forward': 0}
    return pe_ratios

# Fetch financial data from yfinance
def fetch_financials(tickers):
    financials = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            financials[ticker] = {
                'Revenue': info.get('totalRevenue', None),
                'Net Income': info.get('netIncomeToCommon', None),
                'Market Cap': info.get('marketCap', None)
            }
        except Exception as e:
            print(f"Error fetching financial data for {ticker}: {e}")
            financials[ticker] = {
                'Revenue': None,
                'Net Income': None,
                'Market Cap': None
            }
    return financials

# Callback to plot P/E ratios and financials
@app.callback(
    Output('output-div', 'children'),
    Input('plot-button', 'n_clicks')
)
def plot_data(n_clicks):
    if n_clicks > 0 and added_tickers:
        # Fetch data
        pe_ratios = fetch_pe_ratios(added_tickers)
        financials = fetch_financials(added_tickers)

        # Create P/E bar chart
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
            title="P/E & Forward P/E Comparison",
            xaxis_title="Stock Tickers",
            yaxis_title="P/E Ratio",
            barmode='group',
            template='plotly_white'
        )

        # Create financial data table
        financial_data = [
            [ticker, 
             f"{financials[ticker]['Revenue']:,}" if financials[ticker]['Revenue'] else "N/A",
             f"{financials[ticker]['Net Income']:,}" if financials[ticker]['Net Income'] else "N/A",
             f"{financials[ticker]['Market Cap']:,}" if financials[ticker]['Market Cap'] else "N/A"]
            for ticker in added_tickers
        ]
        financial_table = go.Figure(data=[
            go.Table(
                header=dict(
                    values=["Ticker", "Revenue", "Net Income", "Market Cap"],
                    fill_color='paleturquoise',
                    align='left'
                ),
                cells=dict(
                    values=list(zip(*financial_data)),
                    fill_color='lavender',
                    align='left'
                )
            )
        ])

        return html.Div([
            dcc.Graph(figure=pe_fig),
            dcc.Graph(figure=financial_table)
        ])
    return "No tickers to plot. Add tickers and click 'Plot All Tickers'."

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

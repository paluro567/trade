'''
Market data API: Polygon
API Key: hbMwS9pZA4vHHptRcz3ECtmZVpe9KWyp


Polygon tutorial: https://www.youtube.com/watch?v=XPWHiKT_mU0
Create conda environment for downloading dependencies
conda create --name trade python=<version_number>
conda activate trade
install dependencies for this project

pip install polygon-api-client
pip install plotly
'''
import pandas as pd
from polygon import RESTClient
import plotly.graph_objects as go
from plotly.offline import plot
client = RESTClient("hbMwS9pZA4vHHptRcz3ECtmZVpe9KWyp")
print(client.list_trades("PLTR", "2022-04-04", limit=1))

'''
trades = []
for t in client.list_trades("PLTR", "2022-04-04", limit=1):
    trades.append(t)
print(trades)
'''


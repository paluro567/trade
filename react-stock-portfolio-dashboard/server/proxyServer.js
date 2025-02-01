const express = require('express');
const axios = require('axios');
const cors = require('cors');

// node proxyServer.js (for running the server side from the server directory)

const app = express();
const PORT = 5001;

// Replace with your RapidAPI key
const RAPIDAPI_KEY = '9f4a4054b6mshb85831e848d74f5p1d45fbjsn394c3cd28a00';
const RAPIDAPI_HOST = 'yahoo-finance15.p.rapidapi.com';

// Enable CORS for all origins
app.use(cors());

app.get('/api/quote', async (req, res) => {
  try {
    const response = await axios.get(
      'https://yahoo-finance15.p.rapidapi.com/api/v1/markets/stock/quotes',
      {
        headers: {
          'x-rapidapi-host': RAPIDAPI_HOST,
          'x-rapidapi-key': RAPIDAPI_KEY,
        },
        params: {
          ticker: req.query.symbols || 'AAPL,MSFT,^SPX,^NYA,GAZP.ME,SIBN.ME,GEECEE.NS',
        },
      }
    );
    res.json(response.data);
  } catch (error) {
    console.error('Error in proxy server:', error.response?.data || error.message);
    res.status(error.response?.status || 500).json({
      error: 'Failed to fetch data from Yahoo Finance via RapidAPI',
      details: error.response?.data || error.message,
    });
  }
});

app.listen(PORT, () => {
  console.log(`Proxy server running on http://localhost:${PORT}`);
});

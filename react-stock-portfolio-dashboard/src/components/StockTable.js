import React, { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Typography,
  Box,
  TextField,
  Button,
  IconButton,
} from '@mui/material';
import { RemoveCircle } from '@mui/icons-material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css'; // Import calendar styles
import axios from 'axios';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const PORT=5001;

function StockTable() {
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [ticker, setTicker] = useState('');
  const [calendarEvents, setCalendarEvents] = useState([]);
  
  const fetchStockData = async (symbol) => {
    try {
      setLoading(true);
  
      // Fetch stock data from the proxy server
      const response = await axios.get(
        `http://localhost:${PORT}/api/quote?symbols=${symbol}`
      );
  
      // Log response body to debug
      console.log('API Response Body:', response.data.body);
  
      // Find stock info (case-insensitive)
      const stockInfo = response.data.body.find(
        (item) => item.symbol.toLowerCase() === symbol.toLowerCase()
      );
  
      if (!stockInfo) {
        throw new Error(`No data found for ticker: ${symbol}`);
      }
  
      // Parse stock information
      const nextEarningsDate = stockInfo.earningsTimestamp
        ? new Date(stockInfo.earningsTimestamp * 1000).toISOString().split('T')[0]
        : 'N/A';
  
      const stockData = {
        name: stockInfo.longName || stockInfo.shortName || 'Unknown',
        symbol: stockInfo.symbol,
        price: stockInfo.regularMarketPrice || 0,
        change: stockInfo.regularMarketChangePercent || 0,
        peRatio: stockInfo.trailingPE || 0,
        futurePe: stockInfo.forwardPE || 0,
        earningsDate: nextEarningsDate,
      };
  
      // Update stocks and calendar events
      setStocks((prevStocks) => [...prevStocks, stockData]);
  
      if (stockData.earningsDate !== 'N/A') {
        setCalendarEvents((prevEvents) => [
          ...prevEvents,
          { date: new Date(stockData.earningsDate), name: stockData.name },
        ]);
      }
    } catch (error) {
      console.error('Error fetching stock data:', error);
      alert(`Error fetching stock data: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  const handleAddTicker = () => {
    if (ticker.trim()) {
      fetchStockData(ticker.trim());
      setTicker(''); // Clear the input field
    }
  };

  const handleRemoveTicker = (symbol) => {
    setStocks((prevStocks) => prevStocks.filter((stock) => stock.symbol !== symbol));

    // Remove associated calendar events
    setCalendarEvents((prevEvents) =>
      prevEvents.filter((event) => event.name !== stocks.find((s) => s.symbol === symbol)?.name)
    );
  };

  // Chart data
  const chartData = {
    labels: stocks.map((stock) => stock.symbol), // Horizontal axis uses ticker symbols
    datasets: [
      {
        label: 'Current P/E Ratio',
        data: stocks.map((stock) => stock.peRatio),
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
      },
      {
        label: 'Forward P/E Ratio',
        data: stocks.map((stock) => stock.futurePe),
        backgroundColor: 'rgba(153, 102, 255, 0.6)',
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Stock Performance Metrics',
      },
    },
  };

  const tileContent = ({ date, view }) => {
    // Highlight tiles with earnings dates
    if (view === 'month') {
      const events = calendarEvents.filter(
        (event) => event.date.toDateString() === date.toDateString()
      );
      if (events.length > 0) {
        return (
          <Box
            sx={{
              backgroundColor: 'rgba(255, 99, 132, 0.6)',
              color: 'white',
              padding: '2px',
              borderRadius: '5px',
              fontSize: '10px',
            }}
          >
            {events.map((event) => event.name).join(', ')}
          </Box>
        );
      }
    }
    return null;
  };

  return (
    <Box>
      <Typography variant="h4" align="center" gutterBottom>
        Tickers:
      </Typography>
      <Box display="flex" justifyContent="center" alignItems="center" mb={4}>
        <TextField
          label="Enter Ticker Symbol"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAddTicker()} // Trigger Add on Enter
          variant="outlined"
        />
        <Button
          variant="contained"
          color="primary"
          onClick={handleAddTicker}
          style={{ marginLeft: '10px' }}
        >
          Add
        </Button>
      </Box>
      {loading && <CircularProgress />}
      {!loading && stocks.length > 0 && (
        <>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Stock</TableCell>
                  <TableCell>Symbol</TableCell>
                  <TableCell>Price ($)</TableCell>
                  <TableCell>Change (%)</TableCell>
                  <TableCell>P/E Ratio</TableCell>
                  <TableCell>Future P/E</TableCell>
                  <TableCell>Next Earnings Date</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {stocks.map((stock) => (
                  <TableRow key={stock.symbol}>
                    <TableCell>{stock.name}</TableCell>
                    <TableCell>{stock.symbol}</TableCell>
                    <TableCell>${stock.price.toFixed(2)}</TableCell>
                    <TableCell style={{ color: stock.change > 0 ? 'green' : 'red' }}>
                      {stock.change > 0 ? '+' : ''}
                      {stock.change.toFixed(2)}%
                    </TableCell>
                    <TableCell>{stock.peRatio}</TableCell>
                    <TableCell>{stock.futurePe}</TableCell>
                    <TableCell>{stock.earningsDate}</TableCell>
                    <TableCell>
                      <IconButton
                        color="error"
                        onClick={() => handleRemoveTicker(stock.symbol)}
                      >
                        <RemoveCircle />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          <Box mt={4}>
            <Bar data={chartData} options={chartOptions} />
          </Box>
          <Box mt={4}>
            <Typography variant="h6" align="center" gutterBottom>
              Earnings Calendar
            </Typography>
            <Calendar tileContent={tileContent} />
          </Box>
        </>
      )}
    </Box>
  );
}

export default StockTable;

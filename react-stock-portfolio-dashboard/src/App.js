import React from 'react';
import { Container, Typography, Grid } from '@mui/material';
import StockTable from './components/StockTable';

function App() {
  return (
    <Container>
      <Typography variant="h3" align="center" gutterBottom>
        Stock Portfolio Dashboard
      </Typography>
      <Typography variant="subtitle1" align="center">
        Track the performance and key metrics of your portfolio.
      </Typography>
      <Grid container spacing={2} marginTop={2}>
        <Grid item xs={12}>
          <StockTable />
        </Grid>
      </Grid>
    </Container>
  );
}

export default App;

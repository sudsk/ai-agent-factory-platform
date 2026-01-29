import React from 'react';
import { Box, Typography, Card, CardContent, Grid, Chip } from '@mui/material';
import { CheckCircle, Warning } from '@mui/icons-material';

function Monitoring() {
  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>System Monitoring</Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CheckCircle sx={{ color: 'success.main' }} />
                <Typography variant="h6">Platform Health</Typography>
              </Box>
              <Typography variant="h4" sx={{ mt: 2 }}>99.9%</Typography>
              <Typography variant="caption" color="text.secondary">Uptime</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6">Active Agents</Typography>
              <Typography variant="h4" sx={{ mt: 2 }}>42</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Warning sx={{ color: 'warning.main' }} />
                <Typography variant="h6">Alerts</Typography>
              </Box>
              <Typography variant="h4" sx={{ mt: 2 }}>3</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Monitoring;

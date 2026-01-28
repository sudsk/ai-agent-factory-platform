#!/bin/bash

# Create remaining page stubs
mkdir -p src/pages

# Agent Details page
cat > src/pages/AgentDetails.js << 'AGENTDETAILS'
import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Box, Typography, Card, CardContent, Grid, Chip, Button } from '@mui/material';
import { getAgent, invokeAgent } from '../services/api';

function AgentDetails() {
  const { agentName } = useParams();
  const [agent, setAgent] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAgent();
  }, [agentName]);

  const loadAgent = async () => {
    try {
      const data = await getAgent(agentName);
      setAgent(data);
    } catch (error) {
      console.error('Failed to load agent:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Typography>Loading...</Typography>;
  if (!agent) return <Typography>Agent not found</Typography>;

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>{agent.metadata?.name}</Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6">Description</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {agent.metadata?.description}
              </Typography>
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle2">Capabilities</Typography>
                <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
                  {agent.capabilities?.map((cap, i) => <Chip key={i} label={cap} size="small" />)}
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6">Details</Typography>
              <Box sx={{ mt: 2 }}>
                <Typography variant="caption">Status</Typography>
                <Typography variant="body2">{agent.status}</Typography>
              </Box>
              <Box sx={{ mt: 2 }}>
                <Typography variant="caption">Deployment</Typography>
                <Typography variant="body2">{agent.deployment?.target}</Typography>
              </Box>
              <Button variant="contained" fullWidth sx={{ mt: 3 }}>Test Agent</Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default AgentDetails;
AGENTDETAILS

# Intake Requests page
cat > src/pages/IntakeRequests.js << 'REQUESTS'
import React, { useEffect, useState } from 'react';
import { Box, Typography, Card, CardContent, Chip } from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { getIntakeRequests } from '../services/api';

const columns = [
  { field: 'id', headerName: 'ID', width: 90 },
  { field: 'business_unit', headerName: 'Business Unit', width: 150 },
  { field: 'agent_category', headerName: 'Category', width: 150 },
  { field: 'problem_statement', headerName: 'Problem', width: 300 },
  {
    field: 'status',
    headerName: 'Status',
    width: 130,
    renderCell: (params) => (
      <Chip
        label={params.value}
        size="small"
        color={params.value === 'approved' ? 'success' : 'default'}
      />
    ),
  },
  { field: 'priority_score', headerName: 'Score', width: 100 },
  { field: 'created_at', headerName: 'Created', width: 180 },
];

function IntakeRequests() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRequests();
  }, []);

  const loadRequests = async () => {
    try {
      const data = await getIntakeRequests();
      setRequests(data.requests || []);
    } catch (error) {
      console.error('Failed to load requests:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>My Requests</Typography>
      <Card>
        <CardContent>
          <DataGrid
            rows={requests}
            columns={columns}
            pageSize={10}
            loading={loading}
            autoHeight
            disableSelectionOnClick
          />
        </CardContent>
      </Card>
    </Box>
  );
}

export default IntakeRequests;
REQUESTS

# Monitoring page
cat > src/pages/Monitoring.js << 'MONITORING'
import React from 'react';
import { Box, Typography, Card, CardContent, Grid, Chip } from '@mui/material';
import { CheckCircle, Warning } from '@mui/icons-material';

function Monitoring() {
  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>System Monitoring</Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
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
          <Card>
            <CardContent>
              <Typography variant="h6">Active Agents</Typography>
              <Typography variant="h4" sx={{ mt: 2 }}>42</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
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
MONITORING

# Settings page
cat > src/pages/Settings.js << 'SETTINGS'
import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';

function Settings() {
  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>Settings</Typography>
      <Card>
        <CardContent>
          <Typography variant="body1">Settings page - Coming soon</Typography>
        </CardContent>
      </Card>
    </Box>
  );
}

export default Settings;
SETTINGS

# index.js
cat > src/index.js << 'INDEX'
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
INDEX

# index.css
cat > src/index.css << 'CSS'
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
CSS

# public/index.html
mkdir -p public
cat > public/index.html << 'HTML'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#028090" />
    <meta name="description" content="AI Agent Factory Platform" />
    <title>Agent Factory Platform</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
HTML

echo "✓ All remaining files created"

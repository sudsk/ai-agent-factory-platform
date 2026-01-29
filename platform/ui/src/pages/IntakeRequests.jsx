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

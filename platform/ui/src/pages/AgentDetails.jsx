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

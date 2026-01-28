import { Box, Typography, Card, CardContent } from '@mui/material';

function AgentRegistry() {
  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 600 }}>
        AgentRegistry
      </Typography>
      <Card>
        <CardContent>
          <Typography variant="body1">
            AgentRegistry page - Update with your existing code
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}

export default AgentRegistry;

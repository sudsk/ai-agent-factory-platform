import { Box, Typography, Card, CardContent } from '@mui/material';

function AgentDetails() {
  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 600 }}>
        AgentDetails
      </Typography>
      <Card>
        <CardContent>
          <Typography variant="body1">
            AgentDetails page - Update with your existing code
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}

export default AgentDetails;

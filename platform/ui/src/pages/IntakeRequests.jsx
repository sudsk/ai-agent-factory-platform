import { Box, Typography, Card, CardContent } from '@mui/material';

function IntakeRequests() {
  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 600 }}>
        IntakeRequests
      </Typography>
      <Card>
        <CardContent>
          <Typography variant="body1">
            IntakeRequests page - Update with your existing code
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}

export default IntakeRequests;

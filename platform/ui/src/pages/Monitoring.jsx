import { Box, Typography, Card, CardContent } from '@mui/material';

function Monitoring() {
  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 600 }}>
        Monitoring
      </Typography>
      <Card>
        <CardContent>
          <Typography variant="body1">
            Monitoring page - Update with your existing code
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}

export default Monitoring;

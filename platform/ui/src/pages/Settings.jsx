import { Box, Typography, Card, CardContent } from '@mui/material';

function Settings() {
  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 600 }}>
        Settings
      </Typography>
      <Card>
        <CardContent>
          <Typography variant="body1">
            Settings page - Update with your existing code
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}

export default Settings;

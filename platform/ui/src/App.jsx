import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';

// Layout
import Sidebar from './components/Layout/Sidebar';
import TopBar from './components/Layout/TopBar';

// Pages
import Dashboard from './pages/Dashboard';
import AgentRegistry from './pages/AgentRegistry';
import AgentDetails from './pages/AgentDetails';
import IntakePortal from './pages/IntakePortal';
import IntakeRequests from './pages/IntakeRequests';
import Monitoring from './pages/Monitoring';
import Settings from './pages/Settings';

// Theme with MUI v7 features
const theme = createTheme({
  palette: {
    primary: {
      main: '#028090',
      light: '#02C39A',
      dark: '#00A896',
    },
    secondary: {
      main: '#1E2761',
    },
    background: {
      default: '#F5F5F5',
      paper: '#FFFFFF',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 600,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        },
      },
    },
  },
});

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleDrawerToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex' }}>
          <Sidebar open={sidebarOpen} onToggle={handleDrawerToggle} />
          <Box
            component="main"
            sx={{
              flexGrow: 1,
              minHeight: '100vh',
              backgroundColor: 'background.default',
              marginLeft: '240px',
            }}
          >
            <TopBar onMenuClick={handleDrawerToggle} />
            <Box sx={{ p: 3, mt: 8 }}>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/agents" element={<AgentRegistry />} />
                <Route path="/agents/:agentName" element={<AgentDetails />} />
                <Route path="/intake" element={<IntakePortal />} />
                <Route path="/requests" element={<IntakeRequests />} />
                <Route path="/monitoring" element={<Monitoring />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </Box>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;

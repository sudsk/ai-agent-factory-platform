import { useNavigate, useLocation } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Box,
  Typography,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  ViewList as ViewListIcon,
  NoteAdd as NoteAddIcon,
  Assignment as AssignmentIcon,
  Monitoring as MonitoringIcon,
  Settings as SettingsIcon,
  SmartToy as SmartToyIcon,
} from '@mui/icons-material';

const drawerWidth = 240;

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
  { text: 'Agent Registry', icon: <ViewListIcon />, path: '/agents' },
  { text: 'Submit Request', icon: <NoteAddIcon />, path: '/intake' },
  { text: 'My Requests', icon: <AssignmentIcon />, path: '/requests' },
  { text: 'Monitoring', icon: <MonitoringIcon />, path: '/monitoring' },
];

const bottomMenuItems = [
  { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
];

function Sidebar({ open }) {
  const navigate = useNavigate();
  const location = useLocation();

  const handleNavigation = (path) => {
    navigate(path);
  };

  return (
    <Drawer
      variant="persistent"
      anchor="left"
      open={open}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          backgroundColor: '#1E2761',
          color: 'white',
        },
      }}
    >
      <Box
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          borderBottom: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        <SmartToyIcon sx={{ fontSize: 32, color: '#02C39A' }} />
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 700, lineHeight: 1 }}>
            Agent Factory
          </Typography>
          <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)' }}>
            Platform
          </Typography>
        </Box>
      </Box>

      <List sx={{ px: 1, py: 2 }}>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
            <ListItemButton
              onClick={() => handleNavigation(item.path)}
              selected={location.pathname === item.path}
              sx={{
                borderRadius: 2,
                '&.Mui-selected': {
                  backgroundColor: '#02C39A',
                  '&:hover': {
                    backgroundColor: '#00A896',
                  },
                },
                '&:hover': {
                  backgroundColor: 'rgba(2, 195, 154, 0.1)',
                },
              }}
            >
              <ListItemIcon sx={{ color: 'white', minWidth: 40 }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.text}
                primaryTypographyProps={{
                  fontSize: 14,
                  fontWeight: location.pathname === item.path ? 600 : 400,
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Box sx={{ flexGrow: 1 }} />
      <Divider sx={{ borderColor: 'rgba(255,255,255,0.1)' }} />
      <List sx={{ px: 1, py: 2 }}>
        {bottomMenuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              onClick={() => handleNavigation(item.path)}
              selected={location.pathname === item.path}
              sx={{
                borderRadius: 2,
                '&.Mui-selected': {
                  backgroundColor: '#02C39A',
                },
                '&:hover': {
                  backgroundColor: 'rgba(2, 195, 154, 0.1)',
                },
              }}
            >
              <ListItemIcon sx={{ color: 'white', minWidth: 40 }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.text}
                primaryTypographyProps={{
                  fontSize: 14,
                  fontWeight: location.pathname === item.path ? 600 : 400,
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Box sx={{ p: 2, borderTop: '1px solid rgba(255,255,255,0.1)' }}>
        <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.5)' }}>
          Version 1.0.0
        </Typography>
      </Box>
    </Drawer>
  );
}

export default Sidebar;

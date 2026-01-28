import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  TextField,
  InputAdornment,
  Card,
  Grid,
  Chip,
  Button,
  IconButton,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  Search as SearchIcon,
  MoreVert as MoreVertIcon,
  PlayArrow as PlayArrowIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { getAgents } from '../services/api';

function AgentCard({ agent, onSelect, onAction }) {
  const [anchorEl, setAnchorEl] = useState(null);

  const handleMenuClick = (event) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleAction = (action) => {
    handleMenuClose();
    onAction(action, agent);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'default';
      case 'deprecated':
        return 'error';
      default:
        return 'default';
    }
  };

  const getDeploymentIcon = (target) => {
    const icons = {
      'cloud-run': '☁️',
      'gke': '⚙️',
      'agent-engine': '🤖',
      'agentspace': '🌐',
    };
    return icons[target] || '📦';
  };

  return (
    <Card
      sx={{
        cursor: 'pointer',
        transition: 'all 0.2s',
        '&:hover': {
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          transform: 'translateY(-2px)',
        },
      }}
      onClick={() => onSelect(agent)}
    >
      <Box sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
              {agent.metadata?.name || 'Unnamed Agent'}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {agent.metadata?.description || 'No description'}
            </Typography>
          </Box>
          <IconButton size="small" onClick={handleMenuClick}>
            <MoreVertIcon />
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
          >
            <MenuItem onClick={() => handleAction('test')}>
              <PlayArrowIcon sx={{ mr: 1, fontSize: 20 }} /> Test Agent
            </MenuItem>
            <MenuItem onClick={() => handleAction('edit')}>
              <EditIcon sx={{ mr: 1, fontSize: 20 }} /> Edit
            </MenuItem>
            <MenuItem onClick={() => handleAction('deactivate')}>
              <DeleteIcon sx={{ mr: 1, fontSize: 20 }} /> Deactivate
            </MenuItem>
          </Menu>
        </Box>

        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
          <Chip
            label={agent.status || 'unknown'}
            size="small"
            color={getStatusColor(agent.status)}
          />
          <Chip
            label={`${getDeploymentIcon(agent.deployment?.target)} ${agent.deployment?.target || 'N/A'}`}
            size="small"
            variant="outlined"
          />
        </Box>

        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {(agent.capabilities || []).slice(0, 3).map((cap, index) => (
            <Chip
              key={index}
              label={cap}
              size="small"
              sx={{ backgroundColor: '#E3F2FD', color: '#0277BD' }}
            />
          ))}
          {agent.capabilities && agent.capabilities.length > 3 && (
            <Chip
              label={`+${agent.capabilities.length - 3} more`}
              size="small"
              variant="outlined"
            />
          )}
        </Box>

        <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid #eee', display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="caption" color="text.secondary">
            Version: {agent.metadata?.version || 'N/A'}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Owner: {agent.metadata?.owner || 'Unknown'}
          </Typography>
        </Box>
      </Box>
    </Card>
  );
}

function AgentRegistry() {
  const navigate = useNavigate();
  const [agents, setAgents] = useState([]);
  const [filteredAgents, setFilteredAgents] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAgents();
  }, []);

  useEffect(() => {
    filterAgents();
  }, [searchQuery, filterStatus, agents]);

  const loadAgents = async () => {
    try {
      setLoading(true);
      const response = await getAgents();
      setAgents(response.agents || []);
    } catch (error) {
      console.error('Failed to load agents:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterAgents = () => {
    let filtered = agents;

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (agent) =>
          (agent.metadata?.name || '').toLowerCase().includes(query) ||
          (agent.metadata?.description || '').toLowerCase().includes(query) ||
          (agent.capabilities || []).some((cap) => cap.toLowerCase().includes(query))
      );
    }

    // Filter by status
    if (filterStatus !== 'all') {
      filtered = filtered.filter((agent) => agent.status === filterStatus);
    }

    setFilteredAgents(filtered);
  };

  const handleAgentSelect = (agent) => {
    navigate(`/agents/${agent.metadata?.name}`);
  };

  const handleAgentAction = (action, agent) => {
    console.log(`Action ${action} on agent:`, agent.metadata?.name);
    // Implement actions (test, edit, deactivate)
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Agent Registry
        </Typography>
        <Button variant="contained" onClick={() => navigate('/intake')}>
          Request New Agent
        </Button>
      </Box>

      {/* Search and Filters */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
        <TextField
          placeholder="Search agents..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          sx={{ flex: 1 }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant={filterStatus === 'all' ? 'contained' : 'outlined'}
            onClick={() => setFilterStatus('all')}
          >
            All ({agents.length})
          </Button>
          <Button
            variant={filterStatus === 'active' ? 'contained' : 'outlined'}
            onClick={() => setFilterStatus('active')}
            color="success"
          >
            Active ({agents.filter((a) => a.status === 'active').length})
          </Button>
          <Button
            variant={filterStatus === 'inactive' ? 'contained' : 'outlined'}
            onClick={() => setFilterStatus('inactive')}
          >
            Inactive ({agents.filter((a) => a.status === 'inactive').length})
          </Button>
        </Box>
      </Box>

      {/* Agents Grid */}
      {loading ? (
        <Typography>Loading agents...</Typography>
      ) : (
        <Grid container spacing={3}>
          {filteredAgents.map((agent, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <AgentCard
                agent={agent}
                onSelect={handleAgentSelect}
                onAction={handleAgentAction}
              />
            </Grid>
          ))}
        </Grid>
      )}

      {!loading && filteredAgents.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary">
            No agents found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Try adjusting your search or filters
          </Typography>
        </Box>
      )}
    </Box>
  );
}

export default AgentRegistry;

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Grid,
  MenuItem,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import { submitIntakeRequest } from '../services/api';

const categories = [
  'financial',
  'it-ops',
  'compliance',
  'customer-ops',
  'data-analytics',
  'business-process',
];

const urgencyLevels = [
  { value: 'critical', label: 'Critical', color: 'error' },
  { value: 'high', label: 'High', color: 'warning' },
  { value: 'medium', label: 'Medium', color: 'info' },
  { value: 'low', label: 'Low', color: 'default' },
];

const impactLevels = ['high', 'medium', 'low'];

function IntakePortal() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    business_unit: '',
    agent_category: '',
    problem_statement: '',
    expected_outcomes: '',
    estimated_impact: '',
    urgency: '',
    timeline: '',
    data_sources: '',
    compliance_requirements: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (field) => (event) => {
    setFormData({
      ...formData,
      [field]: event.target.value,
    });
  };

  const handleSubmit = async () => {
    try {
      setSubmitting(true);
      setError(null);
      
      // Convert comma-separated strings to arrays
      const payload = {
        ...formData,
        data_sources: formData.data_sources ? formData.data_sources.split(',').map(s => s.trim()) : [],
        compliance_requirements: formData.compliance_requirements ? formData.compliance_requirements.split(',').map(s => s.trim()) : [],
      };

      const response = await submitIntakeRequest(payload);
      setResult(response);
      
      // Show success message
      setTimeout(() => {
        navigate('/requests');
      }, 2000);
      
    } catch (err) {
      console.error('Submission failed:', err);
      setError(err.message || 'Failed to submit request');
    } finally {
      setSubmitting(false);
    }
  };

  const isFormValid = () => {
    return (
      formData.business_unit &&
      formData.agent_category &&
      formData.problem_statement &&
      formData.expected_outcomes &&
      formData.urgency
    );
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 1, fontWeight: 600 }}>
        Submit Agent Request
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Fill out this form to request a new AI agent. Our intake system will process your request
        and help you through the approval process.
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Grid container spacing={3}>
                {/* Business Unit */}
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Business Unit *"
                    value={formData.business_unit}
                    onChange={handleChange('business_unit')}
                    placeholder="e.g., Sales, Engineering, Finance"
                  />
                </Grid>

                {/* Agent Category */}
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    select
                    label="Agent Category *"
                    value={formData.agent_category}
                    onChange={handleChange('agent_category')}
                  >
                    {categories.map((cat) => (
                      <MenuItem key={cat} value={cat}>
                        {cat.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </MenuItem>
                    ))}
                  </TextField>
                </Grid>

                {/* Problem Statement */}
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={4}
                    label="Problem Statement *"
                    value={formData.problem_statement}
                    onChange={handleChange('problem_statement')}
                    placeholder="Describe the problem this agent will solve..."
                    helperText="Be specific about who is affected and what the current pain points are"
                  />
                </Grid>

                {/* Expected Outcomes */}
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    label="Expected Outcomes *"
                    value={formData.expected_outcomes}
                    onChange={handleChange('expected_outcomes')}
                    placeholder="What should this agent accomplish?"
                    helperText="Include specific, measurable outcomes"
                  />
                </Grid>

                {/* Impact & Urgency */}
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    select
                    label="Estimated Impact *"
                    value={formData.estimated_impact}
                    onChange={handleChange('estimated_impact')}
                  >
                    {impactLevels.map((level) => (
                      <MenuItem key={level} value={level}>
                        {level.charAt(0).toUpperCase() + level.slice(1)}
                      </MenuItem>
                    ))}
                  </TextField>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    select
                    label="Urgency *"
                    value={formData.urgency}
                    onChange={handleChange('urgency')}
                  >
                    {urgencyLevels.map((level) => (
                      <MenuItem key={level.value} value={level.value}>
                        {level.label}
                      </MenuItem>
                    ))}
                  </TextField>
                </Grid>

                {/* Timeline */}
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Timeline"
                    value={formData.timeline}
                    onChange={handleChange('timeline')}
                    placeholder="e.g., 2-3 months"
                  />
                </Grid>

                {/* Data Sources */}
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Data Sources"
                    value={formData.data_sources}
                    onChange={handleChange('data_sources')}
                    placeholder="e.g., Salesforce, BigQuery, Internal API"
                    helperText="Comma-separated list of data sources this agent will need"
                  />
                </Grid>

                {/* Compliance Requirements */}
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Compliance Requirements"
                    value={formData.compliance_requirements}
                    onChange={handleChange('compliance_requirements')}
                    placeholder="e.g., GDPR, SOX, HIPAA"
                    helperText="Comma-separated list of compliance requirements"
                  />
                </Grid>

                {/* Error Display */}
                {error && (
                  <Grid item xs={12}>
                    <Alert severity="error">{error}</Alert>
                  </Grid>
                )}

                {/* Success Display */}
                {result && (
                  <Grid item xs={12}>
                    <Alert severity="success">
                      Request submitted successfully! Redirecting to your requests...
                    </Alert>
                  </Grid>
                )}

                {/* Submit Button */}
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                    <Button
                      variant="outlined"
                      onClick={() => navigate('/agents')}
                      disabled={submitting}
                    >
                      Cancel
                    </Button>
                    <Button
                      variant="contained"
                      onClick={handleSubmit}
                      disabled={!isFormValid() || submitting}
                      startIcon={submitting && <CircularProgress size={20} />}
                    >
                      {submitting ? 'Submitting...' : 'Submit Request'}
                    </Button>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Side Panel - Help & Tips */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Tips for a Great Request
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" paragraph>
                  <strong>Be Specific:</strong> Clearly describe the problem and who it affects.
                </Typography>
                <Typography variant="body2" paragraph>
                  <strong>Quantify Impact:</strong> Include metrics and expected improvements.
                </Typography>
                <Typography variant="body2" paragraph>
                  <strong>List Requirements:</strong> Specify data sources and compliance needs upfront.
                </Typography>
                <Typography variant="body2" paragraph>
                  <strong>Check for Duplicates:</strong> Our system will automatically search for similar agents.
                </Typography>
              </Box>
            </CardContent>
          </Card>

          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                What Happens Next?
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                  <Chip label="1" size="small" color="primary" sx={{ mr: 1, mt: 0.5 }} />
                  <Typography variant="body2">
                    Intake agent processes your request
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                  <Chip label="2" size="small" color="primary" sx={{ mr: 1, mt: 0.5 }} />
                  <Typography variant="body2">
                    System checks for similar existing agents
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                  <Chip label="3" size="small" color="primary" sx={{ mr: 1, mt: 0.5 }} />
                  <Typography variant="body2">
                    Request gets prioritized and scored
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'flex-start' }}>
                  <Chip label="4" size="small" color="primary" sx={{ mr: 1, mt: 0.5 }} />
                  <Typography variant="body2">
                    You'll receive approval decision within 2-4 hours
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default IntakePortal;

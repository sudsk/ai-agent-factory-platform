# Agent Factory UI

React-based web interface for the AI Agent Factory Platform.

## Features

- **Dashboard**: Overview of platform statistics and health
- **Agent Registry**: Browse, search, and manage agents
- **Intake Portal**: Submit new agent requests
- **Request Tracking**: Monitor status of your requests
- **Monitoring**: View system health and metrics

## Local Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Setup

```bash
# Install dependencies
npm install

# Set environment variables
cp .env.example .env
# Edit .env with your API URL

# Start development server
npm start
```

The app will run on `http://localhost:3000`

### Environment Variables

Create a `.env` file:

```
REACT_APP_API_URL=http://localhost:8080
```

## Build for Production

```bash
# Create production build
npm run build

# Test production build locally
npx serve -s build
```

## Deploy to GCP

### Using Cloud Build

```bash
# Deploy UI
gcloud builds submit --config cloudbuild.yaml
```

### Using Docker

```bash
# Build image
docker build -t agent-factory-ui .

# Run locally
docker run -p 80:80 agent-factory-ui

# Push to GCR
docker tag agent-factory-ui gcr.io/PROJECT_ID/agent-factory-ui
docker push gcr.io/PROJECT_ID/agent-factory-ui

# Deploy to Cloud Run
gcloud run deploy agent-factory-ui \
  --image gcr.io/PROJECT_ID/agent-factory-ui \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated
```

## Architecture

```
src/
├── components/
│   └── Layout/
│       ├── Sidebar.js          # Left navigation
│       └── TopBar.js           # Top app bar
├── pages/
│   ├── Dashboard.js            # Main dashboard
│   ├── AgentRegistry.js        # Agent browsing
│   ├── AgentDetails.js         # Single agent view
│   ├── IntakePortal.js         # Submit requests
│   ├── IntakeRequests.js       # View requests
│   ├── Monitoring.js           # System health
│   └── Settings.js             # User settings
├── services/
│   └── api.js                  # API client
└── App.js                      # Main app component
```

## API Integration

The UI connects to these backend services:

- **Agent Registry API**: `/agents/*`
- **Intake Processor**: `/agents/intake-processor/invoke`
- **Prioritization Scorer**: `/agents/prioritization-scorer/invoke`
- **Matchmaking Search**: `/agents/matchmaking-search/invoke`
- **Requirements Refiner**: `/agents/requirements-refiner/invoke`

## Customization

### Theme

Edit theme colors in `src/App.js`:

```javascript
const theme = createTheme({
  palette: {
    primary: {
      main: '#028090', // Your brand color
    },
  },
});
```

### Logo

Replace logo in `src/components/Layout/Sidebar.js`

### Navigation

Add/remove menu items in `src/components/Layout/Sidebar.js`:

```javascript
const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
  // Add your items here
];
```

## Production Checklist

- [ ] Update `REACT_APP_API_URL` in cloudbuild.yaml
- [ ] Configure authentication (if needed)
- [ ] Set up proper CORS on backend
- [ ] Enable HTTPS
- [ ] Configure Cloud Armor for DDoS protection
- [ ] Set up monitoring alerts
- [ ] Test on mobile devices
- [ ] Run accessibility audit
- [ ] Configure custom domain

## Troubleshooting

**API calls failing:**
- Check `REACT_APP_API_URL` is correct
- Verify CORS settings on backend
- Check browser console for errors

**Build fails:**
- Clear node_modules: `rm -rf node_modules && npm install`
- Update dependencies: `npm update`

**Slow performance:**
- Enable production build: `npm run build`
- Check network tab for large assets
- Implement code splitting if needed

## Support

For issues or questions:
- Check logs: `gcloud run logs read agent-factory-ui`
- GitHub Issues: [link]
- Slack: #agent-factory-ui

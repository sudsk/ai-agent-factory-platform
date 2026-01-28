# AI Agent Factory Platform

Enterprise-grade AI Agent delivery platform built on Google Cloud Platform with a complete web-based management interface.

## Overview

The AI Agent Factory is a comprehensive platform for building, deploying, and managing AI agents at scale. It provides:

- **Agent Registry**: Central catalog and discovery service
- **Web Dashboard**: Beautiful React UI for agent management
- **Intake System**: Automated request processing and prioritization
- **Governance Engine**: Policy enforcement and compliance
- **Guardrails**: Input/output validation and safety
- **AIOps**: Monitoring, logging, and observability
- **FinOps**: Cost tracking and optimization
- **SDK**: Client libraries for agent development

## Architecture

The platform follows a layered architecture:

1. **User Layer**: Web UI, APIs, integrations
2. **API Gateway**: Authentication, routing, rate limiting
3. **Platform Services**: Registry, Governance, Guardrails, AIOps, FinOps
4. **Agent Runtimes**: Agentspace, Agent Engine, Cloud Run, GKE
5. **GCP Foundation**: Vertex AI, BigQuery, Pub/Sub, etc.

**Key Design Principles:**
- **No central orchestration** - Agents handle their own coordination
- **Direct invocation** - Simple SDK call pattern via Registry
- **Multi-runtime support** - Deploy to Cloud Run, GKE, Agent Engine, or Agentspace
- **Built-in governance** - Security and compliance by default

## Repository Structure

```
ai-agent-factory-platform/
├── platform/
│   ├── ui/                    # React web dashboard (NEW!)
│   ├── agent-registry/        # Agent catalog & discovery service
│   ├── intake-system/         # Request processing backend
│   ├── governance/            # Policy engine
│   ├── guardrails/            # Safety & validation
│   └── aiops/                 # Monitoring & cost tracking
│
├── agents/                    # Internal factory agents
│   ├── intake-processor/      # Processes agent requests
│   ├── prioritization-scorer/ # Scores & ranks requests
│   ├── matchmaking-search/    # Finds similar agents
│   └── requirements-refiner/  # Refines requirements
│
├── sdk/python/                # Python client library
│   └── agent_factory_sdk/
│       ├── registry.py        # Agent discovery & invocation
│       ├── guardrails.py      # Input/output validation
│       ├── monitoring.py      # Observability
│       └── deployment.py      # Deploy to runtimes
│
├── infrastructure/terraform/  # Infrastructure as Code
│   ├── main.tf               # Core GCP resources
│   ├── variables.tf          # Configuration
│   └── modules/              # Reusable modules
│
├── shared/                    # Common utilities
│   ├── schemas/              # JSON schemas
│   ├── libs/                 # Shared libraries
│   └── configs/              # Configuration templates
│
├── docs/                      # Documentation
│   ├── guides/               # How-to guides
│   ├── architecture/         # Architecture docs
│   └── api/                  # API reference
│
└── .github/workflows/         # CI/CD automation
```

## Quick Start

### Prerequisites

- Google Cloud Project with billing enabled
- Terraform >= 1.5
- Python >= 3.11
- Node.js >= 18 (for UI)
- `gcloud` CLI installed and authenticated

### 1. Deploy Infrastructure

```bash
cd infrastructure/terraform
terraform init
terraform apply \
  -var="project_id=YOUR_PROJECT_ID" \
  -var="alert_email=YOUR_EMAIL"
```

This creates:
- Firestore database (Agent Registry)
- Pub/Sub topics (async messaging)
- BigQuery datasets (analytics)
- Cloud Storage buckets (artifacts)
- VPC and networking
- IAM service accounts
- Monitoring alerts

### 2. Deploy Platform Services

```bash
# Deploy Agent Registry
cd platform/agent-registry
gcloud builds submit --config cloudbuild.yaml
```

### 3. Deploy Internal Agents

```bash
# Deploy all 4 internal agents
cd agents/intake-processor
gcloud builds submit --config cloudbuild.yaml

cd ../prioritization-scorer
gcloud builds submit --config cloudbuild.yaml

cd ../matchmaking-search
gcloud builds submit --config cloudbuild.yaml

cd ../requirements-refiner
gcloud builds submit --config cloudbuild.yaml
```

### 4. Deploy Web UI

```bash
cd platform/ui

# Update API URL in cloudbuild.yaml first:
# REACT_APP_API_URL=https://YOUR-AGENT-REGISTRY-URL

gcloud builds submit --config cloudbuild.yaml

# Get UI URL
gcloud run services describe agent-factory-ui \
  --region us-central1 \
  --format 'value(status.url)'
```

### 5. Install SDK

```bash
cd sdk/python
pip install -e .
```

### 6. Test the Platform

```python
from agent_factory_sdk import AgentRegistry

registry = AgentRegistry(project_id="YOUR_PROJECT_ID")

# Test intake processor
result = registry.invoke_agent(
    agent_name="intake-processor",
    input_data={
        "raw_text": "We need an agent to analyze sales data"
    }
)

print(result)
```

Or use the web UI at the URL from step 4!

## Web Dashboard Features

The platform includes a complete React-based management interface:

### **Dashboard** (`/dashboard`)
- Real-time agent statistics
- Invocation trend charts
- System health monitoring
- Recent activity feed

### **Agent Registry** (`/agents`)
- Browse all registered agents
- Search by name, description, capabilities
- Filter by status and deployment target
- Test agents directly from UI
- View detailed agent information

### **Intake Portal** (`/intake`)
- Submit new agent requests via web form
- Guided form with validation
- Auto-processing with intake agents
- Duplicate detection
- Priority scoring

### **Request Tracking** (`/requests`)
- View all your submitted requests
- Track approval status
- See priority scores
- Monitor progress

### **Monitoring** (`/monitoring`)
- Platform health overview
- Active agent count
- Alert indicators
- System metrics

## Development

### Local UI Development

```bash
cd platform/ui

# Install dependencies
npm install

# Create .env file
echo "REACT_APP_API_URL=http://localhost:8080" > .env

# Start dev server
npm start
```

UI runs on `http://localhost:3000`

### Create a New Agent

```bash
# Create agent directory
mkdir my-custom-agent
cd my-custom-agent

# Create structure
mkdir -p src tests
touch src/main.py agent.yaml Dockerfile requirements.txt
```

**agent.yaml**:
```yaml
metadata:
  name: my-custom-agent
  version: 1.0.0
  description: My custom agent
  owner: your-team

deployment:
  target: cloud-run
  cloud_run:
    region: us-central1
    cpu: 2
    memory: 4Gi
    min_instances: 0
    max_instances: 10

capabilities:
  - data-processing
  - analysis

guardrails:
  input_validation: true
  output_validation: true
  pii_detection: true
```

**src/main.py**:
```python
from fastapi import FastAPI
from agent_factory_sdk import AgentRegistry, Guardrails, AgentMonitoring

app = FastAPI()
monitoring = AgentMonitoring(project_id="YOUR_PROJECT", agent_name="my-custom-agent")
Guardrails.init("YOUR_PROJECT")

@app.post("/process")
@Guardrails.validate_input()
@Guardrails.validate_output()
@monitoring.track_invocation()
async def process(request: dict):
    # Your agent logic here
    return {"processed": True, "data": request}
```

See [docs/guides/agent-development.md](docs/guides/agent-development.md) for complete guide.

## Key Features

### ✅ Complete Agent Lifecycle
- Register → Deploy → Monitor → Update → Deactivate
- All automated through SDK and web UI

### ✅ Multi-Runtime Support
- **Cloud Run**: Serverless, recommended for most agents
- **GKE**: Kubernetes for complex needs
- **Agent Engine**: Vertex AI managed
- **Agentspace**: UI-based rapid prototyping

### ✅ Built-in Governance
- Input/output validation on every call
- PII detection and redaction (Google DLP)
- Prompt injection protection
- Rate limiting
- Cost controls per agent

### ✅ Full Observability
- Automatic invocation logging
- Custom metrics to Cloud Monitoring
- Performance tracking
- Cost tracking per agent
- Real-time dashboards

### ✅ Intelligent Intake System
- AI-powered data extraction (Gemini)
- Automatic duplicate detection (TF-IDF similarity)
- Multi-criteria prioritization (ROI, urgency, feasibility)
- Requirements refinement (gap analysis)

### ✅ Self-Service Platform
- Web UI for non-technical users
- Python SDK for developers
- CI/CD automation
- Documentation and examples

## Internal Agents

The platform includes 4 internal agents that power the factory:

1. **intake-processor**
   - Extracts structured data from requests
   - Validates completeness
   - Calls matchmaking to find duplicates
   - Built with Gemini 2.0

2. **prioritization-scorer**
   - Multi-criteria scoring (ROI, strategic, urgency, feasibility, risk)
   - Weighted algorithm
   - Priority levels: CRITICAL, HIGH, MEDIUM, LOW
   - Batch scoring support

3. **matchmaking-search**
   - TF-IDF + cosine similarity
   - Duplicate detection (80% = duplicate, 60% = high similarity)
   - Finds reusable components
   - Recommends extend vs build new

4. **requirements-refiner**
   - LLM-powered gap analysis
   - Generates follow-up questions
   - Suggests implementation patterns
   - Creates user story templates
   - Completeness & clarity scoring

## Documentation

- [Architecture Overview](docs/architecture/overview.md)
- [Agent Development Guide](docs/guides/agent-development.md)
- [UI Development Guide](platform/ui/README.md)
- [Deployment Guide](docs/guides/deployment.md)
- [API Reference](docs/api/)
- [Troubleshooting](docs/guides/troubleshooting.md)

## Cost Estimates

**Monthly costs (moderate usage - 100K requests/month):**

| Component | Cost |
|-----------|------|
| Infrastructure (Firestore, BigQuery, Storage) | $50-150 |
| UI (Cloud Run, minimal when idle) | $10-30 |
| Backend Services (Agent Registry, internal agents) | $50-200 |
| LLM Calls (Gemini) | $100-500 |
| **Total** | **$210-880** |

Scales linearly with usage. UI and idle agents cost almost nothing!

## Production Checklist

Before going to production:

- [ ] Update `PROJECT_ID` in all files
- [ ] Set up proper IAM permissions
- [ ] Configure alerts to your email/Slack
- [ ] Review and adjust resource limits
- [ ] Set up proper secret management
- [ ] Configure backup policies for Firestore
- [ ] Set up monitoring dashboards
- [ ] Update API URL in UI cloudbuild.yaml
- [ ] Test all user flows end-to-end
- [ ] Configure custom domain (optional)
- [ ] Enable Cloud Armor for DDoS protection
- [ ] Set up staging environment
- [ ] Train your team on the platform

## Security

### Implemented
- ✅ Input/output validation with guardrails
- ✅ PII detection and redaction (Google DLP)
- ✅ Prompt injection detection
- ✅ Rate limiting
- ✅ IAM-based access control
- ✅ Security headers (nginx)
- ✅ HTTPS by default (Cloud Run)

### To Add (Production)
- [ ] Authentication (Google OAuth / Identity Platform)
- [ ] Authorization (RBAC)
- [ ] Audit logging
- [ ] Secret rotation
- [ ] Vulnerability scanning

## Support

For questions or issues:

1. Check the [documentation](docs/)
2. Review [example agents](agents/)
3. Check [Terraform examples](infrastructure/terraform/)
4. Review [SDK code](sdk/python/agent_factory_sdk/)

For bugs or feature requests:
- GitHub Issues: [your-repo-url]
- Slack: #agent-factory-support
- Email: platform-team@company.com

## License

Copyright (c) 2025 Your Organization

## What Makes This Platform Special

✅ **Complete Solution** - Backend + Frontend + Infrastructure + Documentation
✅ **Production-Ready** - Not just examples, fully deployable code
✅ **GCP Native** - Fully leverages Google Cloud services
✅ **Flexible** - Support 4 different deployment targets
✅ **Governance-First** - Security and compliance built-in
✅ **Self-Service** - Teams can deploy their own agents via web UI
✅ **Observable** - Full monitoring and cost tracking
✅ **Well-Documented** - Comprehensive guides and examples
✅ **Beautiful UI** - Professional React dashboard
✅ **Agent Autonomy** - No central orchestration, agents coordinate themselves

## Quick Links

- **Deploy Infrastructure**: `terraform apply`
- **Deploy Backend**: `gcloud builds submit`
- **Deploy UI**: `cd platform/ui && gcloud builds submit`
- **Local UI Development**: `cd platform/ui && npm start`
- **Install SDK**: `cd sdk/python && pip install -e .`
- **View UI Guide**: [platform/ui/README.md](platform/ui/README.md)
- **Agent Development**: [docs/guides/agent-development.md](docs/guides/agent-development.md)

---

**You're ready to build!** 🚀

The platform handles all the infrastructure, governance, and operations - you just focus on building great agents!
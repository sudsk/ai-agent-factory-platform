# AI Agent Factory Platform

Enterprise-grade AI Agent delivery platform built on Google Cloud Platform.

## Overview

The AI Agent Factory is a comprehensive platform for building, deploying, and managing AI agents at scale. It provides:

- **Agent Registry**: Central catalog and discovery service
- **Governance Engine**: Policy enforcement and compliance
- **Guardrails**: Input/output validation and safety
- **AIOps**: Monitoring, logging, and observability
- **FinOps**: Cost tracking and optimization
- **SDK**: Client libraries for agent development

## Repository Structure

```
ai-agent-factory-platform/
├── platform/              # Core platform services
├── infrastructure/        # Terraform IaC
├── sdk/                   # Client libraries
├── shared/               # Common utilities
├── agents/               # Internal factory agents
└── docs/                 # Documentation
```

## Quick Start

### Prerequisites

- Google Cloud Project with billing enabled
- Terraform >= 1.5
- Python >= 3.11
- Node.js >= 18 (optional, for tooling)

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/your-org/ai-agent-factory-platform.git
cd ai-agent-factory-platform
```

2. **Set up infrastructure**
```bash
cd infrastructure/terraform/environments/dev
terraform init
terraform apply
```

3. **Install SDK**
```bash
cd sdk/python
pip install -e .
```

4. **Deploy platform services**
```bash
cd platform/agent-registry
gcloud builds submit --config cloudbuild.yaml
```

## Architecture

The platform follows a layered architecture:

1. **User Layer**: Web portals, APIs, integrations
2. **API Gateway**: Authentication, routing, rate limiting
3. **Platform Services**: Registry, Governance, Guardrails, AIOps, FinOps
4. **Agent Runtimes**: Agentspace, Agent Engine, Cloud Run, GKE
5. **GCP Foundation**: Vertex AI, BigQuery, Pub/Sub, etc.

## Documentation

- [Architecture Overview](docs/architecture/overview.md)
- [Agent Development Guide](docs/guides/agent-development.md)
- [Deployment Guide](docs/guides/deployment.md)
- [API Reference](docs/api/)

## License

Copyright (c) 2025 Your Organization

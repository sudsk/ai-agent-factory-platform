#!/bin/bash

# This script creates the complete AI Agent Factory Platform repository structure
# with all necessary files

echo "Creating AI Agent Factory Platform repository structure..."

# Create directory structure
mkdir -p sdk/python/agent_factory_sdk
mkdir -p sdk/python/tests
mkdir -p platform/agent-registry/src
mkdir -p platform/intake-system/{backend,web-ui}
mkdir -p platform/governance/policy-engine/policies
mkdir -p platform/guardrails/services
mkdir -p platform/aiops/{monitoring,cost-tracking}
mkdir -p agents/{intake-processor,prioritization-scorer,matchmaking-search,requirements-refiner}/src
mkdir -p infrastructure/terraform/{modules,environments/{dev,staging,prod}}
mkdir -p shared/{libs,schemas,configs}
mkdir -p docs/{architecture,guides,api}
mkdir -p .github/workflows

echo "✓ Directory structure created"

# Create .gitignore
cat > .gitignore << 'GITIGNORE'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Terraform
.terraform/
*.tfstate
*.tfstate.*
.terraform.lock.hcl

# GCP
*.json
!**/cloudbuild.json
credentials.json
service-account.json

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# Environment
.env
.env.local
GITIGNORE

echo "✓ .gitignore created"

echo ""
echo "Repository structure created successfully!"
echo "Next steps:"
echo "1. cd ai-agent-factory-platform"
echo "2. Review and customize the files"
echo "3. Initialize git: git init"
echo "4. Set up GCP project and credentials"
echo "5. Deploy infrastructure: cd infrastructure/terraform/environments/dev && terraform init && terraform apply"


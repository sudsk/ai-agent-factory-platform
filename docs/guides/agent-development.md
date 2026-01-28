# Agent Development Guide

## Overview

This guide walks you through developing and deploying agents on the AI Agent Factory platform.

## Prerequisites

- Python 3.11+
- GCP account with project created
- `gcloud` CLI installed and authenticated
- Docker installed (for local testing)

## Quick Start

### 1. Install the SDK

```bash
cd sdk/python
pip install -e .
```

### 2. Create Your Agent

Create a new directory for your agent:

```bash
mkdir my-custom-agent
cd my-custom-agent
```

Create the basic structure:

```
my-custom-agent/
├── src/
│   └── main.py
├── tests/
│   └── test_main.py
├── Dockerfile
├── requirements.txt
├── agent.yaml
└── cloudbuild.yaml
```

### 3. Write Your Agent Code

**`src/main.py`**:

```python
from fastapi import FastAPI
from agent_factory_sdk import AgentRegistry, Guardrails, AgentMonitoring

app = FastAPI(title="My Custom Agent")

PROJECT_ID = "your-project-id"
registry = AgentRegistry(project_id=PROJECT_ID)
monitoring = AgentMonitoring(project_id=PROJECT_ID, agent_name="my-custom-agent")

Guardrails.init(PROJECT_ID)

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/process")
@Guardrails.validate_input()
@Guardrails.validate_output()
@monitoring.track_invocation()
async def process(request: dict):
    # Your agent logic here
    result = {"processed": True, "data": request}
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

### 4. Define Agent Configuration

**`agent.yaml`**:

```yaml
metadata:
  name: my-custom-agent
  version: 1.0.0
  description: My custom agent description
  owner: your-team
  contact: team@company.com

deployment:
  target: cloud-run  # or: gke, agent-engine, agentspace
  
  cloud_run:
    region: us-central1
    cpu: 2
    memory: 4Gi
    min_instances: 0
    max_instances: 10
    timeout: 60s

capabilities:
  - data-processing
  - analysis

input_schema:
  type: object
  properties:
    data:
      type: string

output_schema:
  type: object
  properties:
    processed:
      type: boolean

guardrails:
  input_validation: true
  output_validation: true
  pii_detection: true

monitoring:
  sla_latency_ms: 1000
  sla_availability: 99.5
```

### 5. Create Dockerfile

**`Dockerfile`**:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

CMD ["python", "src/main.py"]
```

### 6. Test Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python src/main.py

# Test in another terminal
curl -X POST http://localhost:8080/process \
  -H "Content-Type: application/json" \
  -d '{"data": "test"}'
```

### 7. Deploy to Platform

```bash
# Build and deploy
gcloud builds submit --config cloudbuild.yaml

# Or use the SDK
python -c "
from agent_factory_sdk import AgentDeployer
deployer = AgentDeployer(project_id='your-project-id')
result = deployer.deploy_from_config('agent.yaml')
print(result)
"
```

## Best Practices

### 1. Use Guardrails

Always wrap your agent endpoints with guardrails:

```python
@Guardrails.validate_input(check_prompt_injection=True, check_pii=True)
@Guardrails.validate_output(check_pii=True, redact_pii=True)
async def my_endpoint(request: dict):
    # Your code
    pass
```

### 2. Add Monitoring

Track your agent's performance:

```python
@monitoring.track_invocation()
async def my_endpoint(request: dict):
    # Your code
    pass
```

Record custom metrics:

```python
from agent_factory_sdk import MetricsCollector

metrics = MetricsCollector(project_id=PROJECT_ID, agent_name="my-agent")
metrics.record_metric("custom_metric", 123.45)
metrics.increment_counter("requests_processed")
```

### 3. Call Other Agents

Use the registry to invoke other agents:

```python
from agent_factory_sdk import AgentRegistry

registry = AgentRegistry(project_id=PROJECT_ID)

# Invoke another agent
result = registry.invoke_agent(
    agent_name="data-validator",
    input_data={"data": my_data}
)
```

### 4. Handle Errors Gracefully

```python
from fastapi import HTTPException

try:
    result = process_data(data)
except ValueError as e:
    logger.error(f"Validation error: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Processing error: {e}")
    raise HTTPException(status_code=500, detail="Internal error")
```

### 5. Add Health Checks

Always implement a health check endpoint:

```python
@app.get("/health")
async def health():
    # Check dependencies
    try:
        # Test database connection
        db.ping()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## Advanced Patterns

### Multi-Agent Orchestration with LangGraph

```python
from langgraph.graph import StateGraph
from typing import TypedDict

class AgentState(TypedDict):
    input: str
    result: str

def step1(state: AgentState):
    # Call agent 1
    result = registry.invoke_agent("agent-1", {"data": state["input"]})
    state["intermediate"] = result
    return state

def step2(state: AgentState):
    # Call agent 2
    result = registry.invoke_agent("agent-2", {"data": state["intermediate"]})
    state["result"] = result
    return state

# Build workflow
workflow = StateGraph(AgentState)
workflow.add_node("step1", step1)
workflow.add_node("step2", step2)
workflow.add_edge("step1", "step2")
workflow.set_entry_point("step1")

app = workflow.compile()
```

### Async Processing with Pub/Sub

```python
from agent_factory_sdk import AsyncAgentRegistry

async_registry = AsyncAgentRegistry(project_id=PROJECT_ID)

# Queue async work
result = async_registry.invoke_agent_async(
    agent_name="heavy-processor",
    input_data=large_dataset,
    callback_url="https://my-service/callback"
)

print(f"Queued with message_id: {result['message_id']}")
```

### Caching Results

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def expensive_operation(key: str):
    # This will be cached
    return process(key)
```

## Testing

### Unit Tests

```python
# tests/test_main.py
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_process():
    response = client.post("/process", json={"data": "test"})
    assert response.status_code == 200
    assert "processed" in response.json()
```

### Integration Tests

```python
def test_agent_integration():
    registry = AgentRegistry(project_id=PROJECT_ID)
    
    # Call actual agent
    result = registry.invoke_agent(
        agent_name="my-custom-agent",
        input_data={"data": "test"}
    )
    
    assert result["processed"] == True
```

## Deployment

### CI/CD with Cloud Build

**`cloudbuild.yaml`**:

```yaml
steps:
  # Run tests
  - name: python:3.11
    entrypoint: python
    args: ['-m', 'pytest', 'tests/']
  
  # Build container
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/${_AGENT_NAME}:$SHORT_SHA', '.']
  
  # Push container
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/${_AGENT_NAME}:$SHORT_SHA']
  
  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - '${_AGENT_NAME}'
      - '--image'
      - 'gcr.io/$PROJECT_ID/${_AGENT_NAME}:$SHORT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'

substitutions:
  _AGENT_NAME: 'my-custom-agent'

images:
  - 'gcr.io/$PROJECT_ID/${_AGENT_NAME}:$SHORT_SHA'
```

## Monitoring & Debugging

### View Logs

```bash
# Cloud Run logs
gcloud run logs read my-custom-agent --region us-central1

# All agent logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50
```

### View Metrics

```bash
# Custom metrics
gcloud monitoring time-series list \
  --filter='metric.type="custom.googleapis.com/agent/invocations"'
```

### Debug Issues

1. Check agent health: `curl https://AGENT_URL/health`
2. View Cloud Run console for errors
3. Check Firestore for agent registration
4. Verify IAM permissions
5. Review guardrails logs for validation issues

## Resources

- [SDK API Reference](../api/sdk-reference.md)
- [Platform Architecture](../architecture/overview.md)
- [Example Agents](../../agents/)
- [Troubleshooting Guide](./troubleshooting.md)

## Support

For questions or issues:
- Slack: #agent-factory-support
- Email: platform-team@company.com
- GitHub Issues: https://github.com/your-org/ai-agent-factory-platform/issues

"""
Agent Registry Service

Central registry for agent metadata, discovery, and invocation routing.
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from google.cloud import firestore
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agent Registry", version="1.0.0")

# Initialize Firestore
db = firestore.Client()


class AgentMetadata(BaseModel):
    """Agent metadata model"""
    name: str
    version: str
    description: str
    owner: Optional[str] = None
    contact: Optional[str] = None


class DeploymentConfig(BaseModel):
    """Deployment configuration"""
    target: str  # cloud-run, gke, agent-engine, agentspace
    region: Optional[str] = None
    endpoint: Optional[str] = None


class AgentConfig(BaseModel):
    """Complete agent configuration"""
    metadata: AgentMetadata
    deployment: DeploymentConfig
    capabilities: List[str]
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    guardrails: Optional[Dict[str, Any]] = None
    monitoring: Optional[Dict[str, Any]] = None
    status: str = "active"


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "agent-registry"}


@app.post("/agents")
async def register_agent(agent: AgentConfig):
    """Register a new agent"""
    try:
        agent_name = agent.metadata.name
        
        # Check if agent already exists
        existing = db.collection('agents').document(agent_name).get()
        if existing.exists:
            raise HTTPException(
                status_code=409,
                detail=f"Agent '{agent_name}' already exists"
            )
        
        # Add timestamps
        agent_dict = agent.dict()
        agent_dict['registered_at'] = datetime.utcnow()
        agent_dict['updated_at'] = datetime.utcnow()
        
        # Save to Firestore
        db.collection('agents').document(agent_name).set(agent_dict)
        
        logger.info(f"Registered agent: {agent_name}")
        
        return {
            "status": "registered",
            "agent": agent_name,
            "timestamp": agent_dict['registered_at']
        }
        
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_name}")
async def get_agent(agent_name: str):
    """Get agent metadata"""
    doc = db.collection('agents').document(agent_name).get()
    
    if not doc.exists:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    
    return doc.to_dict()


@app.get("/agents")
async def list_agents(
    status: Optional[str] = None,
    capability: Optional[str] = None,
    deployment_target: Optional[str] = None
):
    """List agents with optional filters"""
    query = db.collection('agents')
    
    if status:
        query = query.where('status', '==', status)
    if capability:
        query = query.where('capabilities', 'array_contains', capability)
    if deployment_target:
        query = query.where('deployment.target', '==', deployment_target)
    
    agents = [doc.to_dict() for doc in query.stream()]
    
    return {"agents": agents, "count": len(agents)}


@app.put("/agents/{agent_name}")
async def update_agent(agent_name: str, updates: Dict[str, Any]):
    """Update agent metadata"""
    doc_ref = db.collection('agents').document(agent_name)
    
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    
    updates['updated_at'] = datetime.utcnow()
    doc_ref.update(updates)
    
    logger.info(f"Updated agent: {agent_name}")
    
    return {"status": "updated", "agent": agent_name}


@app.delete("/agents/{agent_name}")
async def deactivate_agent(agent_name: str):
    """Deactivate an agent (soft delete)"""
    return await update_agent(agent_name, {"status": "inactive"})


@app.post("/agents/{agent_name}/invoke")
async def invoke_agent(
    agent_name: str,
    input_data: Dict[str, Any],
    authorization: Optional[str] = Header(None)
):
    """
    Invoke an agent (proxy request)
    
    This endpoint looks up the agent's endpoint and proxies the request.
    """
    import requests
    
    # Get agent info
    doc = db.collection('agents').document(agent_name).get()
    
    if not doc.exists:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    
    agent_info = doc.to_dict()
    
    if agent_info.get('status') != 'active':
        raise HTTPException(
            status_code=503,
            detail=f"Agent '{agent_name}' is not active"
        )
    
    endpoint = agent_info.get('deployment', {}).get('endpoint')
    
    if not endpoint:
        raise HTTPException(
            status_code=500,
            detail=f"No endpoint configured for agent '{agent_name}'"
        )
    
    # Proxy request to agent
    try:
        response = requests.post(
            endpoint,
            json=input_data,
            headers={"Authorization": authorization} if authorization else {},
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Agent invocation failed: {e}")
        raise HTTPException(status_code=502, detail=f"Agent invocation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
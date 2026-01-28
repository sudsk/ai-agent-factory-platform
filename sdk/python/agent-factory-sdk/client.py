# sdk/python/agent_factory_sdk/client.py

from typing import Any, Dict, Optional
import requests
from google.cloud import firestore

class AgentRegistry:
    """Client for interacting with the Agent Registry"""
    
    def __init__(self, registry_url: str = None):
        self.registry_url = registry_url or os.getenv("AGENT_REGISTRY_URL")
        self.db = firestore.Client()
    
    def invoke_agent(self, agent_name: str, input_data: Dict[str, Any], 
                     timeout: int = 30) -> Dict[str, Any]:
        """
        Directly invoke an agent by name
        
        Args:
            agent_name: Name of the agent to invoke
            input_data: Input data for the agent
            timeout: Request timeout in seconds
            
        Returns:
            Agent response
        """
        # Lookup agent in registry
        agent_info = self._get_agent_info(agent_name)
        
        if not agent_info:
            raise ValueError(f"Agent '{agent_name}' not found in registry")
        
        # Get endpoint based on deployment target
        endpoint = agent_info['endpoint']
        
        # Make direct call
        response = requests.post(
            endpoint,
            json=input_data,
            headers={"Authorization": f"Bearer {self._get_token()}"},
            timeout=timeout
        )
        
        response.raise_for_status()
        return response.json()
    
    def _get_agent_info(self, agent_name: str) -> Optional[Dict]:
        """Fetch agent metadata from Firestore"""
        doc = self.db.collection('agents').document(agent_name).get()
        return doc.to_dict() if doc.exists else None
    
    def search_agents(self, capability: str = None, 
                     deployment_target: str = None) -> list:
        """Search for agents by capability or deployment target"""
        query = self.db.collection('agents')
        
        if capability:
            query = query.where('capabilities', 'array_contains', capability)
        if deployment_target:
            query = query.where('deployment.target', '==', deployment_target)
            
        return [doc.to_dict() for doc in query.stream()]
    
    def register_agent(self, agent_config: Dict[str, Any]):
        """Register a new agent in the registry"""
        agent_name = agent_config['metadata']['name']
        self.db.collection('agents').document(agent_name).set(agent_config)
        
        return {"status": "registered", "agent": agent_name}
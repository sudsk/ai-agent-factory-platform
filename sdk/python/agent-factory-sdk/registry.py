"""
Agent Registry Client

Provides methods to interact with the Agent Registry for discovery and invocation.
"""

import os
import logging
from typing import Any, Dict, List, Optional
import requests
from google.cloud import firestore
from google.auth import default
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Client for interacting with the Agent Registry"""
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        registry_url: Optional[str] = None,
    ):
        """
        Initialize Agent Registry client
        
        Args:
            project_id: GCP project ID (defaults to environment)
            registry_url: URL of registry API (defaults to environment variable)
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT")
        self.registry_url = registry_url or os.getenv("AGENT_REGISTRY_URL")
        self.db = firestore.Client(project=self.project_id)
        self._credentials, _ = default()
    
    def invoke_agent(
        self,
        agent_name: str,
        input_data: Dict[str, Any],
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Directly invoke an agent by name
        
        Args:
            agent_name: Name of the agent to invoke
            input_data: Input data for the agent
            timeout: Request timeout in seconds
            headers: Optional additional headers
            
        Returns:
            Agent response
            
        Raises:
            ValueError: If agent not found
            requests.HTTPError: If invocation fails
        """
        logger.info(f"Invoking agent: {agent_name}")
        
        # Lookup agent in registry
        agent_info = self.get_agent(agent_name)
        
        if not agent_info:
            raise ValueError(f"Agent '{agent_name}' not found in registry")
        
        if agent_info.get('status') != 'active':
            raise ValueError(f"Agent '{agent_name}' is not active (status: {agent_info.get('status')})")
        
        # Get endpoint
        endpoint = agent_info.get('endpoint')
        if not endpoint:
            raise ValueError(f"No endpoint configured for agent '{agent_name}'")
        
        # Prepare headers
        request_headers = {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
            "X-Agent-Caller": "agent-factory-sdk",
        }
        if headers:
            request_headers.update(headers)
        
        # Make request
        try:
            response = requests.post(
                endpoint,
                json=input_data,
                headers=request_headers,
                timeout=timeout
            )
            response.raise_for_status()
            
            logger.info(f"Agent {agent_name} invoked successfully")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to invoke agent {agent_name}: {e}")
            raise
    
    def get_agent(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch agent metadata from registry
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent metadata or None if not found
        """
        doc = self.db.collection('agents').document(agent_name).get()
        return doc.to_dict() if doc.exists else None
    
    def list_agents(
        self,
        status: Optional[str] = None,
        capability: Optional[str] = None,
        deployment_target: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List agents with optional filters
        
        Args:
            status: Filter by status (active, inactive, deprecated)
            capability: Filter by capability
            deployment_target: Filter by deployment target
            
        Returns:
            List of agent metadata
        """
        query = self.db.collection('agents')
        
        if status:
            query = query.where('status', '==', status)
        if capability:
            query = query.where('capabilities', 'array_contains', capability)
        if deployment_target:
            query = query.where('deployment.target', '==', deployment_target)
        
        return [doc.to_dict() for doc in query.stream()]
    
    def search_agents(self, query_text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search agents by name or description
        
        Args:
            query_text: Search query
            limit: Maximum results to return
            
        Returns:
            List of matching agents
        """
        # Simple text search - in production, use Vertex AI Search
        all_agents = self.list_agents(status='active')
        
        results = []
        query_lower = query_text.lower()
        
        for agent in all_agents:
            name = agent.get('metadata', {}).get('name', '').lower()
            description = agent.get('metadata', {}).get('description', '').lower()
            
            if query_lower in name or query_lower in description:
                results.append(agent)
                
            if len(results) >= limit:
                break
        
        return results
    
    def register_agent(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new agent in the registry
        
        Args:
            agent_config: Complete agent configuration
            
        Returns:
            Registration confirmation
        """
        agent_name = agent_config['metadata']['name']
        
        logger.info(f"Registering agent: {agent_name}")
        
        # Validate required fields
        required_fields = ['metadata', 'deployment', 'capabilities']
        for field in required_fields:
            if field not in agent_config:
                raise ValueError(f"Missing required field: {field}")
        
        # Set timestamps
        from datetime import datetime
        agent_config['registered_at'] = datetime.utcnow()
        agent_config['updated_at'] = datetime.utcnow()
        
        # Default status
        if 'status' not in agent_config:
            agent_config['status'] = 'active'
        
        # Save to Firestore
        self.db.collection('agents').document(agent_name).set(agent_config)
        
        logger.info(f"Agent {agent_name} registered successfully")
        
        return {
            "status": "registered",
            "agent": agent_name,
            "timestamp": agent_config['registered_at']
        }
    
    def update_agent(
        self,
        agent_name: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update agent metadata
        
        Args:
            agent_name: Name of agent to update
            updates: Fields to update
            
        Returns:
            Update confirmation
        """
        from datetime import datetime
        
        updates['updated_at'] = datetime.utcnow()
        
        self.db.collection('agents').document(agent_name).update(updates)
        
        logger.info(f"Agent {agent_name} updated successfully")
        
        return {
            "status": "updated",
            "agent": agent_name,
            "timestamp": updates['updated_at']
        }
    
    def deactivate_agent(self, agent_name: str) -> Dict[str, Any]:
        """
        Deactivate an agent (soft delete)
        
        Args:
            agent_name: Name of agent to deactivate
            
        Returns:
            Deactivation confirmation
        """
        return self.update_agent(agent_name, {"status": "inactive"})
    
    def _get_token(self) -> str:
        """Get authentication token"""
        self._credentials.refresh(Request())
        return self._credentials.token


class AsyncAgentRegistry(AgentRegistry):
    """Async wrapper for agent invocation via Pub/Sub"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from google.cloud import pubsub_v1
        self.publisher = pubsub_v1.PublisherClient()
    
    def invoke_agent_async(
        self,
        agent_name: str,
        input_data: Dict[str, Any],
        callback_url: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Invoke agent asynchronously via Pub/Sub
        
        Args:
            agent_name: Name of agent to invoke
            input_data: Input data
            callback_url: Optional webhook for results
            
        Returns:
            Message ID and topic
        """
        import json
        
        topic_path = self.publisher.topic_path(
            self.project_id,
            f"agent-{agent_name}"
        )
        
        message_data = {
            "agent_name": agent_name,
            "input_data": input_data,
            "callback_url": callback_url,
        }
        
        future = self.publisher.publish(
            topic_path,
            json.dumps(message_data).encode('utf-8')
        )
        
        message_id = future.result()
        
        logger.info(f"Async invocation queued for {agent_name}: {message_id}")
        
        return {
            "message_id": message_id,
            "topic": topic_path,
            "agent": agent_name
        }

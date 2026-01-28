"""
Deployment Module

Utilities for deploying agents to different runtimes.
"""

import os
import yaml
import subprocess
from typing import Dict, Any, Optional
from google.cloud import run_v2, container_v1
import logging

logger = logging.getLogger(__name__)


class AgentDeployer:
    """Deploy agents to various runtimes"""
    
    def __init__(self, project_id: str, region: str = "us-central1"):
        """
        Initialize deployer
        
        Args:
            project_id: GCP project ID
            region: GCP region
        """
        self.project_id = project_id
        self.region = region
        self.run_client = run_v2.ServicesClient()
        self.gke_client = container_v1.ClusterManagerClient()
    
    def deploy_from_config(self, config_path: str) -> Dict[str, Any]:
        """
        Deploy agent from agent.yaml configuration
        
        Args:
            config_path: Path to agent.yaml
            
        Returns:
            Deployment result
        """
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        deployment_target = config['deployment']['target']
        
        if deployment_target == 'cloud-run':
            return self.deploy_to_cloud_run(config)
        elif deployment_target == 'gke':
            return self.deploy_to_gke(config)
        elif deployment_target == 'agent-engine':
            return self.deploy_to_agent_engine(config)
        else:
            raise ValueError(f"Unsupported deployment target: {deployment_target}")
    
    def deploy_to_cloud_run(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deploy agent to Cloud Run
        
        Args:
            config: Agent configuration
            
        Returns:
            Deployment result with endpoint URL
        """
        agent_name = config['metadata']['name']
        cloud_run_config = config['deployment'].get('cloud_run', {})
        
        # Build container
        image_uri = self._build_container(agent_name)
        
        # Deploy to Cloud Run
        parent = f"projects/{self.project_id}/locations/{self.region}"
        
        service = run_v2.Service()
        service.name = f"{parent}/services/{agent_name}"
        
        # Configure service
        template = run_v2.RevisionTemplate()
        container = run_v2.Container()
        container.image = image_uri
        
        # Set resources
        resources = run_v2.ResourceRequirements()
        resources.limits = {
            "cpu": str(cloud_run_config.get('cpu', 2)),
            "memory": cloud_run_config.get('memory', '4Gi')
        }
        container.resources = resources
        
        template.containers = [container]
        template.scaling = run_v2.RevisionScaling(
            min_instance_count=cloud_run_config.get('min_instances', 0),
            max_instance_count=cloud_run_config.get('max_instances', 10)
        )
        
        service.template = template
        
        # Create or update service
        try:
            operation = self.run_client.create_service(
                parent=parent,
                service=service,
                service_id=agent_name
            )
            result = operation.result()
            
            endpoint = result.uri
            
            logger.info(f"Agent {agent_name} deployed to Cloud Run: {endpoint}")
            
            return {
                "status": "deployed",
                "target": "cloud-run",
                "endpoint": endpoint,
                "agent": agent_name
            }
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            raise
    
    def deploy_to_gke(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy agent to GKE"""
        agent_name = config['metadata']['name']
        
        # Build container
        image_uri = self._build_container(agent_name)
        
        # Generate Kubernetes manifests
        manifests = self._generate_k8s_manifests(config, image_uri)
        
        # Apply manifests
        for manifest in manifests:
            self._apply_k8s_manifest(manifest)
        
        return {
            "status": "deployed",
            "target": "gke",
            "agent": agent_name
        }
    
    def deploy_to_agent_engine(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy agent to Vertex AI Agent Engine"""
        agent_name = config['metadata']['name']
        agent_engine_config = config['deployment'].get('agent_engine', {})
        
        # Use Vertex AI Agent Builder API
        # This is a placeholder - actual implementation depends on Agent Builder API
        
        logger.info(f"Deploying {agent_name} to Agent Engine")
        
        return {
            "status": "deployed",
            "target": "agent-engine",
            "agent": agent_name
        }
    
    def _build_container(self, agent_name: str) -> str:
        """Build container image using Cloud Build"""
        # Use Cloud Build to build the image
        image_uri = f"gcr.io/{self.project_id}/{agent_name}:latest"
        
        build_config = {
            "steps": [
                {
                    "name": "gcr.io/cloud-builders/docker",
                    "args": ["build", "-t", image_uri, "."]
                }
            ],
            "images": [image_uri]
        }
        
        # Submit build
        subprocess.run(
            ["gcloud", "builds", "submit", 
             "--config", "-", 
             f"--project={self.project_id}"],
            input=yaml.dump(build_config).encode(),
            check=True
        )
        
        return image_uri
    
    def _generate_k8s_manifests(
        self, 
        config: Dict[str, Any], 
        image_uri: str
    ) -> list:
        """Generate Kubernetes manifests"""
        agent_name = config['metadata']['name']
        gke_config = config['deployment'].get('gke', {})
        
        # Deployment manifest
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": agent_name},
            "spec": {
                "replicas": gke_config.get('replicas', 3),
                "selector": {
                    "matchLabels": {"app": agent_name}
                },
                "template": {
                    "metadata": {
                        "labels": {"app": agent_name}
                    },
                    "spec": {
                        "containers": [{
                            "name": agent_name,
                            "image": image_uri,
                            "resources": {
                                "requests": {
                                    "cpu": "1",
                                    "memory": "2Gi"
                                }
                            }
                        }]
                    }
                }
            }
        }
        
        # Service manifest
        service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": agent_name},
            "spec": {
                "selector": {"app": agent_name},
                "ports": [{
                    "protocol": "TCP",
                    "port": 80,
                    "targetPort": 8080
                }],
                "type": "LoadBalancer"
            }
        }
        
        return [deployment, service]
    
    def _apply_k8s_manifest(self, manifest: Dict[str, Any]):
        """Apply Kubernetes manifest"""
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(manifest, f)
            manifest_path = f.name
        
        try:
            subprocess.run(
                ["kubectl", "apply", "-f", manifest_path],
                check=True
            )
        finally:
            os.unlink(manifest_path)
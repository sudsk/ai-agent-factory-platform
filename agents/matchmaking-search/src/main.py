"""
Matchmaking Search Agent

Searches for similar existing agents to avoid duplication.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

import sys
sys.path.append('/app')
from agent_factory_sdk import AgentRegistry, Guardrails, AgentMonitoring

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Matchmaking Search Agent")

PROJECT_ID = "your-project-id"
registry = AgentRegistry(project_id=PROJECT_ID)
monitoring = AgentMonitoring(project_id=PROJECT_ID, agent_name="matchmaking-search")

Guardrails.init(PROJECT_ID)


class SearchRequest(BaseModel):
    """Search request model"""
    description: str
    category: Optional[str] = None
    capabilities: Optional[List[str]] = None
    min_similarity: float = 0.5  # Minimum similarity threshold


class AgentMatch(BaseModel):
    """Agent match result"""
    agent_name: str
    similarity_score: float
    match_reason: str
    agent_metadata: Dict[str, Any]


@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "matchmaking-search"}


@app.post("/search")
@Guardrails.validate_input()
@Guardrails.validate_output()
@monitoring.track_invocation()
async def search_similar_agents(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for similar existing agents
    
    Returns:
        List of matching agents with similarity scores
    """
    try:
        search_req = SearchRequest(**request)
        
        # Get all active agents from registry
        all_agents = registry.list_agents(status='active')
        
        if not all_agents:
            return {
                "matches": [],
                "message": "No active agents found in registry"
            }
        
        # Filter by category if provided
        if search_req.category:
            candidates = [
                a for a in all_agents
                if a.get('metadata', {}).get('category') == search_req.category
            ]
        else:
            candidates = all_agents
        
        if not candidates:
            return {
                "matches": [],
                "message": f"No agents found in category: {search_req.category}"
            }
        
        # Calculate similarity scores
        matches = calculate_similarity(search_req.description, candidates)
        
        # Filter by minimum similarity
        matches = [m for m in matches if m['similarity_score'] >= search_req.min_similarity]
        
        # Sort by similarity score
        matches.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Limit to top 10
        matches = matches[:10]
        
        # Add recommendations
        result = {
            "matches": matches,
            "total_matches": len(matches),
            "search_query": search_req.description,
            "recommendation": generate_recommendation(matches)
        }
        
        logger.info(f"Found {len(matches)} similar agents")
        
        return result
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def calculate_similarity(
    query_description: str, 
    candidate_agents: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Calculate similarity between query and existing agents
    
    Uses TF-IDF + cosine similarity
    """
    
    # Extract descriptions from candidates
    descriptions = []
    for agent in candidate_agents:
        desc = agent.get('metadata', {}).get('description', '')
        problem = agent.get('metadata', {}).get('problem_statement', '')
        # Combine description and problem statement
        full_text = f"{desc} {problem}"
        descriptions.append(full_text)
    
    if not descriptions:
        return []
    
    # Add query to corpus
    corpus = [query_description] + descriptions
    
    # Calculate TF-IDF vectors
    vectorizer = TfidfVectorizer(
        stop_words='english',
        max_features=1000,
        ngram_range=(1, 2)  # Use unigrams and bigrams
    )
    
    try:
        tfidf_matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        # Handle case where corpus is too small
        return []
    
    # Calculate cosine similarity between query and all candidates
    query_vector = tfidf_matrix[0:1]
    candidate_vectors = tfidf_matrix[1:]
    
    similarities = cosine_similarity(query_vector, candidate_vectors)[0]
    
    # Create match objects
    matches = []
    for i, similarity in enumerate(similarities):
        if similarity > 0:  # Only include non-zero matches
            agent = candidate_agents[i]
            matches.append({
                'agent_name': agent.get('metadata', {}).get('name', 'unknown'),
                'similarity_score': float(similarity),
                'match_reason': generate_match_reason(similarity, agent),
                'agent_metadata': {
                    'description': agent.get('metadata', {}).get('description', ''),
                    'category': agent.get('metadata', {}).get('category', ''),
                    'capabilities': agent.get('capabilities', []),
                    'deployment_target': agent.get('deployment', {}).get('target', ''),
                    'endpoint': agent.get('deployment', {}).get('endpoint', '')
                }
            })
    
    return matches


def generate_match_reason(similarity: float, agent: Dict[str, Any]) -> str:
    """Generate human-readable match reason"""
    
    agent_name = agent.get('metadata', {}).get('name', 'Unknown')
    
    if similarity >= 0.8:
        return f"Very similar to {agent_name} - likely duplicate functionality"
    elif similarity >= 0.6:
        return f"High similarity to {agent_name} - consider extending instead of building new"
    elif similarity >= 0.4:
        return f"Moderate similarity to {agent_name} - may share some components"
    else:
        return f"Some overlap with {agent_name} - could reuse patterns"


def generate_recommendation(matches: List[Dict[str, Any]]) -> str:
    """Generate recommendation based on matches"""
    
    if not matches:
        return "No similar agents found. This appears to be a unique request - proceed with new agent development."
    
    top_match = matches[0]
    similarity = top_match['similarity_score']
    agent_name = top_match['agent_name']
    
    if similarity >= 0.8:
        return f"⚠️ DUPLICATE DETECTED: Agent '{agent_name}' has {similarity*100:.0f}% similarity. Strongly recommend extending existing agent instead of creating new one."
    
    elif similarity >= 0.6:
        return f"🔍 HIGH SIMILARITY: Agent '{agent_name}' ({similarity*100:.0f}% match) likely has overlapping functionality. Recommend reviewing before proceeding. Consider: (1) Extend existing agent, (2) Reuse components, (3) Coordinate with owner."
    
    elif similarity >= 0.4:
        return f"📋 MODERATE OVERLAP: {len(matches)} existing agent(s) with related functionality. Review for potential component reuse, but new agent may be justified."
    
    else:
        return f"✅ LOW OVERLAP: Existing agents have limited similarity. New agent development appears justified."


@app.post("/find-reusable-components")
@monitoring.track_invocation()
async def find_reusable_components(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Find reusable components across existing agents
    
    This helps identify common patterns that could be extracted into shared libraries.
    """
    
    try:
        query = request.get('query', '')
        
        # Get all agents
        all_agents = registry.list_agents(status='active')
        
        # Group by common capabilities
        capability_groups = {}
        for agent in all_agents:
            capabilities = agent.get('capabilities', [])
            for cap in capabilities:
                if cap not in capability_groups:
                    capability_groups[cap] = []
                capability_groups[cap].append(agent.get('metadata', {}).get('name'))
        
        # Find capabilities with multiple agents (reusable patterns)
        reusable = {
            cap: agents 
            for cap, agents in capability_groups.items() 
            if len(agents) >= 2
        }
        
        # Recommend components to extract
        recommendations = []
        for cap, agents in reusable.items():
            recommendations.append({
                'capability': cap,
                'used_by_agents': agents,
                'usage_count': len(agents),
                'recommendation': f"Consider extracting '{cap}' as shared library - used by {len(agents)} agents"
            })
        
        recommendations.sort(key=lambda x: x['usage_count'], reverse=True)
        
        return {
            'reusable_components': recommendations,
            'total_capabilities': len(capability_groups),
            'reusable_count': len(reusable)
        }
        
    except Exception as e:
        logger.error(f"Component search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_name}/similar")
async def find_similar_to_agent(agent_name: str, limit: int = 5) -> Dict[str, Any]:
    """Find agents similar to a specific agent"""
    
    # Get target agent
    target_agent = registry.get_agent(agent_name)
    
    if not target_agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    
    # Use agent's description as query
    description = target_agent.get('metadata', {}).get('description', '')
    
    if not description:
        raise HTTPException(status_code=400, detail="Target agent has no description")
    
    # Search for similar agents
    result = await search_similar_agents({
        'description': description,
        'min_similarity': 0.3
    })
    
    # Remove the target agent itself from results
    matches = [m for m in result['matches'] if m['agent_name'] != agent_name]
    
    return {
        'target_agent': agent_name,
        'similar_agents': matches[:limit]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

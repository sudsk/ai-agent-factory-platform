"""
Prioritization Scorer Agent

Scores and ranks agent requests based on multiple criteria.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import numpy as np
from datetime import datetime

import sys
sys.path.append('/app')
from agent_factory_sdk import AgentRegistry, Guardrails, AgentMonitoring, MetricsCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Prioritization Scorer Agent")

PROJECT_ID = "your-project-id"
registry = AgentRegistry(project_id=PROJECT_ID)
monitoring = AgentMonitoring(project_id=PROJECT_ID, agent_name="prioritization-scorer")
metrics = MetricsCollector(project_id=PROJECT_ID, agent_name="prioritization-scorer")

Guardrails.init(PROJECT_ID)


class ScoringRequest(BaseModel):
    """Request model for prioritization scoring"""
    business_unit: str
    agent_category: str
    problem_statement: str
    expected_outcomes: str
    estimated_impact: str  # high, medium, low
    urgency: str  # critical, high, medium, low
    timeline: Optional[str] = None
    resource_requirements: Optional[str] = None
    strategic_alignment: Optional[int] = None  # 1-10
    technical_feasibility: Optional[int] = None  # 1-10
    estimated_cost: Optional[float] = None
    estimated_savings: Optional[float] = None


class PrioritizationScore(BaseModel):
    """Prioritization score output"""
    overall_score: float
    priority_level: str
    component_scores: Dict[str, float]
    recommendation: str
    reasoning: List[str]


@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "prioritization-scorer"}


@app.post("/score")
@Guardrails.validate_input()
@Guardrails.validate_output()
@monitoring.track_invocation()
async def score_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate prioritization score for an agent request
    
    Scoring criteria:
    1. ROI (30%) - Cost savings vs cost
    2. Strategic alignment (25%) - How well it aligns with strategy
    3. Urgency (20%) - Time sensitivity
    4. Technical feasibility (15%) - How easy to implement
    5. Risk/compliance (10%) - Regulatory requirements
    """
    try:
        scoring_req = ScoringRequest(**request)
        
        # Calculate component scores
        roi_score = calculate_roi_score(scoring_req)
        strategic_score = calculate_strategic_score(scoring_req)
        urgency_score = calculate_urgency_score(scoring_req)
        feasibility_score = calculate_feasibility_score(scoring_req)
        risk_score = calculate_risk_score(scoring_req)
        
        # Weighted average
        weights = {
            'roi': 0.30,
            'strategic': 0.25,
            'urgency': 0.20,
            'feasibility': 0.15,
            'risk': 0.10
        }
        
        component_scores = {
            'roi': roi_score,
            'strategic_alignment': strategic_score,
            'urgency': urgency_score,
            'technical_feasibility': feasibility_score,
            'risk_compliance': risk_score
        }
        
        overall_score = (
            roi_score * weights['roi'] +
            strategic_score * weights['strategic'] +
            urgency_score * weights['urgency'] +
            feasibility_score * weights['feasibility'] +
            risk_score * weights['risk']
        )
        
        # Normalize to 0-100
        overall_score = overall_score * 10
        
        # Determine priority level
        if overall_score >= 80:
            priority_level = "CRITICAL"
        elif overall_score >= 65:
            priority_level = "HIGH"
        elif overall_score >= 45:
            priority_level = "MEDIUM"
        else:
            priority_level = "LOW"
        
        # Generate reasoning
        reasoning = generate_reasoning(component_scores, priority_level)
        
        # Generate recommendation
        recommendation = generate_recommendation(
            priority_level, 
            overall_score,
            scoring_req
        )
        
        # Record metrics
        metrics.record_metric("prioritization_score", overall_score)
        metrics.increment_counter("requests_scored", {"priority": priority_level})
        
        result = {
            "overall_score": round(overall_score, 2),
            "priority_level": priority_level,
            "component_scores": {k: round(v, 2) for k, v in component_scores.items()},
            "recommendation": recommendation,
            "reasoning": reasoning,
            "scored_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Scored request: {priority_level} ({overall_score:.2f})")
        
        return result
        
    except Exception as e:
        logger.error(f"Scoring failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def calculate_roi_score(req: ScoringRequest) -> float:
    """Calculate ROI score (0-10)"""
    
    # If costs provided, calculate ROI
    if req.estimated_cost and req.estimated_savings:
        if req.estimated_cost > 0:
            roi = (req.estimated_savings - req.estimated_cost) / req.estimated_cost
            # Map ROI to 0-10 scale
            # ROI > 5x = 10, ROI = 1x = 5, ROI < 0 = 0
            score = min(10, max(0, 5 + roi))
            return score
    
    # Otherwise use impact estimate
    impact_map = {
        'high': 9.0,
        'medium': 6.0,
        'low': 3.0
    }
    
    return impact_map.get(req.estimated_impact.lower(), 5.0)


def calculate_strategic_score(req: ScoringRequest) -> float:
    """Calculate strategic alignment score (0-10)"""
    
    if req.strategic_alignment:
        return float(req.strategic_alignment)
    
    # Default scoring by category
    category_scores = {
        'financial': 8.0,  # High strategic value
        'compliance': 9.0,  # Critical
        'it-ops': 6.0,
        'customer-ops': 7.0,
        'data-analytics': 6.0
    }
    
    return category_scores.get(req.agent_category.lower(), 5.0)


def calculate_urgency_score(req: ScoringRequest) -> float:
    """Calculate urgency score (0-10)"""
    
    urgency_map = {
        'critical': 10.0,
        'high': 8.0,
        'medium': 5.0,
        'low': 2.0
    }
    
    return urgency_map.get(req.urgency.lower(), 5.0)


def calculate_feasibility_score(req: ScoringRequest) -> float:
    """Calculate technical feasibility score (0-10)"""
    
    if req.technical_feasibility:
        return float(req.technical_feasibility)
    
    # Estimate based on resource requirements
    if req.resource_requirements:
        resource_lower = req.resource_requirements.lower()
        if 'complex' in resource_lower or 'extensive' in resource_lower:
            return 4.0
        elif 'moderate' in resource_lower:
            return 6.0
        elif 'simple' in resource_lower or 'minimal' in resource_lower:
            return 9.0
    
    return 6.0  # Default moderate feasibility


def calculate_risk_score(req: ScoringRequest) -> float:
    """Calculate risk/compliance score (0-10)"""
    
    # Higher score = lower risk
    problem = req.problem_statement.lower()
    
    # High risk indicators
    if any(term in problem for term in ['compliance', 'regulatory', 'audit', 'gdpr', 'sox']):
        return 9.0  # High importance due to compliance
    
    # Medium risk
    if any(term in problem for term in ['security', 'privacy', 'risk']):
        return 7.0
    
    # Low risk
    return 5.0


def generate_reasoning(component_scores: Dict[str, float], priority: str) -> List[str]:
    """Generate human-readable reasoning for the score"""
    
    reasoning = []
    
    # ROI reasoning
    roi = component_scores['roi']
    if roi >= 8:
        reasoning.append("Strong ROI potential with high expected value")
    elif roi >= 5:
        reasoning.append("Moderate ROI with positive impact expected")
    else:
        reasoning.append("Lower ROI - consider cost optimization")
    
    # Strategic reasoning
    strategic = component_scores['strategic_alignment']
    if strategic >= 8:
        reasoning.append("Strongly aligned with strategic priorities")
    elif strategic >= 5:
        reasoning.append("Moderate strategic alignment")
    else:
        reasoning.append("Limited strategic alignment - may defer")
    
    # Urgency reasoning
    urgency = component_scores['urgency']
    if urgency >= 8:
        reasoning.append("Time-sensitive request requiring immediate attention")
    elif urgency >= 5:
        reasoning.append("Moderate urgency - schedule within current quarter")
    else:
        reasoning.append("Lower urgency - can be scheduled for future sprint")
    
    # Feasibility reasoning
    feasibility = component_scores['technical_feasibility']
    if feasibility >= 8:
        reasoning.append("Highly feasible with existing capabilities")
    elif feasibility >= 5:
        reasoning.append("Moderate complexity - requires planning")
    else:
        reasoning.append("High complexity - significant resources needed")
    
    return reasoning


def generate_recommendation(
    priority: str, 
    score: float, 
    req: ScoringRequest
) -> str:
    """Generate actionable recommendation"""
    
    if priority == "CRITICAL":
        return f"IMMEDIATE ACTION: Fast-track this request for next sprint. Score: {score:.1f}/100. High strategic value and urgency."
    
    elif priority == "HIGH":
        return f"HIGH PRIORITY: Schedule for current quarter. Score: {score:.1f}/100. Strong business case with good feasibility."
    
    elif priority == "MEDIUM":
        return f"STANDARD PRIORITY: Add to backlog for next quarter. Score: {score:.1f}/100. Solid value but not urgent."
    
    else:
        return f"LOW PRIORITY: Consider for future roadmap. Score: {score:.1f}/100. May want to refine requirements or defer."


@app.post("/batch-score")
@monitoring.track_invocation()
async def batch_score(requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Score multiple requests and rank them"""
    
    scored_requests = []
    
    for req in requests:
        try:
            score_result = await score_request(req)
            scored_requests.append({
                "request": req,
                "score": score_result
            })
        except Exception as e:
            logger.error(f"Failed to score request: {e}")
            scored_requests.append({
                "request": req,
                "score": None,
                "error": str(e)
            })
    
    # Sort by score
    scored_requests.sort(
        key=lambda x: x['score']['overall_score'] if x['score'] else 0,
        reverse=True
    )
    
    return {
        "total_requests": len(requests),
        "scored_successfully": len([r for r in scored_requests if r['score']]),
        "ranked_requests": scored_requests
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

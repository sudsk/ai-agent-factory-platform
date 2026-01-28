"""
Requirements Refiner Agent

Asks intelligent follow-up questions and refines requirements.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import vertexai
from vertexai.generative_models import GenerativeModel
import json

import sys
sys.path.append('/app')
from agent_factory_sdk import AgentRegistry, Guardrails, AgentMonitoring

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Requirements Refiner Agent")

PROJECT_ID = "your-project-id"
vertexai.init(project=PROJECT_ID, location="us-central1")
model = GenerativeModel("gemini-2.0-flash-exp")

registry = AgentRegistry(project_id=PROJECT_ID)
monitoring = AgentMonitoring(project_id=PROJECT_ID, agent_name="requirements-refiner")

Guardrails.init(PROJECT_ID)


class RefineRequest(BaseModel):
    """Requirements refinement request"""
    problem_statement: str
    expected_outcomes: Optional[str] = None
    business_unit: Optional[str] = None
    agent_category: Optional[str] = None
    data_sources: Optional[List[str]] = None
    constraints: Optional[List[str]] = None


@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "requirements-refiner"}


@app.post("/refine")
@Guardrails.validate_input()
@Guardrails.validate_output()
@monitoring.track_invocation()
async def refine_requirements(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Refine requirements by identifying gaps and asking clarifying questions
    
    Returns:
        - Missing information
        - Ambiguities
        - Follow-up questions
        - Refined requirements
    """
    try:
        refine_req = RefineRequest(**request)
        
        # Analyze requirements for gaps
        gaps = identify_gaps(refine_req)
        
        # Identify ambiguities
        ambiguities = identify_ambiguities(refine_req)
        
        # Generate follow-up questions
        questions = await generate_questions(refine_req, gaps, ambiguities)
        
        # Suggest implementation patterns
        patterns = suggest_patterns(refine_req)
        
        # Create user story template
        user_story = create_user_story(refine_req)
        
        result = {
            "analysis": {
                "completeness_score": calculate_completeness(refine_req),
                "clarity_score": calculate_clarity(refine_req),
                "gaps_identified": gaps,
                "ambiguities_found": ambiguities
            },
            "follow_up_questions": questions,
            "suggested_patterns": patterns,
            "user_story_template": user_story,
            "next_steps": generate_next_steps(gaps, ambiguities)
        }
        
        logger.info(f"Refined requirements with {len(questions)} follow-up questions")
        
        return result
        
    except Exception as e:
        logger.error(f"Requirements refinement failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def identify_gaps(req: RefineRequest) -> List[Dict[str, str]]:
    """Identify missing critical information"""
    
    gaps = []
    
    # Check for specific requirements
    if not req.expected_outcomes:
        gaps.append({
            "category": "outcomes",
            "description": "Expected outcomes not specified",
            "impact": "high",
            "question": "What specific, measurable outcomes are expected from this agent?"
        })
    
    if not req.data_sources:
        gaps.append({
            "category": "data",
            "description": "Data sources not identified",
            "impact": "high",
            "question": "What data sources will this agent need to access?"
        })
    
    if not req.business_unit:
        gaps.append({
            "category": "ownership",
            "description": "Business unit not specified",
            "impact": "medium",
            "question": "Which business unit will own and maintain this agent?"
        })
    
    # Check problem statement completeness
    problem_lower = req.problem_statement.lower()
    
    if len(req.problem_statement.split()) < 10:
        gaps.append({
            "category": "problem_definition",
            "description": "Problem statement is too brief",
            "impact": "high",
            "question": "Can you provide more details about the problem, including who is affected and current workarounds?"
        })
    
    # Check for success criteria
    if 'success' not in problem_lower and 'metric' not in problem_lower:
        gaps.append({
            "category": "success_criteria",
            "description": "Success metrics not defined",
            "impact": "medium",
            "question": "How will you measure the success of this agent? What are the key metrics?"
        })
    
    # Check for user personas
    if 'user' not in problem_lower and 'customer' not in problem_lower:
        gaps.append({
            "category": "users",
            "description": "Target users not clearly identified",
            "impact": "medium",
            "question": "Who are the primary users of this agent? What are their roles and needs?"
        })
    
    return gaps


def identify_ambiguities(req: RefineRequest) -> List[Dict[str, str]]:
    """Identify ambiguous or unclear statements"""
    
    ambiguities = []
    
    problem = req.problem_statement.lower()
    
    # Check for vague terms
    vague_terms = ['better', 'faster', 'easier', 'improve', 'optimize', 'enhance', 'automate']
    found_vague = [term for term in vague_terms if term in problem]
    
    if found_vague:
        ambiguities.append({
            "type": "vague_goals",
            "terms": found_vague,
            "description": f"Terms like '{', '.join(found_vague)}' are subjective and need quantification",
            "clarification_needed": f"Please specify: how much {found_vague[0]}? By what measure?"
        })
    
    # Check for undefined scope
    if any(term in problem for term in ['all', 'every', 'complete', 'entire']):
        ambiguities.append({
            "type": "scope_creep",
            "description": "Scope may be too broad",
            "clarification_needed": "Consider defining MVP scope first. What's the minimum viable version?"
        })
    
    # Check for missing constraints
    if req.constraints is None or len(req.constraints) == 0:
        ambiguities.append({
            "type": "constraints",
            "description": "No constraints specified",
            "clarification_needed": "Are there any technical, budget, or timeline constraints?"
        })
    
    return ambiguities


async def generate_questions(
    req: RefineRequest, 
    gaps: List[Dict], 
    ambiguities: List[Dict]
) -> List[Dict[str, str]]:
    """Generate intelligent follow-up questions using LLM"""
    
    prompt = f"""
You are a requirements analyst helping refine an AI agent request.

Problem Statement: {req.problem_statement}
Expected Outcomes: {req.expected_outcomes or 'Not specified'}
Business Unit: {req.business_unit or 'Not specified'}
Category: {req.agent_category or 'Not specified'}

Identified Gaps:
{json.dumps(gaps, indent=2)}

Identified Ambiguities:
{json.dumps(ambiguities, indent=2)}

Generate 5-7 specific, actionable follow-up questions that would help clarify these requirements. 
Focus on:
1. Quantifying vague statements
2. Identifying edge cases
3. Understanding integration points
4. Clarifying success criteria
5. Understanding user workflows

Return ONLY a JSON array of questions, each with "question", "category", and "priority" (high/medium/low).
Format: [{"question": "...", "category": "...", "priority": "..."}]
"""
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean response
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        questions = json.loads(response_text)
        return questions
        
    except Exception as e:
        logger.error(f"Failed to generate questions: {e}")
        # Fallback to gap-based questions
        return [
            {
                "question": gap["question"],
                "category": gap["category"],
                "priority": gap["impact"]
            }
            for gap in gaps
        ]


def suggest_patterns(req: RefineRequest) -> List[Dict[str, str]]:
    """Suggest implementation patterns based on requirements"""
    
    patterns = []
    
    problem = req.problem_statement.lower()
    category = (req.agent_category or '').lower()
    
    # Pattern matching
    if any(term in problem for term in ['analyze', 'report', 'insight', 'trend']):
        patterns.append({
            "pattern": "Data Analysis Agent",
            "description": "Query data sources, perform analysis, generate insights",
            "example_agents": ["sales-analytics-agent", "performance-dashboard-agent"],
            "estimated_complexity": "medium"
        })
    
    if any(term in problem for term in ['automate', 'process', 'workflow', 'task']):
        patterns.append({
            "pattern": "Workflow Automation Agent",
            "description": "Orchestrate multi-step processes, handle approvals, integrate systems",
            "example_agents": ["expense-approval-agent", "onboarding-automation-agent"],
            "estimated_complexity": "high"
        })
    
    if any(term in problem for term in ['recommend', 'suggest', 'predict']):
        patterns.append({
            "pattern": "Recommendation Agent",
            "description": "Analyze patterns, make predictions, provide recommendations",
            "example_agents": ["product-recommendation-agent", "risk-prediction-agent"],
            "estimated_complexity": "medium-high"
        })
    
    if 'compliance' in category or any(term in problem for term in ['compliance', 'audit', 'risk']):
        patterns.append({
            "pattern": "Compliance Monitoring Agent",
            "description": "Check against policies, flag violations, generate audit reports",
            "example_agents": ["gdpr-compliance-agent", "soc2-audit-agent"],
            "estimated_complexity": "high"
        })
    
    if any(term in problem for term in ['answer', 'question', 'help', 'support']):
        patterns.append({
            "pattern": "Conversational Assistant Agent",
            "description": "Natural language interface, FAQ handling, guided workflows",
            "example_agents": ["hr-helpdesk-agent", "it-support-agent"],
            "estimated_complexity": "medium"
        })
    
    return patterns


def create_user_story(req: RefineRequest) -> Dict[str, str]:
    """Create user story template"""
    
    # Extract or infer persona
    problem = req.problem_statement
    
    # Try to identify persona from problem statement
    persona = "a business user"
    if "analyst" in problem.lower():
        persona = "a data analyst"
    elif "manager" in problem.lower():
        persona = "a manager"
    elif "developer" in problem.lower():
        persona = "a developer"
    
    user_story = {
        "format": "As a [persona], I want [action], so that [benefit]",
        "filled": f"As {persona}, I want {req.problem_statement[:100]}, so that {req.expected_outcomes or '[benefit to be defined]'}",
        "acceptance_criteria": [
            "Given [context]",
            "When [action]",
            "Then [expected outcome]"
        ],
        "definition_of_done": [
            "Functionality works as specified",
            "Unit tests pass",
            "Integration tests pass",
            "Documentation updated",
            "Deployed to production",
            "Monitoring in place"
        ]
    }
    
    return user_story


def calculate_completeness(req: RefineRequest) -> float:
    """Calculate requirements completeness score (0-100)"""
    
    score = 0
    total_criteria = 10
    
    if req.problem_statement and len(req.problem_statement) >= 50:
        score += 2
    if req.expected_outcomes:
        score += 2
    if req.business_unit:
        score += 1
    if req.agent_category:
        score += 1
    if req.data_sources and len(req.data_sources) > 0:
        score += 2
    if req.constraints and len(req.constraints) > 0:
        score += 1
    
    # Check for specific details in problem statement
    problem_lower = req.problem_statement.lower()
    if any(word in problem_lower for word in ['metric', 'measure', 'kpi']):
        score += 0.5
    if any(word in problem_lower for word in ['user', 'customer', 'stakeholder']):
        score += 0.5
    
    return (score / total_criteria) * 100


def calculate_clarity(req: RefineRequest) -> float:
    """Calculate requirements clarity score (0-100)"""
    
    score = 100
    
    problem_lower = req.problem_statement.lower()
    
    # Deduct for vague terms
    vague_terms = ['better', 'faster', 'easier', 'improve', 'optimize', 'enhance']
    vague_count = sum(1 for term in vague_terms if term in problem_lower)
    score -= (vague_count * 10)
    
    # Deduct for very short description
    if len(req.problem_statement.split()) < 15:
        score -= 20
    
    # Deduct for missing specifics
    if not any(word in problem_lower for word in ['metric', 'measure', 'kpi', 'goal']):
        score -= 15
    
    return max(0, score)


def generate_next_steps(gaps: List[Dict], ambiguities: List[Dict]) -> List[str]:
    """Generate recommended next steps"""
    
    next_steps = []
    
    high_priority_gaps = [g for g in gaps if g.get('impact') == 'high']
    
    if high_priority_gaps:
        next_steps.append(f"CRITICAL: Address {len(high_priority_gaps)} high-priority information gaps before proceeding")
    
    if ambiguities:
        next_steps.append(f"Clarify {len(ambiguities)} ambiguous requirements to avoid scope creep")
    
    next_steps.extend([
        "Schedule requirements review meeting with stakeholders",
        "Create detailed user stories with acceptance criteria",
        "Identify data sources and access requirements",
        "Define success metrics and monitoring approach",
        "Estimate timeline and resource requirements"
    ])
    
    return next_steps


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

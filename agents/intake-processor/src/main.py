"""
Intake Processor Agent

Processes and validates agent intake requests.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import vertexai
from vertexai.generative_models import GenerativeModel
import logging
import json

# Add parent directory to path for SDK import
import sys
sys.path.append('/app')

from agent_factory_sdk import AgentRegistry, Guardrails, AgentMonitoring

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Intake Processor Agent")

# Initialize
PROJECT_ID = "your-project-id"  # Set from environment
vertexai.init(project=PROJECT_ID, location="us-central1")
model = GenerativeModel("gemini-2.0-flash-exp")

registry = AgentRegistry(project_id=PROJECT_ID)
monitoring = AgentMonitoring(project_id=PROJECT_ID, agent_name="intake-processor")

# Initialize guardrails
Guardrails.init(PROJECT_ID)


class IntakeRequest(BaseModel):
    """Intake request model"""
    business_unit: Optional[str] = None
    agent_category: Optional[str] = None
    problem_statement: Optional[str] = None
    expected_outcomes: Optional[str] = None
    estimated_impact: Optional[str] = None
    urgency: Optional[str] = None
    timeline: Optional[str] = None
    data_sources: Optional[List[str]] = None
    compliance_requirements: Optional[List[str]] = None


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "agent": "intake-processor"}


@app.post("/process")
@Guardrails.validate_input(check_prompt_injection=True, check_pii=True, redact_pii=True)
@Guardrails.validate_output(check_pii=True, redact_pii=True)
@monitoring.track_invocation()
async def process_intake(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process intake request
    
    Steps:
    1. Extract structured data
    2. Validate completeness
    3. Check for duplicates
    4. Return processed request
    """
    try:
        # Step 1: Extract structured data if raw text provided
        if isinstance(request.get('raw_text'), str):
            structured = await extract_structured_data(request['raw_text'])
        else:
            structured = IntakeRequest(**request).dict()
        
        # Step 2: Validate
        validation = validate_request(structured)
        
        if not validation['is_valid']:
            return {
                "status": "invalid",
                "errors": validation['errors'],
                "request": structured
            }
        
        # Step 3: Check for similar agents (call matchmaking agent)
        try:
            similar_agents = registry.invoke_agent(
                agent_name="matchmaking-search",
                input_data={
                    "description": structured.get('problem_statement', ''),
                    "category": structured.get('agent_category', '')
                },
                timeout=10
            )
        except Exception as e:
            logger.warning(f"Matchmaking agent unavailable: {e}")
            similar_agents = {"matches": []}
        
        # Return processed request
        return {
            "status": "processed",
            "structured_request": structured,
            "validation": validation,
            "similar_agents": similar_agents.get('matches', []),
            "next_steps": [
                "Review similar agents to avoid duplication",
                "Proceed to prioritization if no duplicates",
                "Refine requirements if validation issues"
            ]
        }
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def extract_structured_data(raw_text: str) -> Dict[str, Any]:
    """Extract structured data from raw text using LLM"""
    
    prompt = f"""
Extract structured information from this agent request and return ONLY valid JSON (no markdown, no backticks):

{raw_text}

Return JSON with these fields:
- business_unit: string
- agent_category: string (one of: financial, it-ops, compliance, customer-ops, data-analytics)
- problem_statement: string (clear description)
- expected_outcomes: string
- estimated_impact: string (high/medium/low)
- urgency: string (critical/high/medium/low)
- timeline: string
- data_sources: array of strings
- compliance_requirements: array of strings

Return ONLY the JSON object, nothing else.
"""
    
    response = model.generate_content(prompt)
    response_text = response.text.strip()
    
    # Remove markdown code blocks if present
    if response_text.startswith('```'):
        response_text = response_text.split('```')[1]
        if response_text.startswith('json'):
            response_text = response_text[4:]
        response_text = response_text.strip()
    
    try:
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response: {response_text}")
        raise ValueError(f"Failed to extract structured data: {e}")


def validate_request(structured: Dict[str, Any]) -> Dict[str, Any]:
    """Validate required fields"""
    
    required_fields = [
        'business_unit',
        'agent_category',
        'problem_statement',
        'expected_outcomes',
        'urgency'
    ]
    
    missing = [f for f in required_fields if not structured.get(f)]
    
    warnings = []
    
    # Check optional but recommended fields
    if not structured.get('estimated_impact'):
        warnings.append("estimated_impact not provided")
    if not structured.get('data_sources'):
        warnings.append("data_sources not specified")
    
    return {
        "is_valid": len(missing) == 0,
        "errors": missing,
        "warnings": warnings
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)